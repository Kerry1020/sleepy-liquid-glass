"""Render report from existing frozen measurements only."""
from pathlib import Path
import json

O = Path(__file__).resolve().parent
d = json.loads((O / 'budget-result.json').read_text())


def table(headers, rows):
    return '\n'.join(['| ' + ' | '.join(headers) + ' |',
                      '| ' + ' | '.join(['---'] * len(headers)) + ' |'] +
                     ['| ' + ' | '.join(map(str, row)) + ' |' for row in rows])


def triple(row):
    return '/'.join(str(row[x]) for x in ['improved', 'regressed', 'unchanged'])


peak = {(x['platform'], x['segment']): x for x in d['neutral_peaks']}
peak_rows = []
for platform in ['native', 'body8', 'additive', 'screen', 'candidate']:
    row = [platform]
    for seg in ['neutral_top', 'neutral_left', 'neutral_right']:
        x = peak[(platform, seg)]
        row.append(f"{x['peak_minus_shoulder_luma']:.5f} @ {x['raw_argmax_inset_pt']:.2f}pt")
    peak_rows.append(row)

probe_rows = []
for ref in ['body8', 'additive', 'screen']:
    rows = {x['field']: x for x in d['new_probe_whole_fixed_scan_counts']
            if x['reference'] == ref and x['track'] == 'corner'}
    probe_rows.append([ref] + [triple(rows[f]) for f in ['raw', 'smooth', 'd1', 'd2']])

history_rows = []
for scene in ['fine_grid-light', 'color_stripes-light', 'tonal_blocks-light', 'synthetic_landscape-light']:
    for ref in ['additive', 'screen', 'original']:
        summary = next(x for x in d['history_raw_rmse_counts']
                       if x['scene'] == scene and x['reference'] == ref)
        history_rows.append([scene, ref, triple(summary['straight_rgb']), triple(summary['corner_rgb'])])

derivative_rows = []
for scene in ['fine_grid-light', 'color_stripes-light', 'tonal_blocks-light', 'synthetic_landscape-light']:
    for ref in ['additive', 'screen', 'original']:
        rows = {x['field']: x for x in d['history_corner16_whole_fixed_scan_counts']
                if x['scene'] == scene and x['reference'] == ref}
        derivative_rows.append([scene, ref] + [triple(rows[f]) for f in ['raw', 'smooth', 'd1', 'd2']])

clip = {(x['reference'], x['endpoint']): x for x in d['history_inward_clipping_vs_each_reference']}
clipping_rows = [[ref, clip[(ref, '0')]['channels'], clip[(ref, '255')]['channels'],
                  clip[(ref, '0')]['rows_with_new_endpoint'], clip[(ref, '255')]['rows_with_new_endpoint']]
                 for ref in ['additive', 'screen', 'original', 'native']]

lines = [
    '# Budget-normalized Alert rim increment — fixed probe and history decision',
    '',
    'Date: 2026-11-15. This is an experiment report, not native appearance acceptance.',
    '',
    '## Decision',
    '',
    'The budget-normalized increment fixes the prescribed124-pixel colored-side clipping and restores '
    'a visible neutral-side highlight that the screen-only increment lost. It preserves the fixed '
    'zero-delta top, deep body, Sheet10 and dark controls. The result remains mixed: new-probe '
    'corner raw error is22 improved/22 regressed/4 unchanged against additive, while its corner '
    'D1 and D2 errors regress on39 and40 of48 tracks. Fine-grid, tonal and landscape history '
    'retain background-specific regressions. This candidate must not be described as final native '
    'parity, a physical thickness measurement or a universal optical improvement.',
    '',
    'No parameter, region, mask, sampling gate or pass threshold was changed after decoding. '
    'The parent agent owns implementation, release and subsequent experiment decisions.',
    '',
    '## Registered change and references',
    '',
    'After the inherited additive shine, the registered implementation uses:',
    '',
    '```text',
    'H = max(coverage - glass, 0)',
    'E = coverage * addedFloor',
    'Y = dot(H, [0.2126, 0.7152, 0.0722])',
    'if Y > 0:',
    '    alpha = dockOneMinusExp(E / Y)',
    '    glass += alpha * H',
    '```',
    '',
    'The exponential was chosen structurally before the candidate GPU output, using the existing '
    'stable primitive. No new intensity/width parameter was fitted. `Y` uses encoded working RGB '
    'headroom and is not measured linear-light luminance. Real-number boundedness does not establish '
    'the behavior of half precision, conversion or8-bit saturation; those are measured below. '
    'The inherited additive shine can already clip.',
    '',
    'Light Alert stays at blur8/refraction60/profile1, CPU side0/corner0/flat.06, shine.16, '
    'angular floor.08 and the same geometry/tone. Sheet10, dark, Menu, Dock and Material Design '
    'remain outside this formula change. Original additive and zero-delta branches are retained.',
    '',
    'References: native iOS26.5; body8 with zero added floor; additive floor; screen-only increment; '
    'current budget increment. History has no body8-only capture. Original factory history is '
    'reported only as combined blur+rim+compositing context.',
    '',
    '## Provenance and batch separation',
    '',
    '- Frozen plan: `budget-analysis-plan.md` SHA256 '
    '`d8eb67aac6ddc26adf3a0e093ac9afae85c23819405305e0fc04f77878d27011`.',
    '- Frozen manifest: `budget-analysis-plan.json` SHA256 '
    '`2769ee22ebc61c2d3fe54cc33f5778563142585080e90311a72b3c4928a0956f`; '
    '279 baseline/source/script hashes, seven syntax-checked analysis scripts.',
    '- New4: `../panels-alert-floor-budget-20261115`, frozen before image decode in '
    '`budget-probes-predecode.json`.',
    '- Complete history16: `../panels-alert-floor-budget-history-r2-20261115`, explicit parent '
    'handback after source/geometry checks; frozen before first decode in `budget-history-predecode.json`.',
    '- First history run stopped after6 captures because a system blue usage reminder covered '
    'the app. Its failure/screenshots remain preserved, but were not optically decoded in this '
    'analysis. Parent retry receipt: `../panel-alert-floor-budget-history-retry.json`; '
    'r2 uses identical gates and only a different run ID.',
    '- Historical CSVs retain legacy7-support corner derivative columns for provenance. Final '
    'corner smooth/D1/D2 interpretation uses only recomputed16-contiguous-clear-pixel results '
    'in `budget-history-corner16-metrics.json`.',
    '- Some inherited JSON labels say “isolated screen increment”; the candidate pixels are the '
    'registered budget increment. This report corrects that descriptive label without altering '
    'frozen scripts or numerical results.',
    '',
    '## Fixed geometry, color and sampling',
    '',
    'World750×1334px at2pixels per375×667pt/dp. Alert pane `[55,515,695,859]px`, '
    'actual Window `[46,509,704,865]px`. Sheet pane `[16,635,734,1318]px`. All original '
    'native accessibility/Android layout union masks remain expanded by2pt. No warp, '
    'resizing, registration, contour fitting or region movement is used for measurements.',
    '',
    'Raw and ICC-to-sRGB decodes are independently checked equal. Derivatives use the frozen '
    'sigma.75pt, seven-sample reflected-endpoint smoothing and never cross a masked gap. '
    'Corner derivatives require16 contiguous original clear pixels. Reported optical numbers '
    'are encoded RGB/luma errors, not radiometric or physical thickness estimates.',
    '',
    '## Exact controls',
    '',
    table(['Control', 'Result'], [
        ['New2 Sheet10, actual Window/visible app/deep80/body vs prior Sheet10', 'all zero changes'],
        ['New2 Alert deep80 and all original body ROIs vs additive', 'all zero changes'],
        ['New2 Alert central top vs additive and screen', 'all zero changes'],
        ['History8 dark carriers, Window + visible app ×3 references', '48/48 exact zero checks'],
        ['History4 light Alerts, deep80/body/top vs additive and screen', '56/56 exact zero checks'],
        ['History4 light Sheet10 vs screen-batch Sheet10, Window + visible app', '8/8 exact zero checks'],
        ['History light Sheet vs additive/original radius12', 'combined12→10 response; not an unchanged control'],
    ]),
    '',
    'The central top full-display region `[280,503,470,539]` contains27360 RGBA channels. '
    'Its actual-Window intersection `[280,509,470,539]` contains22800 RGBA channels. '
    'Exterior rows503..<509 lie outside the Window and are explicitly unavailable there; '
    'they are checked separately in full display. No synthetic Window padding or sample shift '
    'is used. Only central top is a zero-delta control; the full-width top side wings are not.',
    '',
    'Full-display differences elsewhere include status/system context and are retained in raw '
    'outputs; no full-display identity is claimed for entire captures.',
    '',
    '## Prescribed124 colored-side pixels',
    '',
    'Fixed left-side tangent y307..<338pt (62 original screen rows), insets0.25 and0.75pt '
    '(screen columns55 and56), plus all eight same-tangent shoulder samples8.25..11.75pt. '
    'Both current62-pixel rows have zero channels at0 or255. All original124×8×3 shoulder '
    'values are identical to additive and screen. Additive had62 red255 values in the first '
    'row and30 in the second.',
    '',
    table(['Inset', 'native mean RGB', 'body8', 'additive', 'screen', 'budget'], [
        [f"{x['inset_pt']:.2f}pt"] +
        [','.join(f'{v:.3f}' for v in x['platforms'][p]['mean_edge_rgb'])
         for p in ['native', 'body8', 'additive', 'screen', 'candidate']]
        for x in d['primary124']]),
    '',
    'Individual raw values, shoulders and same-tangent response vectors are retained in '
    '`budget-124-pixels.json` and `.csv`; the means do not replace those original samples.',
    '',
    '## Neutral straight-edge visibility',
    '',
    'The frozen raw peak0..<4pt is measured against its original8..<12pt shoulder. '
    'Top uses x140..<235pt; sides use y353..<359pt. Values below are peak-minus-shoulder '
    'encoded luma and peak inset. Bottom remains context-contaminated and diagnostic only.',
    '',
    table(['Platform', 'Top', 'Left', 'Right'], peak_rows),
    '',
    'Budget left/right pass the unchanged8-count visibility gate and recover the native0.25pt '
    'raw peak location. Their contrast still falls short of native by5.14772 and6.91319 '
    'encoded counts respectively. Both native and budget have only two original half-height '
    'pixels on these peaks: FWHM remains unresolved under the unchanged minimum3-pixel gate. '
    'Interpolated crossings are diagnostics and must not be published as resolved widths.',
    '',
    '![Five-way identical fixed crops and neutral-edge curves](budget-five-way-fixed-comparison.png)',
    '',
    '## New4 corner response',
    '',
    'Each field compares48 fixed Alert corner tracks to native by mean RGB MAE over the '
    'whole original scan. Table cells are improved/regressed/unchanged. Raw, smooth and '
    'derivative results must be kept separate.',
    '',
    table(['Reference', 'Raw', 'Smooth', 'D1', 'D2'], probe_rows),
    '',
    'Against additive, preserving high contrast without clipping did not preserve the native '
    'corner derivative match. These39/40 derivative regressions are a material limitation, '
    'even though the candidate improves most derivatives relative to the rejected screen-only '
    'increment. Every original corner/depth/scope result is retained.',
    '',
    '## History16: background-specific response',
    '',
    'Raw RGB RMSE summary below uses the original historical metric: four fixed straight edges '
    '(inward0..<20pt) and24 fixed corner-depth tracks. Cells are improved/regressed/unchanged '
    'against native. This RMSE summary is different from the mean-MAE table after it.',
    '',
    table(['Background', 'Reference', 'Straight RGB RMSE', 'Corner RGB RMSE'], history_rows),
    '',
    'Landscape regresses on all four raw straight RMSE tracks versus additive; tonal regresses '
    'on three. Additive comparison cannot be suppressed simply because the candidate broadly '
    'improves the rejected screen-only variant. Likewise, comparison with original factory '
    'includes multiple earlier changes and cannot isolate this increment.',
    '',
    'The following independent whole-scan mean-RGB-MAE counts recompute corner smooth/D1/D2 '
    'from original raw tracks with the16-contiguous-pixel gate. MAE can have a different '
    'direction from RMSE, so both outputs are preserved and labeled.',
    '',
    table(['Background', 'Reference', 'Raw MAE', 'Smooth MAE', 'D1 MAE', 'D2 MAE'], derivative_rows),
    '',
    'All dark corner/straight/body outputs are unchanged against all three historical references. '
    'Light Alert body outputs are unchanged against additive and screen. Body differences '
    'against original factory are retained as combined earlier blur-response context.',
    '',
    '## Clipping: precise reference-dependent conclusion',
    '',
    'New4 fixed Alert inward samples have no newly saturated0/255 channels versus body8. '
    'This does not establish zero saturation against every reference or everywhere in history.',
    '',
    'History fixed inward straight and corner samples produce the following endpoint differences. '
    'Counts retain overlapping tracks and repeated pixels; they are not unique pixel counts.',
    '',
    table(['Reference', 'New0 channels', 'New255 channels', 'Rows with new0', 'Rows with new255'], clipping_rows),
    '',
    'The single newly255 sample relative to screen is `color_stripes-light`, straight right, '
    'inset2.25pt, B channel, one sample within the62-pixel row. Additive already has255 '
    'at that location. Thus “no new inward clipping” is valid relative to additive here, '
    'but is false as a blanket claim about screen/native/original factory. Existing factory '
    'and native-relative endpoints remain reported, including dark reference differences.',
    '',
    '## Retained regressions and scope limits',
    '',
    '`budget-regressions.json` preserves every negative result, with `budget-regression-index.csv` '
    'for background/edge/corner/depth/field lookup. It includes732 new-probe Alert negative '
    'rows across frozen overlapping scopes,34 historical straight negative field rows, '
    '690 historical corner16 negative rows across both scopes, and12 factory-relative body '
    'negative rows. These are row counts with overlapping comparisons, not independent samples '
    'or failure percentages.',
    '',
    'The prescribed three user observations—background sharpness, nonlinear near-edge stretch '
    'and thin-edge highlight—cannot all be established by a rim-composition experiment. Blur8 '
    'and refraction profile remain fixed here; no new displacement fit is inferred from the '
    'luma curves. Independent unseen backgrounds, other sizes, full dynamic sequences and '
    'controls outside these Alert/Sheet probes are not validated by this report. No unseen '
    'noise or heldout input was read and no additional experiment was started.',
    '',
    '## Reproduction and publication files',
    '',
    'Frozen measurements are reproducible from the handed-back complete batches using the '
    'seven frozen scripts listed in `budget-analysis-plan.json`. The driver invocation was:',
    '',
    '```text',
    '/usr/bin/python3 -B budget_history_driver.py ../panels-alert-floor-budget-history-r2-20261115',
    '```',
    '',
    '`budget_summarize_evidence.py`, `budget_plot_fixed_comparison.py` and '
    '`budget_write_decision.py` only assemble already measured outputs/presentation; they '
    'do not retune, change gates or create new measurements. `budget-manifest.json` hashes '
    'all current budget report/data/scripts and the historical generated outputs.',
    '',
    'Suggested public assets: this decision report, the five-way figure, frozen plan and '
    'predecode manifests, `budget-result.json`, all-reference tables, original124-pixel '
    'CSV/JSON, clipping and regression indices. Preserve complete per-pixel/raw/derivative '
    'exports with the artifact archive so readers can check aggregate claims.',
    '',
]
(O / 'budget-decision.md').write_text('\n'.join(lines))
print(O / 'budget-decision.md')
