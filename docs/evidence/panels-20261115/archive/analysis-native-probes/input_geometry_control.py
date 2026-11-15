#!/usr/bin/env python3
"""Exact, unregistered input-raster geometry control versus Alert-body8.

Read only matrix-declared accepted captures. Bind files before first candidate
decode. Never resample, move, register, or create image copies.
"""
from pathlib import Path
import hashlib
import io
import json
import numpy as np
from PIL import Image, ImageCms

O = Path(__file__).resolve().parent
P = O.parent
B = P / 'panels-alert-body8-20261115'
C = P / 'panels-input-geometry-20261115'
D = O / 'input-geometry'
D.mkdir(exist_ok=True)

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def save(name, value):
    (D / name).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')

def key(c):
    return c['background'], c.get('theme'), c.get('carrier', 'background'), c.get('phase', 'background')

bm = json.loads((B / 'matrix.json').read_text())
cm = json.loads((C / 'matrix.json').read_text())
assert bm['status'] == cm['status'] == 'passed'
bc = {key(c): c for c in bm['captures']}
cc = {key(c): c for c in cm['captures']}
assert set(bc) == set(cc) and len(cc) == 4
bb = {c['background']: c for c in bm['baselines']}
cb = {c['background']: c for c in cm['baselines']}
assert set(bb) == set(cb) and len(cb) == 2

files = [Path(__file__)]
for directory, matrix in [(B, bm), (C, cm)]:
    files += [directory / 'matrix.json', directory / 'capture-result.json']
    for c in matrix['captures'] + matrix['baselines']:
        files += [directory / c['screen_png'], directory / c['window_png']]
for name in ['capture-plan.json', 'display-before.json', 'display-restored.json']:
    if (C / name).exists():
        files.append(C / name)
freeze = D / 'run-input-freeze.json'
assert not freeze.exists(), 'Do not overwrite an existing candidate control.'
save('run-input-freeze.json', {
    'status': 'before-first-input-geometry-candidate-pixel-decode',
    'control': str(B), 'candidate': str(C),
    'files': {str(p): sha(p) for p in files},
    'accepted_matrix_captures_only': True,
    'rejected_display_files_not_decoded': True,
    'no_registration_resampling_recentring_fitting_or_image_copies': True,
})

def decode(p):
    with Image.open(p) as im:
        raw = np.asarray(im.convert('RGBA')).copy()
        icc = im.info.get('icc_profile')
        norm = np.asarray(ImageCms.profileToProfile(
            im.convert('RGB'), ImageCms.ImageCmsProfile(io.BytesIO(icc)),
            ImageCms.createProfile('sRGB'), outputMode='RGB'
        )) if icc else raw[:, :, :3].copy()
        meta = {
            'path': str(p), 'file_sha256': sha(p), 'mode': im.mode,
            'size_px': list(im.size),
            'rgba_sha256': hashlib.sha256(raw.tobytes()).hexdigest(),
            'icc_sha256': hashlib.sha256(icc).hexdigest() if icc else None,
            'rgb_equals_icc_to_srgb': bool(np.array_equal(raw[:, :, :3], norm)),
            'alpha_min_max': [int(raw[:, :, 3].min()), int(raw[:, :, 3].max())],
        }
        return raw, norm, meta

def arraydiff(a, b, origin):
    assert a.shape == b.shape
    delta = b.astype(np.int16) - a.astype(np.int16)
    changed = np.any(delta != 0, axis=2)
    yy, xx = np.where(changed)
    box = None if not len(xx) else [int(xx.min()), int(yy.min()), int(xx.max()) + 1, int(yy.max()) + 1]
    result = {
        'identical': not bool(changed.any()),
        'changed_pixels': int(changed.sum()),
        'max_abs_channel_delta': int(np.abs(delta).max()),
        'mean_abs_channel_delta': float(np.abs(delta).mean()),
        'changed_bbox_local_px_exclusive': box,
        'changed_bbox_screen_px_exclusive': None if box is None else
            [box[0] + origin[0], box[1] + origin[1], box[2] + origin[0], box[3] + origin[1]],
    }
    if len(xx):
        result['first_12_changed_samples'] = [
            {'local_xy_px': [int(x), int(y)],
             'screen_xy_px': [int(x + origin[0]), int(y + origin[1])],
             'body8': a[y, x].tolist(), 'input_geometry': b[y, x].tolist()}
            for y, x in zip(yy[:12], xx[:12])
        ]
    return result

def diffmeta(a, b, path=''):
    if isinstance(a, dict) and isinstance(b, dict):
        result = []
        for k in sorted(set(a) | set(b)):
            if k == 'window_identity':
                continue
            if k not in a or k not in b:
                result.append({'path': path + '/' + k, 'body8': a.get(k), 'input_geometry': b.get(k)})
            else:
                result.extend(diffmeta(a[k], b[k], path + '/' + k))
        return result
    if a != b:
        return [{'path': path, 'body8': a, 'input_geometry': b}]
    return []

rows = []
for k in sorted(cc):
    old, new = bc[k], cc[k]
    geometry_fields = [
        'window_geometry', 'window_size_px', 'content_origin_in_window_px',
        'content_origin_on_screen_px', 'actual_alert_layout',
        'sheet_geometry_comparison', 'measurements', 'background_canvas',
        'content_density_observations', 'native_alert_alignment',
    ]
    metadata = {field: diffmeta(old.get(field), new.get(field), field) for field in geometry_fields}
    metadata = {field: diffs for field, diffs in metadata.items() if diffs}
    row = {'key': list(k), 'geometry_metadata_differences_excluding_window_identity': metadata, 'comparisons': []}
    for kind in ['window', 'screen']:
        name = kind + '_png'
        a, an, am = decode(B / old[name])
        b, bn, bm = decode(C / new[name])
        origin = new['window_geometry']['captured_surface_screen_rect_px'][:2] if kind == 'window' else [0, 0]
        assert am['size_px'] == bm['size_px']
        row['comparisons'].append({
            'kind': kind, 'origin_screen_px': origin,
            'body8': am, 'input_geometry': bm,
            'raw_rgba': arraydiff(a, b, origin),
            'normalized_srgb': arraydiff(an, bn, origin),
        })
    rows.append(row)

backgrounds = []
for k in sorted(cb):
    row = {'input': k, 'comparisons': []}
    for kind in ['window', 'screen']:
        name = kind + '_png'
        a, an, am = decode(B / bb[k][name])
        b, bn, bm = decode(C / cb[k][name])
        row['comparisons'].append({
            'kind': kind, 'body8': am, 'input_geometry': bm,
            'raw_rgba': arraydiff(a, b, [0, 0]),
            'normalized_srgb': arraydiff(an, bn, [0, 0]),
        })
    backgrounds.append(row)

all_window_zero = all(next(c for c in r['comparisons'] if c['kind'] == 'window')['raw_rgba']['identical'] for r in rows)
all_screen_zero = all(next(c for c in r['comparisons'] if c['kind'] == 'screen')['raw_rgba']['identical'] for r in rows)
result = {
    'status': 'strict-pixel-control' if all_window_zero and all_screen_zero else 'nonzero-control-difference',
    'all_four_accepted_actual_windows_raw_rgba_zero_difference': all_window_zero,
    'all_four_accepted_composited_displays_raw_rgba_zero_difference': all_screen_zero,
    'capture_comparisons': rows, 'background_comparisons': backgrounds,
    'scope': 'Only fixed 750x1334 calibration world and the four accepted REST captures. No material parity claim; prior Alert-body8 optical limitations remain.',
}
save('control-comparison.json', result)
print(json.dumps({
    'status': result['status'], 'actualWindow_all_zero': all_window_zero, 'display_all_zero': all_screen_zero,
    'captures': [{'key': r['key'], 'metadata_difference_fields': list(r['geometry_metadata_differences_excluding_window_identity']),
                  'pixels': [{'kind': c['kind'], **c['raw_rgba']} for c in r['comparisons']]} for r in rows],
    'backgrounds': [{'input': r['input'], 'pixels': [{'kind': c['kind'], **c['raw_rgba']} for c in r['comparisons']]} for r in backgrounds],
}, indent=2))
