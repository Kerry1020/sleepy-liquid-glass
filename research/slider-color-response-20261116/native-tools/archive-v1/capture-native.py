#!/usr/bin/env python3
"""Bounded full100 native captures, with unchanged original RGB star and flat."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import plistlib
import re
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT / '.local/native-project'
DERIVED = ROOT / '.local/DerivedData'
ROUNDS = ['control-pre', 'global-R', 'global-G', 'global-B',
          'mask-R', 'mask-G', 'mask-B', 'control-post']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prepared_native_files():
    mapping = json.loads((ROOT.parent / 'slider-fixtures/SOURCE-MAP.json').read_text())
    paths = [Path(row['export_path']).relative_to('tools/native-glass-reference')
             for row in mapping['files']
             if row['export_path'].startswith('tools/native-glass-reference/')]
    assert len(paths) == 17
    return {str(p): sha(PROJECT / p) for p in paths}


def native_binaries():
    products = DERIVED / 'Build/Products/Debug-iphonesimulator'
    bundles = [products / 'GlassNativeReference.app',
               products / 'GlassNativeReferenceUITests-Runner.app']
    tests = list(bundles[1].glob('PlugIns/*.xctest'))
    assert len(tests) == 1, 'Exactly one actual XCTest executable required'
    paths = set()
    for bundle in bundles + tests:
        info = plistlib.loads((bundle / 'Info.plist').read_bytes())
        assert (bundle / info['CFBundleExecutable']).is_file()
        # Debug builds place real App code in .debug.dylib. Bind every product
        # file, including dylibs, plug-ins, resources and signing metadata.
        paths.update(p for p in bundle.rglob('*') if p.is_file())
    configurations = list((DERIVED / 'Build/Products').glob('*.xctestrun'))
    assert len(configurations) == 1
    paths.update(configurations)
    return {str(p.relative_to(DERIVED)): sha(p) for p in sorted(paths)}


def simulator_identity(udid):
    devices = json.loads(subprocess.check_output(['xcrun', 'simctl', 'list', 'devices', '-j']))['devices']
    matches = [(runtime, d) for runtime, rows in devices.items() for d in rows if d['udid'] == udid]
    assert len(matches) == 1 and matches[0][1]['state'] == 'Booted'
    runtime = matches[0][0]
    runtimes = json.loads(subprocess.check_output(['xcrun', 'simctl', 'list', 'runtimes', '-j']))['runtimes']
    metadata = next(r for r in runtimes if r['identifier'] == runtime)
    assert metadata['version'] == '26.5' and metadata['buildversion'] == '23F77'
    return {'udid': udid, 'runtime': runtime, 'build': metadata['buildversion']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['build', 'capture'])
    parser.add_argument('--simulator', required=True)
    parser.add_argument('--round', choices=ROUNDS)
    parser.add_argument('--attempt', default='r1')
    args = parser.parse_args()
    assert re.fullmatch(r'[a-zA-Z0-9-]+', args.attempt)
    assert PROJECT.is_dir()
    if args.phase == 'build':
        output = ROOT / '.local' / ('build-' + args.attempt)
    else:
        assert args.round, '--round is required for capture'
        freeze = json.loads((ROOT / 'freeze.json').read_text())
        for relative, expected in freeze['files'].items():
            assert sha(ROOT / relative) == expected, relative
        assert prepared_native_files() == freeze['prepared_native_files'], 'Native source changed after freeze'
        assert native_binaries() == freeze['native_binaries'], 'Native executable/configuration changed after freeze'
        assert simulator_identity(args.simulator) == freeze['simulator'], 'Simulator identity changed'
        output = ROOT / 'rounds' / args.round / ('native-' + args.attempt)
    output.mkdir(parents=True, exist_ok=False)
    receipt = {'started_unix': time.time(), 'phase': args.phase,
               'simulator': args.simulator, 'round': args.round, 'commands': [],
               'scope': 'Two full100 held endpoints, one shape/flat pair. Calibration only.'}

    def save():
        (output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')

    def run(command, name, timeout=120):
        started = time.time()
        with (output / (name + '.log')).open('w') as log:
            result = subprocess.run(command, cwd=PROJECT, stdout=log,
                                    stderr=subprocess.STDOUT, timeout=timeout)
        receipt['commands'].append({'argv': command, 'exit_code': result.returncode,
                                    'seconds': time.time() - started})
        save()
        if result.returncode:
            raise RuntimeError(name + ' failed; original log retained')

    receipt['native_sources'] = {str(p.relative_to(PROJECT)): sha(p)
        for folder in ['App', 'UITests'] for p in (PROJECT / folder).glob('*.swift')}
    save()
    if args.phase == 'build':
        run(['xcodebuild', 'build-for-testing', '-project', 'GlassNativeReference.xcodeproj',
             '-scheme', 'GlassNativeReference', '-destination', 'platform=iOS Simulator,id=' + args.simulator,
             '-derivedDataPath', str(DERIVED), '-parallel-testing-enabled', 'NO'], 'build', 240)
        receipt['finished_unix'] = time.time()
        save()
        print(json.dumps({'output': str(output), 'build': 'passed'}))
        return

    spec_root = ROOT / 'inputs/rounds' / args.round
    spec = json.loads((spec_root / 'shape-spec.json').read_text())
    manifest = json.loads((spec_root / 'inputs/manifest.json').read_text())
    assert spec['scheduled_stages'] == ['full100']
    assert len(spec['stages']) == 6 and len(manifest['inputs']) == 8
    receipt['freeze_sha256'] = sha(ROOT / 'freeze.json')
    receipt['prepared_native_files'] = prepared_native_files()
    receipt['native_binaries'] = native_binaries()
    receipt['simulator_identity'] = simulator_identity(args.simulator)
    receipt['spec_sha256'] = sha(spec_root / 'shape-spec.json')
    receipt['manifest_sha256'] = sha(spec_root / 'inputs/manifest.json')
    receipt['binary_sha256'] = {}
    products = DERIVED / 'Build/Products/Debug-iphonesimulator'
    for bundle in ['GlassNativeReference.app', 'GlassNativeReferenceUITests-Runner.app']:
        product = products / bundle
        run(['xcrun', 'simctl', 'install', args.simulator, str(product)], 'install-' + bundle)
        info = plistlib.loads((product / 'Info.plist').read_bytes())
        receipt['binary_sha256'][bundle] = sha(product / info['CFBundleExecutable'])
        container = Path(subprocess.check_output(['xcrun', 'simctl', 'get_app_container',
            args.simulator, info['CFBundleIdentifier'], 'data'], text=True).strip())
        folder = container / 'Documents/holdout'
        folder.mkdir(parents=True, exist_ok=True)
        shutil.copy2(spec_root / 'shape-spec.json', folder / 'shape-spec.json')
        shutil.copy2(spec_root / 'inputs/manifest.json', folder / 'manifest.json')
        if bundle == 'GlassNativeReference.app':
            for row in manifest['inputs']:
                source = spec_root / 'inputs' / row['file']
                assert sha(source) == row['sha256']
                shutil.copy2(source, folder / source.name)
    save()
    with (output / 'observer.log').open('w') as log:
        observer = subprocess.Popen([sys.executable, str(ROOT / 'native-tools/capture-held-endpoints.py'),
            '--simulator', args.simulator, '--output', str(output / 'held')], stdout=log, stderr=subprocess.STDOUT)
        try:
            candidates = list((DERIVED / 'Build/Products').glob('*.xctestrun'))
            assert len(candidates) == 1
            run(['xcodebuild', 'test-without-building', '-xctestrun', str(candidates[0]),
                 '-destination', 'platform=iOS Simulator,id=' + args.simulator,
                 '-parallel-testing-enabled', 'NO', '-test-timeouts-enabled', 'YES',
                 '-default-test-execution-time-allowance', '120', '-maximum-test-execution-time-allowance', '120',
                 '-resultBundlePath', str(output / 'result.xcresult'),
                 '-only-testing:GlassNativeReferenceUITests/NativeReferenceTests/testSliderColorResponseFullCoverage'], 'test', 180)
        finally:
            observer.terminate()
            try:
                observer.wait(timeout=5)
            except subprocess.TimeoutExpired:
                observer.kill()
                observer.wait(timeout=5)
    events = [json.loads(line) for line in (output / 'held/capture-events.jsonl').read_text().splitlines()]
    assert native_binaries() == freeze['native_binaries'], 'Products changed during test execution'
    assert len(events) == 2 and all(e.get('exitCode') == 0 and 'observerError' not in e for e in events)
    assert {e['coverageLabel'] for e in events} == {'full100'}
    assert len({e['run'] for e in events}) == 2
    copied = []
    for event in events:
        run_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', event['run'])
        trace = Path(event['tracePathObserved']).resolve()
        container_root = (Path.home() / 'Library/Developer/CoreSimulator/Devices' /
                          args.simulator / 'data/Containers/Data/Application').resolve()
        relative = trace.relative_to(container_root).parts
        assert len(relative) == 5 and relative[1:] == ('Documents', 'reference', run_name, 'trace.jsonl')
        source = trace.parent
        assert json.loads((source / 'session.json').read_text())['run'] == event['run']
        destination = output / 'traces' / run_name
        shutil.copytree(source, destination)
        copied.append((source, destination))
    run([sys.executable, str(ROOT / 'native-tools/verify-full100-endpoints.py'),
         '--out', str(output), '--spec', str(spec_root / 'shape-spec.json')], 'strict-verification')
    strict = json.loads((output / 'endpoint-verification-strict.json').read_text())
    assert strict['status'] == 'passed'
    assert strict['verifiedHeldEndpoints'] == 2 and strict['verifiedShapeFlatPairs'] == 1
    # Archive complete original traces losslessly before removing duplicates.
    storage = []
    for source, destination in copied:
        trace = destination / 'trace.jsonl'
        data = trace.read_bytes()
        compressed = gzip.compress(data, mtime=0)
        archive = destination / 'trace.jsonl.gz'
        archive.write_bytes(compressed)
        assert gzip.decompress(archive.read_bytes()) == data
        digest = hashlib.sha256(data).hexdigest()
        trace.unlink()
        simulator_trace = source / 'trace.jsonl'
        if simulator_trace.is_file() and sha(simulator_trace) == digest:
            simulator_trace.unlink()
        storage.append({'archive': str(archive.relative_to(output)), 'original_sha256': digest,
                        'original_bytes': len(data), 'archive_bytes': len(compressed),
                        'archive_sha256': sha(archive)})
    receipt.update(finished_unix=time.time(), captures=2, verified_held_endpoints=2,
                   verified_shape_flat_pairs=1, lossless_trace_storage=storage)
    artifacts = [output / 'index-strict.json', output / 'endpoint-verification-strict.json',
                 output / 'held/capture-events.jsonl']
    artifacts.extend(Path(event['path']) for event in events)
    artifacts.extend(destination / 'session.json' for _, destination in copied)
    assert all(p.resolve().is_relative_to(output.resolve()) for p in artifacts)
    receipt['analysis_artifacts'] = {str(p.relative_to(output)): sha(p) for p in artifacts}
    save()
    print(json.dumps({'output': str(output), 'strict': 'passed', 'captures': 2}), flush=True)


if __name__ == '__main__':
    main()
