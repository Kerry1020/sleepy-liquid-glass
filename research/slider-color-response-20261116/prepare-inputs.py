#!/usr/bin/env python3
"""Prepare eight full100-only color-response rounds from the tracked star source.

This is input preparation only. It does not build, capture, fit, or validate any
native material. It refuses to overwrite an existing inputs package or receipt.
All source paths resolve from this script, so a moved repository is supported.
"""
from pathlib import Path
import copy
import hashlib
import json
import shutil
import tempfile
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
SOURCE = REPO / 'docs/design/evidence/glass-slider-star-20261115/source'
OUTPUT = ROOT / 'inputs'
VERIFICATION = ROOT / 'source-verification.json'
STAGES = ['ingress01', 'ingress10', 'ingress50', 'ingress75', 'full100', 'far50']
ROUNDS = [('control-pre', None, None), ('global-R', 'global', 0),
          ('global-G', 'global', 1), ('global-B', 'global', 2),
          ('mask-R', 'mask', 0), ('mask-G', 'mask', 1),
          ('mask-B', 'mask', 2), ('control-post', None, None)]
DELTA = 20
EXPECTED_SOURCE_HASHES = {
    'shape-spec.json': '72be8139c968276426532797141097d4ec30a131ff67313794e3689c455a3616',
    'inputs/manifest.json': '6c7bd1861fc1e97bbe34726fb24910a4e56719c8f4061bffc10ba42b4b8914fe',
    'inputs/st01_rgb_star_d16.png': '9757bdb14092023996f2bd46d30b682799aac1fe06c221b7cad256c991e46724',
    'inputs/st00_flat128.png': '6e4291536355bff3dae7dee3957eec96bf4f3efc7566dd4257721a635ad8340b',
    'masks/st01_rgb_star_d16-left_blue-coverage16.png': '0520b9b21148d9b0febef0f706c5ae9766d6ba3f6600d483e6d0f1980083202d',
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')


def relative(path):
    return path.relative_to(REPO).as_posix()


def geometry(shape):
    """Color-independent geometry; all AA count/support hashes stay included."""
    out = copy.deepcopy(shape)
    for key in ['id', 'source_png', 'source_sha256', 'color_partition', 'color_rgb']:
        out.pop(key, None)
    for region in out['regions']:
        region.pop('color_rgb', None)
    for node in [out, *out['regions']]:
        for key in ['coverage_count_mask_png', 'binary_mask_png']:
            if key in node:
                node[key] = Path(node[key]).name
    return out


def mask_refs(node):
    if isinstance(node, dict):
        for key, value in node.items():
            if key in ['coverage_count_mask_png', 'binary_mask_png']:
                yield value
            else:
                yield from mask_refs(value)
    elif isinstance(node, list):
        for value in node:
            yield from mask_refs(value)


def point_masks_to_shared(node):
    if isinstance(node, dict):
        for key, value in list(node.items()):
            if key in ['coverage_count_mask_png', 'binary_mask_png']:
                node[key] = '../../source-masks/' + Path(value).name
            else:
                point_masks_to_shared(value)
    elif isinstance(node, list):
        for value in node:
            point_masks_to_shared(value)


def main():
    if OUTPUT.exists() or OUTPUT.is_symlink() or VERIFICATION.exists():
        raise SystemExit('Refusing to overwrite existing inputs/ or source-verification.json. Preserve the published package.')
    source_hashes = {}
    for name, expected in EXPECTED_SOURCE_HASHES.items():
        actual = sha((SOURCE / name).read_bytes())
        if actual != expected:
            raise SystemExit('Tracked source differs from frozen dependency: ' + name)
        source_hashes[name] = actual
    original_spec = json.loads((SOURCE / 'shape-spec.json').read_text())
    original_manifest = json.loads((SOURCE / 'inputs/manifest.json').read_text())
    assert original_manifest['schema'] == 1 and original_manifest['split'] == 'calibration'
    assert len(original_manifest['inputs']) == 8
    assert [s['id'] for s in original_spec['stages']] == STAGES
    base_id = original_spec['first_input_id']
    assert base_id == 'st01_rgb_star_d16' and original_spec['flat_input_id'] == 'st00_flat128'
    base_entry = next(e for e in original_spec['inputs'] if e['id'] == base_id)
    base_shape = base_entry['shape']
    assert [r['id'] for r in base_shape['regions']] == ['left_blue', 'middle_red', 'right_green']
    base_geometry = geometry(base_shape)
    geometry_sha = sha(json.dumps(base_geometry, sort_keys=True, separators=(',', ':')).encode())
    base_png = SOURCE / 'inputs' / (base_id + '.png')
    with Image.open(base_png) as image:
        assert image.mode == 'RGB' and image.size == (750, 1334)
        base = np.asarray(image).copy()
        icc = image.info.get('icc_profile')
    assert icc and sha(icc) == original_spec['rasterization']['icc_sha256']
    assert int(base.min()) == 48 and int(base.max()) == 232
    with Image.open(SOURCE / 'masks/st01_rgb_star_d16-left_blue-coverage16.png') as image:
        assert image.mode == 'L' and image.size == (750, 1334)
        counts = np.asarray(image).astype(np.int16)
    assert counts.min() == 0 and counts.max() == 16
    # Explicit nearest-integer, half-up: no bankers-rounding ambiguity at .5.
    increments = (DELTA * counts + 8) // 16
    assert increments.min() == 0 and increments.max() == DELTA
    flat_bytes = (SOURCE / 'inputs/st00_flat128.png').read_bytes()
    with Image.open(SOURCE / 'inputs/st00_flat128.png') as image:
        assert image.info.get('icc_profile') == icc and np.all(np.asarray(image) == 128)
    compatibility = [e for e in original_manifest['inputs'] if e['id'] not in [base_id, 'st00_flat128']]
    # Only hash/copy the six loader-compatibility files; do not decode or schedule
    # them. In particular, preparing this package does not consume a seven-star.
    for entry in original_manifest['inputs']:
        data = (SOURCE / 'inputs' / entry['file']).read_bytes()
        assert sha(data) == entry['sha256'] and len(data) == entry['bytes']
        source_hashes['inputs/' + entry['file']] = sha(data)
    refs = sorted(set(mask_refs(original_spec)))
    mask_hashes = {name: sha((SOURCE / name).read_bytes()) for name in refs}
    plans = []
    verification = {
        'schema': 1, 'status': 'INPUT_PREPARATION_ONLY_NOT_CAPTURE_OR_ACCEPTANCE',
        'study_id': 'slider_color_response_20261116_full100_only',
        'schedule_scope': 'full100-only: 8 rounds x first-input plus unchanged st00_flat128; not six-pose capture',
        'scheduled_stages': ['full100'], 'source_root': relative(SOURCE),
        'source_sha256': source_hashes, 'source_mask_sha256': mask_hashes,
        'base_source': {'id': base_id, 'mode': 'RGB', 'size_px': [750, 1334],
            'icc_sha256': sha(icc), 'channel_min_RGB': base.min(axis=(0, 1)).tolist(),
            'channel_max_RGB': base.max(axis=(0, 1)).tolist(), 'geometry_sha256': geometry_sha},
        'delta_rule': {'amplitude_encoded_byte': DELTA,
            'global': 'output[p,c] = original[p,c] + 20 for the selected channel at every PNG pixel',
            'mask': 'output[p,c] = original[p,c] + floor((20*left_blue_count[p]+8)/16); original count is 0..16',
            'rounding': 'nearest integer, exact half-up; count4 ->5, count2 ->3; not NumPy bankers rounding',
            'other_channels': 'byte-identical to original', 'clipping': 'forbidden; assert pre-cast min>=0 and max<=252'},
        'flat': {'id': 'st00_flat128', 'sha256': sha(flat_bytes), 'byte_identical_in_every_round': True,
            'meaning': 'Ordinary all-128 flat. It is never relabeled as a global/masked source.'},
        'compatibility_inputs': {'count_per_round': 6,
            'ids': [e['id'] for e in compatibility], 'decoded': False, 'scheduled': False,
            'reason': 'Existing eight-input loader only. Copy/hash is not native observation or holdout consumption.'},
        'rounds': [], 'new_capture': False, 'seven_point_consumed': False,
        'limits': ['Source generation only; protocol/runner/capture and analysis are separate.',
            'No fitted color matrix, sampling kernel, material change, or optical acceptance.',
            'Original geometry/AA count masks/coordinates and ICC are preserved; source bytes change only by the stated per-channel additive rule.'],
    }
    local = ROOT / '.local'
    local.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='prepare-', dir=local) as temp:
        staging = Path(temp) / 'inputs'
        staging.mkdir()
        for name in refs:
            out = staging / 'source-masks' / Path(name).name
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(SOURCE / name, out)
        for round_name, scope, channel in ROUNDS:
            root = staging / 'rounds' / round_name
            png_dir = root / 'inputs'
            png_dir.mkdir(parents=True)
            first_id = base_id if scope is None else base_id + '_' + scope + '_' + 'rgb'[channel] + '20'
            delta = np.zeros(base.shape, dtype=np.int16)
            if scope == 'global':
                delta[..., channel] = DELTA
            elif scope == 'mask':
                delta[..., channel] = increments
            candidate = base.astype(np.int16) + delta
            assert candidate.min() >= 0 and candidate.max() <= 252
            png = png_dir / (first_id + '.png')
            if scope is None:
                png.write_bytes(base_png.read_bytes())
            else:
                Image.fromarray(candidate.astype(np.uint8), mode='RGB').save(png, icc_profile=icc)
            with Image.open(png) as image:
                actual = np.asarray(image).astype(np.int16)
                assert image.mode == 'RGB' and image.size == (750, 1334)
                assert image.info.get('icc_profile') == icc
            assert np.array_equal(actual - base.astype(np.int16), delta)
            png_sha = sha(png.read_bytes())
            (png_dir / 'st00_flat128.png').write_bytes(flat_bytes)
            for entry in compatibility:
                shutil.copyfile(SOURCE / 'inputs' / entry['file'], png_dir / entry['file'])
            manifest = copy.deepcopy(original_manifest)
            manifest['set_id'] = 'slider_color_20261116_' + round_name.lower().replace('-', '_')
            for entry in manifest['inputs']:
                if entry['id'] == base_id:
                    entry.update(id=first_id, file=first_id + '.png', sha256=png_sha, bytes=png.stat().st_size)
            write_json(png_dir / 'manifest.json', manifest)
            spec = copy.deepcopy(original_spec)
            # Historical trace paths and previous feasibility claims do not
            # describe this new preparation-only, full100-only color protocol.
            for old in ['native_public_geometry_reference', 'prior_asset', 'analysis_limitations',
                        'diagnostic', 'diagnostic_metadata', 'g_only_diagnostic']:
                spec.pop(old, None)
            spec['status'] = 'prepared encoded-RGB color-response input; full100-only; not captured or accepted'
            spec['first_input_id'] = first_id
            spec['world']['background_rgb'] = [128, 128, 128]
            if scope == 'global':
                spec['world']['background_rgb'][channel] += DELTA
            spec['rasterization']['base_method'] = original_spec['rasterization']['method']
            spec['rasterization']['method'] = ('Original PNG bytes unchanged' if scope is None else
                'Original encoded-sRGB raster plus selected-channel additive integer delta; no resampling or geometry rerasterization')
            for entry in spec['inputs']:
                if entry['id'] == base_id:
                    entry.update(id=first_id, role='only scheduled multicolor first input for this round', source_sha256=png_sha)
                    shape = entry['shape']
                    shape.update(id=first_id, source_png='inputs/' + first_id + '.png', source_sha256=png_sha)
                    for region in shape['regions']:
                        if scope == 'global' or (scope == 'mask' and region['id'] == 'left_blue'):
                            region['color_rgb'][channel] += DELTA
                    shape['color_partition'] = original_spec['inputs'][1]['shape']['color_partition'] + '; additive color rule in color_response_preparation; original coverage masks retained'
                    assert geometry(shape) == base_geometry
                elif entry['id'] != 'st00_flat128':
                    entry['role'] = 'loader compatibility only; not decoded or scheduled in this full100-only study'
            point_masks_to_shared(spec)
            spec['scheduled_stages'] = ['full100']
            spec['scheduled_input_ids'] = [first_id, 'st00_flat128']
            spec['color_response_preparation'] = {
                'study_id': verification['study_id'], 'round': round_name, 'scope': scope or 'control',
                'channel': 'RGB'[channel] if channel is not None else None, 'delta': DELTA if scope else 0,
                'source_base_sha256': EXPECTED_SOURCE_HASHES['inputs/st01_rgb_star_d16.png'],
                'source_background_rgb': spec['world']['background_rgb'],
                'mask': '../../source-masks/st01_rgb_star_d16-left_blue-coverage16.png' if scope == 'mask' else None,
                'mask_delta_rule': verification['delta_rule']['mask'] if scope == 'mask' else None,
                'capture_scope': 'full100-only; inherited six stages are geometry compatibility, not scheduled capture',
                'capture_or_acceptance': False,
            }
            assert spec['stages'] == original_spec['stages']
            assert len(spec['inputs']) == len(manifest['inputs']) == 8
            assert not any(k in spec for k in ['diagnostic', 'g_only_diagnostic', 'native_public_geometry_reference', 'prior_asset'])
            write_json(root / 'shape-spec.json', spec)
            for path in mask_refs(spec):
                f = root / path
                assert f.is_file() and sha(f.read_bytes()) == mask_hashes['masks/' + f.name]
            counts_by_delta = {str(int(value)): int(np.sum(delta[..., channel] == value))
                               for value in np.unique(delta[..., channel])} if scope else {'0': int(base.shape[0] * base.shape[1])}
            row = {
                'round': round_name, 'scope': scope or 'control', 'channel': 'RGB'[channel] if channel is not None else None,
                'first_input_id': first_id, 'flat_input_id': 'st00_flat128',
                'shape_spec': 'inputs/rounds/' + round_name + '/shape-spec.json',
                'input_manifest': 'inputs/rounds/' + round_name + '/inputs/manifest.json',
                'first_source': 'inputs/rounds/' + round_name + '/inputs/' + first_id + '.png',
                'shape_spec_sha256': sha((root / 'shape-spec.json').read_bytes()),
                'input_manifest_sha256': sha((png_dir / 'manifest.json').read_bytes()),
                'source_sha256': png_sha, 'source_bytes': png.stat().st_size, 'icc_sha256': sha(icc),
                'channel_min_RGB': actual.min(axis=(0, 1)).tolist(), 'channel_max_RGB': actual.max(axis=(0, 1)).tolist(),
                'delta_min_RGB': delta.min(axis=(0, 1)).tolist(), 'delta_max_RGB': delta.max(axis=(0, 1)).tolist(),
                'delta_nonzero_pixels_RGB': np.sum(delta != 0, axis=(0, 1)).tolist(),
                'selected_delta_histogram': counts_by_delta, 'source_background_rgb': spec['world']['background_rgb'],
                'geometry_sha256': geometry_sha, 'geometry_equal': True, 'stages_equal': True,
                'scheduled_stages': ['full100'], 'flat_sha256': sha((png_dir / 'st00_flat128.png').read_bytes()),
                'all_eight_loader_input_hashes_match': all(sha((png_dir / e['file']).read_bytes()) == e['sha256'] for e in manifest['inputs']),
                'compatibility_inputs_not_scheduled': True, 'no_clipping': True, 'new_capture': False,
            }
            plans.append({'id': round_name, 'shape_spec': 'rounds/' + round_name + '/shape-spec.json',
                'input_dir': 'rounds/' + round_name + '/inputs', 'first_input_id': first_id,
                'flat_input_id': 'st00_flat128', 'scheduled_stages': ['full100'], 'scheduled_input_ids': [first_id, 'st00_flat128']})
            verification['rounds'].append(row)
        write_json(staging / 'rounds.json', {'schema': 1, 'study_id': verification['study_id'],
            'status': 'prepared_inputs_only', 'scope': 'full100-only, not six-pose capture',
            'order': [r[0] for r in ROUNDS], 'rounds': plans, 'seven_point_consumed': False})
        assert verification['rounds'][0]['source_sha256'] == verification['rounds'][-1]['source_sha256'] == EXPECTED_SOURCE_HASHES['inputs/st01_rgb_star_d16.png']
        files = [p for p in staging.rglob('*') if p.is_file()]
        verification['package_files'] = {p.relative_to(staging).as_posix(): {'sha256': sha(p.read_bytes()), 'bytes': p.stat().st_size} for p in sorted(files)}
        verification['package_file_count'] = len(files)
        verification['package_bytes'] = sum(p.stat().st_size for p in files)
        verification['generator_sha256'] = sha(Path(__file__).read_bytes())
        staging.rename(OUTPUT)
        write_json(VERIFICATION, verification)
    print(json.dumps({'status': verification['status'], 'rounds': len(plans), 'scheduled_stages': ['full100'],
        'files': verification['package_file_count'], 'bytes': verification['package_bytes'],
        'source_verification': relative(VERIFICATION), 'seven_point_consumed': False}, indent=2))


if __name__ == '__main__':
    main()
