#!/usr/bin/env python3
"""Freeze frost intervention subgroups using r2 calibration inputs only.

No r3 capture, image, result, or analysis is read by this script. These are
calibration selected diagnostics, not preregistered or held-out validation.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda p: json.loads(Path(p).read_text())
index = HERE / 'witness/android-matched-native-v1/android-quadratic-witness-r1/index-original.json'
row = next(c for c in read(index)['captures'] if c['stage_id'] == 'ingress75')
array_path = HERE / 'analysis-android-v1_1/ingress75-world-grid.npz'
native_path = HERE / 'analysis-native-v1_1/ingress75-world-grid.npz'
target_path = HERE / 'primary-ingress75-excessB-mask.png'
plan_path = HERE / 'analysis-plan.json'
plan = read(plan_path)
sources = {r['role']: Path(r['source_png']) for r in plan['source_packets']}
for r in plan['source_packets']:
    assert sha(r['source_png']) == r['source_sha256']
data, native = np.load(array_path), np.load(native_path)
x, y = data['x'], data['y']
assert np.array_equal(x, native['x']) and np.array_equal(y, native['y'])
target = np.asarray(Image.open(target_path)) > 0
assert target.shape == x.shape and target.sum() == 283
left, top, width, height = row['actual_carrier_bounds_world_xywh']
cx, cy, radius = left + width / 2, top + height / 2, height / 2
dx = x - np.clip(x, cx - (width - height) / 2, cx + (width - height) / 2)
dy = y - cy
length = np.hypot(dx, dy)
inset = radius - length
nx, ny = dx / np.maximum(length, 1e-12), dy / np.maximum(length, 1e-12)
depth = 7.8 * np.maximum(1 - inset / 7.5, 0) ** 2
qx, qy = x - depth * nx, y - depth * ny
g = (np.asarray(Image.open(sources['witness']), dtype=float)[..., 1]
     - np.asarray(Image.open(sources['control']), dtype=float)[..., 1])
world_scale = np.asarray(row['source_layout_geometry']['layout_size_px']) / row['source_layout_geometry']['density'] / [375, 667]
px, py = qx / world_scale[0] * 2 - .5, qy / world_scale[1] * 2 - .5
ix, iy = np.floor(px).astype(int), np.floor(py).astype(int)
fx, fy = px - ix, py - iy
assert ix.min() >= 0 and iy.min() >= 0 and ix.max() < g.shape[1] - 1 and iy.max() < g.shape[0] - 1
source_g = (g[iy, ix] * (1-fx) * (1-fy) + g[iy, ix+1] * fx * (1-fy)
            + g[iy+1, ix] * (1-fx) * fy + g[iy+1, ix+1] * fx * fy)
masks = {'target': target, 'reverse68_sourceG_gt24': target & (source_g > 24),
         'neutral138_sourceG_le4': target & (source_g <= 4),
         'frost_band222_inset1_5_to7': target & (inset >= 1.5) & (inset <= 7)}
assert [int(m.sum()) for m in masks.values()] == [283, 68, 138, 222]
old_g = data['raw_witness_minus_control'][..., 1]
native_g = native['raw_witness_minus_control'][..., 1]
q = lambda a: np.percentile(a, [0, 10, 50, 90, 100]).tolist()
assert abs(np.median(old_g[masks['reverse68_sourceG_gt24']]) - 46.22841546210552) < 1e-9
out = HERE / 'r2-frost-subgroups-frozen-v1'
out.mkdir(exist_ok=False)
np.savez_compressed(out / 'masks.npz', x=x, y=y, source_g=source_g, inset=inset, **masks)
for name, m in masks.items():
    Image.fromarray(m.astype(np.uint8)*255).save(out / (name + '.png'))
report = {'scope': 'R2 calibration-derived frost intervention diagnostics; not held-out or native inverse mapping',
          'r3_read': False, 'script_sha256': sha(__file__),
          'equation': 'q=p-7.8*max(1-inset/7.5,0)^2*n; original source index=q/world_scale*2-.5',
          'actual_source_world_scale_xy': world_scale.tolist(),
          'inputs': {str(p): sha(p) for p in [index, array_path, native_path, target_path, plan_path, *sources.values()]},
          'masks': {}, 'files': {p.name: sha(p) for p in sorted(out.iterdir()) if p.is_file()}}
for name, m in masks.items():
    report['masks'][name] = {'samples': int(m.sum()), 'area_pt2': float(m.sum()/16),
                           'sourceG_q0_10_50_90_100': q(source_g[m]),
                           'nativeG_q0_10_50_90_100': q(native_g[m]),
                           'r2G_q0_10_50_90_100': q(old_g[m]), 'inset_q0_10_50_90_100': q(inset[m])}
(out / 'freeze.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'output': str(out), 'freeze_sha256': sha(out/'freeze.json'), 'masks': report['masks']}, indent=2))
