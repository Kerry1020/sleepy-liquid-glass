#!/usr/bin/env python3
"""Prepare an ignored native build tree; only XCTest stage selection changes."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent
FIXTURE = ROOT.parent / 'slider-fixtures'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reuse-derived-data', type=Path)
    args = parser.parse_args()
    project = ROOT / '.local/native-project'
    if project.exists():
        raise SystemExit('Refusing to overwrite an existing prepared project')
    mapping = json.loads((FIXTURE / 'SOURCE-MAP.json').read_text())
    selected = [row for row in mapping['files'] if row['export_path'].startswith('tools/native-glass-reference/')]
    assert len(selected) == 17
    for row in selected:
        source = FIXTURE / row['export_path']
        assert digest(source) == row['sha256'], source
        relative = Path(row['export_path']).relative_to('tools/native-glass-reference')
        target = project / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    subprocess.run(['patch', '-p1', '--forward', '--input', str(ROOT / 'native-tools/native-full100-only.patch')], cwd=project, check=True)
    derivation = json.loads((ROOT / 'native-tools/derivation.json').read_text())
    assert digest(project / 'UITests/NativeReferenceTests.swift') == derivation['native_test_patch']['patched_test_sha256']
    unchanged = {}
    for row in selected:
        relative = Path(row['export_path']).relative_to('tools/native-glass-reference')
        if relative.parts[0] == 'App':
            assert digest(project / relative) == row['sha256']
            unchanged[str(relative)] = row['sha256']
    derived = ROOT / '.local/DerivedData'
    reused = None
    if args.reuse_derived_data:
        source = args.reuse_derived_data.resolve()
        assert source.is_dir() and not derived.exists()
        # Rename existing cache on the same volume rather than duplicating it.
        source.rename(derived)
        reused = str(source)
    receipt = {'nativeAppSourcesUnchanged': unchanged,
               'testSourceSha256': digest(project / 'UITests/NativeReferenceTests.swift'),
               'reusedCacheFrom': reused, 'derivedData': str(derived),
               'scope': 'Native application and controls unchanged; XCTest selects original full100 stage only.'}
    (ROOT / '.local/preparation.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
