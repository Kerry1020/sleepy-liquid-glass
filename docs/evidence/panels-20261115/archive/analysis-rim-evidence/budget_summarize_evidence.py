"""Summarize frozen budget outputs; no new image decoding or fitted parameters."""
from pathlib import Path
from collections import Counter, defaultdict
import csv
import hashlib
import json

O = Path(__file__).resolve().parent


def read(name):
    return json.loads((O / name).read_text())


def write(name, value):
    (O / name).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def zero(item):
    return item['changed_channels'] == 0 and item['max_abs'] == 0


def counts(rows):
    c = Counter(r['direction'] for r in rows)
    return {k: c[k] for k in ('improved', 'regressed', 'unchanged')}


def groups(rows, fields):
    buckets = defaultdict(list)
    for row in rows:
        buckets[tuple(row.get(f) for f in fields)].append(row)
    return [{**dict(zip(fields, key)), **counts(value)}
            for key, value in sorted(buckets.items(), key=lambda x: str(x[0]))]


pc = read('budget-controls.json')
pt = read('budget-primary-controls.json')
hc = read('budget-history-controls.json')['rows']
probes = read('budget-all-reference-probe-metrics.json')
history = read('budget-history-metric-changes.json')
corners = read('budget-history-corner16-metrics.json')['metrics']
primary = read('budget-124-summary.json')
clip = read('budget-history-clipping-pointwise.json')

dark_checks = []
light_checks = []
sheet_checks = []
for row in hc:
    if row['theme'] == 'dark':
        for ref in ('additive', 'original', 'screen'):
            for domain in ('window', 'visible_app'):
                key = domain + '_vs_' + ref
                dark_checks.append({'input': row['input'], 'carrier': row['carrier'],
                                    'field': key, **row[key], 'passed': zero(row[key])})
    elif row['carrier'] == 'alert':
        keys = ['deep80_vs_additive', 'deep80_vs_screen',
                'neutral_top_full_declared_display',
                'neutral_top_actual_window_intersection',
                'neutral_top_display_vs_screen', 'neutral_top_window_vs_screen']
        for key in keys:
            light_checks.append({'input': row['input'], 'field': key,
                                 **row[key], 'passed': zero(row[key])})
        for name in ('original_body_rois', 'original_body_rois_vs_screen'):
            for roi, value in row[name].items():
                light_checks.append({'input': row['input'], 'field': name,
                                     'roi': roi, **value, 'passed': zero(value)})
    else:
        # Same Sheet10 reference exists in prior screen batch, but not in additive/original history.
        for key in ('window_vs_screen', 'visible_app_vs_screen'):
            sheet_checks.append({'input': row['input'], 'field': key,
                                 **row[key], 'passed': zero(row[key])})

probe_sheet_checks = []
probe_body_checks = []
for row in pc:
    if row['carrier'] == 'sheet':
        for key in ('actual_window', 'visible_app_screen', 'deep80_rgba'):
            probe_sheet_checks.append({'input': row['input'], 'field': key,
                                       **row[key], 'passed': zero(row[key])})
    else:
        probe_body_checks.append({'input': row['input'], 'field': 'deep80_rgba',
                                  **row['deep80_rgba'], 'passed': zero(row['deep80_rgba'])})
        for roi, value in row['original_body_rois'].items():
            probe_body_checks.append({'input': row['input'], 'field': 'original_body_rois',
                                      'roi': roi, **value, 'passed': zero(value)})

new_clip = []
new_clip_by_scene = []
for ref in ('additive', 'original', 'native', 'screen'):
    for end in ('0', '255'):
        key = 'new' + end + '_vs_' + ref + '_channels'
        inward = [r for r in clip if r['distance_pt'] >= 0]
        new_clip.append({'reference': ref, 'endpoint': end,
                         'channels': sum(sum(r[key]) for r in inward),
                         'rows_with_new_endpoint': sum(any(r[key]) for r in inward),
                         'sample_policy': 'fixed inward samples; overlapping tracks retained'})
        for scene in sorted({r['scene'] for r in inward}):
            selected = [r for r in inward if r['scene'] == scene]
            new_clip_by_scene.append({'scene': scene, 'reference': ref, 'endpoint': end,
                                      'channels': sum(sum(r[key]) for r in selected),
                                      'rows_with_new_endpoint': sum(any(r[key]) for r in selected)})

probe_alert = [r for r in probes if r['carrier'] == 'alert']
probe_whole = [r for r in probe_alert if r['scope'] == 'whole_fixed_scan']
history_straight = [r for r in history if r['mode'] == 'raw' and r['region'] == 'straight']
history_corner = [r for r in corners if r['scope'] == 'whole_fixed_scan']

regressions = {
    'policy': 'All frozen scopes retained; overlapping bins/whole scans are not independent samples. '
              'History corner derivatives use the recomputed 16-contiguous-pixel support only; '
              'legacy 7-support exported derivative columns are excluded.',
    'probe_alert_all_scopes': [r for r in probe_alert if r['direction'] == 'regressed'],
    'history_straight_raw_mode': [r for r in history_straight if r['direction'] == 'regressed'],
    'history_corner16_all_scopes': [r for r in corners if r['direction'] == 'regressed'],
    'history_body_raw_mode': [r for r in history if r['mode'] == 'raw' and r['region'] == 'body'
                              and r['direction'] == 'regressed'],
}
write('budget-regressions.json', regressions)

result = {
    'status': 'mixed_optical_result_not_native_appearance_acceptance',
    'candidate_history': str(O.parent / 'panels-alert-floor-budget-history-r2-20261115'),
    'failed_history_optical_decode': False,
    'metadata_note': 'Some inherited script labels say isolated screen increment; candidate is '
                     'the preregistered budget-normalized headroom exponential. These labels do not '
                     'change any image, region, threshold, reference or numerical calculation.',
    'controls': {
        'dark8_three_references_all_zero': all(r['passed'] for r in dark_checks),
        'dark8_actual_checks': dark_checks,
        'light_alert4_body_deep80_top_additive_and_screen_all_zero':
            all(r['passed'] for r in light_checks),
        'light_alert4_actual_checks': light_checks,
        'light_sheet4_vs_existing_screen_sheet10_all_zero': all(r['passed'] for r in sheet_checks),
        'light_sheet4_screen_sheet10_actual_checks': sheet_checks,
        'light_sheet4_additive_and_original_scope': 'combined radius12to10; not strict unchanged control',
        'new_probe_sheet10_2_all_zero': all(r['passed'] for r in probe_sheet_checks),
        'new_probe_sheet10_actual_checks': probe_sheet_checks,
        'new_probe_alert2_deep80_body_vs_additive_all_zero':
            all(r['passed'] for r in probe_body_checks),
        'new_probe_alert2_actual_checks': probe_body_checks,
        'new_probe_top_actual_checks': pt,
    },
    'primary124': primary,
    'neutral_peaks': read('budget-all-reference-neutral-peaks.json'),
    'history_inward_clipping_vs_each_reference': new_clip,
    'history_inward_clipping_by_scene': new_clip_by_scene,
    'history_new255_vs_screen_rows': [r for r in clip if r['distance_pt'] >= 0
                                      and any(r['new255_vs_screen_channels'])],
    'new_probe_clipping': read('budget-clipping-summary.json'),
    'new_probe_whole_fixed_scan_counts': groups(probe_whole, ['reference', 'track', 'field']),
    'new_probe_whole_fixed_scan_by_input': groups(probe_whole, ['input', 'reference', 'track', 'field']),
    'history_raw_rmse_counts': read('budget-history-summary.json'),
    'history_straight_all_fields_by_background': groups(history_straight, ['scene', 'reference', 'field']),
    'history_corner16_whole_fixed_scan_counts': groups(history_corner, ['scene', 'reference', 'field']),
    'history_corner16_both_scopes_counts': groups(corners, ['scene', 'reference', 'scope', 'field']),
    'all_regressions': 'budget-regressions.json',
    'limits': [
        'No new noise/heldout inputs or parameter fitting.',
        'Encoded working RGB curves do not identify physical thickness or linear-light transport.',
        'Raw neutral native and candidate FWHM have only 2 half-height pixels; unchanged minimum3 gate unresolved.',
        'No registration, warp, ROI movement or mask relaxation.',
        'Top exterior six Window rows are unavailable and separately represented by full-display samples.',
        'History has no body8-only captures.',
        'Mean error counts are not acceptance percentages and cannot establish frame-by-frame dynamic parity.',
    ],
}
write('budget-result.json', result)
assert all(r['passed'] for r in dark_checks + light_checks + sheet_checks + probe_sheet_checks + probe_body_checks)

# Flat regression index links each background/edge/depth/field back to a full JSON row.
index = []
for group, rows in regressions.items():
    if not isinstance(rows, list):
        continue
    for idx, row in enumerate(rows):
        index.append({'group': group, 'json_row': idx, 'input': row.get('input', row.get('scene')),
                      'reference': row['reference'], 'track': row.get('track', row.get('region', 'corner')),
                      'edge_or_corner': row.get('corner', row.get('segment', row.get('name'))),
                      'depth_pt': row.get('depth_pt'), 'scope': row.get('scope', row.get('field')),
                      'field': row['field'], 'baseline_error': row.get('baseline_native_mean_mae', row.get('baseline')),
                      'candidate_error': row.get('candidate_native_mean_mae', row.get('candidate'))})
with (O / 'budget-regression-index.csv').open('w', newline='') as f:
    w = csv.DictWriter(f, list(index[0]))
    w.writeheader()
    w.writerows(index)

print(json.dumps({
    'dark8_controls': len(dark_checks), 'dark_all_zero': result['controls']['dark8_three_references_all_zero'],
    'light_alert_controls': len(light_checks), 'light_sheet10_controls': len(sheet_checks),
    'history_clip': new_clip,
    'probe_counts': result['new_probe_whole_fixed_scan_counts'],
    'regression_counts': {k: len(v) for k, v in regressions.items() if isinstance(v, list)},
}, indent=2))
