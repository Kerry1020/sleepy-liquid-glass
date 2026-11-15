# Sheet true-radius API12 → 10: response improved locally, parity rejected

The response changes in the intended direction in several fixed regions, but it does not match the native Sheet. Native S07 passes all14 rows, phase A12 passes0/14, and phase B10 passes only1/14. The other13 candidate rows fail the unchanged secondary-derivative-peak gate. They remain visible descriptive tracks, not fine correspondence/width evidence. No gate, source shaping, plateau or ROI was changed.

The sole eligible candidate row, y335.75pt, has raw10–90 width12.324pt versus native9.648pt. Its smoothed50% crossing is96.385pt versus native95.696pt (difference0.689pt; individual sampling floor±0.25pt), and contrast26.609 versus30.010 encoded counts. The matching phase A row is ineligible; its descriptive width12.579pt, crossing97.158pt and contrast23.425 are retained for context, not treated as accepted location measurements. Improving the candidate to one identifiable row does not establish a complete material match.

## Controls, routing and provenance

Both complete actual Alert Windows are RGBA pixel-identical to phase A, as are both plain-background Windows. All observed pane/canvas/unit-basis, source mapping, Window placement, foreground slots and content density are exact. Geometry/mask/exclusion definitions and all32 shape/carrier audits are unchanged. Sheet changes remain within the recorded pane: coordinate402200 changed Window pixels, maximum channel delta6; shapes150901, maximum7. Full-screen system-overlay changes are separately retained with exact coordinates; full-display equality is not claimed.

The build receipt and source hash freeze were bound before phase B first decode. GlassHost.kt SHA2565b4236fdf6340b4b42b8a783920b75e11359c6b52598a803322b7399ff3c820d and GlassFilterBands.kt SHAd0fcf91e572f2270de6d3a2316fc0cbc1e2667c482a0390eb6565288e2c4e8f2 satisfy the required routing-source binding. Receipt SHA50ecb5966250592be904bf2a1be5bb2415acc4214fa6b2c9034f37cce76fe930 declares successful build and unchanged build/test sources. RawRGB equals ICC-normalized sRGB for all compared images. Rejected-display images were not decoded.

Phase A true-radius12 reuses exact shared12; phase B true-radius10 uses the local preblur fallback because only2.5/12/16 bands exist. Thus this is the deployed API-input engineering response, including the deterministic execution-route switch. It does not independently isolate numerical radius in one Gaussian path and cannot recover physical sigma or thickness. No extra global band/dependency or radius6 was introduced. Dark was not captured; it retains its declared original factory/null path, without a dark pixel-parity claim.

## All14 S07 rows

Widths below are descriptive wherever a row fails. “unresolved” means raw crossings are missing/nonunique; smoothing does not replace the raw result. The full per-row gate data are in `phaseA-phaseB-S07-all14.json`.

| y(pt) | Native raw width | A12 raw width | B10 raw width | Native50% | A1250% | B1050% | Native/A12/B10 contrast | B gate |
|---:|---:|---:|---:|---:|---:|---:|---|---|
|334.75|9.949|12.383|12.014|95.827|97.114|96.368|27.199/22.940/24.696|secondary peak>0.8|
|335.25|9.813|11.947|12.432|95.729|97.347|96.259|28.260/22.462/25.758|secondary peak>0.8|
|335.75|9.648|12.579|12.324|95.696|97.158|96.385|30.010/23.425/26.609|pass|
|336.25|10.076|12.867|unresolved|95.641|97.026|96.172|31.654/24.113/27.775|secondary peak>0.8|
|336.75|9.918|12.782|11.806|95.608|96.886|96.596|33.882/25.174/27.985|secondary peak>0.8|
|337.25|10.146|12.183|12.341|95.694|97.061|96.464|36.005/25.069/29.630|secondary peak>0.8|
|337.75|9.596|12.083|11.860|95.609|96.880|96.296|37.171/26.131/30.797|secondary peak>0.8|
|338.25|10.123|12.426|12.111|95.706|96.842|96.046|38.338/27.297/31.760|secondary peak>0.8|
|338.75|9.823|11.785|11.752|95.682|96.837|96.150|39.026/26.816/32.343|secondary peak>0.8|
|339.25|10.152|12.112|11.501|95.658|96.772|96.218|39.881/27.673/32.926|secondary peak>0.8|
|339.75|10.017|unresolved|11.828|95.712|96.957|96.113|40.946/27.782/33.882|secondary peak>0.8|
|340.25|9.921|12.355|11.667|95.745|96.743|96.113|42.112/28.464/35.049|secondary peak>0.8|
|340.75|9.835|12.756|11.146|95.720|96.525|96.224|43.068/29.525/34.740|secondary peak>0.8|
|341.25|9.922|12.126|11.612|95.688|96.881|96.197|43.757/28.942/35.907|secondary peak>0.8|

## Fixed region response

All180 independent segment/bin comparisons are retained in `phaseA-phaseB-fixed-roi-all180.json` and CSV. Each keeps its original primary, corner-proximal or backing-context label. The table below shows every light Sheet primary interior bin as phaseB minus phaseA native RGB MAE; negative is a smaller encoded-color error for that channel. This is descriptive local error, not inferred transmission, dispersion or an aggregate parity score.

| Source | Segment | Inward bin(pt) | Δ native MAE(R,G,B counts) |
|---|---|---|---|
|coordinate|top_left|[0, 2]|-0.097, +0.294, -0.371|
|coordinate|top_left|[2, 4]|-0.119, +0.083, -0.149|
|coordinate|top_left|[4, 12]|-0.078, -0.118, -0.580|
|coordinate|top_left|[12, 20]|-0.163, -0.174, -0.556|
|coordinate|top_left|[20, 24]|-0.118, -0.108, -0.550|
|coordinate|top_right|[0, 2]|+0.046, +0.738, +0.163|
|coordinate|top_right|[2, 4]|-0.163, +0.381, +0.442|
|coordinate|top_right|[4, 12]|-0.017, -0.707, -0.312|
|coordinate|top_right|[12, 20]|+0.044, -1.176, -0.545|
|coordinate|top_right|[20, 24]|-0.014, -0.742, -0.534|
|coordinate|left_upper_straight|[0, 2]|-0.130, -0.043, +0.359|
|coordinate|left_upper_straight|[2, 4]|-0.141, +0.000, +1.848|
|coordinate|left_upper_straight|[4, 12]|-1.378, -0.484, -2.995|
|coordinate|left_upper_straight|[12, 20]|-1.076, -0.147, -2.340|
|coordinate|left_upper_straight|[20, 24]|-1.446, -0.598, -3.707|
|coordinate|right_upper_straight|[0, 2]|-0.250, -0.207, -0.152|
|coordinate|right_upper_straight|[2, 4]|-0.859, +0.098, -0.370|
|coordinate|right_upper_straight|[4, 12]|-0.133, -0.250, +0.247|
|coordinate|right_upper_straight|[12, 20]|+0.283, -0.321, +0.242|
|coordinate|right_upper_straight|[20, 24]|+0.136, -0.283, -0.054|
|shapes|top_left|[0, 2]|-0.151, +0.502, -0.083|
|shapes|top_left|[2, 4]|-0.970, -0.621, -0.058|
|shapes|top_left|[4, 12]|-1.005, -1.321, -0.349|
|shapes|top_left|[12, 20]|-0.517, -0.609, -0.492|
|shapes|top_left|[20, 24]|-1.341, -1.820, -0.598|
|shapes|top_right|[0, 2]|+0.137, +0.433, +0.653|
|shapes|top_right|[2, 4]|+0.278, +0.760, +0.927|
|shapes|top_right|[4, 12]|-0.320, -0.582, -0.982|
|shapes|top_right|[12, 20]|-0.267, -0.387, -0.836|
|shapes|top_right|[20, 24]|-0.287, -1.140, -1.610|
|shapes|left_upper_straight|[0, 2]|+0.065, +0.054, -0.022|
|shapes|left_upper_straight|[2, 4]|-0.043, +0.152, -0.076|
|shapes|left_upper_straight|[4, 12]|-0.005, +0.003, -0.005|
|shapes|left_upper_straight|[12, 20]|+0.000, +0.000, +0.000|
|shapes|left_upper_straight|[20, 24]|+0.000, +0.000, +0.000|
|shapes|right_upper_straight|[0, 2]|-0.043, -0.076, -0.109|
|shapes|right_upper_straight|[2, 4]|+0.239, +0.000, +0.000|
|shapes|right_upper_straight|[4, 12]|-0.783, -0.005, +0.071|
|shapes|right_upper_straight|[12, 20]|-1.043, +0.024, -0.019|
|shapes|right_upper_straight|[20, 24]|-0.962, +0.022, +0.098|

The shapes top-left4..12pt region improves RGB MAE by[1.005,1.321,0.349]counts and12..20 by[0.517,0.609,0.492]. Coordinate top-left4..12 improves[0.078,0.118,0.580]. This does not extend uniformly to the rim: shapes top-right0..2 regresses[0.137,0.433,0.653], shapes top-right2..4 regresses[0.278,0.760,0.927], and coordinate left2..4 blue error increases1.848counts. All other bins and mixed-context diagnostics remain reported rather than averaged away.

Every fixed straight track, corner raster slice and narrow-rim track has a row-matched phaseA/phaseB delta export. The sampling support, mask, derivative eligibility and all Alert values are exact controls. Body/exterior and rim native/A/B objects are retained separately. Exterior means are identical to native for each source/carrier, so the changes are not an exterior-scrim adjustment. The fully masked middle-left body diagnostic stays unresolved; no substitute region was selected.

## Rim, complete-feature and interpretation limits

Sheet top-center rim tracks remain foreground-masked and unresolved. The bottom neutral track has native peak excess28.290encoded-luma counts; phaseA excess36.714 and phaseB36.713 remain above it. Its apparent halfheight width has mixed backing context, so it is not a physical thickness measurement or isolated softness estimate. Narrow peaks that fail the3-original-pixel coverage gate retain unresolved FWHM. No brightness-to-thickness or brightness-to-stretch conversion is made.

All16 source shapes across both carriers remain in the original audit. None has a fully clear, unclipped95%-mass material support, so no complete centroid or2D mapping was forced. S07 remains a scalar local contour. Backing-control appearance and broad-footprint differences between platforms remain systematic limitations.

The parent supports/regions/gates were frozen before the first native/baseline analysis; the exact S07 localization was operationalized inside those supports after that initial review and before these candidates. This candidate comparison does not retroactively make S07 an independent confirmatory feature. The two selected inputs are calibration, not held-out tests. There was no warp, registration, fitted translation, source substitution, new ROI, free optical fit or overall similarity percentage. No static result here establishes dynamic, multi-size or whole-product parity.

Decision: retain the experiment as a documented API-response result; do not mark the Sheet material aligned. A further implementation change needs its own frozen hypothesis and controls, without lowering these visibility gates.
