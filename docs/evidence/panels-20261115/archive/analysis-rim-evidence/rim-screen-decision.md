# Screen-only incremental floor — clipping repair passes, appearance rejected

The declared screen-only increment with nonnegative headroom removes the observed colored-side red plateau and preserves delta-zero top/body controls. It substantially weakens the required neutral side highlight and worsens many fixed corners and historical curves. It is not accepted as the final native appearance. No intensity, floor, width, material, geometry or threshold was retuned after capture.

The frozen plan is `rim-screen-increment-frozen-plan.md` (SHA256 `98ad62d4c92c43a60b8bca15a76ffb2b2faf01821155af24592ff90628ecfb19`), with the separately frozen intentional `max(coverage-glass,0)` and Sheet10 receipt in `rim-screen-increment-predecode-amendment.{md,json}`. The original shine expression remains additive; only the additional angular-floor signal is screen-composed. All source/material/CPU flat.06/shine.16/floor.08 settings remain as declared. New4 and complete historical-r2 file hashes were saved before their respective first decodes.

## Primary124 pixels: clipping removed, color/lift still mismatched

The same62 pixels at fixed shapes left y307..<338pt were retained for each inset.25/.75pt. Every original RGB value, eight same-tangent8..<12pt shoulder samples and edge-minus-shoulder response for native/body8/additive/screen are in `rim-screen-124-pixels.{csv,json}`. Candidate red255 counts are0/62 and0/62, compared with additive62/62 and30/62; candidate has no0/255 channels at these124 points. Candidate shoulders are strictly unchanged versus additive. This passes the registered colored-side clipping mechanism gate.

| Inset | Native mean RGB | Body8 mean RGB | Additive floor mean RGB | Screen increment mean RGB |
|---|---|---|---|---|
|.25pt|252.55,225.08,248.56|248.61,189.35,227.48|255,206.26,244.40|249.02,193.73,229.26|
|.75pt|248.90,213.10,241.56|242.50,196.60,226.16|250.98,206.89,236.44|242.95,198.95,227.34|

The candidate approaches body8 again and loses much of the useful green/blue edge lift. No fixed inward Alert sample in the new probes or historical set introduces0/255 versus additive; the complete per-channel and pointwise data are retained. Sheet10-versus12 changes, including their own clipping differences, are separately scoped to radius response rather than Alert compositing.

## Delta-zero top and strict controls

- For both new probes, the complete original neutral-top x140..<235pt, signed−5.75..<12pt display rectangle[280,503,470,539]px has27360 RGBA channels with zero difference versus additive. Its actual-Window intersection[280,509,470,539]px has22800 channels with zero difference. The first four inner rows and all raw/smoothed/D1/D2 top curves also remain exactly equal. The actual Window starts at screen509px, so exterior rows503..<509 cannot be claimed as Window samples; their original coordinates are retained and separately tested in the composited display. No padded or shifted Window data were invented.
- Both new Sheet10 actual Windows and visible App areas are strictly identical to the declared `panels-sheet-radius10-20261115` controls. Those controls' Alert actual Windows are also strictly identical to the old additive-floor reference, confirming its continued use for the Alert mechanism.
- New Alert deep80px rectangles and every originally declared unmasked body ROI are strictly RGBA-identical to additive. All four historical light Alert deep80/body controls are also strictly identical; their central delta-zero top tracks are separately retained.
- Historical four dark Alerts and four dark Sheets have strictly identical actual Windows and visible App regions versus both the actual original-dark reference and additive history. Full-display system-bar differences are reported separately.
- Four historical light Sheets are radius10 observations without like-for-like historical radius10 strict controls. Their native/previous12 results describe the combined radius-response change. They are not reported as unchanged controls or attributed to Alert screen composition.

Independent raw RGBA and ICC-normalized sRGB decodes are identical. Original750×1334 coordinates,2px density, actual Window origins/layout, original source bytes, fixed foreground union+2pt, all declared segments and original gates remain unchanged.

## Neutral side loss and fixed-corner regressions

Shapes neutral top0..<2pt mean RGB MAE stays4.4719. Neutral left worsens2.2708→8.0694 and right2.9931→7.7986 versus additive. Left2..<4pt also worsens.8472→1.4236, while right2..<4pt improves.8819→.5417. Neither side may be hidden in a combined mean.

The fixed left rim maximum above its8..<12pt shoulder drops14.634→.805 encoded luma counts, compared with native16.002; the right drops17.016→1.736, compared with native19.995. The left's raw first4pt maximum moves.25→.75pt, while native remains.25pt. These weak candidate maxima fail the original minimum8-count visibility gate and are not evidence of an identified physical peak or taper. Native half-height support remains only2 original pixels, so the original minimum3-pixel rule still leaves native FWHM unresolved.

Against additive, the new-probe48 Alert whole-fixed-scan raw RGB corner tracks improve15, regress31 and remain equal2. Every original depth, side and mask is preserved, with raw/smoothed/D1/D2 scored separately and16 contiguous original pixels required for corner-derivative interpretation. This blocks an all-corner improvement claim even though the red plateau is removed.

## Complete historical-r2 results

The first historical attempt stopped after6 captures when an external API/send-to-device floating overlay failed display-readiness. Its failed images and retry receipt remain untouched. Only the complete `panels-alert-floor-screen-history-r2-20261115`16-observation batch enters these optical results. The parent reports the retry changed only run identity, retaining installed binaries, source bytes, geometry, timing and readiness thresholds; hashes and failure provenance are in `rim-screen-history-predecode.json` and the root retry receipt.

Historical light Alert comparisons against additive isolate the screen increment at constant blur8/rim settings. Each original4 straight and24 corner RGB result is listed below; original body ROI RGB errors are unchanged4/4 for every source.

| Source | Straight improve/regress | Corner improve/regress |
|---|---:|---:|
|fine_grid|2/2|10/14|
|color_stripes|0/4|3/21|
|tonal_blocks|1/3|9/15|
|synthetic_landscape|0/4|0/24|

The separate original-factory comparison combines blur+rim+composition. It still has mixed colored-source results: stripes straight3/1 and corner8/16; tonal straight3/1 and corner24/0; grid/landscape straight4/0 and corner24/0. These are contextual combined effects, not acceptance or attribution solely to screen. Every per-source raw/ICC body/straight/corner result and newly clipped channel is retained in `rim-screen-history-metric-changes.json`, `rim-screen-history-clipping*.json` and the original curve CSVs. Final historical corner smooth/D1/D2 interpretation is recomputed from the original raw samples using the frozen16-contiguous-pixel gate in `rim-screen-history-corner16-metrics.json`; legacy historical7-support derivative exports remain as provenance and are not used for this final corner interpretation.

![Fixed four-way crop and curves](rim-screen-four-way-fixed-comparison.png)

The figure uses the existing fixed colored-side support only: all four crops are the same original60×62px rectangle, with inset.25/.75pt columns marked; no source warp, registration or newly selected favorable ROI is used. The curves use the frozen neutral top/left intervals. They illustrate both the successful clipping repair and the lost side highlight.

This experiment establishes that the declared bounded incremental operation removes the specific additive-floor saturation while retaining its strict controls. It does not supply the required native side brightness, all-corner behavior, physical thickness or final appearance. Keep it as a rejected appearance mechanism probe; all inputs remain public REST calibration, without independent-heldout, motion, production-page or99.99% parity claims.
