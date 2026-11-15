"""Restore exact archived research bytes to a NEW destination; never runs the archived tools."""
from pathlib import Path
import argparse
import gzip
import hashlib
import json

parser = argparse.ArgumentParser()
parser.add_argument('destination', type=Path)
args = parser.parse_args()
E = Path(__file__).resolve().parent
root = E.parent.parent.parent
target = args.destination.resolve()
assert not target.exists(), 'Choose a new destination; existing directories are never overwritten.'
source = json.loads((E / 'sources.json').read_text())
for row in source['records']:
    file = root / row['published']
    raw = file.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == row['published_sha256']
    restored = gzip.decompress(raw) if row['processing'].startswith('deterministic lossless gzip') else raw
    assert hashlib.sha256(restored).hexdigest() == row['source_sha256']
    relative = Path(row['source_namespace']).relative_to('panel-study')
    assert '..' not in relative.parts and not relative.is_absolute()
    output = target / relative
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(restored)
print('Restored exact historical files. Archived scripts retain original research dependencies and paths.')
