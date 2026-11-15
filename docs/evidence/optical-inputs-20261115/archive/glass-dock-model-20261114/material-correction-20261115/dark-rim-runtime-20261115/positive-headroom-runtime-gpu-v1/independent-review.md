# Positive-headroom GPU packet: independent review

Reviewer: `/root/dock_rim_sources_audit`; date: 2026-11-15.
Scope: static source/provenance review and independent numerical recomputation
from existing CSV/JSON. No device operation, build, image decoding, refit, new
experiment, runtime mutation, or modification of previous reports/frozen files.

## Decision

Keep positive headroom disabled by default. It lowers top-edge mean absolute
error and native-zero target error, but adds two observed false-255 output
codes, increases the worst own-body error, and worsens pooled right-corner
first/second derivative errors against native. This is a useful isolated
calibration diagnostic, not acceptance of softer native highlights.

## Exact packet identities

| Record | SHA256 |
|---|---|
| New build receipt | `a7ed60d44b8fe44c92f6688568a968ae96eb7ad9f829c206fd08068fba684e3c` |
| probe.py | `0d5b6d12f66fd1555b6d301122f56f4dc1bc94b2d95413e5200f51ec0e44070e` |
| protocol.json | `22632c7ec6a525bfb4dc7122f6cf470e2ed944dc41eefdc6a0f7a7f4eeb753f9` |
| plan.json | `c690bc940585282b60a61eb3a767d990db23f77f4e13f9e8bd5555df1f9472a7` |
| freeze.json | `02f284a1032585936a7bafa4c72f24624cdc191b89e94fe167d4dd6301a51ace` |
| report.json | `92105d4b59c9a222c7fde9b80a7c32685869c208bb62e1bebab8f206ae048583` |

The report status is
`positive_headroom_static_diagnostics_controls_passed_not_native_acceptance`.
It retains 54 REST captures, 67 regions, 21,708 metric rows, 7,236 regression
rows, 44,712 strip samples, and 1,296 top-own-body samples. Both historical
controls and all 27 mechanism controls passed as recorded.

## Provenance and analysis gates

- New build/protocol identities match plan/freeze. Historical r2 six runtime
  sources, two test sources, and two XML files resolve through exactly ten
  archived-original aliases. The ten archived SHA values were independently
  checked and remain bound in the new plan.
- Historical APK hashes remain historical declarations at overwritten live
  paths; they are not relabeled as current byte verification. Current live APK
  paths bind the new build hashes. Old `identity`, `verify`, and
  `reference_metadata` routines are not used for historical live identities.
- The unchanged `A.analyze` code first decodes only new `logit_control` and
  CROSS historical-control gray77/gray128 windows. It computes whole-window
  raw and ICC differences for both controls, requires strict zero, and writes
  failure evidence before stopping. Candidate/native decoding follows this
  gate, never precedes it.
- `zero_mechanism` and `zero_passed` remain the original implementations:
  nominal depth >=32, outside actual rectangle, and farbody ten rows require
  raw/ICC maxima and changed counts all zero. Nominal depth >=4 is retained as
  complete changed-pixel diagnostics, not relaxed body acceptance.
- All 27 inputs/native traits and complete evaluation loops remain. Frozen
  offline report, diagnostic summary, and all-degradations CSV are SHA-bound.
  Their 14 improved/13 degraded RGB groups are explicitly offline observations;
  those counts must not be substituted for the GPU result below.

## Independently recomputed aggregate errors

All values below use the recorded ICC sample values. "RGB" without own-body
means the uncentered channel error; it does not assert a fresh raw-PNG decode.
Own-body error subtracts each image's own body median before comparison.

| Metric | Logit control | Positive headroom |
|---|---:|---:|
| Top first3 own-body RGB MAE | 3.370370 | 3.074074 |
| Top all16 own-body RGB MAE | 0.698302 | 0.642747 |
| Top first3 own-body RMSE | 6.316417 | 6.456247 |
| Top own-body maximum absolute error | 33 | 34 |
| Top first3 uncentered RGB MAE | 3.662551 | 3.432099 |
| Top all16 uncentered RGB MAE | 2.292438 | 2.249228 |
| Nominal edge 0..4px RGB MAE | 4.623092 | 4.510274 |
| Nominal edge 0..4px Y-prime MAE | 3.608740 | 3.687606 |
| Six right-corner strips RGB value MAE | 3.434884 | 3.452876 |
| Six right-corner strips first-derivative error MAE | 1.287900 | 1.334599 |
| Six right-corner strips second-derivative error MAE | 2.321261 | 2.368300 |

Top own-body scene counts: 15 improve, 12 degrade. Uncentered top RGB: 12
improve, 15 degrade. Edge RGB: 12 improve, 15 degrade; edge Y-prime: 11 improve,
16 degrade. Mean improvement therefore does not imply improvement across most
backgrounds or error measures.

The edge RGB depth bins retain mixed outcomes: 0..1px MAE 8.930424->8.550992;
1..2px 4.840754->4.687749; 2..3px 2.524181->2.612685; 3..4px
2.051246->2.054687. The overall edge maximum remains 85.

## Endpoint and worst-top checks

| Native target / subset | Samples | Control MAE | Headroom MAE |
|---|---:|---:|---:|
| Zero, first2 | 8 | 7.625000 | 0 |
| Zero, first3 | 10 | 7.700000 | 1.600000 |
| Zero, all16 | 36 | 7.916667 | 6.222222 |
| 255, first3 | 6 | 0.166667 | 0.166667 |
| 255, all16 | 32 | 0.437500 | 0.437500 |

False-zero observed codes remain 0->0. False-255 observed codes increase 0->2:
`chroma_b_pos`, B, `(375,1168)`, native247; and `chroma_r_pos`, R,
`(375,1168)`, native246. Both candidate values are255. These are quantized
observations; the CSV alone cannot establish internal shader clipping.

The worst top point degradation is `ms07_green`, G, `(375,1169)`:
native236, control244, candidate252. Uncentered absolute error increases
8->16; own-body absolute error increases13->21. The maximum candidate
own-body error34 occurs in `muted_blue`, B, y1169 (native223, control242,
candidate243); the control's own-body error there was33.

## Right-corner derivative results

Derivative error is `abs(candidate_difference - native_difference)`, not the
amplitude of the candidate difference itself. Each strip has 81 groups
(27 scenes x 3 channels). Positive MAE delta denotes regression.

| Strip | First MAE delta | First degraded/improved/equal | Second MAE delta | Second degraded/improved/equal |
|---|---:|---:|---:|---:|
| right_upper_y1180 | +0.063058 | 56/17/8 | +0.057099 | 49/17/15 |
| right_upper_y1192 | +0.079665 | 61/14/6 | +0.140551 | 62/13/6 |
| right_upper_y1204 | +0.045937 | 51/12/18 | +0.116402 | 59/18/4 |
| right_lower_y1256 | -0.032730 | 34/33/14 | -0.097002 | 33/46/2 |
| right_lower_y1268 | +0.054973 | 52/13/16 | +0.038936 | 41/28/12 |
| right_lower_y1280 | +0.049763 | 51/19/11 | +0.016590 | 41/37/3 |
| All486 groups / pooled delta | +0.046699 | 305/108/73 | +0.047039 | 285/159/42 |

Pooling the six strips within each scene: first derivative has20 degraded/7
improved scenes; second derivative has15 degraded/10 improved/2 equal.
Y-prime pooled derivative errors also regress: first1.229516->1.263432;
second2.218830->2.234969.

Worst local derivative degradation: `chroma_r_neg`, R, `(695,1192)`.
First differences native18/control20/candidate38 yield error2->20 (+18).
Second differences native23/control24/candidate51 yield error1->28 (+27).
The worst first-derivative group is that same scene/strip/channel,
MAE0.433962->1.075472. The worst second-derivative group is
`chroma_b_neg`/`right_upper_y1192`/B, MAE0.923077->1.961538.

For cyan `chroma_r_neg`, G, y1268, x691..695:

```text
native:   [153,188,226,207,146]
control:  [151,205,230,133,137]
headroom: [151,200,222,131,137]
```

The97-code drop becomes91, mainly from peak suppression. It remains one pixel
too early; x694 is76 codes below native and the erroneous following rebound
increases+4->+6. Native instead drops19 then61. This does not repair the
transition's position or valley.

## Complete scene-level signed MAE changes

All scenes are dark. Positive means worse; negative means better. Corner
columns pool all six measured right-corner strips. All16 top-own-body changes
have the same signs as first3 because this intervention changes only the first
two sampled rows in the top strip.

| Scene | Top3 own | Top3 RGB | Edge RGB | Edge Y-prime | Corner d1 | Corner d2 |
|---|---:|---:|---:|---:|---:|---:|
| new_gray_0 | -5.3333 | -5.3333 | -3.0757 | -3.0871 | +0.1180 | +0.1962 |
| ms01_gray_26 | -3.3333 | -3.3333 | -1.7097 | -1.7148 | +0.1159 | +0.1498 |
| new_gray_36 | -1.6667 | -1.6667 | -0.6888 | -0.6898 | +0.0745 | +0.1097 |
| ms08_blue | +0.6667 | +1.5556 | +1.0292 | +1.4109 | +0.0580 | +0.1034 |
| chroma_r_neg | -1.6667 | -3.8889 | -2.6215 | -1.9460 | +0.0290 | -0.0084 |
| ms07_green | +1.8889 | +0.5556 | +0.2974 | +1.6586 | +0.1139 | +0.2152 |
| new_gray_51 | +1.0000 | +1.0000 | +0.6526 | +0.6521 | +0.0352 | +0.0232 |
| new_gray_58 | -0.1111 | +0.3333 | +0.2200 | +0.2209 | +0.0062 | 0 |
| new_gray_64 | -0.6667 | -0.6667 | -0.3284 | -0.3272 | -0.0248 | -0.0190 |
| new_gray_70 | -1.0000 | -0.3333 | -0.2262 | -0.2248 | -0.0414 | -0.0844 |
| ms02_gray_77 | -1.6667 | -1.6667 | -0.9504 | -0.9488 | -0.0311 | -0.0781 |
| chroma_g_pos | -0.8889 | -0.4444 | -0.2958 | -1.1996 | -0.0290 | -0.0717 |
| muted_blue | +0.5556 | +0.5556 | +0.3802 | +0.3352 | +0.0104 | -0.0105 |
| muted_green | -3.8889 | -3.8889 | -2.5611 | -1.0677 | +0.0166 | +0.1013 |
| new_gray_90 | -0.2222 | +1.1111 | +0.1984 | +0.1944 | -0.0580 | -0.1730 |
| new_gray_102 | +2.3333 | +2.3333 | +0.8477 | +0.8440 | -0.0331 | -0.1540 |
| chroma_b_pos | +1.2222 | +1.2222 | +0.8248 | +0.3071 | +0.0807 | +0.0675 |
| ms03_gray_128 | +1.3333 | +1.3333 | +0.8211 | +0.8206 | -0.0041 | -0.1329 |
| chroma_b_neg | +2.0000 | -1.1111 | -0.8127 | +1.4662 | +0.0849 | 0 |
| new_gray_153 | +0.6667 | +0.6667 | +0.4993 | +0.4991 | +0.0373 | -0.0316 |
| muted_red | -0.1111 | +1.4444 | +0.9562 | +0.9365 | +0.0683 | +0.1013 |
| chroma_g_neg | +0.6667 | +1.1111 | +0.7523 | +1.1005 | +0.0663 | +0.0949 |
| ms04_gray_179 | -1.3333 | -1.3333 | -0.6933 | -0.6930 | +0.0932 | +0.1266 |
| new_gray_204 | -0.6667 | -0.6667 | -0.2179 | -0.2175 | +0.1491 | +0.2426 |
| chroma_r_pos | +0.7778 | +2.5556 | +1.6912 | +1.6909 | +0.1097 | +0.1899 |
| new_gray_217 | +1.6667 | +1.6667 | +1.2669 | +1.2666 | +0.1739 | +0.2616 |
| ms06_red | -0.2222 | +0.6667 | +0.6982 | +0.8419 | +0.0414 | +0.0506 |

## Internal numerical consistency

- All162 top summaries were rebuilt from actual values and body medians:
  maximum discrepancy0. Control/candidate body medians are unchanged.
- All357,696 recorded first/second-difference fields were independently rebuilt
  from samples:0 mismatches.
- All28,944 numeric regression fields were rebuilt from metric pairs:
  0 mismatches.
- Current logit control versus the previous CROSS/logit control:178,848 strip
  fields and9,072 top fields compare exactly, across all27 scenes.

## Limits retained

This is public static calibration at one size. Only six existing right-side
corner scanlines are measured; left corners remain unmeasured. Actual outline,
CPU coverage, and shadow are not isolated. The packet does not establish full
corner geometry, highlight, material, held-out, dynamic, acceleration,
multiple-size, native, or production acceptance. No previous body's/logit's
improvement is counted as this intervention's gain.
