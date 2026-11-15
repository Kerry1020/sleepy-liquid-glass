# Alert outline-zero mechanism decision

**Mixed; do not accept as a finished visual fix.** This candidate removes only the Alert CPU dark stroke, retains the original shine table, and restores the original16/12 blur and60 refraction. The optional blur support is dormant. It is a measured mechanism intermediate, not a no-refraction or low-blur result.

All unchanged original straight regions, all fixed corner slices, foreground union masks and original deep80px controls are reused. Native new-probe source/geometry/repeat proofs remain in `../analysis-native-probes`. The new files and fixed controls were frozen before first new-image pixel decode in `outline-zero-predecode.json`. Raw and ICC-normalized RGBA are identical for every image entering this comparison. No image registration, resize, source substitution or failed-sample removal occurs.

## Controls

- Both unchanged Sheet actual Windows are exactly equal across all4,002,000 RGBA channels each. Their complete display screenshots differ in system bars; the visible application area is strictly zero difference. The full-display differences are retained, not called zero.
- Both Alert original deep80px rectangles are strictly zero difference across353,280 RGBA channels each. Every originally declared unmasked Alert body ROI is strictly equal.
- The8px-eroded bounding rectangle is retained only as a diagnostic: near a rounded corner it is not guaranteed deep optical interior. Its distinction from the actual80px control was recorded before decoding.
- All48 originally fixed Alert corner-slice mean RGB errors improve. All12 original straight first0..<2pt means improve. These observations do not cancel the explicit neutral-top regression below.

## Neutral top and side results

Fixed shapes neutral top x140..<235pt, original pixel centers:

| Inward pt | iOS native RGB | Android baseline RGB | Android outline-zero RGB |
|---:|---|---|---|
|0.25|237.542,248.037,248.795|239.463,239.463,239.463|254.653,254.653,254.653|
|0.75|227.579,241.274,243.026|243.042,243.042,243.042|same as baseline|
|1.25|222.532,231.663,233.937|229.484,229.484,229.484|same as baseline|
|1.75|226.358,231.905,233.595|228.042,228.042,228.042|same as baseline|

The peak moves outward from0.75 to0.25pt, but142 of the190 first-row pixels become RGB255 white. Native and baseline both have zero255 pixels in that row. Neutral top0..<2pt mean RGB error increases5.1465→5.9596. This is a concrete nonnative white plateau; it is not rescued by a more accurate peak location. The proposed0.08 angular floor does not affect this top angular interval and cannot repair the plateau.

Neutral left/right0..<2pt errors improve19.0972→9.2708 and20.7917→11.1458. At0.25pt, outline-zero side RGB remains about[229.083,215.417,224.333]/[222.417,218.750,216.667] versus native[247.833,236.500,245.667]/[246.000,243.583,241.500]. Removing the dark line alone therefore does not reproduce the remaining side light. Beyond the first row, these neutral profiles are unchanged.

The source-neutral Alert bottom candidate remains backing-context contaminated. Its worsened0..<2pt result6.8500→7.8070 is retained but is not treated as a pure highlighter coefficient.

## CPU flat0.06 prediction, not a rendering result

A light flat opacity0.06 is half of the observed original0.12. Holding the recorded raster coverage and underlying shader result fixed, half-interpolating the measured0.12 and0 endpoints predicts first-row mean RGB247.058 in all channels. Its mean-RGB error relative to native is4.077 versus6.609 baseline and9.861 outline-zero. The first four rows' mean-RGB prediction is about4.514 versus5.147 baseline. The pixelwise CPU alpha model also predicts no255 values after that line, but this is not an actual candidate capture and must not be reported as passing GPU clipping checks.

This can suppress the white plateau and improve average top brightness; it cannot recover the native unequal RGB values or fix the unchanged0.75pt shoulder. Existing source/context and sampling differences remain. Therefore0.06 is a defensible bounded candidate, not evidence that the top is sufficiently matched. Actual line interpolation, raster quantization, corner blending and dark appearance still require capture. Per-row predictions are in `outline-zero-top-flat06-prediction.json`; all original tracks and controls remain alongside them.

## Minimum dark verification using public historical sources

The historical native Alert matrix already includes four declared sources (`fine_grid`, `color_stripes`, `tonal_blocks`, `synthetic_landscape`) in both themes, with the same320×172pt pane and375×667 world. `../analysis-alert-baseline/analyze_alert_baseline.py` and `../native-alert-map.md` bind source originals, actual before contexts, delivery hashes, foreground masks, and fixed straight/corner ROIs. These are public historical calibration, not unpublished noise or heldout input.

`../analysis-dark-scrim/analysis.json` establishes that all four dark Alert actual Windows are strictly byte-identical before/after the external scrim correction. Thus the original inside-pane baseline curves at positive inward distance remain applicable to `panels-dark-scrim-20261115`; the exterior negative-distance curve must use the actual new screenshot because its dim has changed. The original fixed historical top joins x62..<104 and271..<313; it is a colored-response diagnostic, not the new neutral-top segment. No ROI from the new probes is silently imposed on the old reference.

For a selected final Alert rim candidate, a bounded minimum is the existing two new inputs ×light×Alert/Sheet four REST, plus the four historical dark Alert REST. The latter reuse all original top/left/right/bottom and corner profiles, retain all regressions, and require the same source identity and pane geometry. This eight-REST scope covers unchanged Sheet controls, the newly observed light white plateau, multiple dark backgrounds and side/corner behavior. It does not constitute full dark new-probe, independent validation, dynamic, size, or product acceptance. The already existing reference first-four-row dark tracks are extracted unchanged in `historical-dark-fixed-rim.csv`.
