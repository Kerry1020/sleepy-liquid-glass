# Panel outer-rim evidence, fixed neutral candidates

This read-only follow-up uses the already frozen shapes-source neutral tangent intervals, world coordinates, and native/Android union foreground mask from `../panel-probes-preparation/analysis-plan.md` and `../analysis-native-probes/geometry-and-mask.json`. It does not read unpublished noise/heldout inputs, register images, fit material parameters, change source code, or operate devices. All seven raw/ICC image decodes are identical; input file SHA256 values are in `inputs.json`. Existing full capture/geometry/repeat provenance is retained in `../analysis-native-probes`.

`tracks.csv` retains signed distances −1.75 through 11.75pt at the original 0.5pt pixel centers, each platform's mean RGB and tangent RGB range, and the number of excluded samples. `curves-and-derivatives.csv` adds the frozen sigma0.75pt / seven-sample reflected-end smoothing and first/second derivatives, never crossing a masked gap. `summary.json` retains every declared candidate, including fully masked and contaminated ones. Native and Android geometry is not fitted to the highlight peak.

## Actionable observations

| Fixed neutral candidate | iOS 26.5 peak inset / encoded luma | Android baseline peak inset / encoded luma | Interpretation |
|---|---:|---:|---|
| Alert top, x140..<235 | 0.25pt / 245.86 | 0.75pt / 243.04 | Clear outermost placement difference; not a measured physical thickness |
| Alert left, y353..<359 | 0.25pt / 239.57 | 2.75pt / 221.82 | Android first4pt has no positive peak above its8..<12pt shoulder |
| Alert right, y353..<359 | 0.25pt / 243.95 | 3.75pt / 221.61 | Same absent side highlight; Android very first interior pixel is strongly darkened |
| Sheet top, x140..<160 and215..<235 | excluded | excluded | Both candidates are entirely covered by the frozen conservative grabber strip; no replacement ROI is chosen |
| Sheet bottom, x140..<235 | 0.25pt / 248.46 | 0.25pt /255.00 | Diagnostic only: native Dock backing differs; Android already clips to white and stays broader |

The Alert top source is uniform, and native before-display tangent variation is at most1 encoded count per channel. The left/right source and before-display are uniform. No direct foreground is excluded from these Alert candidates. Their output still contains colored halos from nearby shapes through the material footprint, so the table is an observed edge/material response rather than a pure isolated specular coefficient. The fixed bottom Alert candidate fails before-display neutrality (range233/67/42), and its peak/FWHM is retained only as contaminated diagnostic output.

Every native candidate's half-height peak occupies only two original pixels (bottom Alert only one). The preregistered three-pixel support requirement therefore leaves all native FWHM values unresolved. Do not turn the 0.5pt raster peak-location difference into subpixel optical accuracy or infer a continuous taper width from it. The sampling uncertainty is at least±0.25pt per platform.

The Sheet bottom Android half-height width is2.92pt versus an unresolved, visibly shorter native peak; its raw values and native/Android backing mismatch are retained. This cannot justify a global strengthening of Sheet highlights. The Sheet top neutral candidates provide no accepted inference under the current mask.

## Source mechanism and bounded next intervention

The current Alert side discrepancy has a direct source counterpart: `LiquidGlassRim.alert` uses `minimumShine=0`; the `liquidGlassShineTurns` angular table ends atπ/2 with zero brightness. Thus side-oriented edge samples get no additive shine. In addition, `GlassControlModifier.onDrawFront` draws a0.5dp CPU black stroke with light Alert side opacity0.35, strongest exactly at the missing bright side pixel. At inset0.25pt the fixed left/right native RGB is about[247.83,236.50,245.67]/[246.00,243.58,241.50]; Android is[188.75,177.50,184.67]/[183.25,180.33,178.50].

These data support an Alert-only mechanism test that isolates CPU dark hairline placement and the angular minimum-shine behavior. Increasing global shine alone would also brighten the top and cannot remove the existing dark side stroke. No native coefficient, accepted parameter, or product fix is inferred here. The sharpness, geometric stretching, and outer-rim questions remain separate; this analysis changes none of them.

`source-references.json` freezes the consulted source bytes. `initial-error.txt` preserves two export-only script failures; the rerun changed CSV field union and integer serialization only, with identical capture/ROI/threshold/decoded inputs.
