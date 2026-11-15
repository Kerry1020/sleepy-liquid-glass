# Independent source-only tracker review

Review date: 2026-11-14. Scope: `track_dots.py`, known source-point metadata contract, and independent in-memory synthetic counterexamples. No native/Android captures or rendered test outputs were read. The reviewer did not modify the tracker or frozen v1 artifacts.

## Confirmed numerical/logic defects

### 1. Weak retained matches do not establish disappearance

`track_one` labels a point `disappeared` when all retained NCC candidates have `weak_or_disappeared` local shape. The retained top three are only a correspondence shortlist, not an exhaustive contrast test over the search region.

Synthetic reproduction: a source dark square at (350.5,1050.5), radius 4, with five uniquely colored small context marks. The observed search area contains a strong dark elongated 5×30-pixel patch with >100 sRGB-code contrast, plus three 0.5%-contrast source-patch copies centered at (280.5,970.5), (350.5,970.5), and (420.5,970.5). The three weak copies obtain NCC 1.000000000, .999999988 and .999999969, but local projected peaks are only .90066642. V1 reports `disappeared` despite strong signal remaining in its search region.

Action: retain `unidentified` with a weak-candidate reason unless a separately declared full-search signal bound supports disappearance. Preserve the distinction between failure of correspondence and absence of detectable contrast.

### 2. The search-boundary flag ignores clamped image boundaries

The current flag checks only distance from the source anchor against the nominal ±160-pixel radius. It ignores a peak on the first/last valid correlation row/column when the search box was clamped by the canvas.

Synthetic reproduction: source (102.5,1050.5), radius 4, full scene translated by (−88,0). The sigma-0 template radius is 14. The best peak is at (14.5,1050.5), exactly the first valid correlation column. NCC is 1 and shape valid, but `search_boundary=false`, so v1 reports `tracked`.

Action: record effective search-center bounds per template and flag peaks at the actual `scores` array boundary in addition to the nominal search limit. Do not silently treat a clamped maximum as an interior peak.

### 3. Foreground gating checks a point rather than component support

`annotate_candidate` checks the correlation center against foreground rectangles. A visible component can overlap a foreground glyph/label while its center is outside that rectangle, contaminating both centroid and morphology.

Synthetic reproduction: a white observed component spans pixel box [176,1192,192,1208], centered at (184,1200), with radius-10 shape support. Its center is (92,600) points, outside the first foreground rectangle [48,592,91,640]. Nevertheless 96 of its 256 pixels overlap that rectangle's pixel extent [96,1184,182,1280]. V1 records no foreground risk.

Action: preserve component pixel support and intersect it with the declared foreground regions; record overlap fraction. A conservative template-support intersection may be reported separately. The same actual support should define component saturation rather than using the entire bounding box.

### 4. Weighted centroids cannot identify shared component support

Identity competition only rejects accepted centers within 2 pixels. Color projection changes the centroid weighting, so two identities can claim exactly the same component support while their weighted centroids are farther apart.

Numerical reproduction: background 128; rectangle [340,1046,350,1054] is RGB(190,20,160), adjacent rectangle [350,1046,360,1054] is RGB(160,20,190). Call `local_shape` at (350,1050), radius 10, sigma 0, using source RGB(232,48,48) and RGB(48,48,232) directions. Both shapes are valid with identical box [340,1046,360,1054] and area 160. Their centers are (348.587223587,1050) and (351.412776413,1050): separation 2.825552826 pixels. The 2-pixel test misses their identical support.

Action: retain exact component pixels/RLE, then detect identity competition using actual support intersection or a declared overlap fraction. Bounding boxes alone also admit unrelated components; they are only an inexpensive broad phase. Preserve both identities and their evidence under `fused`/ambiguous rather than assigning two independent displacements.

## Contract and implementation checks

- The initial reviewed CLI did not bind `points_json.image_sha256` to `--source`; an otherwise same-sized wrong source image could be processed. A later read showed this assertion added. Keep it in v2 and also validate schema, coordinate origin/scale, dimensions, seed/input identity and source-point count/bounds before tracking.
- The FFT valid-correlation implementation was checked against direct Pearson correlation at every valid position for independent 11×15 random data and a 3×5 template. Maximum absolute error was 4.4408921e−16. No convolution-index or sign defect was found.
- Source coordinates use the top-left image edge; pixel centers are integer index +.5. `crop_template`, correlation-center reconstruction and component pixel-center moments consistently use this convention. Subpixel source centers should still be compared with the observable source centroid where appropriate, as the code already records.
- The moment axes explicitly mean four times the square root of weighted pixel-center covariance eigenvalues. They are descriptive intensity moments, not an unblurred disk/physical ellipse fit. No numerical defect was found in that definition.
- Color and context NCC thresholds may reject adapted colors; this is acceptable as `unidentified`. Such rejected color evidence must not be reinterpreted as physical absence.
- Source-overlap metadata is a declared conservative source-identity gate. It does not prove that a component is fused in the target; preserve source-overlap and observed-support competition as separate reasons.
- CSV missing-center handling is safe for rows produced by current v1 because absent centers use the default pair; explicit `None` vectors and an empty points list should be preflight rejected or handled rather than producing unpacking/`flat[0]` errors.
- Optional baseline tracking is independent work and roughly doubles tracking time. Its rows should remain separate from actual-output displacements; this review did not infer a native baseline or inspect one.

All fixes should be made as a new version before actual output is read, preserving frozen v1. Any later output-driven algorithm revisions require a new validation split.
