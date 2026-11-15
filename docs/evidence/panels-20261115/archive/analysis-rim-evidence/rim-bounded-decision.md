# Bounded light Alert rim result — candidate rejected as final appearance

The declared light Alert candidate preserves body8/refraction60/profile1 and changes only the rim stage to CPU side0/corner0/flat.06 plus angular minimumShine.08. Its neutral outer-top whitening and missing neutral side peak improve, but the candidate introduces red-channel saturation on a colored fixed side and still worsens individual corner/background curves. It is not an accepted final material.

The preregistration remains `rim-next-frozen-plan.md`, SHA256 `179c6679b5400d5fd8551279b4ad99fc82eb456c8fa01203d62d0cf235ca10ac`. The unchanged 750×1334 original coordinates, actual Window geometry, foreground union expanded2pt, fixed tracks, raw/ICC separation and gates were retained. No image translation, resize, fitted contour, ROI relocation, parameter search, unpublished noise or heldout data entered. One export parser fix for masked blank CSV cells is retained in `rim-bounded-completion-initial-error.txt`.

## Strict controls passed

- New two-source Sheet actual Windows and visible App area are strictly RGBA-identical to body8. New light Alert deep80px rectangles and all originally declared unmasked body ROIs are also strictly identical to body8. System-bar differences remain separate.
- Historical four dark Alerts and eight Sheets have strictly identical actual Windows and visible App areas against `panels-dark-scrim-20261115`. This uses the actual dark reference, not a nonexistent body8-dark capture.
- Independent raw/ICC decodes are identical in all tracks. Full channel counts, file hashes, source mappings and capture provenance remain in the linked JSON files.

## Neutral-top/side improvement is bounded

In fixed shapes top x140..<235pt, the first inner row .25pt changes from142/190 RGB255 pixels to zero; all four original .25/.75/1.25/1.75pt rows have zero any255. The mean first row is[247.558,247.558,247.558]. Fixed top/left/right0..<2pt mean RGB MAE versus native respectively changes5.9596→4.4719,9.1111→2.2708 and8.6250→2.9931. Top is also better than the original styled5.1465 baseline.

Top/left/right candidate peaks all lie at the same .25pt original raster sample as native, with at least±.25pt sampling uncertainty per platform. Both candidate and native have only two half-height support pixels. Their FWHM remains unresolved under the original minimum-three-pixel requirement. These statements do not establish equal physical thickness, continuous taper width or subpixel matching. Neutral bottom remains backing-context contaminated; Sheet top neutral intervals remain excluded by the original grabber mask.

## New colored-side clipping is a decisive failure

Fixed shapes Alert left y307..<338pt has62 original pixels per normal row. At .25pt the candidate clips red for62/62 pixels; at .75pt it clips red for30/62. Native and body8 clip none of these channels. No green/blue channel is255 there, so this is a red plateau rather than pure-white pixels. No other fixed inward new-probe segment introduces0/255 versus body8; every channel and masked sample remains in `rim-bounded-clipping-all-fixed.json` and pointwise comparisons.

`rim-bounded-left-red-124-pixels.{csv,json}` retains every original pixel, each platform RGB, all8 original same-tangent shoulder samples in8..<12pt, mean shoulder and edge-minus-shoulder response. Shoulder values are strictly unchanged between candidate and body8 for all124 points.

At .25pt, mean RGB is body8[248.613,189.355,227.484], candidate[255,206.258,244.403], native[252.548,225.081,248.565]. Candidate-minus-body8 green/blue increases are16.903/16.919 counts. Every point's G/B increments agree to within1 encoded count. Using their mean only as an additive-arithmetic consistency diagnostic yields red261..269.5 before a clamp, exceeding255 at62/62 points. This is not recovery of the unobservable unclamped red value. At .75pt G/B mean increments10.290/10.274 similarly predict30/62 points at or above255, matching the actual30/62.

The paired captures plus source support additive floor illumination as the direct local clipping mechanism: the final shader adds the same scalar to premultiplied RGB via `glass += coverage * shineAround(turn) * shineAcross(...)`, then returns `min(glass,float3(coverage))`. `minimumShine` floors all eight angular light nodes. The CPU side/corner gradients are both zero in these first side samples, so flat.06 does not account for their increments. This evidence does not identify the iOS lighting equation. A different compositing intervention requires a new frozen plan and capture identity.

![Fixed colored left-side channels](rim-bounded-left-red-124-pixels.png)

## Corner and historical regressions are retained

The new-probe48 Alert whole-scan raw RGB corner comparisons improve29 and regress19. Both probes' entire six-depth top-right sets regress slightly. Strict16-original-pixel contiguous-support derivatives also remain mixed: coordinate D1/D2 each19 improvements/5 regressions; shapes D1 is19/5 and D2 is18/6. Every raw/smoothed/D1/D2 result is separately preserved for whole fixed scans and inward-only diagnostic scopes. Shapes neutral right2..<4pt MAE worsens.5486→.8819.

Historical light captures combine blur16→8 and the rim change; they cannot isolate the rim effect. The original per-source straight/corner/body ROIs and foreground masks are unchanged. Counts below are separate per source and are not a pooled acceptance metric.

| Historical light source | Straight RGB improve/regress | Corner RGB improve/regress | Body ROI RGB improve/regress |
|---|---:|---:|---:|
| fine_grid |4/0|24/0|1/3|
| color_stripes |3/1|9/15|0/4|
| tonal_blocks |3/1|23/1|2/2|
| synthetic_landscape |4/0|24/0|1/3|

The stripes left straight RGB RMSE worsens16.7601→17.6436. Tonal bottom worsens6.5335→6.6134. The largest listed stripes corner raw RMSE regression isTR@4.25pt21.6029→24.5765; every other corner depth and derivative remains in `rim-bounded-history-metric-changes.json`. A sharper response is not equivalent to universally lower fixed-pixel color error.

This candidate resolves part of the neutral edge placement/whitening issue, passes its unchanged controls, and fails final rim acceptance due to colored-side clipping plus retained corner/background regressions. All data remain public calibration. No independent-test, complete motion, production-page or99.99% parity conclusion follows.
