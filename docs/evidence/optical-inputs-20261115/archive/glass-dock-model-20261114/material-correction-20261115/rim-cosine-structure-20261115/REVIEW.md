# Finite half-cosine rim structure comparison

This bounded numerical comparison uses already-public calibration curves only. It changes no runtime or device and does not accept a material, amplitude model, default, motion or heldout performance. The old power1.5 proposal remains rejected.

Method was frozen before parsing the N curve JSON. V1 stopped before writing a report when an entire held RGB group had no identifiable channels. The preserved r2 amendment only retains null metrics for those groups; it does not change the curve families, width grid, eligibility, amplitude projection or defined-data weighting. Both registrations, the original script and failure record remain in this folder.

The observed native local body is subtracted separately for each profile/channel. Each eligible channel receives a signed nuisance amplitude fitted to its full16 samples. Complete source-RGB groups, including both themes and duplicate M/N anchor captures, are left out together when choosing width. The held group's nuisance amplitude is then reprojected. This tests conditional profile shape, not prediction of native colors or amplitude.

There are32 packet/theme records but14 unique source-RGB groups. Thirteen groups are identifiable under the registered rules. Gray230 is preserved as unidentifiable because its outer sample saturates255 in every channel. The32 records contain166 eligible REST profile/channels. Repeats are byte-value identical on these fixed lines and add no independent samples.

Profiles are top x375/y1168..1183 and right y1230/x707..692, with center depths0.25,0.75,...,7.75dp. Body is the median of samples6..15. A channel is excluded for any0/255 sample, body range>2 codes, or maximum signal<4 codes. Excluded channels and reasons remain in report.json.

The two families are `max(1−d/w,0)` and `cos(pi*d/(2*w)) if d<w else0`. Both scan w=0.80..2.00dp in0.01dp steps. The cosine is explicitly truncated; it cannot become positive again at distant depths.

| Conditional grouped LOSO metric | Linear | Half-cosine |
|---|---:|---:|
| Full16 MAE | 0.300280003 | 0.106574227 |
| Full16 MSE | 0.456611995 | 0.089231165 |
| Full16 RMSE | 0.675730712 | 0.298715860 |
| Third-pixel MAE, same group weights | 0.853089555 | 0.144230769 |

Every cosine fold selects1.19dp. Linear folds select1.27 or1.28dp. Full-calibration widths are likewise1.19 and1.27dp. All13 identifiable held RGB groups improve in full16 MSE; the unidentifiable14th group remains null. This is evidence for testing the no-plateau/short-tail cosine shape in the real GPU path, not evidence that its runtime amplitude, compositing, angular response or total material is correct.

| Held source RGB | Linear full16 MSE | Half-cosine full16 MSE | Cosine−linear |
|---|---:|---:|---:|
| 0,0,0 | 0.266568792 | 0.005418102 | -0.261150690 |
| 102,102,102 | 0.565727006 | 0.024457863 | -0.541269142 |
| 128,128,128 | 0.404109785 | 0.079958270 | -0.324151514 |
| 153,153,153 | 0.667391194 | 0.112942872 | -0.554448322 |
| 179,179,179 | 0.546695457 | 0.020082523 | -0.526612934 |
| 204,204,204 | 0.479846705 | 0.009991954 | -0.469854752 |
| 230,230,230 | unidentifiable | unidentifiable | unknown |
| 232,48,48 | 0.397160044 | 0.083591620 | -0.313568425 |
| 26,26,26 | 0.263670683 | 0.000019507 | -0.263651177 |
| 36,36,36 | 0.517370938 | 0.268193839 | -0.249177098 |
| 48,232,48 | 0.253527303 | 0.158860920 | -0.094666384 |
| 48,48,232 | 0.355671332 | 0.042480338 | -0.313190994 |
| 51,51,51 | 0.501233522 | 0.232954511 | -0.268279011 |
| 77,77,77 | 0.716983171 | 0.121052826 | -0.595930345 |

At1.19dp support ends before the third pixel center at1.25dp, so its predicted rim signal is exactly0. The native third-sample residuals are at most1 code under the registered local-body estimate. Across the166 channel/profile observations, the descriptive unweighted third-pixel MAE is0.857554745 for linear and0.120481928 for cosine; these channels are not independent experimental units. Full raw residual vectors, signed amplitudes and out-of-range predictions are retained for every eligible channel in every fold.

The remaining error is not zero. Gray36, gray51 and green are the largest held-group cosine errors. Median-body subtraction, code quantization, two or three nonzero samples, unknown clipping coverage and unknown raster filtering limit what can be recovered. No unique physical lens surface or private UIKit implementation follows from this comparison.

Independent scalar recomputation checked664 fitted channel profiles (both families, REST/repeat), with maximum amplitude and residual differences 1.42e-14/1.42e-14. It re-evaluates the fixed report with Python scalar sums rather than the analyzer's NumPy projection; it does not supply additional calibration data.

Method r2 SHA256: `1ffb131c984f1bf617826bafd9737c34866551bd9ed69a0f745a55cdf0119af1`. Report SHA256: `2b77f97b59b0f7f11d66c5350837ee29432f94a1ce0ac4857439559091b22f81`.

Files: analyze.py, method.json, method-r2.json, analyze.registration-v1.py, v1-failure.json, report.json, scalar-check-and-summary.json and this review.
