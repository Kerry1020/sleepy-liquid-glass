#!/usr/bin/env python3
"""Bind this signed experiment before acquisition, reusing exact native builds."""
from pathlib import Path
import datetime
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
OLD = ROOT.parent / 'slider-color-response-20261116'
LINEAR = ROOT.parent / 'slider-linear-response-20261116'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert not (ROOT/'freeze.json').exists(), 'Refusing overwrite'
    assert not list((ROOT/'rounds').glob('*/native-*')), 'Freeze must precede capture'
    original = json.loads((OLD/'freeze.json').read_text())
    for relative, expected in original['files'].items():
        assert sha(OLD/relative) == expected, relative
    module_spec = importlib.util.spec_from_file_location('signed_collector', ROOT/'capture-native.py')
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    collector = module.collector()
    assert collector.prepared_native_files() == original['prepared_native_files']
    assert collector.native_binaries() == original['native_binaries']
    assert collector.simulator_identity(original['simulator']['udid']) == original['simulator']
    assert sha(ROOT/'prepare-inputs.py') == json.loads((ROOT/'source-verification.json').read_text())['generator_sha256']
    helpers = ROOT/'native-tools'
    helpers.mkdir(exist_ok=True)
    for name in ('capture-held-endpoints.py', 'verify-full100-endpoints.py'):
        target = helpers/name
        if target.exists():
            assert sha(target) == sha(OLD/'native-tools'/name)
        else:
            shutil.copyfile(OLD/'native-tools'/name, target)
    tests = {}
    for script in (ROOT/'collect-signed.py', LINEAR/'analyze-signed-g.py'):
        result = subprocess.run([sys.executable, str(script), '--self-test'],
                                text=True, capture_output=True, check=True)
        tests[str(script.relative_to(ROOT.parent))] = json.loads(result.stdout)
    paths = [p for p in ROOT.rglob('*') if p.is_file() and
             not any(part in ('.local', 'rounds', '__pycache__') for part in p.relative_to(ROOT).parts)]
    # Round inputs live under inputs/rounds; include them explicitly despite the
    # exclusion above, which prevents acquisition output from entering a freeze.
    paths.extend(p for p in (ROOT/'inputs').rglob('*') if p.is_file())
    paths.extend([LINEAR/'analyze-signed-g.py', LINEAR/'NEXT-TEST.md', LINEAR/'LIMITS.md',
                  OLD/'freeze.json', OLD/'capture-native.py', OLD/'evidence/manifest.json'])
    paths.extend(OLD/relative for relative in original['files'])
    manifest = json.loads((OLD/'evidence/manifest.json').read_text())
    assert manifest['freeze_sha256'] == sha(OLD/'freeze.json')
    for name in ('control-pre', 'global-G'):
        for path in (OLD/'evidence/rounds'/name/'native-r1').rglob('*'):
            if path.is_file():
                row = manifest['files'][str(path.relative_to(OLD/'evidence'))]
                assert sha(path) == row['sha256'] and path.stat().st_size == row['bytes'], path
                paths.append(path)
    files = {}
    for path in sorted(set(paths)):
        relative = __import__('os').path.relpath(path, ROOT)
        files[relative] = sha(path)
    frozen = {'schema': 1, 'frozen_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'scope': 'Signed G response calibration only; no optical acceptance or product change',
              'round_order': collector.ROUNDS, 'files': files, 'synthetic_checks': tests,
              'prepared_native_files': collector.prepared_native_files(), 'native_binaries': collector.native_binaries(),
              'simulator': original['simulator'], 'reused_old_freeze_sha256': sha(OLD/'freeze.json'),
              'new_capture_sessions_at_freeze': 0}
    target = ROOT/'freeze.json'
    with target.open('x') as stream:
        json.dump(frozen, stream, indent=2, allow_nan=False); stream.write('\n')
    print(json.dumps({'freeze_sha256': sha(target), 'bound_files': len(files), 'synthetic_checks': tests}))


if __name__ == '__main__':
    main()
