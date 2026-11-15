# Isolated-shape paired-response calibration

This directory defines a static calibration diagnostic, not a fidelity claim. Its
method and source identities are frozen before its author reads this packet's
actual captures. Only the four registered calibration pairs are supported. The
independent `test/` split is neither opened nor accepted by this analyzer.

## Run order

```sh
python3 analysis/analyze_calibration.py --self-check
python3 analysis/analyze_calibration.py --freeze
python3 analysis/analyze_calibration.py --analyze \
  --native-index native-calibration/native-dock-index.json \
  --android-result android-candidate-calibration/result.json
```

Run from this packet's root, or use absolute paths. The program resolves its
synthetic protocol relative to its own file. An existing freeze or output is
never overwritten. Method edits invalidate the freeze; preserve the old version
and document a new method rather than silently re-freezing after seeing outputs.

## Experimental unit and response definition

Each pair contains an opaque RGB128 control and one known three-color circle,
triangle, star, or asymmetric polygon. The geometry JSON retains the analytic
boundary, exact 4×4 subpixel coverage counts, band colors, original file/pixel
hashes, coverage area and pixel-center moments. The analyzer reconstructs every
calibration input pixel from those counts before processing captured output.
It does not treat a drawn circle as a point source or infer renderer linearity.

At fixed world pixel `p`, the measured conditional response is

`D_system(p) = C_system,shape(p) − C_system,control(p)`.

`C` is color-managed sRGB code RGB in 0–255. Both signed RGB and signed
`Y′ = .2126 R + .7152 G + .0722 B` are retained. A separate linear-light
diagnostic is computed by decoding each original RGB image with the sRGB transfer
curve and then subtracting its weighted Y values. The linear-light diagnostic is
not obtained by decoding signed RGB differences. No background median, distant
mean, white level or fitted gain is subtracted. A source-dependent change of the
whole material therefore remains visible in both local and remote domains.

Native–Android residuals compare these conditional responses at identical
coordinates. Absolute shape-image and control-image RGB errors are reported
alongside them; cancellation in a difference image must not hide baseline errors.
The native REST/repeat response difference is a descriptive repeat check. It is
not an error correction, significance threshold or confidence interval. No
Android repeat is invented when the capture fixture supplies one REST image.

## Sampling, layers and state

The source world remains 750×1334 physical pixels at 2 px/pt. Native PNGs must
have exactly this size. Android uses only its recorded source origin and an
integer window crop at density2; fractional origins, scaling, rotation or clipped
worlds stop analysis. There is no output-driven registration or interpolation.
Embedded ICC profiles are converted to sRGB with perceptual intent0. Untagged output is
explicitly labeled as an sRGB assumption. Original profile/file hashes remain in
the report. Bare captured source worlds are compared to the reconstructed source
and the residual is reported, not normalized away.

The frozen masks include the full canvas, nominal Dock capsule, nominal selected
lens, broad glyph neighborhoods, their nominal base-only complement, inner and
outer rim bands, backing-scroll text, a fixed remote guard, a source-centered
128px disk and its complement. Eight fixed image-direction sectors and four
source-radius bands describe response spread. All source-color-band supports
remain separate. These regions overlap intentionally and are not independent
replicates. A nominal geometry or AX rectangle is not an optical layer mask;
glyph blur and content adaptation can influence every region. Native SF Symbols
and Android Material foreground are not assumed identical.

Nominal capsule boundaries are evaluated at offsets −1,0,+1 physical pixel
(−.5,0,+.5pt), while observed pixels stay fixed. All offsets are reported; none is
selected to improve an error. `sampling-spec.json` freezes every mask count and
bit-pattern hash. Actual AX tab rectangles and actual public material traits are
preserved as diagnostics. Public effective traits do not expose private material
shader adaptation. If control, shape, repeat or platform public themes differ,
the data are retained and labeled; a conditional response is not silently
reclassified as a same-material estimate.

## Area, directions, components and color

Inclusive thresholds 1,2,4,8,16 code values are all retained. They are descriptive
sensitivity levels, not perceptual visibility or pass/fail thresholds. Detection
uses the maximum absolute RGB difference plus separate positive/negative R, G,
B and Y′ lobes. Positive and negative effects cannot cancel one another in these
maps. No morphology, denoising, minimum-area filter, largest-component selection
or forced object matching is applied. All exact 8-connected components remain,
including single pixels, split responses and zero-component cases.

Each component records area, bounding box, amplitude-weighted centroid and
covariance, principal-axis orientation when identifiable, direction from the
known source center, mean signed RGB, overlap with the original source coverage,
nominal layer counts and canvas clipping flags. IDs are local to a
system/pair/theme/lobe/threshold and convey no correspondence. A zero-component
result means only "unresolved under this specified threshold and observable
image/state"; it does not establish disappearance. Direction is an image-space
descriptor, not a tracked optical ray. Threshold area is shown beside source
coverage area because different shape families do not have equal area at equal
circumradius. Such an area ratio is not recovered physical magnification.

## Outputs and interpretation limits

`*-signed-responses.npz` preserves full-canvas float32 signed RGB/Y′/linear-Y
fields for native REST, native repeat and Android candidate. This serialization
does not replace the hashed original PNGs, and summary calculations use float64.
The CSVs expose signed/absolute statistics by stratum, all area thresholds,
native–Android residuals, native repeats and bare-source guards.
`components.jsonl.gz` keeps every component. `capture-sources-and-state.json`
retains image/profile hashes, crop rules, native provenance/AX and Android actual
geometry/material metadata. `report.json` hashes each produced file.

This is a deliberately targeted calibration sample, informed by a prior pilot.
Four shape cases × two requested themes are correlated observations, not eight
independent draws from arbitrary content. The selected lens, backing text,
nonlinear color/material adaptation, blur, warp, clipping and occlusion are
possible contributors to the observed response. The method assumes neither a
linear shift-invariant PSF nor a one-to-one source/output topology and cannot
uniquely identify glass thickness, IOR or a native private shader. It produces no
global similarity percentage, native-equivalence verdict or dynamic-parity
claim. A future independent test needs a frozen analysis contract before its
actual outputs are read; calibration-based method revisions must be disclosed.
