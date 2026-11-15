# One-pilot rejection audit: n05 light native

This is a descriptive audit of `tracking-v2/n05_dots_s0-light-native/per-source.json` and its registered source/native REST PNGs only. It does not change a threshold, tracker, product parameter or capture. The full 24-job matrix remains necessary. These test outputs have now informed the following **future probe-design suggestions**, so those suggestions are not design-blind.

![Known input and native Dock crop](source-native-dock.png)

The preview is an unretouched crop of y=1010…1334 pixels, placed side by side. It includes the native foreground and selected lens. It is a visual aid, not correspondence ground truth.

## What the pilot establishes

The frozen source-in-Dock rectangle is [42,1168,708,1292] pixels. It contains 140 registered source centers: 109 radius-1.5, 18 radius-4, and 13 radius-10 dots. Their final statuses are **138 unidentified, 2 multiple_lobes, 0 tracked, 0 disappeared**. The entire image's 53 `tracked` points have observed centers outside the Dock. They cannot establish glass-body correspondence or count as a glass pass.

All 140 points produced three retained candidates. The table counts failed gates among those 420 candidates; the failures overlap and must not be summed as causal percentages.

| Frozen gate | Failed candidates |
| --- | ---: |
| Context NCC ≥ .40 | 371 |
| RGB NCC ≥ .40 | 240 |
| Source context SD ≥ 1 | 127 |
| Valid isolated shape | 95 |
| No foreground-component intersection | 36 |
| Search peak away from effective boundary | 30 |
| Scalar NCC ≥ .60 | 15 |
| Component saturated fraction ≤ .05 | 8 |

The dominant problem is **not uniformly low scalar NCC**. All 109 fine source points have at least one candidate above .60. Yet 108/140 highest-scoring candidates are outside the Dock; only 26 are in its unselected body and 6 in the selected lens. The unchanged exterior contains many clean circles of the same few sizes/colors, and the translation template can favor those exterior lookalikes over a blurred/deformed interior image.

The input generator's radius-64 neighborhood signatures are unique, but the tracker does not match that whole neighborhood. A fine-dot sigma-0 template has radius 9 pixels, increasing to 13/21 at sigma 2/6. Unique radius-64 source constellations therefore do not establish identity inside these smaller templates. In the fine group, 79/109 source points have no retained candidate passing context NCC; 39/109 have none passing source-context SD. Small circular dots can remain easy to correlate geometrically while lacking usable identity context.

Five source points retain at least one candidate passing all eight per-candidate gates. None supplies a unique accepted displacement:

- IDs ending `000352`, `001353`, `001393` fail the frozen peak margin .08 with margins .00454, .00453 and .00642.
- `000713` has two eligible selected-lens patch matches at (198.5,1218.5) and (201.5,1221.5), separated by about 4.24 pixels. `multiple_lobes` is a conservative matcher status; these candidates are not proof of two distinct physical images.
- `001288` has three eligible candidates outside the Dock. It also receives `multiple_lobes`; that is ambiguous patch identity, not established native multivalued refraction.

## Which explanations are supported

**Foreground is a real but partial obstruction.** Fifty-eight source centers nominally lie under one of the four fixed icon/label masks. A source position alone does not reveal the observed position after refraction. The actual candidate-support gate rejects 36/420 candidates, while the selected lens and foreground visibly cover part of the available signal. It would be incorrect to attribute all 140 rejections to foreground.

**Shape and context change matter.** Of 420 retained candidates, shape rejection comprises 71 weak-local-contrast results, 8 multiple-component patches, 8 truncated components and 8 cases with no connected component; 325 have valid local shape. A valid shape still need not identify its source. Source dots are visibly smoothed or stretched in the native body, and neighboring responses/foreground can enter one patch. The dot field is not optically absent as a whole.

**The blur model is only a limited template family.** Frozen sigmas are 0,2,6 pixels with translation-only matching. Highest-scoring templates use sigma 0 for 96 points, sigma 2 for 34, sigma 6 for 10; because so many winners are exterior lookalikes, these counts are not native blur estimates. The image suggests smoothing and nonuniform shape changes, but this pilot does not uniquely separate blur, nonaffine refraction, tint adaptation, lens layering or occlusion. No effective sigma or native physical thickness is inferred.

**Hue/contrast adaptation is not isolated.** The 240 RGB-NCC failures establish that candidate RGB patterns often fail the fixed source-color check. They do not establish 240 native hue changes: many candidates have the wrong identity or are exterior matches. The source-to-output projection and neighborhood changes are confounded.

**Source crowding also exists.** Thirty of the 140 source points have geometrically overlapping source disks. This is a declared conservative source-identity obstacle; it is separate from target-component fusion. Earlier rejection gates prevent most points from reaching that source-overlap branch.

No frozen threshold should be relaxed on this pilot. Keep all failure records and finish the registered matrix. The present evidence supports a limit on identifiability for this probe/tracker pair, not a physical-disappearance result or a pass/fail judgment for the candidate material.

## Proposed next static probe, not generated or registered

The next design should separate **detectability** from **identity**. Simply making an already isolated monochrome dot larger would improve some signal but could make source identity less unique. A coded shape or a phase identity is needed alongside adequate size and separation.

One bounded, reproducible sparse-phase proposal is:

1. Use a full-canvas 8×16 stratified lattice at 750×1334, with each cell-center rounded to a pixel center and an independent integer jitter in [−6,+6] pixels. Position rules apply to the whole canvas; do not select a location based on Dock overlap or captured appearance.
2. Assign phase `(column mod 4)+4*(row mod 4)`. Each of 16 static phases contains eight probes, with centers at least 321 pixels apart under the declared jitter. Nominal ±160-pixel search neighborhoods then do not overlap between source centers. This supports a known exposure identity; it still does not justify forced nearest-neighbor target matching or assume bounded native refraction is true.
3. Use copied ideal masks with radii 8,12,20 pixels rather than 1.5/4/10. Each phase contains four radius-8, two radius-12 and two radius-20 probes, with balanced light/dark pairs per radius on code-128 gray. Preserve ideal masks, source coordinates, polarity, phase, seed, hashes and all source identities.
4. Optionally capture a sign-reversed A/B pair per phase using identical mask pixels. Matching light/dark area per radius makes A/B source histograms identical. A neutral reference and repeated A/B REST observations can expose fixed foreground contamination or changing state. **Histogram identity does not guarantee native material state identity**, so any difference-based interpretation must retain the possibility of adaptation and nonlinearity. Do not call a difference image a physical PSF without an independently tested linearity assumption.
5. Proposed fresh seeds are calibration `3402000001…3402000004` and test `2122000001…2122000004`, disjoint from this packet. They are suggestions only: lock generation, point/phase counts, state checks, correspondence rules and analysis before generating the new test set. Use calibration to establish feasibility; if the design changes, freeze a new version and fresh test seeds.

This complete proposal is 16 phases, or 32 if sign-reversed pairs are used, per seed before neutral/reference repeats and theme/role expansion. Its capture cost must be reviewed explicitly; it is not permission to start that matrix. A compact alternative is one uniquely coded asymmetric coarse constellation per cell, but its identity must first survive the declared blur/warp/foreground synthetic cases in calibration, and the entire constellation must be treated as one group rather than pretending every subdot is independently identified.

The purpose of such a next probe is to produce enough known support to say which source response was observed or remained unresolved. It still cannot uniquely identify native refractive index, physical thickness, blur or rendering internals.

## Artifacts and reproducibility

`audit_rejections.py` reads the one completed report and frozen protocol, checks its observed PNG hash, and writes `rejection-summary.json` plus a 140-row `per-source-rejection-summary.csv`. It does not rerun the tracker. The JSON contains nonexclusive gate counts, a clearly ordered gate cascade, radius groups and the five eligible-but-unaccepted examples. All interpretation above is limited to this one light/native seed.
