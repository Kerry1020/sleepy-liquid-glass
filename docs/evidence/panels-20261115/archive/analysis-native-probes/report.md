# Nonperiodic native panel calibration: static feasibility

This run establishes measurable local color contours on iOS 26.5 and rejects two Android mechanism candidates. It does **not** recover a unique two-dimensional refraction field, a physical lens thickness, a blur kernel, an animation match, or an overall reproduction percentage. The two sources are calibration inputs, not an independent test set.

The native Alert is measurably sharper than the current Android Alert at the identified S02 triangle edge and the unique coordinate seam. Turning refraction from60 to0 changes some local contour locations but leaves broad transitions and produces excessive blue contrast near the top. The subsequent clear-edge candidate also fails: several fixed transitions become wider and weaker. Neither candidate is accepted as a fix.

## Provenance and readiness

`predecode-freeze.json` was written before the first native output pixel decode. It binds the frozen analysis plan, oracle, selected PNGs, loader manifest, original native target, fourteen PNGs, fourteen AX attachments, requests and both complete sessions. The five original native App files match the11/14 binary freeze byte for byte. Only the UI test runner changed for this capture method. The native capture test passed; the initial postprocessor had an obsolete pre-install container UUID. Export was recovered from the same run's current public container without recapture.

All fourteen screenshots match the declared request, source, loader hash and session UUID. They occur after the request and before the next requested operation. AX follows each screenshot. At every REST capture the latest public controller trace reports no presentation or dismissal in progress. Both sessions report iOS26.5/23F77,375×667pt at2px/pt, light style, normal transparency and normal motion. Both exported original backgrounds match the shared selected PNG bytes. See `capture-receipts.json`.

Native Alert AX is[27.5,257.5,347.5,429.5]pt. Native Sheet AX is[8,317.7,367,659]pt; this remains distinct from the frozen material raster[8,317.5,367,659]pt. Android Alert and Sheet attached material rectangles are the exact frozen raster rectangles. The candidate retains the exact source hash, source world, unit pixel basis, pane geometry and all exported foreground slot rectangles. No image is resized, registered, recentered, translated by a fitted parameter, warped or substituted.

The native same-presentation repeat is pixel-identical across the entire display in all four conditions: zero changed pixels and zero RGB difference. Foreground AX boxes also repeat exactly. These repeats measure capture stability and are not independent samples. Before/after context differs in the coordinate session due to screen UI and tiny rendered context changes; the Alert fixed exterior ROI remains pixel-identical. No context difference was corrected or removed. `context-stability.json` retains the actual differences.

Every decoded image inspected in the main analysis has identical raw RGB and ICC-normalized sRGB tracks. `decode-provenance.json` records file, ICC and decoded hashes. One track is retained where the two representations are exactly equal.

## Masks and limits

The direct foreground mask is the union of actual native AX and Android layout rectangles, expanded2pt. Alert uses title, message and both actions. Virtual giant/offscreen scrollbars are excluded from the visible foreground list. Sheet includes its grabber, native text, switch, slider and action. Android exports the complete Sheet content box rather than each text row; this conservative box masks otherwise potentially usable middle regions. No separate Android grabber slot is exported, so the central Sheet top strip[140,317.5,235,353.5]pt is explicitly excluded. This makes the frozen Sheet top-center highlight diagnostic unavailable; it does not invalidate the clean top-left/top-right Alert bands. See `geometry-and-mask.json` and `exclusions.json`.

Backing UI differs between the two apps: native system presentation buttons and native Dock versus Android fixture presentation controls. A foreground mask cannot remove a backing control's broad material footprint. Body and lower-Sheet measurements retain that limitation. Local contour values are apparent rendered color contours, not a guaranteed isolated source-coordinate mapping.

Every one of the sixteen shapes is audited separately in both carriers. None supports a complete material-only centroid under the source pane/foreground geometry. A shape partly outside the pane cannot be completed using its unrefracted exterior pixels. The audit retains all IDs and source2D structure tensors. The only measured shape contour in this pass is the explicitly identified local S02 right edge; other IDs remain unmeasured, not asserted absent. See `all-shape-geometry-audit.json`.

## Local S02 contour

The source is the blue S02 triangle, whose pane-clipped design occupies x116..220px,y460..564px. The fixed oracle support is unchanged. The local scalar scan is x84.25..141.75pt at every original row y261.75..277.25pt in0.5pt steps. High and neutral plateaus are x84..92 and120..140pt. RGB contrast is projected onto S02's declared source direction[-154,-89,41]. The source/contrast vectors, robust neutral spread, secondary derivative peaks, crossing multiplicity, raw curves and failed gates are retained.

The parent plan preregistered the source support, normal/tangent regions, smoothing and gates before output decode. These exact local plateau/scan operational choices were made after the first native/baseline review, then frozen before decoding refraction0 and reused unchanged for clear-edge. Thus this is an exploratory localization within the preregistered source support, not an independently preregistered confirmatory contour test. The complete fixed straight/corner curves also retain the outer rows and all other regions; the local diagnostic does not replace them.

This is a right-edge horizontal color contour. It does not by itself identify a two-dimensional source coordinate or normal refraction. The frozen secondary-peak gate fails for all Android rows because their broad derivative response has multiple similarly high local peaks. Their crossing/width values below therefore remain **descriptive diagnostics**, not accepted fine displacement measurements. Native passes18/32 rows; it also retains fourteen failed rows. No gate was relaxed to obtain a result.

Representative original, unsmoothed10–90% widths in pt:

|World y / inward distance|Native|Baseline60|Refraction0|Clear-edge|
|---|---:|---:|---:|---:|
|265.75 /8.25|12.60|23.51|23.18|26.01|
|269.75 /12.25|12.53|24.14|24.57|27.04|
|273.75 /16.25|12.22|23.72|24.21|27.43|

The source width is0.40pt under linear threshold interpolation of original pixel samples, below the0.5pt sampling interval; this is not subpixel optical resolution. The fixed sigma0.75pt seven-sample smoothing is also reported separately. It changes the source step width to about1.93pt but leaves the native/Android width difference clearly visible. Apparent width combines material blur, coordinate deformation, color mixing and sampling; it is not a separately recovered blur kernel.

At y269.75, the source-colored contrast amplitude is49.88 native,42.72 baseline and36.01 clear-edge encoded counts. The source-color direction cosines are about0.93..0.95. The candidate thus weakens the feature while widening it. At y261.75, refraction0 contrast rises to46.19 versus18.69 native and21.07 baseline, even though its crossing gets closer. Matching one crossing while doubling the observed contrast is not a successful fix.

Fixed-smoothed50% crossings in pt:

|World y|Native|Baseline60|Refraction0|Clear-edge|
|---|---:|---:|---:|---:|
|261.75|102.71|107.66|102.19|108.05|
|265.75|103.74|106.21|103.50|105.91|
|269.75|104.59|105.51|104.46|105.51|
|273.75|105.74|105.65|105.55|106.16|

These do not support “larger shift is always better.” Refraction0 moves the first rows toward native while leaving the broad edge and worsening color amplitude. Native y269.75 passes the stated local gates and has a minimum sampling/peak-tie location floor of±0.25pt. That floor is not a full statistical confidence interval; material/backdrop mixing remains a separate systematic limitation.

![Fixed S02 source-color contours](S02-local-contours.png)

## Unique coordinate seam

The second diagnostic is the unique vertical source seam at x77pt, within the frozen Alert top-left tangent segment. Its adjacent source xcells are[72,154) and[154,244)px. Rows before and after the y530px cell boundary are kept distinct. The local scan is x62.25..103.75pt with original fixed plateaus[62,70) and[96,104)pt. Local source RGB direction is computed from the actual known adjacent source values at the same row, not from the rendered output.

At y261.75, native and baseline output contrast directions have cosine−0.064 and0.040 to that same-row source seam. The visibility/color identity gate fails. The output might contain mixed or differently mapped source rows; it is not valid to invert its RGB into a source coordinate. Native passes25/32 later-row local contour gates, while Android baseline/refraction0/clear-edge retain their failed isolation gates.

Representative fixed-smoothed diagnostics:

|World y|Native50% crossing|Baseline60|Refraction0|Clear-edge|
|---|---:|---:|---:|---:|
|265.75|73.08|79.13|78.47|79.89|
|269.75|75.36|79.05|78.51|80.50|
|273.75|76.70|78.88|78.67|80.30|

Native10–90% raw widths are12.23,12.72 and12.73pt respectively; baseline widths are21.04,20.66,20.70pt. Clear-edge widths increase to21.41,22.95,23.28pt. This second source corroborates broad-edge regression rather than a source-wide coordinate translation. The source tensor is two-dimensional, but one color seam after blur still cannot uniquely identify a two-dimensional inverse field.

![Fixed unique source seam](coordinate-local-contours.png)

## Exterior, body, corners and rim

The fixed exterior native and baseline Android rendered ROIs are pixel-identical in all four conditions. Coordinate source encoded-through-origin gains are approximately0.80000 with about0.283count RMS quantization residual. These are encoded RGB diagnostics, not physical transparency or energy. There is no exterior scrim mismatch to remove before comparing panels.

All fixed straight segments and each distance bin are reported separately in `straight-tracks.csv` and `straight-bin-stats.json`: raw RGB, fixed smoothing, D1,D2, clear-pixel count and context status. Every frozen corner horizontal scan is retained in `corner-raster-tracks.csv`, with gaps and contiguous-run eligibility. No fitted contour normals or replacement samples are used. Body/exterior means, quantiles, chroma, gradient energy and encoded gains are in `body-exterior.json`.

`candidate-fixed-roi-delta.json` contains180 individual segment/bin comparisons without pooling them into a score. One material regression illustrates the practical change: shapes Alert top-left inward12..20pt has native mean RGB[186.8,206.6,250.9], baseline[193.9,209.8,242.6] and clear-edge[199.5,211.5,239.0]. Candidate RGB MAE against native increases by[5.56,1.69,3.66]counts. Coordinate in that same region increases by[2.51,1.06,4.16]. Sheet changes are also mixed and do not rescue the failed Alert candidate.

Narrow rim/highlight is analyzed independently in `narrow-rim-diagnostics.json` and `narrow-rim-tracks.csv`. Native shapes Alert top has a peak at inward0.25pt,22.29 encoded luma counts above its4..12pt shoulder. Baseline top peak is0.75pt,19.91counts. Both fail the minimum three-original-pixel peak-coverage/FWHM gate. The current2px/pt capture therefore does **not** resolve the full narrow peak shape, and no precise highlighter softening width or physical thickness is claimed. Native left/right fixed segments show positive rim peaks; baseline those segments do not show the same narrow positive response. Some candidate-neutral segments fail before-image neutrality due to backing controls. Even eligible same-coordinate neutral rows can have a broad footprint contaminated by nearby shapes/UI; all remain mixed highlight/backdrop diagnostics.

## Decision and next boundary

Reject refraction0 and clear-edge as runtime fixes. Preserve their evidence. The static images support identified apparent sharpness differences and specific local contour discrepancies. They do not establish a unique source mapping, a physical thickness law, a motion curve or99.99% parity. Solve the real sampling/blur mechanism without fitting these two probes into an acceptance score. Dock/panel static optics and the mechanical highlight remain unfinished; dynamic size/speed/acceleration work should not advance ahead of those static questions.
