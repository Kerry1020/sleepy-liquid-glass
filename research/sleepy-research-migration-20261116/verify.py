#!/usr/bin/env python3
"""Verify exact preservation of the pinned Sleepy research migration."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--source", type=Path)
parser.add_argument("--manifest", type=Path, help="An additional migration manifest; defaults to the original 52-file batch")
args = parser.parse_args()
here = Path(__file__).resolve().parent
root = here.parents[1]
manifest = json.loads((args.manifest or here / "SOURCE-MAP.json").read_text())
entries = manifest["files"]
assert len(entries) == manifest["file_count"]
assert len({entry["source_path"] for entry in entries}) == len(entries)
assert sum(entry["bytes"] for entry in entries) == manifest["total_bytes"]
assert sum(entry["storage"] == "new" for entry in entries) == manifest["new_files"]
assert sum(entry["storage"] == "reused" for entry in entries) == manifest["reused_files"]
for entry in entries:
    target = (root / entry["asset_path"]).resolve()
    assert target.is_relative_to(root), entry["asset_path"]
    data = target.read_bytes()
    assert len(data) == entry["bytes"], entry["source_path"]
    assert hashlib.sha256(data).hexdigest() == entry["sha256"], entry["source_path"]
    blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    assert blob == entry["source_git_blob"], entry["source_path"]
    if args.source:
        original = subprocess.check_output(["git", "show", manifest["source_commit"] + ":" + entry["source_path"]], cwd=args.source)
        assert original == data, entry["source_path"]
print(json.dumps({"verified_files": len(entries), "bytes": manifest["total_bytes"], "new_versions": manifest["new_files"], "reused_files": manifest["reused_files"], "pinned_source_checked": args.source is not None}))
