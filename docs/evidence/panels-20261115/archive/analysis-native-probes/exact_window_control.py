#!/usr/bin/env python3
"""Unregistered exact accepted-Window control; no material-score fitting."""
from pathlib import Path
import hashlib
import io
import json
import sys
import numpy as np
from PIL import Image, ImageCms

O = Path(__file__).resolve().parent
P = O.parent
control = Path(sys.argv[1]).resolve()
candidate = Path(sys.argv[2]).resolve()
output = (O / sys.argv[3]).resolve()
assert output.is_relative_to(O) and output != O
output.mkdir(exist_ok=True)
assert not (output / 'run-input-freeze.json').exists(), 'Preserve previous control output.'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def save(name, value):
    (output / name).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')

def key(c):
    return c['background'], c.get('theme', 'light'), c.get('carrier', 'background'), c.get('phase', 'background')

matrices = [json.loads((p / 'matrix.json').read_text()) for p in [control, candidate]]
assert all(m['status'] == 'passed' for m in matrices)
captures = [{key(c): c for c in m['captures']} for m in matrices]
backgrounds = [{c['background']: c for c in m['baselines']} for m in matrices]
assert set(captures[0]) == set(captures[1]) and len(captures[1]) == 4
assert set(backgrounds[0]) == set(backgrounds[1]) and len(backgrounds[1]) == 2
assert all(c['phase'] == 'rest' and c['theme'] == 'light' for c in captures[1].values())

files = [Path(__file__), O / 'sheet-body6-plan.json', O / 'sheet-body6-plan.md', O / 'sheet-body6-plan-revisions.json']
for directory, matrix in zip([control, candidate], matrices):
    files += [directory / 'matrix.json', directory / 'capture-result.json', directory / 'capture-plan.json', directory / 'display-restored.json']
    for c in matrix['captures'] + matrix['baselines']:
        files += [directory / c['window_png'], directory / c['screen_png']]
save('run-input-freeze.json', {
    'status': 'before-first-this-candidate-pixel-decode',
    'control_directory': str(control), 'candidate_directory': str(candidate),
    'files': {str(p): sha(p) for p in files},
    'read_only_matrix_declared_accepted_images': True,
    'rejected_display_files_not_decoded': True,
    'no_registration_resize_recenter_warp_parameter_fit': True,
    'no_duplicate_screenshot_files': True,
})

def read(p):
    with Image.open(p) as im:
        rgba = np.asarray(im.convert('RGBA')).copy()
        icc = im.info.get('icc_profile')
        normalized = np.asarray(ImageCms.profileToProfile(
            im.convert('RGB'), ImageCms.ImageCmsProfile(io.BytesIO(icc)),
            ImageCms.createProfile('sRGB'), outputMode='RGB'
        )) if icc else rgba[:, :, :3].copy()
        return rgba, normalized, {
            'path': str(p), 'file_sha256': sha(p), 'mode': im.mode,
            'size_px': list(im.size), 'rgba_sha256': hashlib.sha256(rgba.tobytes()).hexdigest(),
            'rgb_identical_to_icc_normalized_srgb': bool(np.array_equal(rgba[:, :, :3], normalized)),
            'icc_sha256': hashlib.sha256(icc).hexdigest() if icc else None,
        }

def compare(a, b, origin):
    assert a.shape == b.shape
    d = b.astype(np.int16) - a.astype(np.int16)
    changed = np.any(d != 0, axis=2)
    yy, xx = np.where(changed)
    box = None if not len(xx) else [int(xx.min()), int(yy.min()), int(xx.max()) + 1, int(yy.max()) + 1]
    bands = []
    for y in np.where(changed.any(axis=1))[0]:
        if not bands or y != bands[-1][-1] + 1:
            bands.append([int(y)])
        else:
            bands[-1].append(int(y))
    boxes = []
    for ys in bands:
        ry, rx = np.where(changed[ys[0]:ys[-1] + 1])
        boxes.append({'screen_box_exclusive': [int(rx.min()) + origin[0], ys[0] + origin[1], int(rx.max()) + 1 + origin[0], ys[-1] + 1 + origin[1]], 'changed_pixels': int(len(rx))})
    return {
        'identical': not bool(changed.any()), 'changed_pixels': int(changed.sum()),
        'max_abs_channel_delta': int(np.abs(d).max()),
        'mean_abs_channel_delta': float(np.abs(d).mean()),
        'mean_signed_channel_delta': d.mean(axis=(0, 1)).tolist(),
        'changed_bbox_local_exclusive': box,
        'changed_bbox_screen_exclusive': None if box is None else [box[0] + origin[0], box[1] + origin[1], box[2] + origin[0], box[3] + origin[1]],
        'changed_row_band_boxes': boxes,
    }

def stable_window_geometry(c):
    return {k: v for k, v in c['window_geometry'].items() if k != 'window_identity'}

def slots(c):
    return {m['tag']: {k: m[k] for k in ['actual_root_rect_px', 'actual_window_rect_px', 'actual_screen_rect_px'] if k in m} for m in c['measurements']}

def density(c):
    return [{k: z[k] for k in ['scene', 'surface', 'slot', 'density', 'font_scale'] if k in z} for z in c['content_density_observations']]

rows = []
for group, collection in [('capture', captures), ('background', backgrounds)]:
    for k in sorted(collection[1]):
        a, b = collection[0][k], collection[1][k]
        geometry = {field: a.get(field) == b.get(field) for field in [
            'window_size_px', 'content_origin_in_window_px', 'content_origin_on_screen_px',
            'actual_alert_layout', 'sheet_geometry_comparison', 'background_canvas',
        ] if field in a or field in b}
        if group == 'capture':
            geometry.update(window_geometry=stable_window_geometry(a) == stable_window_geometry(b), foreground_slots=slots(a) == slots(b), content_density=density(a) == density(b))
        row = {'group': group, 'key': list(k) if isinstance(k, tuple) else k, 'geometry_exact': geometry, 'images': []}
        for kind in ['window', 'screen']:
            av, an, am = read(control / a[kind + '_png'])
            bv, bn, bm = read(candidate / b[kind + '_png'])
            origin = b['window_geometry']['captured_surface_screen_rect_px'][:2] if group == 'capture' and kind == 'window' else [0, 0]
            row['images'].append({'kind': kind, 'control': am, 'candidate': bm, 'raw_rgba': compare(av, bv, origin), 'normalized_srgb': compare(an, bn, origin)})
        rows.append(row)

result = {
    'control_directory': str(control), 'candidate_directory': str(candidate),
    'all_capture_geometry_exact': all(all(r['geometry_exact'].values()) for r in rows if r['group'] == 'capture'),
    'rows': rows, 'material_parity_accepted': False,
}
save('exact-control-comparison.json', result)
print(json.dumps({
    'geometry_exact': result['all_capture_geometry_exact'],
    'rows': [{'group': r['group'], 'key': r['key'], 'geometry_exact': r['geometry_exact'],
              'images': [{'kind': i['kind'], 'identical': i['raw_rgba']['identical'], 'changed_pixels': i['raw_rgba']['changed_pixels'], 'bbox': i['raw_rgba']['changed_bbox_screen_exclusive'], 'max_delta': i['raw_rgba']['max_abs_channel_delta']} for i in r['images']]} for r in rows],
}, indent=2))
