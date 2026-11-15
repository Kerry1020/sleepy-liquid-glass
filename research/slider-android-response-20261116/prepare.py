#!/usr/bin/env python3
"""Derive explicit Android metadata without changing frozen S images/specs."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT.parents[1]
ROUNDS = ('control-pre', 'global-G', 'mask-G', 'control-post')


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--geometry-spec', type=Path, required=True)
    args = ap.parse_args()
    old = json.loads(args.geometry_spec.read_text())
    reference = old['native_public_geometry_reference']
    files = {}
    for name in ROUNDS:
        source = ASSETS / 'research/slider-color-response-20261116/inputs/rounds' / name
        source_spec = source / 'shape-spec.json'
        spec = json.loads(source_spec.read_text())
        native_path = ASSETS / 'research/slider-color-response-20261116/evidence/rounds' / name / 'native-r1/index-strict.json'
        native = json.loads(native_path.read_text())
        # Validate the exact centre against the independently saved native index.
        pair, = native['captures']
        bounds = pair['actual_carrier_bounds_world_xywh']
        assert bounds == pair['flat_actual_carrier_bounds_world_xywh']
        observed_center = [bounds[0] + bounds[2] / 2, bounds[1] + bounds[3] / 2]
        assert max(abs(a - b) for a, b in zip(observed_center, [187.7223825454712, 429.5])) < 1e-10
        spec['native_public_geometry_reference'] = reference
        full, = [s for s in spec['stages'] if s['id'] == 'full100']
        full['actual_carrier_target_center_world_pt'] = [187.7223825454712, 429.5]
        spec['status'] = 'derived Android six-stage capture metadata; only full100 compared with S native'
        spec['scheduled_stages'] = [s['id'] for s in spec['stages']]
        spec['android_derivation'] = {
            'original_spec_asset_path': str(source_spec.relative_to(ASSETS)),
            'original_spec_sha256': sha(source_spec),
            'native_index_asset_path': str(native_path.relative_to(ASSETS)),
            'native_index_sha256': sha(native_path),
            'historical_geometry_spec_sha256': sha(args.geometry_spec),
            'historical_geometry_reference': reference,
            'modified_existing_fields': ['status', 'scheduled_stages'],
            'added_fields': ['native_public_geometry_reference', 'stages[full100].actual_carrier_target_center_world_pt', 'android_derivation'],
            'unchanged': 'all source PNG/manifest bytes and all original six stage definitions/nominal targets',
            'limits': 'Other five stages have no matched S native endpoint; original source input-role descriptions refer to the native preparation, not Android loader decoding.'
        }
        target = ROOT / 'derived' / name / 'shape-spec.json'
        data = (json.dumps(spec, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode()
        if target.exists():
            assert target.read_bytes() == data, 'Refusing to overwrite changed derived spec'
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        manifest_path = source / 'inputs/manifest.json'
        manifest = json.loads(manifest_path.read_text())
        assert manifest['split'] == 'calibration' and len(manifest['inputs']) == 8
        for row in manifest['inputs']:
            png = manifest_path.parent / row['file']
            assert sha(png) == row['sha256'] and png.stat().st_size == row['bytes']
        for path in [target, source_spec, native_path, manifest_path, *[manifest_path.parent / r['file'] for r in manifest['inputs']]]:
            files[str(path.relative_to(ASSETS))] = sha(path)
    receipt = ROOT / 'derived' / 'SOURCE-MAP.json'
    data = (json.dumps({'schema': 1, 'rounds': ROUNDS, 'source_geometry_spec': str(args.geometry_spec),
                       'source_geometry_spec_sha256': sha(args.geometry_spec), 'files': files,
                       'scope': 'Metadata derivation only; no image copy, native mutation or product source change.'}, indent=2) + '\n').encode()
    if receipt.exists():
        assert receipt.read_bytes() == data
    else:
        receipt.write_bytes(data)
    print(json.dumps({'derived_specs': 4, 'bound_unique_files': len(files), 'source_images_unchanged': True}))


if __name__ == '__main__':
    main()
