#!/usr/bin/env python3
"""Restore original trace bytes for rerunning strict verification; refuse overwrites."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture', required=True, type=Path)
    args = parser.parse_args()
    root = args.capture.resolve()
    receipt = json.loads((root / 'receipt.json').read_text())
    for row in receipt['lossless_trace_storage']:
        archive = root / row['archive']
        assert archive.resolve().is_relative_to(root)
        compressed = archive.read_bytes()
        assert sha(compressed) == row['archive_sha256']
        data = gzip.decompress(compressed)
        assert sha(data) == row['original_sha256'] and len(data) == row['original_bytes']
        target = archive.with_suffix('')
        with target.open('xb') as stream:
            stream.write(data)
    print(json.dumps({'restored_original_traces': len(receipt['lossless_trace_storage'])}))


if __name__ == '__main__':
    main()
