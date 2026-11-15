# Fixed plateau-frost diagnostic

The existing `edgeFrost(width≤8, blur)` decay cannot reasonably supply the observed near-constant broad transition at both lower442 and444 while preserving the sharper inner rows. If the deficit is modeled as local filtering, the next bounded diagnostic needs a plateau and a short inner shoulder. This does not identify the native PSF or prove the actual GPU result.

This report uses only saved native and valid narrowD5/W6.5 r2 scalar Slider `.25 HELD` evidence. No native image was filtered, registered, sharpened or color-fitted. No device, production edit, build, Git operation or parameter search was performed. The preceding manifest, geometry and readiness checks are reused from [valid r2 analysis](narrow-r2-analysis.json); the first fallback arm remains excluded. Current input receipts and all28 two-theme row results are in [the small JSON](plateau-frost-diagnostic.json).

## Why the existing envelope is insufficient

The recorded held carrier is `[84.592445, 411.3445, 142.07144, 448.65543]` dp at density `2.9750001`. At the straight central MR band, lower442.25 has inset6.405430dp and lower444.25 has inset4.405430dp. Native blue widths are2.296581 and2.366460pt; current r2 widths are0.895948 and0.837976pt. Their descriptive extra Gaussian-equivalent sigmas areabout0.825 and0.863dp.

`f(d,W)=1−smoothstep(W/3,W,d)`. In the shoulder, `f=(27/4)(d/W)(1−d/W)²`. For `W≤6.40543` the deeper row gets no additional frost. For `6.40543<W≤8`, the ratio `fDeep/fNear=(dDeep/dNear)((W−dDeep)/(W−dNear))²` increases with W. Therefore the most favorable ratio within the current bound is atW8:

`fDeep/fNear=0.214718/0.750440=0.286123` versus the needed width-deficit scale ratioabout0.955. The existing rim frost is zero at the deeper row and positive at the shallower one, which further reduces the total ratio.

One fixed counterexample makes lower442 total frost1.1dp with W8, requiring additional edge blur5.122989dp. It then produces total frost3.9039dp at lower444 and5.4269dp at upper414. The actual Vogel projected kernel SDs become3.2231 and4.5142dp, versus0.8433dp at the calibrated deeper row. This is an analytic response-envelope counterexample, not a full rendered prediction or an amplitude search.

The sharper counterexample is lower442 at inset6.405 versus upper418 at inset6.905: native widths2.297 versus0.852pt. The broadening must largely disappear within that0.5dp gap if one common inset-based local filter is to explain it. The old W8 long decay retains weights0.2147 versus0.1091 and cannot create that plateau-to-sharp transition by increasing only blur.

## One fixed bounded diagnostic

```text
d = actual Android surface inset
g = smoothstep(1.5, 2.0, d) * (1 - smoothstep(6.5, 7.0, d))
totalFrost = mix(existingFrost, 1.1, g)
```

This changes the frost profile only; refraction, bevel, geometry, dispersion and source graph remain fixed in the diagnostic. It is a total-frost replacement inside the gated band, not an additional1.1dp added everywhere. The lower447 row already matches at inset1.405, motivating the outer gate; broad lower442 and sharp upper418 locate the short inner shoulder. These values were selected once from the observed rows and were not optimized or validated on an independent holdout.

At the saved density, the existing32 tap Vogel sampling formula for frost1.1dp has horizontal SD0.843344dp and mean0.006445dp. Its scale is close to the0.825–0.870dp descriptive broad-row deficit. A real implementation must scale plateau strength with the same lift as existing frost while keeping its support fixed; this report does not implement or adopt it.

For a read-only plausibility check, the actual r2 blue rows are convolved once with a centered Gaussian whose variance is `max(VogelVariance(candidate)−VogelVariance(existing),0)`. The same fixed103..113 search and103..105/111..113 plateaus are used. This is a variance surrogate over composed output, not an emulation of the actual2D source sampler.

| World y, light | Native width | Narrow r2 width | Fixed surrogate width |
|---:|---:|---:|---:|
|412.25|2.133974|2.654018|2.654018|
|413.25|2.309881|1.536667|2.284355|
|414.25|2.365797|0.895351|2.341696|
|415.25|2.428571|0.959865|2.332623|
|416.25|2.337500|0.917652|2.363788|
|418.25|0.852381|0.895948|0.895948|
|420.25|0.422069|0.895948|0.895948|
|438.25|0.413072|0.895948|0.895948|
|440.25|0.513517|0.895948|0.895948|
|442.25|2.296581|0.895948|2.312853|
|444.25|2.366460|0.837976|2.331580|
|446.25|2.225806|1.231123|2.345777|
|447.25|1.866528|1.877976|1.877976|
|448.25|0.400000|0.909091|0.909091|

Both themes are retained individually in JSON. Their central broad rows agree; small outer-row dark differences remain and were not averaged away.

## Counterexamples retained

- Lower446 becomesabout2.346pt versus native2.226: the candidate slightly over-broadens it.
- Upper415 remainsabout2.333pt versus native2.429: a residual deficit remains.
- Upper418 remains0.896pt versus native0.852: even this modest original excess is not repaired.
- Interior420/438/440 remain0.896pt versus native0.422/0.413/0.514. More nonnegative blur cannot repair their existing measured excess.
- Upper412 remains2.654pt versus native2.134, and outer448 remains0.909pt versus native0.400. Outer geometry/contour/title differences prevent calling these pure-blur observations, but they are not hidden.
- The candidate leaves midpoint and source-field/cap-bending errors unresolved. Width improvements do not identify or validate refraction.

## PSF and inference limits

- Offline fixed single-Slider .25 HELD diagnostic; no new capture, renderer execution or parameter search. No Dock, panel, Range or dynamics acceptance.
- The same observed14 rows were used to choose the fixed diagnostic. This is exploratory, not an independent holdout or native-PSF identification.
- The original native/source/r2 profiles are unchanged. Native own-source width0.400pt and Android own-source widthabout0.636394pt retain their raster-phase difference. No source deconvolution, registration, sharpening or color fit.
- Gaussian-equivalent sigma from 10-90 widths assumes local shift-invariant Gaussian response only as a descriptive scale. Broad/mixed edge response does not establish that assumption.
- Vogel horizontal variance uses the saved shader constants, density, noheld blur and legacy sigma-mode contract. The surrogate convolves existing composed output rows with a centered Gaussian of the incremental kernel variance; this is not the actual 2D shader/source/alpha/dispersion/tone/highlight pipeline.
- The actual finite Vogel kernel has a small nonzero mean, unlike the centered Gaussian surrogate; individual taps, rasterization, varying fields and boundaries can change the output.
- Upper rows intersect the conservative native title/exterior exclusion; outer rows can contain contour/material differences. Retained counterexamples are not asserted to be pure blur failures.
- Normal/refraction source-field, midpoint and cap-bending errors remain independent. Later source-field changes require new renderer evidence rather than reuse of these predicted widths.
- All cited prior manifest/geometry/readiness verification is reused from narrow-r2-analysis.json; this document adds input JSON/source receipts, not a new APK reproducibility audit.

The observed width variation motivates this diagnostic family. Neither the Gaussian equivalent nor the narrow Gaussian surrogate is a recovered native kernel, physical glass thickness, full-renderer result or acceptance score.
