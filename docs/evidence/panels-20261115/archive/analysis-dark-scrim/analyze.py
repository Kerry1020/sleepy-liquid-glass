from pathlib import Path
import json, hashlib
import numpy as np
from PIL import Image

DEST = Path(__file__).resolve().parent
P = DEST.parent
OLD = P / 'panels-current-baseline-20261115'
NEW = P / 'panels-dark-scrim-20261115'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def arr(p): return np.array(Image.open(p).convert('RGBA'), dtype=np.int16)
def diff(a, b):
    assert a.shape == b.shape and a.size > 0
    d = np.abs(a - b)
    return dict(max_abs=int(d.max()), changed_channels=int(np.count_nonzero(d)), mean_abs=float(d.mean()))
def window_roi(a, capture, rect):
    origin = capture['window_geometry']['captured_surface_screen_rect_px']
    x1, y1, x2, y2 = [rect[i] - origin[i % 2] for i in range(4)]
    assert 0 <= x1 < x2 <= a.shape[1] and 0 <= y1 < y2 <= a.shape[0]
    return a[y1:y2, x1:x2]

old_matrix = json.loads((OLD / 'matrix.json').read_text())
new_matrix = json.loads((NEW / 'matrix.json').read_text())
old_captures = {(c['scene'], c['phase']): c for c in old_matrix['captures']}
rows = []
for c in new_matrix['captures']:
    o = old_captures[(c['scene'], c['phase'])]
    ow, nw = arr(OLD / o['window_png']), arr(NEW / c['window_png'])
    os, ns = arr(OLD / o['screen_png']), arr(NEW / c['screen_png'])
    assert o['window_geometry']['captured_surface_screen_rect_px'] == c['window_geometry']['captured_surface_screen_rect_px']
    l, t, r, b = [55, 515, 695, 859] if c['carrier'] == 'alert' else [16, 635, 734, 1318]
    deep = [l + 80, t + 80, r - 80, b - 80]
    exterior = [64, 352, 686, 440]
    x1, y1, x2, y2 = exterior
    base = arr(NEW / c['display_baseline_png'])[y1:y2, x1:x2, :3].astype(float)
    current = ns[y1:y2, x1:x2, :3].astype(float)
    previous = os[y1:y2, x1:x2, :3].astype(float)
    rows.append(dict(
        scene=c['scene'], theme=c['theme'], carrier=c['carrier'],
        full_actual_window_rgba=diff(ow, nw),
        visible_app_screen_rgba=diff(os[80:1302], ns[80:1302]),
        deep_pane_screen_roi_px=deep,
        deep_pane_rgba=diff(window_roi(ow, o, deep), window_roi(nw, c, deep)),
        exterior_roi_px=exterior,
        exterior_old_gain_zero_intercept_rgb=(np.sum(base * previous, axis=(0, 1)) / np.sum(base * base, axis=(0, 1))).tolist(),
        exterior_new_gain_zero_intercept_rgb=(np.sum(base * current, axis=(0, 1)) / np.sum(base * base, axis=(0, 1))).tolist(),
    ))

record = dict(
    scope='Exterior dim correction only; not thickness/refraction acceptance',
    old_matrix_sha256=sha(OLD / 'matrix.json'), new_matrix_sha256=sha(NEW / 'matrix.json'),
    analysis_policy='Raw RGBA strict controls. Window separate from screen; screen coordinates mapped using observed Window rectangle. Visible screen excludes system-bar top80/bottom32. Fixed historical exterior ROI; deep optical body rectangle inset80px is not full optical contour. No geometric image transforms.',
    light_full_window_unchanged=all(r['full_actual_window_rgba']['max_abs'] == 0 for r in rows if r['theme'] == 'light'),
    light_visible_screen_unchanged=all(r['visible_app_screen_rgba']['max_abs'] == 0 for r in rows if r['theme'] == 'light'),
    dark_alert_full_window_unchanged=all(r['full_actual_window_rgba']['max_abs'] == 0 for r in rows if r['theme'] == 'dark' and r['carrier'] == 'alert'),
    all_deep_pane_unchanged=all(r['deep_pane_rgba']['max_abs'] == 0 for r in rows),
    results=rows,
)
(DEST / 'analysis.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({k: v for k, v in record.items() if k != 'results'}, indent=2))
for r in rows:
    print(r['scene'], 'gain', np.round(r['exterior_old_gain_zero_intercept_rgb'], 4).tolist(), '->', np.round(r['exterior_new_gain_zero_intercept_rgb'], 4).tolist(), 'window max', r['full_actual_window_rgba']['max_abs'], 'deep max', r['deep_pane_rgba']['max_abs'], 'screen max', r['visible_app_screen_rgba']['max_abs'])
