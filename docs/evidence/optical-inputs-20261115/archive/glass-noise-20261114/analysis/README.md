# Known-source dot correspondence

Use **`track_dots_v2.py`** for the next evaluation. Its protocol and implementation must be frozen before this analyst opens actual native or Android captures. `track_dots.py`, `tracking-protocol.json`, and `frozen-tracker.json` preserve the original v1; its documented counterexamples are not erased. See [the independent v1 review](tracker-v1-review.md) and [the synthetic review helper](review_counterexamples.py).

![Constructed source, known translation, blur, and blank rejection; not native glass measurements](synthetic-selftest-v2.png)

The figure contains constructed inputs only. The synthetic self-tests establish selected code paths and numerical conventions; they are not measurements of native glass, general correspondence accuracy, or a guarantee that each point can be identified.

## Run contract

Dependencies are Python, NumPy, Pillow, and Pillow's LittleCMS2. The freeze records their versions; actual runs reject changed NumPy, Pillow, or LittleCMS2 versions. No SciPy, OpenCV, or nearest-neighbor identity assignment is used.

```sh
python3 -B track_dots_v2.py --self-test
python3 -B track_dots_v2.py --freeze

python3 -B track_dots_v2.py \
  --source /absolute/test/n05_dots_s0.png \
  --points /absolute/test/n05_dots_s0.points.json \
  --observed /absolute/exact-750x1334-capture.png \
  --label native-light \
  --output /absolute/new-run-directory
```

Run these commands from this `analysis` directory or use absolute script paths. Freeze once. `--freeze` refuses to overwrite an existing v2 protocol or freeze. Each output directory must be new. Optional `--baseline /absolute/no-control-capture.png` tracks the baseline separately into `baseline-per-source.json`; it does not subtract baseline geometry or register images.

The CLI verifies the frozen implementation, protocol, input registration, source PNG hash, point-table hash, registered input identity/seed, point count, dimensions, opaque RGB source, embedded ICC profile, decoded source pixels, and the complete source-coordinate contract before opening an observed capture. Each point retains its provided identity. Pixel coordinates have their origin at the image's top-left edge; pixel `(i,j)` has center `(i+.5,j+.5)`. Continuous source centers are already in that coordinate system and must not receive an additional half-pixel offset.

Observed and baseline inputs must be exactly 750×1334 pixels. There is no fitted registration, rescaling, learned mapping, parameter search, or optimization against observed output. Profiled images are converted through LittleCMS to sRGB before RGB projection. Unprofiled images are explicitly assumed sRGB, and that assumption is retained in the report. Nonopaque alpha is rejected; there is no implicit compositing or alpha dropping. Original file hashes and color-conversion diagnostics are recorded.

## Measurements and rejections

The source RGB direction, relative to the declared RGB128 background, projects the known source neighborhood and observed search region. Cached source blur scales are sigma0/2/6 pixels. Local translation NCC uses an FFT numerator and integral-image local mean/variance. The search radius is 160 pixels for sources within an expanded nominal Dock rectangle and 8 pixels elsewhere. Far-source rows are labeled `outside_support`; their separate `control_status` describes the local control search and must not be counted as Dock refraction.

At most three spatially separated candidates survive. They retain NCC, color/context diagnostics, effective search bounds, layer label, foreground risk, local contrast, segmentation, and saturation. Minimum NCC is .60; color NCC and annular context NCC are .40; source-context standard deviation is at least one code. The unique best-peak margin is .08. Component contrast must reach two codes and SNR3. Segmentation uses 25/50/75% local-peak thresholds, with 50% primary and eight-neighbor connectivity. The protocol contains the full fixed rules.

Both the nominal search limit and the actual clamped correlation-array boundary are checked. A component whose center is outside a foreground glyph rectangle can still intersect that rectangle: v2 tests the actual component support and retains the pixel count/fraction. The full template rectangle's foreground overlap is also recorded, as a separate diagnostic. Template/context contamination is not automatically rejected solely on that diagnostic, so an unflagged primary component is not proof of a clean correspondence. Saturation rejection uses actual component pixels; bounding-box saturation is retained separately for comparison.

The primary morphology includes a weighted centroid, area, RGB/contrast, moment axes, angle, bounding box, and lossless global pixel-support runs `[y,x_start,x_stop]`, with exclusive `x_stop`. Axes are defined as `4*sqrt(weighted covariance eigenvalue)` and describe observed intensity blobs. They are not an unblurred disk fit, recovered physical ellipse, glass thickness, refractive index, or IOR estimate. Displacement from the ideal continuous source center is accompanied by displacement from the observable source centroid where that reference is identifiable, exposing rasterization offsets.

Source-overlap metadata conservatively rejects independent source identity and records a distinct reason. Separately, two accepted source identities sharing observed component pixels are rejected as `fused`, even when their RGB-weighted centroids differ by more than two pixels. A two-pixel center-competition gate is retained as an additional conservative rejection. Overlapping bounding boxes alone do not establish shared support. Rejected accepted-measurement fields move into `rejected_measurement`; they remain diagnostic JSON evidence rather than accepted CSV displacement.

Multiple eligible correspondences produce `multiple_lobes`, preserving candidates without forcing one displacement. Failures of identity, contrast, search-boundary, or shape assumptions remain `unidentified`. **V2 never emits `disappeared`**: weak contrast at the retained top-three NCC hypotheses cannot establish signal absence throughout the search region. The enum is reserved for compatibility and is explicitly marked unused. Every source identity remains in JSON and CSV, including failures, overlap, and edge clipping.

Each candidate's layer is classified against fixed nominal rectangles: `outside_dock`, `selected_lens_layer`, or `dock_base_nominal_bounds`. These are not recovered alpha or capsule boundaries. An original/outside candidate must stay labeled outside; filter by layer when counting Dock lobes. The selected lens is another glass layer over the Dock and must not be pooled with bare Dock measurements. The conservative icon/label masks and layer rectangles describe the recorded reference fixture; other layouts or states require a separately declared protocol.

## What this does not establish

Large non-affine distortion, unknown blur/tint, occlusion, overlapping source disks, several images of one point, and nearby features can defeat a local translation template. Limited search and candidate retention can miss correspondences; masks are conservative and fixture-specific. A status or engineering confidence score is not a calibrated probability, a proof of physical correspondence, or a universal yield claim. The fixed input families are targeted stimuli, not a random sample of natural photographs or all UI interactions.

The method is inspired by known-source windows and local correlation in Rajendran, Bane and Vlachos, *A Dot-Tracking Methodology for Background-Oriented Schlieren*, arXiv1812.10870, section3. Its small-displacement/yield and fluid inversion assumptions are not imported into this glass analysis. No native thickness, IOR, alpha boundary, per-millisecond equality, or 99.99% parity is inferred.

`input-only-runtime-smoke.json` is the preserved v1 source-equals-observed timing smoke: 128 sampled sources took about2.05 seconds on this machine. It is not actual holdout performance and is not a v2 timing claim. The v2 freeze records known synthetic counterexamples: weak-template false absence, a clamped-boundary peak, 96 foreground-overlap pixels with the center outside the mask, and two identities sharing160 pixels despite centroids2.82555 pixels apart. Synthetic rejections are retained rather than removed to improve a success rate.

Any actual output used to revise this algorithm or its thresholds becomes calibration. Preserve both versions, every failure, and original capture bytes. An output-driven v3 must be explicitly versioned and evaluated on new test seeds; it must not silently replace this frozen v2.
