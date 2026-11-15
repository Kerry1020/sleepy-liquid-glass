#!/usr/bin/env python3
"""Describe frozen Alert power.5 output without changing the analyzer or inputs."""
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent
BASE = OUT.parent / 'analysis-alert-baseline'
CURRENT = json.loads((OUT / 'analysis.json').read_text())
PREVIOUS = json.loads((BASE / 'analysis.json').read_text())
FREEZE = json.loads((OUT / 'frozen-analysis-plan.json').read_text())
CHANGES = [r for r in CURRENT['candidate_comparison']['metric_changes'] if r['mode'] == 'raw']
assert CURRENT['script_sha256'] == FREEZE['analyzer']['sha256']
assert CURRENT['all_raw_equal_icc_srgb']
assert hashlib.sha256((BASE / 'analysis.json').read_bytes()).hexdigest() == FREEZE['baseline']['sha256']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pair(before, after):
    return f'{before:.6f} → {after:.6f}'


def group_counts(rows):
    counts = Counter(r['direction'] for r in rows)
    return '/'.join(str(counts[k]) for k in ('improved', 'regressed', 'unchanged'))


def old_scene(name):
    return next(s for s in PREVIOUS['scenes'] if s['scene'] == name)


control_groups = defaultdict(list)
for row in CURRENT['candidate_comparison']['pixel_controls']:
    control_groups[row['region']].append(row)
assert all(r['changed_pixels'] == 0 for rows in control_groups.values() for r in rows)

lines = [
    '# Alert profile power.5 — frozen historical calibration comparison',
    '',
    'Changing only Alert `refractionProfilePower` from1 to.5 does not resolve the native bend. '
    'Both stripe scenes have larger left/right RGB error; light stripe bottom bending becomes smaller. '
    'The top stripe centroid span increases, but remains far below native. Other background/edge '
    'diagnostics are mixed. These calibration results do not support accepting this candidate as a general improvement.',
    '',
    'The plan isolates the Alert material role in `GlassControlModifier`. Boundary depth60dp and '
    'support20dp remain fixed; Sheet, contour, normals, tint, blur, shine and scrim remain unchanged. '
    'The shader already has a nonlinear rise profile. Power.5 changes the interior shoulder, '
    'and is not a claim about UIKit\'s actual formula. Source SHA matched the plan before decoding.',
    '',
    'Eight REST inputs use only the four public historical calibration backgrounds in light/dark. '
    'They are not an independent test set, production-page proof, or motion validation. '
    'The native reference is real SwiftUI Alert on iOS26.5. '
    'Original375×667pt/dp displays are750×1334px; actual Android pane is[55,515,695,859]px. '
    'No resize, warp, recenter, fitted image translation or source substitution was performed.',
    '',
    'The existing final analyzer and every ROI were frozen before decoding this candidate. '
    'Straight/corner raw RGB and fixed-smoothing first/second derivatives retain the.5pt sample grid. '
    'Derivative smoothing is sigma.75pt,7samples with reflected endpoints. Foreground exclusion '
    'is the union of native and actual Android layout boxes expanded2pt. Native AX is not recovered optical alpha. '
    'Raw encoded RGB and ICC-normalized sRGB were evaluated independently; all inputs declare PNG sRGB '
    'with no ICC, so the tracks are byte-identical. CSVs store one raw track; JSON retains both.',
    '',
    '## Exact unchanged controls',
    '',
    '|Region|Scenes per color track|Changed pixels, raw / ICC|Maximum channel change|',
    '|---|---:|---:|---:|',
]
for region, rows in sorted(control_groups.items()):
    raw = [r for r in rows if r['mode'] == 'raw']
    icc = [r for r in rows if r['mode'] == 'icc_srgb']
    lines.append(f'|{region}|{len(raw)}|{sum(r["changed_pixels"] for r in raw)} / '
                 f'{sum(r["changed_pixels"] for r in icc)}|{max(r["maximum_abs_channel"] for r in rows):.0f}|')
lines += [
    '',
    'Each full Sheet Window is1,000,500pixels and preserves all RGBA values, including color/alpha '
    'under transparent pixels. Alert controls are14,088px outside the pane bbox and19,510px in the '
    'conservative deep region after foreground exclusion. The deep rectangle '
    '[61.5,291.5,313.5,395.5]pt lies beyond every34dp corner extent; it is a guaranteed deep subset, '
    'not a recovered full20dp contour-distance mask. Each action inner8pt control is15,872px and '
    'is listed separately because the child material samples its parent. All32 body ROI errors remain unchanged.',
    '',
    '## Per-scene diagnostic directions',
    '',
    'I/R/U means numerical improvement/regression/unchanged at tolerance1e−9, not a significance '
    'or acceptance test. All small changes remain listed. Each scene has4body,12straight and72corner '
    'raw metrics. Corner scans are horizontal raster slices, include curved coverage/exterior '
    'and the unchanged native/Android dark-scrim difference, and do not measure physical thickness in isolation.',
    '',
    '|Scene|Body I/R/U|Straight I/R/U|Corner I/R/U|',
    '|---|---|---|---|',
]
for row in CURRENT['candidate_comparison']['scene_summary_raw']:
    cells = [row['scene']]
    for region in ('body', 'straight', 'corner'):
        g = row['groups'][region]
        cells.append('/'.join(str(g[k]) for k in ('improved', 'regressed', 'unchanged')))
    lines.append('|' + '|'.join(cells) + '|')
lines += [
    '',
    '## All straight-edge before/after errors',
    '',
    'RGB is encoded8bit RGB RMSE; D1 is RGB/pt; D2 is RGB/pt². Entries are baseline → candidate. '
    'Scores use inward0..<20pt except bottom0..<10pt, exactly as the baseline analyzer.',
    '',
    '|Scene|Edge|RGB RMSE|D1 RMSE|D2 RMSE|',
    '|---|---|---:|---:|---:|',
]
for scene in CURRENT['scenes']:
    name = scene['scene']
    before = old_scene(name)['tracks']['raw']['straight']
    for edge, after in scene['tracks']['raw']['straight'].items():
        cells = [name, edge]
        cells += [pair(before[edge][key], after[key]) for key in
                  ('rgb_rmse_inward_0_20', 'd1_rgb_rmse_inward_0_20', 'd2_rgb_rmse_inward_0_20')]
        lines.append('|' + '|'.join(cells) + '|')
lines += [
    '',
    '## All body ROI errors',
    '',
    'These diagnostics do not change under this isolated edge-shoulder candidate. The two side '
    'gutters have620px each; lower gaps have1,800px each. Native backing controls differ from '
    'the Android fixture, so body RGB discrepancy is not a unique material-transfer estimate.',
    '',
    '|Scene|left_gutter RMSE|right_gutter RMSE|left_gap RMSE|right_gap RMSE|',
    '|---|---:|---:|---:|---:|',
]
for scene in CURRENT['scenes']:
    before = old_scene(scene['scene'])['tracks']['raw']['body']
    after = scene['tracks']['raw']['body']
    cells = [scene['scene']] + [pair(before[k]['rgb_rmse'], after[k]['rgb_rmse']) for k in after]
    lines.append('|' + '|'.join(cells) + '|')
lines += [
    '',
    '## Fixed blue-feature centroid response',
    '',
    '|Trait|Band|Native span pt|Baseline span pt|Power.5 span pt|',
    '|---|---|---:|---:|---:|',
]
for scene in CURRENT['scenes']:
    if not scene['scene'].startswith('color_stripes-'):
        continue
    before = old_scene(scene['scene'])['tracks']['raw']['blue_feature_tracks']
    for band, after in scene['tracks']['raw']['blue_feature_tracks'].items():
        lines.append(f'|{scene["scene"].split("-")[-1]}|{band}|'
                     f'{after["native"]["centroid_x_range_pt"]:.6f}|'
                     f'{before[band]["android"]["centroid_x_range_pt"]:.6f}|'
                     f'{after["android"]["centroid_x_range_pt"]:.6f}|')
lines += [
    '',
    'The frozen window is x60.25..<96pt with positive `B−(R+G)/2` weights. '
    'This is color-response bending in original world coordinates, not identified stripe correspondence '
    'or physical ray displacement. The top/bottom/body bands and all masks match baseline. '
    'A larger span alone cannot accept a profile because coverage, color and blur can also change it.',
    '',
    '![Unshifted fixed blue-feature centroid paths](blue-feature-bend-comparison.png)',
    '',
    '## Complete corner data and limits',
    '',
    '[corner-comparison.md](corner-comparison.md) retains all192corner/depth rows with RGB/D1/D2 '
    'baseline → candidate, including every regression and unchanged metric. '
    '`analysis.json` records all1,408raw/ICC before-after metrics, all controls, input hashes '
    'and unchanged sample counts. CSVs retain fixed raw RGB/smoothed/D1/D2 samples; '
    'foreground gaps remain masked and derivatives never cross those gaps. '
    'Existing phase diagnostics are marked unidentified and never shift either image.',
    '',
    'Dark exterior response remains native≈.52 and Android≈.40; power.5 leaves this unchanged. '
    'The narrower/wider color-centroid response and mixed error changes do not establish '
    'physical thickness, universal optics, or a reproduction percentage. '
    'No noise holdouts were read and no dynamic or other-control work was performed.',
    '',
    '## Provenance',
    '',
    f'- Analyzer SHA256 `{CURRENT["script_sha256"]}` (reused in place).',
    f'- Baseline analysis SHA256 `{FREEZE["baseline"]["sha256"]}`.',
    f'- Candidate analysis SHA256 `{digest(OUT / "analysis.json")}`.',
    f'- Predecode freeze SHA256 `{digest(OUT / "frozen-analysis-plan.json")}`.',
    f'- Plan SHA256 `{FREEZE["plan"]["sha256"]}`.',
    f'- Candidate source SHA256 `{FREEZE["source"]["sha256"]}`.',
    '',
    'The original baseline and rejected frost8 artifacts were not modified. '
    'The report/figure builder reads only existing analyzer CSV/JSON output.',
]
(OUT / 'README.md').write_text('\n'.join(lines) + '\n')

corner = [
    '# All frozen corner/depth comparisons', '',
    'Historical calibration only. Same samples, masks and algorithm as baseline; no curve/image fitting. '
    'Horizontal scans include curved coverage/exterior and scrim confounds. Units: RGB, RGB/pt, RGB/pt². '
    'I/R/U counts include all3 metrics at each depth with tolerance1e−9. Entries are baseline → power.5.', '',
    '|Scene|Corner/depth pt|RGB RMSE|D1 RMSE|D2 RMSE|I/R/U|',
    '|---|---|---:|---:|---:|---|',
]
for scene in CURRENT['scenes']:
    name = scene['scene']
    for position in ('TL', 'TR', 'BL', 'BR'):
        before = old_scene(name)['tracks']['raw']['corner'][position]
        for b, a in zip(before, scene['tracks']['raw']['corner'][position]):
            label = f'{position}@{a["depth_pt"]}'
            relevant = [r for r in CHANGES if r['scene'] == name and r['region'] == 'corner' and r['name'] == label]
            cells = [name, label]
            cells += [pair(b[key], a[key]) if b[key] is not None and a[key] is not None else 'masked'
                      for key in ('rgb_rmse', 'd1_rgb_rmse', 'd2_rgb_rmse')]
            cells.append(group_counts(relevant))
            corner.append('|' + '|'.join(cells) + '|')
(OUT / 'corner-comparison.md').write_text('\n'.join(corner) + '\n')

def read_tracks(directory):
    with (directory / 'blue-feature-tracks.csv').open(newline='') as f:
        return list(csv.DictReader(f))

new_rows, old_rows = read_tracks(OUT), read_tracks(BASE)
fig, axes = plt.subplots(2, 3, figsize=(11, 8), sharex=True)
for row, theme in enumerate(('light', 'dark')):
    scene = f'color_stripes-{theme}'
    for col, band in enumerate(('top', 'body', 'bottom')):
        ax = axes[row, col]
        for rows, platform, label, color, style in [
            (new_rows, 'native', 'Native iOS26.5', '#2357a1', '-'),
            (old_rows, 'android', 'Android baseline', '#7b7b7b', '--'),
            (new_rows, 'android', 'Alert power.5', '#c36d21', '-'),
        ]:
            chosen = [r for r in rows if r['scene'] == scene and r['platform'] == platform and r['band'] == band]
            ax.plot([float(r['positive_blue_centroid_x_pt']) for r in chosen],
                    [float(r['y_pt']) for r in chosen], style, color=color, label=label)
        ax.set_xlim(74, 80)
        ax.invert_yaxis()
        ax.set_title(f'{theme} / {band}', fontsize=10)
        ax.set_xlabel('World x centroid, pt / dp')
        ax.set_ylabel('World y, pt / dp')
        ax.grid(alpha=.2)
axes[0, 0].legend(fontsize=8)
fig.suptitle('Fixed blue-opponent centroids; no recenter / warp / correspondence fit')
fig.tight_layout()
fig.savefig(OUT / 'blue-feature-bend-comparison.png', dpi=120)
plt.close(fig)
print(json.dumps({'readme': str(OUT / 'README.md'), 'corner_rows': 192,
                  'raw_metric_rows': len(CHANGES), 'figure': str(OUT / 'blue-feature-bend-comparison.png')}))
