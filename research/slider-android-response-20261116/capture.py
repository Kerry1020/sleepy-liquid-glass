#!/usr/bin/env python3
"""Run the external frozen fixture; retain failed evidence and device originals."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT.parents[1]
ROUNDS = ('control-pre', 'global-G', 'mask-G', 'control-post')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(argv, **kwargs):
    return subprocess.run([str(x) for x in argv], capture_output=True, text=True, check=True, **kwargs).stdout.strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--host', type=Path, required=True)
    ap.add_argument('--adb', type=Path, required=True)
    ap.add_argument('--serial', required=True)
    ap.add_argument('--round', choices=ROUNDS, required=True)
    ap.add_argument('--tag', default='android-r2')
    args = ap.parse_args()
    assert re.fullmatch(r'[A-Za-z0-9-]+', args.tag)
    freeze_path = ROOT / 'FREEZE.json'
    freeze = json.loads(freeze_path.read_text())
    for rel, expected in freeze['files'].items():
        assert sha(ROOT / rel) == expected, f'Frozen asset changed: {rel}'
    for rel, expected in freeze['host_files'].items():
        assert sha(args.host / rel) == expected, f'Host source/APK changed: {rel}'
    assert run(['git', '-C', args.host, 'rev-parse', 'HEAD']) == freeze['host_commit']
    assert not run(['git', '-C', args.host, 'status', '--porcelain']), 'Host must stay clean'
    out = ROOT / 'evidence/rounds' / args.round / args.tag
    out.mkdir(parents=True, exist_ok=False)
    adb = [args.adb, '-s', args.serial]
    def device(*argv):
        return run([*adb, *argv])
    source = ASSETS / 'research/slider-color-response-20261116/inputs/rounds' / args.round
    spec = ROOT / 'derived' / args.round / 'shape-spec.json'
    manifest_path = source / 'inputs/manifest.json'
    manifest = json.loads(manifest_path.read_text())
    run_id = f'g-response-{args.round}-{args.tag}-{sha(spec)[:12]}-20261116'
    remote_name = f'slider-S-{args.round}'
    remote_input = '/sdcard/Android/data/com.lingion.sleepy.debug/files/' + remote_name
    remote_result = '/sdcard/Android/data/com.lingion.sleepy.debug/files/slider-optical-world/' + run_id
    receipt = {'schema': 1, 'started_unix': time.time(), 'serial': args.serial,
               'run': run_id, 'round': args.round, 'tag': args.tag,
               'freeze_sha256': sha(freeze_path), 'host_commit': freeze['host_commit'],
               'collector_sha256': sha(Path(__file__)), 'input_role': 'calibration',
               'build_receipt_sha256': sha(ASSETS / 'research/slider-android-host/host-build-20261116.json'),
               'sources': {p: h for p, h in freeze['host_files'].items() if '/build/' not in p},
               'build': {'host_commit': freeze['host_commit'], 'apks': freeze['apks'],
                         'build_receipt_sha256': sha(ASSETS / 'research/slider-android-host/host-build-20261116.json')},
               'display_before': {k: device('shell', 'wm', k) for k in ('size', 'density')},
               'input_sha256': {}, 'files': [], 'test_passed': False}
    def save():
        (out / 'receipt.json').write_text(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
    save()
    pulled = False
    def preserve_remote():
        nonlocal pulled
        if pulled:
            return
        receipt['pull_output'] = device('pull', remote_result, out / 'trace')
        pulled = True
        hashes = device('shell', 'find', remote_result, '-type', 'f', '-exec', 'sha256sum', '{}', '+')
        remote_hashes = dict((line.split(None, 1)[1].strip(), line.split()[0]) for line in hashes.splitlines())
        for file in sorted((out / 'trace').rglob('*')):
            if file.is_file():
                rel = file.relative_to(out / 'trace')
                expected = remote_hashes[remote_result + '/' + str(rel)]
                assert sha(file) == expected, f'Host/device mismatch: {rel}'
                receipt['files'].append({'file': str(file.relative_to(out)), 'sha256': expected, 'host_device_match': True})
    try:
        probe = subprocess.run([str(x) for x in [*adb, 'shell', 'test', '-e', remote_result]], capture_output=True, text=True)
        assert probe.returncode == 1, 'Result exists or absence was not verified'
        receipt['packages'] = []
        for apk in freeze['apks']:
            path = device('shell', 'pm', 'path', apk['application_id']).splitlines()
            assert len(path) == 1 and path[0].startswith('package:')
            remote_apk = path[0][8:]
            actual = device('shell', 'sha256sum', remote_apk).split()[0]
            assert actual == apk['sha256'], 'Installed APK differs from frozen build'
            receipt['packages'].append({'application_id': apk['application_id'], 'path': remote_apk,
                                        'sha256': actual, 'matches_frozen_build': True})
        device('shell', 'mkdir', '-p', remote_input)
        for file, key in [(spec, 'shape-spec.json'), (manifest_path, 'inputs/manifest.json'),
                          *[(manifest_path.parent / row['file'], 'inputs/' + row['file']) for row in manifest['inputs']]]:
            device('push', file, remote_input + '/' + file.name)
            assert device('shell', 'sha256sum', remote_input + '/' + file.name).split()[0] == sha(file)
            receipt['input_sha256'][key] = sha(file)
        argv = [*adb, 'shell', 'am', 'instrument', '-w', '-r', '-e', 'class',
                'com.lingion.sleepy.ui.component.AssetNativeSliderOpticalWorldRenderTest#captureNativeSliderOpticalWorld',
                '-e', 'glassSliderFixedShapeCoverage', 'true', '-e', 'glassSliderOpticalRunId', run_id,
                '-e', 'glassSliderOpticalExternalInputsDirectory', remote_name,
                '-e', 'glassSliderOpticalInputRole', 'calibration', '-e', 'glassSliderOpticalThemes', 'light',
                'com.lingion.sleepy.debug.test/com.lingion.sleepy.SleepyRenderTestRunner']
        receipt['argv'] = [str(x) for x in argv]
        save()
        try:
            process = subprocess.run(receipt['argv'], capture_output=True, text=True, timeout=240)
        except subprocess.TimeoutExpired as error:
            def decoded(value):
                return value.decode(errors='replace') if isinstance(value, bytes) else value or ''
            (out / 'instrumentation.txt').write_text(decoded(error.stdout) + decoded(error.stderr))
            receipt['instrumentation_timeout_seconds'] = 240
            raise
        (out / 'instrumentation.txt').write_text(process.stdout + process.stderr)
        receipt['exit_code'] = process.returncode
        receipt['test_passed'] = process.returncode == 0 and 'OK (1 test)' in process.stdout
        preserve_remote()
        assert len(receipt['files']) == 49, 'Expected49 original files'
        assert receipt['test_passed'], 'Instrumentation failed; keep evidence'
    except BaseException as error:
        receipt['error'] = repr(error)
        raise
    finally:
        if not pulled:
            try:
                preserve_remote()
            except BaseException as error:
                receipt['partial_evidence_recovery_error'] = repr(error)
        try:
            receipt['display_after'] = {k: device('shell', 'wm', k) for k in ('size', 'density')}
        except BaseException as error:
            receipt['display_after_error'] = repr(error)
        receipt['finished_unix'] = time.time()
        save()
    assert receipt['display_after'] == receipt['display_before'], 'Device display changed'
    indexer = ASSETS / 'docs/design/evidence/glass-slider-star-20261115/frozen-calibration-tools/index-android-shape-captures.py'
    print(run(['python3', indexer, '--result', out / 'trace/result.json', '--spec', spec, '--out', out / 'index.json']))
    print(json.dumps({'round': args.round, 'output': str(out), 'test_passed': True, 'files': len(receipt['files'])}), flush=True)


if __name__ == '__main__':
    main()
