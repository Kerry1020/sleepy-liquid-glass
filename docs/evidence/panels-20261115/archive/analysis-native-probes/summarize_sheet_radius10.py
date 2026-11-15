#!/usr/bin/env python3
"""Report the already frozen Sheet API-input response without refitting."""
from pathlib import Path
import collections
import csv
import hashlib
import json
import numpy as np

ROOT = Path(__file__).resolve().parent
O = ROOT / 'sheet-radius10'
A = O / 'phaseA-fixed'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text())

def save(name, value):
    (O / name).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')

def writecsv(name, rows):
    with (O / name).open('w', newline='') as f:
        w = csv.DictWriter(f, list(rows[0]))
        w.writeheader()
        w.writerows(rows)

def fmt(value):
    return 'unresolved' if value is None else f'{value:.3f}'

plan = read(ROOT / 'sheet-body6-plan.json')
assert plan['revision'] == 2 and plan['excluded_radii'] == [6]
assert plan['runtime_routing_disclosure']['same_Gaussian_execution_path'] is False
exact = read(O / 'exact-control-comparison.json')
assert exact['all_capture_geometry_exact']
alert_controls = [r for r in exact['rows'] if r['group'] == 'capture' and r['key'][2] == 'alert']
assert len(alert_controls) == 2
assert all(i['raw_rgba']['identical'] for r in alert_controls for i in r['images'] if i['kind'] == 'window')
assert all(i['raw_rgba']['identical'] for r in exact['rows'] if r['group'] == 'background' for i in r['images'] if i['kind'] == 'window')
for name in ['geometry-and-mask.json', 'all-shape-geometry-audit.json', 'exclusions.json']:
    assert read(O / name) == read(A / name), name

aa = read(O / 'phaseA-local/Sheet-S07-local-contours.json')
bb = read(O / 'Sheet-S07-local-contours.json')
index = lambda data, platform: {r['world_y_pt']: r for r in data if r['platform'] == platform}
ar, br, nr = index(aa, 'candidate'), index(bb, 'candidate'), index(bb, 'native')
assert list(sorted(br)) == plan['S07']['row_centers_pt']
assert len(ar) == len(br) == len(nr) == 14
assert index(aa, 'native') == nr
rowcomparisons = []
for y in sorted(br):
    rowcomparisons.append({
        'world_y_pt': y, 'inward_distance_pt': y - 317.5,
        'native': nr[y], 'phaseA_true12_shared': ar[y], 'phaseB_true10_local': br[y],
        'interpretation': 'Only eligible rows support fine scalar comparison. Failed rows and unresolved raw crossings remain descriptive; no fitted radius or2D map.',
    })
save('phaseA-phaseB-S07-all14.json', rowcomparisons)

mae_a = read(A / 'candidate-fixed-roi-delta.json')
mae_b = read(O / 'candidate-fixed-roi-delta.json')
key = lambda r: (r['input'], r['carrier'], r['segment'], tuple(r['bin_pt']))
am = {key(r): r for r in mae_a}
assert len(am) == len(mae_b) == 180
roi = []
for b in mae_b:
    a = am[key(b)]
    assert a['clear_original_pixels'] == b['clear_original_pixels']
    assert a['native_mean_rgb'] == b['native_mean_rgb']
    row = {k: b[k] for k in ['input', 'carrier', 'segment', 'context', 'bin_pt', 'clear_original_pixels']}
    row.update(native_mean_rgb=b['native_mean_rgb'], phaseA_native_mae_rgb=a['candidate_native_mae_rgb'], phaseB_native_mae_rgb=b['candidate_native_mae_rgb'], phaseB_minus_phaseA_native_mae_rgb=(np.array(b['candidate_native_mae_rgb']) - a['candidate_native_mae_rgb']).tolist(), phaseA_mean_rgb=a['candidate_mean_rgb'], phaseB_mean_rgb=b['candidate_mean_rgb'], phaseB_minus_phaseA_mean_rgb=(np.array(b['candidate_mean_rgb']) - a['candidate_mean_rgb']).tolist())
    if row['carrier'] == 'alert':
        assert row['phaseA_native_mae_rgb'] == row['phaseB_native_mae_rgb']
        assert row['phaseA_mean_rgb'] == row['phaseB_mean_rgb']
    roi.append(row)
save('phaseA-phaseB-fixed-roi-all180.json', roi)
roi_csv = []
for r in roi:
    flat = {k: r[k] for k in ['input', 'carrier', 'segment', 'context', 'clear_original_pixels']}
    flat['bin_pt'] = str(r['bin_pt'])
    for name in ['native_mean_rgb', 'phaseA_native_mae_rgb', 'phaseB_native_mae_rgb', 'phaseB_minus_phaseA_native_mae_rgb', 'phaseA_mean_rgb', 'phaseB_mean_rgb', 'phaseB_minus_phaseA_mean_rgb']:
        for channel, value in zip('rgb', r[name]):
            flat[name + '_' + channel] = value
    roi_csv.append(flat)
writecsv('phaseA-phaseB-fixed-roi-all180.csv', roi_csv)

track_summaries = []
for filename, identity in [
    ('straight-tracks.csv', ['input', 'carrier', 'segment', 'context', 'representation', 'distance_pt', 'clear_original_pixels']),
    ('corner-raster-tracks.csv', ['input', 'carrier', 'corner', 'depth_pt', 'distance_pt', 'masked', 'longest_clear_run_px', 'derivative_eligible']),
    ('narrow-rim-tracks.csv', ['carrier', 'segment', 'distance_pt', 'clear_tangent_pixels']),
]:
    with (A / filename).open() as f:
        av = [r for r in csv.DictReader(f) if r['platform'] == 'rim_blur']
    with (O / filename).open() as f:
        bv = [r for r in csv.DictReader(f) if r['platform'] == 'rim_blur']
    makekey = lambda r: tuple(r[k] for k in identity)
    ai = {makekey(r): r for r in av}
    assert len(ai) == len(bv)
    rows = []
    for b in bv:
        a = ai[makekey(b)]
        row = {k: b[k] for k in identity}
        for k in b:
            if k in identity or k == 'platform':
                continue
            if k.startswith(('raw_', 'smooth_', 'd1_', 'd2_')):
                row['phaseA_' + k] = a[k]
                row['phaseB_' + k] = b[k]
                row['phaseB_minus_phaseA_' + k] = float(b[k]) - float(a[k]) if a[k] and b[k] else ''
        if row.get('carrier') == 'alert':
            assert all(v == 0 or v == '' for k, v in row.items() if k.startswith('phaseB_minus_phaseA_'))
        rows.append(row)
    output_name = 'phaseA-phaseB-' + filename
    writecsv(output_name, rows)
    track_summaries.append({'file': output_name, 'row_count': len(rows), 'source_identity_and_masks_equal': True, 'all_alert_deltas_zero': True})
save('phaseA-phaseB-track-controls.json', track_summaries)

body_a = read(A / 'body-exterior.json')
body_b = read(O / 'body-exterior.json')
body_key = lambda r: (r['input'], r['carrier'], r['region'])
ba = {body_key(r): r for r in body_a if r['platform'] == 'rim_blur'}
bn = {body_key(r): r for r in body_b if r['platform'] == 'native'}
body = []
for b in body_b:
    if b['platform'] != 'rim_blur':
        continue
    a = ba[body_key(b)]
    n = bn[body_key(b)]
    assert a['n'] == b['n'] == n['n']
    if b['region'] == 'exterior':
        assert a['mean_rgb'] == b['mean_rgb'] == n['mean_rgb']
    body.append({'input': b['input'], 'carrier': b['carrier'], 'region': b['region'], 'native': n, 'phaseA': a, 'phaseB': b})
save('phaseA-phaseB-body-exterior-all.json', body)

rim_a = read(A / 'narrow-rim-diagnostics.json')
rim_b = read(O / 'narrow-rim-diagnostics.json')
ra = {(r['carrier'], r['segment']): r for r in rim_a if r['platform'] == 'rim_blur'}
rn = {(r['carrier'], r['segment']): r for r in rim_b if r['platform'] == 'native'}
rim = [{'carrier': r['carrier'], 'segment': r['segment'], 'native': rn[(r['carrier'], r['segment'])], 'phaseA': ra[(r['carrier'], r['segment'])], 'phaseB': r} for r in rim_b if r['platform'] == 'rim_blur']
save('phaseA-phaseB-rim-all.json', rim)

failed_b = dict(collections.Counter(f for r in br.values() for f in r['failed_gates']))
summary = {
    'status': 'not-parity-accepted',
    'native_eligible_rows': sum(r['eligible'] for r in nr.values()),
    'phaseA_eligible_rows': sum(r['eligible'] for r in ar.values()),
    'phaseB_eligible_rows': sum(r['eligible'] for r in br.values()),
    'total_S07_rows': 14,
    'phaseB_failed_gate_counts': failed_b,
    'all_actual_alert_windows_zero_difference': True,
    'all_geometry_mask_slot_density_source_controls_exact': True,
    'fixed_roi_comparisons': len(roi),
    'causal_scope': 'Same true-radius API12 to10 plus deterministic shared12-band to local-preblur routing; not one common Gaussian execution path.',
    'no_fitted_sigma_or_thickness': True,
    'no_material_dynamic_multisize_or_holdout_acceptance': True,
}
save('decision.json', summary)

report = [
    '# Sheet true-radius API12 → 10: response improved locally, parity rejected',
    '',
    'The response changes in the intended direction in several fixed regions, but it does not match the native Sheet. Native S07 passes all14 rows, phase A12 passes0/14, and phase B10 passes only1/14. The other13 candidate rows fail the unchanged secondary-derivative-peak gate. They remain visible descriptive tracks, not fine correspondence/width evidence. No gate, source shaping, plateau or ROI was changed.',
    '',
    'The sole eligible candidate row, y335.75pt, has raw10–90 width12.324pt versus native9.648pt. Its smoothed50% crossing is96.385pt versus native95.696pt (difference0.689pt; individual sampling floor±0.25pt), and contrast26.609 versus30.010 encoded counts. The matching phase A row is ineligible; its descriptive width12.579pt, crossing97.158pt and contrast23.425 are retained for context, not treated as accepted location measurements. Improving the candidate to one identifiable row does not establish a complete material match.',
    '',
    '## Controls, routing and provenance',
    '',
    'Both complete actual Alert Windows are RGBA pixel-identical to phase A, as are both plain-background Windows. All observed pane/canvas/unit-basis, source mapping, Window placement, foreground slots and content density are exact. Geometry/mask/exclusion definitions and all32 shape/carrier audits are unchanged. Sheet changes remain within the recorded pane: coordinate402200 changed Window pixels, maximum channel delta6; shapes150901, maximum7. Full-screen system-overlay changes are separately retained with exact coordinates; full-display equality is not claimed.',
    '',
    'The build receipt and source hash freeze were bound before phase B first decode. GlassHost.kt SHA2565b4236fdf6340b4b42b8a783920b75e11359c6b52598a803322b7399ff3c820d and GlassFilterBands.kt SHAd0fcf91e572f2270de6d3a2316fc0cbc1e2667c482a0390eb6565288e2c4e8f2 satisfy the required routing-source binding. Receipt SHA50ecb5966250592be904bf2a1be5bb2415acc4214fa6b2c9034f37cce76fe930 declares successful build and unchanged build/test sources. RawRGB equals ICC-normalized sRGB for all compared images. Rejected-display images were not decoded.',
    '',
    'Phase A true-radius12 reuses exact shared12; phase B true-radius10 uses the local preblur fallback because only2.5/12/16 bands exist. Thus this is the deployed API-input engineering response, including the deterministic execution-route switch. It does not independently isolate numerical radius in one Gaussian path and cannot recover physical sigma or thickness. No extra global band/dependency or radius6 was introduced. Dark was not captured; it retains its declared original factory/null path, without a dark pixel-parity claim.',
    '',
    '## All14 S07 rows',
    '',
    'Widths below are descriptive wherever a row fails. “unresolved” means raw crossings are missing/nonunique; smoothing does not replace the raw result. The full per-row gate data are in `phaseA-phaseB-S07-all14.json`.',
    '',
    '| y(pt) | Native raw width | A12 raw width | B10 raw width | Native50% | A1250% | B1050% | Native/A12/B10 contrast | B gate |',
    '|---:|---:|---:|---:|---:|---:|---:|---|---|',
]
for y in sorted(br):
    vals = [nr[y], ar[y], br[y]]
    widths = [fmt(v.get('descriptive_raw_10_90_width_pt')) for v in vals]
    locs = [fmt(v['cross50'][0] if len(v['cross50']) == 1 else None) for v in vals]
    contrasts = '/'.join(fmt(v['contrast_amplitude']) for v in vals)
    report.append(f'|{y:.2f}|{widths[0]}|{widths[1]}|{widths[2]}|{locs[0]}|{locs[1]}|{locs[2]}|{contrasts}|{"pass" if br[y]["eligible"] else "secondary peak>0.8"}|')
report += [
    '',
    '## Fixed region response',
    '',
    'All180 independent segment/bin comparisons are retained in `phaseA-phaseB-fixed-roi-all180.json` and CSV. Each keeps its original primary, corner-proximal or backing-context label. The table below shows every light Sheet primary interior bin as phaseB minus phaseA native RGB MAE; negative is a smaller encoded-color error for that channel. This is descriptive local error, not inferred transmission, dispersion or an aggregate parity score.',
    '',
    '| Source | Segment | Inward bin(pt) | Δ native MAE(R,G,B counts) |',
    '|---|---|---|---|',
]
for r in roi:
    if r['carrier'] == 'sheet' and r['context'] == 'primary' and r['bin_pt'][0] >= 0:
        report.append('|'+r['input'].replace('panel_probe_', '')+'|'+r['segment']+'|'+str(r['bin_pt'])+'|'+', '.join(f'{v:+.3f}' for v in r['phaseB_minus_phaseA_native_mae_rgb'])+'|')
report += [
    '',
    'The shapes top-left4..12pt region improves RGB MAE by[1.005,1.321,0.349]counts and12..20 by[0.517,0.609,0.492]. Coordinate top-left4..12 improves[0.078,0.118,0.580]. This does not extend uniformly to the rim: shapes top-right0..2 regresses[0.137,0.433,0.653], shapes top-right2..4 regresses[0.278,0.760,0.927], and coordinate left2..4 blue error increases1.848counts. All other bins and mixed-context diagnostics remain reported rather than averaged away.',
    '',
    'Every fixed straight track, corner raster slice and narrow-rim track has a row-matched phaseA/phaseB delta export. The sampling support, mask, derivative eligibility and all Alert values are exact controls. Body/exterior and rim native/A/B objects are retained separately. Exterior means are identical to native for each source/carrier, so the changes are not an exterior-scrim adjustment. The fully masked middle-left body diagnostic stays unresolved; no substitute region was selected.',
    '',
    '## Rim, complete-feature and interpretation limits',
    '',
    'Sheet top-center rim tracks remain foreground-masked and unresolved. The bottom neutral track has native peak excess28.290encoded-luma counts; phase B remains above it. Its apparent halfheight width has mixed backing context, so it is not a physical thickness measurement or isolated softness estimate. Narrow peaks that fail the3-original-pixel coverage gate retain unresolved FWHM. No brightness-to-thickness or brightness-to-stretch conversion is made.',
    '',
    'All16 source shapes across both carriers remain in the original audit. None has a fully clear, unclipped95%-mass material support, so no complete centroid or2D mapping was forced. S07 remains a scalar local contour. Backing-control appearance and broad-footprint differences between platforms remain systematic limitations.',
    '',
    'The parent supports/regions/gates were frozen before the first native/baseline analysis; the exact S07 localization was operationalized inside those supports after that initial review and before these candidates. This candidate comparison does not retroactively make S07 an independent confirmatory feature. The two selected inputs are calibration, not held-out tests. There was no warp, registration, fitted translation, source substitution, new ROI, free optical fit or overall similarity percentage. No static result here establishes dynamic, multi-size or whole-product parity.',
    '',
    'Decision: retain the experiment as a documented API-response result; do not mark the Sheet material aligned. A further implementation change needs its own frozen hypothesis and controls, without lowering these visibility gates.',
]
bottom = next(r for r in rim if r['carrier'] == 'sheet' and r['segment'] == 'bottom')
report = '\n'.join(report) + '\n'
report = report.replace('phase B remains above it.', f'phaseA excess{bottom["phaseA"]["peak_excess_luma"]:.3f} and phaseB{bottom["phaseB"]["peak_excess_luma"]:.3f} remain above it.')
(O / 'report.md').write_text(report)
summary['report_sha256'] = sha(O / 'report.md')
save('decision.json', summary)
save('output-manifest.json', {'report_sha256': sha(O / 'report.md'), 'summary_script_sha256': sha(Path(__file__)), 'files': {str(p): sha(p) for p in [O / 'build-before-decode.json', O / 'run-input-freeze.json', O / 'exact-control-comparison.json', O / 'phaseA-phaseB-S07-all14.json', O / 'phaseA-phaseB-fixed-roi-all180.json', O / 'phaseA-phaseB-body-exterior-all.json', O / 'phaseA-phaseB-rim-all.json', O / 'decision.json']}})
print(json.dumps(summary, indent=2))
