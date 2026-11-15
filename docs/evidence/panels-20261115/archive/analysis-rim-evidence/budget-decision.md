# Budget-normalized Alert rim increment — fixed probe and history decision

Date: 2026-11-15. This is an experiment report, not native appearance acceptance.

## Decision

The budget-normalized increment fixes the prescribed124-pixel colored-side clipping and restores a visible neutral-side highlight that the screen-only increment lost. It preserves the fixed zero-delta top, deep body, Sheet10 and dark controls. The result remains mixed: new-probe corner raw error is22 improved/22 regressed/4 unchanged against additive, while its corner D1 and D2 errors regress on39 and40 of48 tracks. Fine-grid, tonal and landscape history retain background-specific regressions. This candidate must not be described as final native parity, a physical thickness measurement or a universal optical improvement.

No parameter, region, mask, sampling gate or pass threshold was changed after decoding. The parent agent owns implementation, release and subsequent experiment decisions.

## Registered change and references

After the inherited additive shine, the registered implementation uses:

```text
H = max(coverage - glass, 0)
E = coverage * addedFloor
Y = dot(H, [0.2126, 0.7152, 0.0722])
if Y > 0:
    alpha = dockOneMinusExp(E / Y)
    glass += alpha * H
```

The exponential was chosen structurally before the candidate GPU output, using the existing stable primitive. No new intensity/width parameter was fitted. `Y` uses encoded working RGB headroom and is not measured linear-light luminance. Real-number boundedness does not establish the behavior of half precision, conversion or8-bit saturation; those are measured below. The inherited additive shine can already clip.

Light Alert stays at blur8/refraction60/profile1, CPU side0/corner0/flat.06, shine.16, angular floor.08 and the same geometry/tone. Sheet10, dark, Menu, Dock and Material Design remain outside this formula change. Original additive and zero-delta branches are retained.

References: native iOS26.5; body8 with zero added floor; additive floor; screen-only increment; current budget increment. History has no body8-only capture. Original factory history is reported only as combined blur+rim+compositing context.

## Provenance and batch separation

- Frozen plan: `budget-analysis-plan.md` SHA256 `d8eb67aac6ddc26adf3a0e093ac9afae85c23819405305e0fc04f77878d27011`.
- Frozen manifest: `budget-analysis-plan.json` SHA256 `2769ee22ebc61c2d3fe54cc33f5778563142585080e90311a72b3c4928a0956f`; 279 baseline/source/script hashes, seven syntax-checked analysis scripts.
- New4: `../panels-alert-floor-budget-20261115`, frozen before image decode in `budget-probes-predecode.json`.
- Complete history16: `../panels-alert-floor-budget-history-r2-20261115`, explicit parent handback after source/geometry checks; frozen before first decode in `budget-history-predecode.json`.
- First history run stopped after6 captures because a system blue usage reminder covered the app. Its failure/screenshots remain preserved, but were not optically decoded in this analysis. Parent retry receipt: `../panel-alert-floor-budget-history-retry.json`; r2 uses identical gates and only a different run ID.
- Historical CSVs retain legacy7-support corner derivative columns for provenance. Final corner smooth/D1/D2 interpretation uses only recomputed16-contiguous-clear-pixel results in `budget-history-corner16-metrics.json`.
- Some inherited JSON labels say “isolated screen increment”; the candidate pixels are the registered budget increment. This report corrects that descriptive label without altering frozen scripts or numerical results.

## Fixed geometry, color and sampling

World750×1334px at2pixels per375×667pt/dp. Alert pane `[55,515,695,859]px`, actual Window `[46,509,704,865]px`. Sheet pane `[16,635,734,1318]px`. All original native accessibility/Android layout union masks remain expanded by2pt. No warp, resizing, registration, contour fitting or region movement is used for measurements.

Raw and ICC-to-sRGB decodes are independently checked equal. Derivatives use the frozen sigma.75pt, seven-sample reflected-endpoint smoothing and never cross a masked gap. Corner derivatives require16 contiguous original clear pixels. Reported optical numbers are encoded RGB/luma errors, not radiometric or physical thickness estimates.

## Exact controls

| Control | Result |
| --- | --- |
| New2 Sheet10, actual Window/visible app/deep80/body vs prior Sheet10 | all zero changes |
| New2 Alert deep80 and all original body ROIs vs additive | all zero changes |
| New2 Alert central top vs additive and screen | all zero changes |
| History8 dark carriers, Window + visible app ×3 references | 48/48 exact zero checks |
| History4 light Alerts, deep80/body/top vs additive and screen | 56/56 exact zero checks |
| History4 light Sheet10 vs screen-batch Sheet10, Window + visible app | 8/8 exact zero checks |
| History light Sheet vs additive/original radius12 | combined12→10 response; not an unchanged control |

The central top full-display region `[280,503,470,539]` contains27360 RGBA channels. Its actual-Window intersection `[280,509,470,539]` contains22800 RGBA channels. Exterior rows503..<509 lie outside the Window and are explicitly unavailable there; they are checked separately in full display. No synthetic Window padding or sample shift is used. Only central top is a zero-delta control; the full-width top side wings are not.

Full-display differences elsewhere include status/system context and are retained in raw outputs; no full-display identity is claimed for entire captures.

## Prescribed124 colored-side pixels

Fixed left-side tangent y307..<338pt (62 original screen rows), insets0.25 and0.75pt (screen columns55 and56), plus all eight same-tangent shoulder samples8.25..11.75pt. Both current62-pixel rows have zero channels at0 or255. All original124×8×3 shoulder values are identical to additive and screen. Additive had62 red255 values in the first row and30 in the second.

| Inset | native mean RGB | body8 | additive | screen | budget |
| --- | --- | --- | --- | --- | --- |
| 0.25pt | 252.548,225.081,248.565 | 248.613,189.355,227.484 | 255.000,206.258,244.403 | 249.016,193.726,229.258 | 250.419,208.161,235.290 |
| 0.75pt | 248.903,213.097,241.565 | 242.500,196.597,226.161 | 250.984,206.887,236.435 | 242.952,198.952,227.339 | 245.081,208.048,232.016 |

Individual raw values, shoulders and same-tangent response vectors are retained in `budget-124-pixels.json` and `.csv`; the means do not replace those original samples.

## Neutral straight-edge visibility

The frozen raw peak0..<4pt is measured against its original8..<12pt shoulder. Top uses x140..<235pt; sides use y353..<359pt. Values below are peak-minus-shoulder encoded luma and peak inset. Bottom remains context-contaminated and diagnostic only.

| Platform | Top | Left | Right |
| --- | --- | --- | --- |
| native | 22.94872 @ 0.25pt | 16.00170 @ 0.25pt | 19.99542 @ 0.25pt |
| body8 | 31.65263 @ 0.25pt | 0.05215 @ 1.75pt | 0.00000 @ 3.25pt |
| additive | 24.55789 @ 0.25pt | 14.63445 @ 0.25pt | 17.01585 @ 0.25pt |
| screen | 24.55789 @ 0.25pt | 0.80537 @ 0.75pt | 1.73610 @ 0.25pt |
| candidate | 24.55789 @ 0.25pt | 10.85398 @ 0.25pt | 13.08223 @ 0.25pt |

Budget left/right pass the unchanged8-count visibility gate and recover the native0.25pt raw peak location. Their contrast still falls short of native by5.14772 and6.91319 encoded counts respectively. Both native and budget have only two original half-height pixels on these peaks: FWHM remains unresolved under the unchanged minimum3-pixel gate. Interpolated crossings are diagnostics and must not be published as resolved widths.

![Five-way identical fixed crops and neutral-edge curves](budget-five-way-fixed-comparison.png)

## New4 corner response

Each field compares48 fixed Alert corner tracks to native by mean RGB MAE over the whole original scan. Table cells are improved/regressed/unchanged. Raw, smooth and derivative results must be kept separate.

| Reference | Raw | Smooth | D1 | D2 |
| --- | --- | --- | --- | --- |
| body8 | 31/15/2 | 38/10/0 | 39/9/0 | 34/14/0 |
| additive | 22/22/4 | 15/31/2 | 6/39/3 | 6/40/2 |
| screen | 36/11/1 | 42/6/0 | 46/2/0 | 42/6/0 |

Against additive, preserving high contrast without clipping did not preserve the native corner derivative match. These39/40 derivative regressions are a material limitation, even though the candidate improves most derivatives relative to the rejected screen-only increment. Every original corner/depth/scope result is retained.

## History16: background-specific response

Raw RGB RMSE summary below uses the original historical metric: four fixed straight edges (inward0..<20pt) and24 fixed corner-depth tracks. Cells are improved/regressed/unchanged against native. This RMSE summary is different from the mean-MAE table after it.

| Background | Reference | Straight RGB RMSE | Corner RGB RMSE |
| --- | --- | --- | --- |
| fine_grid-light | additive | 3/1/0 | 10/14/0 |
| fine_grid-light | screen | 2/2/0 | 12/12/0 |
| fine_grid-light | original | 4/0/0 | 24/0/0 |
| color_stripes-light | additive | 3/1/0 | 21/3/0 |
| color_stripes-light | screen | 4/0/0 | 24/0/0 |
| color_stripes-light | original | 3/1/0 | 11/13/0 |
| tonal_blocks-light | additive | 1/3/0 | 13/9/2 |
| tonal_blocks-light | screen | 3/1/0 | 15/9/0 |
| tonal_blocks-light | original | 3/1/0 | 23/1/0 |
| synthetic_landscape-light | additive | 0/4/0 | 1/23/0 |
| synthetic_landscape-light | screen | 4/0/0 | 24/0/0 |
| synthetic_landscape-light | original | 4/0/0 | 24/0/0 |

Landscape regresses on all four raw straight RMSE tracks versus additive; tonal regresses on three. Additive comparison cannot be suppressed simply because the candidate broadly improves the rejected screen-only variant. Likewise, comparison with original factory includes multiple earlier changes and cannot isolate this increment.

The following independent whole-scan mean-RGB-MAE counts recompute corner smooth/D1/D2 from original raw tracks with the16-contiguous-pixel gate. MAE can have a different direction from RMSE, so both outputs are preserved and labeled.

| Background | Reference | Raw MAE | Smooth MAE | D1 MAE | D2 MAE |
| --- | --- | --- | --- | --- | --- |
| fine_grid-light | additive | 13/9/2 | 13/11/0 | 2/22/0 | 2/22/0 |
| fine_grid-light | screen | 7/16/1 | 8/16/0 | 21/3/0 | 19/5/0 |
| fine_grid-light | original | 24/0/0 | 21/3/0 | 24/0/0 | 24/0/0 |
| color_stripes-light | additive | 22/2/0 | 24/0/0 | 17/7/0 | 15/9/0 |
| color_stripes-light | screen | 24/0/0 | 24/0/0 | 24/0/0 | 24/0/0 |
| color_stripes-light | original | 3/21/0 | 3/21/0 | 24/0/0 | 24/0/0 |
| tonal_blocks-light | additive | 13/9/2 | 7/15/2 | 5/15/4 | 5/17/2 |
| tonal_blocks-light | screen | 12/12/0 | 15/9/0 | 19/3/2 | 22/2/0 |
| tonal_blocks-light | original | 17/7/0 | 15/9/0 | 24/0/0 | 24/0/0 |
| synthetic_landscape-light | additive | 1/20/3 | 1/23/0 | 4/19/1 | 7/16/1 |
| synthetic_landscape-light | screen | 23/1/0 | 24/0/0 | 24/0/0 | 24/0/0 |
| synthetic_landscape-light | original | 23/1/0 | 24/0/0 | 24/0/0 | 24/0/0 |

All dark corner/straight/body outputs are unchanged against all three historical references. Light Alert body outputs are unchanged against additive and screen. Body differences against original factory are retained as combined earlier blur-response context.

## Clipping: precise reference-dependent conclusion

New4 fixed Alert inward samples have no newly saturated0/255 channels versus body8. This does not establish zero saturation against every reference or everywhere in history.

History fixed inward straight and corner samples produce the following endpoint differences. Counts retain overlapping tracks and repeated pixels; they are not unique pixel counts.

| Reference | New0 channels | New255 channels | Rows with new0 | Rows with new255 |
| --- | --- | --- | --- | --- |
| additive | 0 | 0 | 0 | 0 |
| screen | 0 | 1 | 0 | 1 |
| original | 0 | 2548 | 0 | 219 |
| native | 110 | 5556 | 99 | 502 |

The single newly255 sample relative to screen is `color_stripes-light`, straight right, inset2.25pt, B channel, one sample within the62-pixel row. Additive already has255 at that location. Thus “no new inward clipping” is valid relative to additive here, but is false as a blanket claim about screen/native/original factory. Existing factory and native-relative endpoints remain reported, including dark reference differences.

## Retained regressions and scope limits

`budget-regressions.json` preserves every negative result, with `budget-regression-index.csv` for background/edge/corner/depth/field lookup. It includes732 new-probe Alert negative rows across frozen overlapping scopes,34 historical straight negative field rows, 690 historical corner16 negative rows across both scopes, and12 factory-relative body negative rows. These are row counts with overlapping comparisons, not independent samples or failure percentages.

The prescribed three user observations—background sharpness, nonlinear near-edge stretch and thin-edge highlight—cannot all be established by a rim-composition experiment. Blur8 and refraction profile remain fixed here; no new displacement fit is inferred from the luma curves. Independent unseen backgrounds, other sizes, full dynamic sequences and controls outside these Alert/Sheet probes are not validated by this report. No unseen noise or heldout input was read and no additional experiment was started.

## Reproduction and publication files

Frozen measurements are reproducible from the handed-back complete batches using the seven frozen scripts listed in `budget-analysis-plan.json`. The driver invocation was:

```text
/usr/bin/python3 -B budget_history_driver.py ../panels-alert-floor-budget-history-r2-20261115
```

`budget_summarize_evidence.py`, `budget_plot_fixed_comparison.py` and `budget_write_decision.py` only assemble already measured outputs/presentation; they do not retune, change gates or create new measurements. `budget-manifest.json` hashes all current budget report/data/scripts and the historical generated outputs.

Suggested public assets: this decision report, the five-way figure, frozen plan and predecode manifests, `budget-result.json`, all-reference tables, original124-pixel CSV/JSON, clipping and regression indices. Preserve complete per-pixel/raw/derivative exports with the artifact archive so readers can check aggregate claims.
