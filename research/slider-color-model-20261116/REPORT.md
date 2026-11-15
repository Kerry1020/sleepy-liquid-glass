# Existing Slider U: tested unclipped affine color models fail at the rim

The existing finite encoded-byte response rejects the tested unclipped color-response families at parts of the rim. It does **not** identify the native mechanism, justify changing global saturation, or supply an accepted production correction. A fixed 8pt **unclipped affine** radial correction fails at the rim even when its six offdiagonal coefficients are independently fitted.

**Interpretation correction:** these calculations reject the explicitly tested **unclipped** encoded-affine families. They do not reject a shared saturation followed by internal clipping and later gain/offset. The sample with unequal R/B responses has a concrete clipped counterexample; see [limits and counterexample](../slider-linear-response-20261116/LIMITS.md). No native processing order or necessity of a per-output-row transform was established. A [prespecified signed-G experiment](../slider-signedG-response-20261116/PROTOCOL.md) tests the restricted observable families further. The original numerical arrays and counts below are unchanged.

This is post-processing of the already consumed original RGB-star calibration, not new evidence or an independent holdout. No captures, traces, xcresults, original PNG decoding, product edits or Git writes were performed. The plan was written before this U fit. The authoritative results are in `results-final/analysis.json` and `results-final/model-arrays.npz`.

## What was measured

`U_ij = global-j-shape_i − pre-shape_i` is output channel i's response to a **finite +20 encoded-sRGB byte** whole-scene perturbation of input channel j. Values below are raw output bytes. Divide U by 20 only for a finite encoded-response matrix; that is not a radiometric Jacobian. All nine entries and all residual components are retained.

The original 88×88 ROI has 7,744 pixels. The prespecified above-rail, inside-capsule 0..3pt edge domain has 563 pixels; 186 lie at 0..1pt and 377 at 1..3pt. The original primary domain, y<422 and capsule inset>=1pt, has 1,630 pixels. Capsule inset comes from public carrier geometry; it is not identified native alpha or a physical bevel.

The source analysis passed its declared gates with exactly zero recorded geometry range and zero ordinary-flat/post-control drift. This removes those observed differences from this comparison; it does not eliminate finite-step color nonlinearity or make a tolerance a physical error bound.

## Structural expressiveness

The shader's existing luminance weights are w=(.2126,.7152,.0722). The tested unclipped encoded-affine brightness and saturation model has matrix

```text
A = b [s I + (1−s) 1 wᵀ].
```

For this diagnostic the more permissive raw response is `Uhat=a I+c 1 wᵀ`, with a and c independently free at **each pixel**, without physical sign constraints. Failure of this upper bound rejects globally selected brightness/saturation only within this unclipped encoded-affine model; it does not exclude clipping or later nonlinear stages. Compatibility would not identify valid shader parameters.

Least-squares residuals and **exact unconstrained-family T4 feasibility** are distinct measurements. T4 failure is established by interval elimination, not inferred from the least-squares maximum. All T1/T4/T8 results are retained.

| Per-pixel family | Coefficients | Edge 0..3pt LS RMSE | Edge LS max | Edge exact T4 failures | Entire ROI exact T4 failures |
|---|---:|---:|---:|---:|---:|
| Scalar gain `gI` | 1 | 2.263 | 14.000 | 127 / 563 | 137 / 7,744 |
| Basic brightness+saturation `aI+c1wᵀ` | 2 | 1.276 | 11.571 | 60 / 563 | 67 / 7,744 |
| Independent diagonal + shared luminance `diag(d)+c1wᵀ` | 4 | 0.580 | 4.954 | 5 / 563 | 5 / 7,744 |
| Output-row coupling `diag(a)+diag(c)1wᵀ` | 6 | 0.204 | 1.780 | 0 / 563 | 0 / 7,744 |

The six-coefficient family still has 15 T1 failures, all at the edge. It is an expressive structural upper bound, not a measured native stage. In the original primary domain its LS RMSE is 0.144, maximum 1.018, and exact T1 failures are zero. The two-coefficient family has five primary T4 failures, all among pixels with inset>=8pt; an exclusively edge-local change of this tested unclipped saturation model therefore cannot explain all U components.

The fixed-weight two-coefficient model retains five edge T8 failures. Merely loosening to T8 does not make that family universally compatible. This is distinct from the preceding common-alpha U/M diagnostic, whose T8 incompatibilities were zero: they test different restrictions.

## Offdiagonal and diagonal evidence

Within the tested unclipped saturation model, the two offdiagonal entries **within a given input column must be equal**, regardless of the choice of luminance weights. In the edge domain, their maximum signed-pair difference magnitudes are R=2, G=9 and B=2 bytes. Five pixels have a G-column difference of 9 bytes, which cannot be made simultaneously within T4 because two T4 errors can cover at most 8 bytes.

One actual U matrix at world (192.75,411.25), capsule inset .35pt, is:

```text
               input R    G    B
output R          26       0    0
output G          −3      14   −1
output B          −3      −9   18
```

The `out-R,in-G=0` and `out-B,in-G=−9` pair alone contradicts the tested unclipped repeated-column coupling at T4, even with independent diagonal gains and even if w were changed. No shared saturation coefficient within that family repairs it; this does not reject shared saturation with clipping or later gain/offset.

The diagonals are also not one gain: in the edge domain the mean diagonal response is (18.091,15.725,17.732), with ranges R=0..31, G=9..20, B=9..22. Negative offdiagonals are consistent with encoded sharpening/chroma contrast, but do not establish saturation as its unique cause. Fitting the rejected two-coefficient model produces implied b=.254..1.000 and s=1.000..2.442 at the edge. Those are descriptive fits, **not** recommended brightness/saturation settings; choosing their mean would conceal the rejected structure.

The six-coefficient row family keeps different output responses while preserving each row's fixed offdiagonal luminance ratio. It is the smallest of the **tested unclipped** families not rejected at T4. No assertion is made that six is the globally minimum parameter count, or that this family identifies whether color mixing precedes or follows sampling.

## A fixed local unclipped matrix was tested and rejected

The extra correction has fixed support

```text
q(d) = max(1−d/8,0)² for d>=0; q=0 outside the public capsule.
```

Even original-pixel checkerboard locations in above-rail 0<=d<8pt fit shared coefficients. Odd locations are an internal spatial cross-check, not independent holdout. Two candidates were tested:

1. `Uhat=g(x)I+k q(d)(I−1wᵀ)`: one shared saturation coefficient with a free scalar gain at every pixel.
2. `Uhat=diag(d(x))+q(d)C_off`: six shared offdiagonal coefficients and independently free per-pixel diagonal gains.

| Shared fixed-q candidate | Edge all-component RMSE | Edge max | Edge pixels with fitted max>4 | Odd cross-check max>4 |
|---|---:|---:|---:|---:|
| Shared saturation k | 1.714 | 11.615 | 84 / 563 | 41 / 284 |
| Six shared offdiagonals | 1.176 | 10.027 | 78 / 563 | 37 / 284 |

These are not just poor least-squares choices. Within these fixed-q unclipped candidates, exact coefficient-interval intersections show **no shared coefficients exist at T4** over 0..3pt for either candidate, on even locations, odd locations or their union. The shared-saturation candidate remains impossible at T8. Six shared offdiagonals become compatible at T8. Both candidates are T4-compatible separately over 1..3pt and 3..8pt, so the unsatisfied 0..1pt rim cannot be hidden by averaging the whole face.

The fitted six-offdiagonal candidate does stay within 3.222 bytes in the original primary domain, but its rim failure rejects adopting it as a complete Slider material. A good average or primary-domain fit cannot excuse the contour where the user's complaint is most visible.

## Optional candidate scope and rejection boundary

An **uncommitted, Slider-only unclipped candidate family** with separate output gains and luminance-like coupling may be explored independently from the source-coordinate/refraction field. It is optional, not a required native stage or product change. The results reject the tested unclipped families and fixed radial candidates; they do not exclude globally shared saturation followed by clipping or establish that output-row parameters are necessary. The fitted U matrix is not an Android-to-native correction: this study contains no matching Android U matrix, and native U already includes the native material and background-dependent response.

An optional diagnostic candidate may expose a local color-response term separately from sampling while retaining the observed nine-component response and preserving other controls. The current six-coefficient per-pixel fit is an upper bound within the tested unclipped families, not a required runtime parameterization or a production lookup table. A simpler compact law for those coefficients has **not** been established here; adding an arbitrary spatial/content function merely to interpolate these pixels would overfit the only baseline. No production change follows from these fits alone.

If such an optional compact candidate is explored, reject its claimed sufficiency if:

- its frozen same-grid U cannot meet T4 in the prespecified edge and primary domains, including the 0..1pt rim;
- it repairs diagonal gains while breaking repeated offdiagonal response, or hides one component through RGB/ROI pooling;
- it requires a color transform of the whole app or non-Slider controls to repair this local material;
- it claims to retain a shared-alpha encoded-affine U/M response despite the existing common-alpha contradictions;
- it treats fitted finite encoded gains as recovered thickness, chromatic displacement, linear-light saturation or native processing order;
- it is accepted from this single already-consumed baseline without separately prespecified amplitudes, colors and holdouts.

The preceding unclipped U/M result remains a restriction on those specific model families: common alpha failed T4 at 49 pixels, input-column families were compatible, and output rows failed at two rim pixels. A constant local color matrix with a single spatial kernel cannot be declared sufficient simply because it fits U. Those separate mask constraints must remain visible. No M values were used to fit the present models.

Finite +20 encoded changes can conflate transfer/gamma, local clipping or floors, content-dependent gain/tint, different direct and optical contributions, and color-dependent sampling. A row-shaped U response is consistent with several such mechanisms. The current data do not distinguish them, and this report initiates no new experiments.

## Reproduction

```sh
python3 research/slider-color-model-20261116/analyze-model.py --self-test
python3 research/slider-color-model-20261116/analyze-model.py --output /new/empty/output
```

The script uses exact scalar interval elimination for the declared linear families, so SciPy is unnecessary. Synthetic checks cover all four exact structural families, bounded perturbations, offdiagonal/diagonal contradictions and shared-local coefficient feasibility. All source hashes are recorded in the result. A platform BLAS status-warning issue in the first numerical run was avoided with explicit NumPy contractions; the repeated arrays differed by at most 1.43e-14, with model conclusions unchanged. Only the final explicit-contraction results are retained.
