# New nonperiodic panel probes: preregistered feasibility analysis

The first matrix is exactly two new calibration sources × native Alert/Sheet × light × REST, on iOS26.5 and Android. It has four observations per platform. Six gray files are `compatibility_unselected` placeholders and are excluded from capture and analysis. This is an identifiability check; it is not an independent test set, motion test, fit of material parameters, or parity acceptance.

The selected source PNGs are750×1334 RGB8 with embedded sRGB ICC. `manifest.json` binds their bytes and decoded RGB. `oracle.json` records every coarse coordinate cell and every shape's positions, vertices/bbox, color, raster-mask hash and visible centroid. The input contains no hidden/noise/old holdout source. Neither probe simulates glass.

## Why these sources are needed

The eight existing historical conditions show that vertical stripes have exactly zero normal input gradient on both carriers' top/bottom bands, despite a nonzero tangent gradient. For example, the Alert stripe top source normal/tangent RGB-gradient RMS is0/23.9394 encoded units per pt; Sheet top is0/25.0648. Thus those curves cannot identify normal refraction. Alert tonal blocks have zero source gradient in both top/bottom directions. Fine-grid input has two-dimensional excitation but repeated positions; its bottom normal gradient is also much weaker than the tangent gradient. Existing Sheet side profiles mix upper and lower backing contexts. These are reasons to change excitation, not reasons to fit more shader parameters.

`panel_probe_coordinate` has104 irregular cells, widths72–120px and full-row heights96–124px, with a final42px canvas-edge row. Every cell has independent non-collinear RGB x/y ramps and a nonperiodic color arrangement. `panel_probe_shapes` has16 filled, individually colored shapes, nominal dimensions80–124px; it has no microdots, thin outline-only identifiers or text. Shape placements are not an independent sampling distribution and are not asserted to remain separable through16dp material blur. Visibility must be measured.

## Gates before interpreting output

1. Require original750×1334 display captures,375×667pt/dp world at2px per unit, light appearance, normal transparency, declared source identity, and actual attached panel geometry. Alert pane must be[55,515,695,859]px; Sheet material raster must be[16,635,734,1318]px. Record the native Sheet AX317.7pt versus raster317.5pt distinction. No image registration, recenter, resize, warp, fitted translation, or substituted native source is permitted.
2. Bind each actual before-display/background plate and after-display capture to its PNG SHA and request/confirmation trace. A bare drawing input does not by itself establish the composed backdrop. Match or document behind-pane controls independently; a direct foreground mask cannot remove broad blur of different backing controls.
3. Decode raw RGB and ICC-normalized sRGB separately. Retain a single CSV track only when those decoded tracks are exactly identical. Never turn an encoded RGB ratio into physical transparency/energy.
4. Define direct-foreground exclusion by the union of native AX boxes and actual Android layout boxes, expanded2pt. This algorithm is frozen before output decoding. Log every excluded sample; do not silently replace an unusable ROI. For Sheet, include the drag indicator and all content/actions in the foreground union.
5. Require REST display convergence using the capture receipts. A single REST still cannot establish repeatability or animation. This plan adds no repeat, dark, size or motion conditions to the first matrix.

Failure of a geometry, source, color or readiness gate invalidates the affected observation for optical inference. Keep its capture and report the failure; do not silently move the pane or ROI to make it pass.

## Fixed straight-edge regions

All coordinates below are logical world pt/dp, half-open. Samples use original pixel centers with0.5pt spacing, first signed distance−5.75pt. Positive distance points inward. Do not pool disjoint tangent segments before reporting them.

|Carrier / segment|Boundary and inward sign|Tangent interval|Last inward distance|
|---|---|---|---:|
|Alert left|x27.5, +|y307..<338|24|
|Alert right|x347.5, −|y307..<338|24|
|Alert top left|y257.5, +|x62..<104|20|
|Alert top right|y257.5, +|x271..<313|20|
|Alert bottom left|y429.5, −|x62..<104|10|
|Alert bottom right|y429.5, −|x271..<313|10|
|Sheet top left|y317.5, +|x48..<110|24|
|Sheet top right|y317.5, +|x265..<327|24|
|Sheet left upper straight|x8, +|y353.5..<365|24|
|Sheet right upper straight|x367, −|y353.5..<365|24|
|Sheet left lower diagnostic|x8, +|y610..<625|24|
|Sheet right lower diagnostic|x367, −|y610..<625|24|
|Sheet bottom left diagnostic|y659, −|x48..<110|24|
|Sheet bottom right diagnostic|y659, −|x265..<327|24|

The old Sheet upper side interval347..<353.5 is retained separately as a **corner-proximal raster diagnostic**, not joined to upper straight or lower side. Its first29.5pt-from-top samples can lie within the current Android36dp top corner. Native optical contour equality is not assumed. Lower side/bottom still carry different backing-UI context and do not become clean primary material ROIs simply because the new input is known.

Report signed-distance bins separately: exterior[−6,0), first rim[0,2), second rim[2,4), shoulder[4,12), interior[12,20), and deep[20,24). Truncate bins at each declared last distance. Save raw RGB, fixed-smoothing RGB, D1 and D2, with the existing sigma.75pt/7sample reflected-end smoothing and0.5pt derivative spacing. Do not differentiate across foreground gaps. These bins separate narrow rim behavior from broad shoulder/body behavior; they are not recovered physical depths.

## Fixed corner raster regions

Keep all four Alert corners at the existing horizontal scan depths4.25,8.25,12.25,16.25,20.25,24.25pt from the respective top/bottom. The horizontal inward range is−5.75..<28pt,0.5pt spacing, from x27.5 or347.5. Apply the same foreground union to each scan and retain masked gaps. These are horizontal raster slices, not fitted normals.

For Sheet top corners, use depths4.25,8.25,12.25,16.25,20.25,24.25,28.25,32.25pt from y317.5 and horizontal inward range−5.75..<40pt from x8/367. For bottom corners, use depths4.25,8.25,12.25,16.25pt from y659 and horizontal inward range−5.75..<24pt. Do not pool36dp-top and20dp-bottom Android corner contexts. Native contour is observed, never replaced by that Android contour.

A corner row needs at least16 contiguous clear original pixels (8pt) for derivative/shape diagnostics. Shorter rows retain raw appearance samples but are labeled insufficient. A2D corner may be correspondence-ineligible even when these1D RGB curves are valid.

## Keep four measurement questions separate

**Input / exterior scrim.** Check actual bare input versus actual before-display at the fixed source coordinates. Exterior ROIs stay Alert[32,176,343,220] and Sheet[24,170,351,272]pt. For shapes, the three known RGB swatches K01–K03 are additional individual exterior controls. Report before/after RGB, through-origin channel/all-channel gain and residual as encoded-color diagnostics only. Do not subtract a fitted dimming field to make the glass match.

**Body color and texture transfer.** Keep Alert body rectangles left[49.5,307,54.5,338], right[320.5,307,325.5,338], gap left[60,350,110,359], gap right[265,350,315,359]. Keep Sheet upper-left[48,348,110,365] primary; middle-left[48,430,110,442] and lower-right[265,610,327,625] remain diagnostics. Report means, RGB quantiles, local contrast and gradient energy. Compare source-to-body and source-to-edge at the same oracle features. Brightness/chroma/contrast changes are not coordinate displacement.

**Apparent blur / edge sharpness.** Use only oracle-declared color seams or shape edges that are single, isolated transitions in the fixed region. In each original-pixel transect, report observed10–90% color-edge width and source width, using local two-side RGB levels to normalize amplitude. Preserve the absolute levels as well. At least4 clear original pixels must exist on each plateau; the transition must be monotone except for a separately recorded narrow rim. Multiple crossings, a clipped plateau, hue reversal or superposed control makes width unidentified. This is apparent edge width, not an independently recovered blur kernel: refraction/stretch can also alter it. Report the corresponding location/stretch diagnostic beside it; do not call a color boost a sharper geometric feature.

**Apparent displacement / stretch.** Use source oracle IDs, unique color/shape context and fixed world coordinates. Trace visible contour crossings or a complete detectable feature's centroid and extent; never search a global image translation or warp the screenshots. A complete-feature centroid/size is allowed only if its support is inside the observation window, clear of foreground, and separated from another ID. Otherwise report only an eligible local contour crossing, or unidentified. Compare the output feature locations and horizontal/vertical extents with the same source feature, per feature and distance bin. A uniform RGB increase with unchanged contour coordinates is a color change. A wider color-edge spread alone is not geometric stretch.

Each shape's fixed search/support window is its oracle design bbox expanded64px on each side, clipped only to the original source canvas. This is declared before output decoding; it is not recentered on a detected peak. Neighboring fixed windows may overlap, but two detected IDs may not be merged to produce one centroid. Each coordinate cell's local appearance support is its declared half-open bbox; local seam profiles are split at the oracle cuts rather than averaged across unrelated cells.

## Fixed visibility / uniqueness gates

These are conservative engineering gates for whether a measurement may be attempted. They are not universal statistical confidence bounds, and they are not thresholds for iOS/Android parity.

- Project feature-to-neutral RGB contrast onto the source feature's declared color direction. Require absolute output amplitude at least8 encoded channel-equivalent counts and at least5× the local neutral-region robust spread, with a1count quantization floor. Record the full RGB contrast vector; if its direction cosine to the source code is below0.7, color identity is unconfirmed. Do not force that feature to its nearest oracle point.
- A location/width measurement needs at least12 clear original pixels across the visible feature/transition support and an isolated signed edge peak. Any secondary peak within the oracle cell/support exceeding80% of the primary, or a missing opposing plateau, marks the correspondence ambiguous. Dense coordinate cells may pass appearance/gradient analysis while failing local correspondence.
- A centroid/extent measurement needs a full connected support of at least64 clear original pixels, at least95% of the observed contrast mass inside its fixed support, and no overlap of another detected ID. These conditions cannot rescue an intrinsically pane-clipped source shape. Such a shape is limited to eligible local contour measurements.
- A2D displacement/shape claim additionally needs source gradient-tensor eigenvalue ratio λmin/λmax≥0.05 within the **declared feature support**. Rank-one texture can support a single normal-direction observation, not a2D vector. Record both eigenvalues. A large source tensor does not guarantee uniqueness after blur.
- Estimate a local edge location only from a unique crossing/peak in its declared oracle support. Report pixel sampling uncertainty of at least±0.25pt plus the measured half-width of any tied/flat peak. If location uncertainty exceeds1pt, mark that scalar location unresolved for fine comparison. Do not interpolate across a foreground or pane-coverage gap to manufacture a location.

If16dp blur erases a marker or merges neighbors, the correct result is **not identifiable at this feature scale**. Keep its ID, failed gate and diagnostic curves. Do not lower the gates, introduce small-dot fitting, choose a nicer feature, or tune the shader from a failed correspondence.

## Narrow highlight diagnostic

Treat the user's observation as three separate hypotheses: source colors remain sharper, near-edge feature deformation is larger, and a narrow outer highlight accompanies rapid profile falloff. The first two require the color-edge and geometric diagnostics above. Highlight amplitude is not evidence of either by itself.

In the shapes source only, reserve fixed candidate-neutral tangent segments: Alert top/bottom x140..<235pt and left/right y353..<359pt; Sheet top x140..<160 and215..<235pt, bottom x140..<235pt. Apply the same foreground mask, including drag indicators. Analyze distance−2..<4pt separately from4..<12pt. Report encoded luminance/RGB excess, peak location, FWHM, and first/second derivatives without fitting the optical profile.

These are **candidate** neutral highlight diagnostics. Verify source/before-display neutrality and visible backing context before calling one eligible. Require per-channel source/before local range≤2counts and no direct foreground in the sampled row. A broad material footprint can still include nearby shapes or backing controls: if these are not matched or a halo overlaps, label the result mixed highlight/backdrop response and do not attribute it to thickness alone. No neutral third input is added to this matrix. Narrow-band peak/FWHM is unresolved if fewer than3 original pixels cover the detected peak, the half-height crossing is missing, or another peak is above80% of the primary.

## Required report / stop condition

Report every source/carrier/segment separately, including failed gates, body/exterior differences, edge widths, contour/feature movement, corner scans and rim profiles. Keep raw/ICC provenance and all exclusions. Do not pool the four light observations into an overall winner, produce a reproduction percentage, infer material thickness from one highlight, or fit freely chosen blur/refraction/tint/shine parameters.

If no near-edge feature is identifiable after capture, stop optics fitting and report which feature scales/positions failed. A revised stimulus must be a separately versioned calibration plan with new hashes, not a silent replacement of these inputs. Dynamic approach/size/speed experiments remain future work after static identifiability and panel material are established.
