#!/usr/bin/env python3
"""Bind the two small external sources; never edits Sleepy or historical capture files."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CLASS = 'com.lingion.sleepy.ui.component.sliderlayerresearch.SliderLayerObservationTest'
PIN_FILE = ROOT / 'source-pins.json'


def require(value, message):
    if not value:
        raise ValueError(message)


def expected():
    pins = json.loads(PIN_FILE.read_text())
    source_root = ROOT / 'sources'
    actual = set()
    for path in source_root.rglob('*'):
        require(not path.is_symlink(), 'Symlink in source tree')
        if path.is_file():
            relative = path.relative_to(source_root).as_posix()
            actual.add(relative)
            data = path.read_bytes()
            require(relative in pins['files'], 'Unexpected external source: ' + relative)
            require(hashlib.sha256(data).hexdigest() == pins['files'][relative]['sha256'] and
                    len(data) == pins['files'][relative]['bytes'], 'Changed source: ' + relative)
    require(actual == set(pins['files']) and len(actual) == 2, 'Expected exactly the observer and small test')
    for path in (source_root, *source_root.parents):
        require(not path.is_symlink(), 'Symlink in source-root ancestry')
    return {'schema': 1, 'status': 'SOURCE_PREPARED_NOT_BUILT_OR_RUN', 'test_class': CLASS,
            'compose_contract': '1.12.1', 'sources': 'sources', 'files': pins['files'],
            'source_pins_sha256': hashlib.sha256(PIN_FILE.read_bytes()).hexdigest(),
            'optical_acceptance': False, 'gradle_executed': False, 'device_used': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Read-only receipt/source validation')
    args = parser.parse_args()
    receipt = expected()
    data = (json.dumps(receipt, indent=2) + '\n').encode()
    path = ROOT / '.local/preparation.json'
    require(not path.parent.is_symlink() and not path.is_symlink(), 'Symlink in receipt path')
    if args.check or path.exists():
        require(path.is_file() and path.read_bytes() == data, 'Receipt missing or changed; no overwrite is allowed')
    else:
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(data)
    print(json.dumps(receipt, sort_keys=True))


if __name__ == '__main__':
    main()
