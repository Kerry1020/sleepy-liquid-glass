"""Verify publication hashes and lossless compressed-source identity, using only the standard library."""
from pathlib import Path
import gzip
import hashlib
import json

E = Path(__file__).resolve().parent
root = E.parent.parent.parent
source = json.loads((E / 'sources.json').read_text())
sha = lambda data: hashlib.sha256(data).hexdigest()
checks = 0
for row in source['records']:
    raw = (root / row['published']).read_bytes()
    assert sha(raw) == row['published_sha256'], row['published']
    restored = gzip.decompress(raw) if row['processing'].startswith('deterministic lossless gzip') else raw
    assert sha(restored) == row['source_sha256'], row['source_namespace']
    assert len(restored) == row['source_bytes']
    checks += 1
for row in source['figures'] + source['original_crop_records']:
    assert sha((root / row['published']).read_bytes()) == row['published_sha256'], row['published']
    checks += 1
manifest = E / 'publication-manifest.json'
if manifest.is_file():
    data = json.loads(manifest.read_text())
    for name, row in data['files'].items():
        raw = (root / name).read_bytes()
        assert sha(raw) == row['sha256'] and len(raw) == row['bytes'], name
        checks += 1
print('Passed ' + str(checks) + ' source/publication hash checks; no device or build required.')
