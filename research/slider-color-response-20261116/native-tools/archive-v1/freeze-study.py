#!/usr/bin/env python3
"""Bind the calibration plan, inputs and already-built native test before capture."""
import argparse
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--simulator', required=True)
    args = parser.parse_args()
    target = ROOT / 'freeze.json'
    assert not target.exists(), 'Refusing to replace a pre-capture freeze'
    assert not list((ROOT / 'rounds').glob('*/native-*')), 'Freeze must precede all new captures'
    module_spec = importlib.util.spec_from_file_location('collector', ROOT / 'capture-native.py')
    collector = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(collector)
    preparation = json.loads((ROOT / '.local/preparation.json').read_text())
    build_path = ROOT / '.local/build-r1/receipt.json'
    build = json.loads(build_path.read_text())
    assert build['phase'] == 'build' and len(build['commands']) == 1
    assert build['commands'][0]['exit_code'] == 0 and build['simulator'] == args.simulator
    native = collector.prepared_native_files()
    for relative, digest in preparation['nativeAppSourcesUnchanged'].items():
        assert native[relative] == digest, relative
    for relative, digest in build['native_sources'].items():
        assert native[relative] == digest, relative
    assert native['UITests/NativeReferenceTests.swift'] == preparation['testSourceSha256']
    test = subprocess.run([sys.executable, str(ROOT / 'analyze-response.py'), '--self-test'],
                          capture_output=True, text=True, check=True)
    synthetic = json.loads(test.stdout)
    assert synthetic['status'] == 'synthetic_contract_checks_passed'
    for source, filename in [(ROOT / '.local/preparation.json', 'preparation-receipt.json'),
                             (build_path, 'build-r1-receipt.json')]:
        destination = ROOT / 'native-tools' / filename
        assert not destination.exists()
        destination.write_bytes(source.read_bytes())
    synthetic_path = ROOT / 'native-tools/synthetic-self-test.json'
    assert not synthetic_path.exists()
    synthetic_path.write_text(json.dumps(synthetic, indent=2) + '\n')
    paths = [ROOT / p for p in ['PROTOCOL.md', 'analyze-response.py', 'prepare-inputs.py',
                               'prepare-native.py', 'capture-native.py', 'freeze-study.py',
                               'source-verification.json']]
    paths.extend(p for p in (ROOT / 'native-tools').rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    paths.extend(p for p in (ROOT / 'inputs').rglob('*') if p.is_file())
    fixture = ROOT.parent / 'slider-fixtures'
    mapping = json.loads((fixture / 'SOURCE-MAP.json').read_text())
    paths.append(fixture / 'SOURCE-MAP.json')
    paths.extend(fixture / row['export_path'] for row in mapping['files']
                 if row['export_path'].startswith('tools/native-glass-reference/'))
    files = {str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else
             '../slider-fixtures/' + str(p.relative_to(fixture)): sha(p)
             for p in sorted(set(paths))}
    result = {'schema': 1, 'frozen_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'scope': 'Calibration of original RGB five-point star at full100; not optical acceptance.',
              'scheduled_stages': ['full100'], 'round_order': collector.ROUNDS,
              'files': files, 'prepared_native_files': native,
              'native_binaries': collector.native_binaries(),
              'simulator': collector.simulator_identity(args.simulator),
              'synthetic_checks': synthetic,
              'new_capture_sessions_at_freeze': 0}
    with target.open('x') as stream:
        stream.write(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'freeze': str(target), 'sha256': sha(target),
                      'bound_files': len(files), 'native_files': len(native),
                      'native_binary_config_files': len(result['native_binaries'])}))


if __name__ == '__main__':
    main()
