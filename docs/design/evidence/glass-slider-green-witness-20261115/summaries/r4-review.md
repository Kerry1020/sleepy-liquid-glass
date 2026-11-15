# Narrow-shoulder r4: substantial G improvement with remaining local regressions

The captured r4 G finite difference substantially improves ingress50,
ingress75 and full100 RMSE and MAE against native relative to r2. It is a
stronger G calibration candidate than r2 and the rejected frost-half r3.
It does not establish native equivalence or uniformly improve all pixels.
Joint RGB evidence remains necessary before choosing a production parameter.

## Gates and scope

The accepted r4 witness and control indexes each contain six shape/flat pairs.
The frozen v1.1 analyzer was used unchanged. All six stages have flat RGB p99
`[0,0,0]` on both the original capture pixel lattice and the bilinear world grid.
Comparing all r2/r4 shape and flat observations together, the maximum ranges of
carrier bounds, carrier center, presentation matrix, source origin and source
sampling matrix are all zero. Effective opacity remains unobserved. Every r4
stage is therefore still `MAPPING_UNKNOWN_PIXEL_DIAGNOSTICS_ONLY`.

No registration, source-image edit, threshold change, gain fit, inferred native
thickness or new acceptance rule is used. All data are calibration. The world
grid interpolates encoded capture bytes at 0.25 pt spacing; the separate
original-pixel metrics retain direct integer subtraction. Capsule domain masks
are based on observed public carrier geometry rather than inferred optical alpha.

## Positive G support at all four thresholds

Each vector below lists areas in pt² at thresholds **4 / 8 / 16 / 24**.
The frozen target has area 17.6875 pt²; the complete fixed ROI has area 1936 pt².

| Pose/domain | Native | r2 | r4 |
|---|---|---|---|
| Ingress75 target | 7.375 / 3.9375 / 0.625 / 0.0625 | 17 / 15.4375 / 12.625 / 9.8125 | 10.125 / 8.375 / 5.875 / 3.3125 |
| Ingress75 complete ROI | 68.5625 / 54.8125 / 41.1875 / 32.625 | 82.75 / 72.8125 / 60.1875 / 50.875 | 73.5625 / 65.0625 / 53.625 / 44.9375 |
| Full100 same frozen target | 14.75 / 13.1875 / 12.1875 / 9.75 | 14.1875 / 13.8125 / 13 / 12.5 | 14.1875 / 13.6875 / 12.875 / 12.0625 |
| Full100 complete ROI | 74.875 / 64.375 / 54.75 / 46.625 | 74.875 / 67.5625 / 57.3125 / 50.3125 | 72.3125 / 65.375 / 55.4375 / 48.0625 |

Ingress75 target median G falls **27.018 to 6.825**, compared with native 2.75.
All 283 frozen target samples become darker. Its RMSE falls 25.493 to 9.928,
but high-threshold support remains excessive. Full100 target median G falls
36.866 to 33.141, compared with native 25.25.

The full100 threshold-4 complete-ROI area was numerically exact in r2 and is
2.5625 pt² too small in r4. Agreement of total area alone does not guarantee
correct locations; the support-set audit below retains the corresponding misses.

No pose has negative G support at any of the four thresholds.

## Complete-ROI errors against native

These RMSE and MAE values use the same frozen world grid, without registration.

| Pose | RMSE r2 → r4 | MAE r2 → r4 |
|---|---|---|
| Ingress01 | 1.21334 → 1.21288 | 0.13326 → 0.13320 |
| Ingress10 | 1.81447 → 1.81883 | 0.18269 → 0.18309 |
| Ingress50 | 2.28144 → 1.38614 | 0.28798 → 0.17161 |
| Ingress75 | 3.63129 → 2.37648 | 0.60539 → 0.41296 |
| Full100 | 2.30604 → 1.76324 | 0.37829 → 0.28224 |
| Far50 | 1.89995 → 1.89839 | 0.15776 → 0.15771 |

Ingress10 has a small regression. Ingress01, ingress10 and far50 differ at only
5, 21 and 8 original Android ROI pixels respectively, each by at most one byte.
Ingress01 and far50 threshold support areas are unchanged. This is not evidence
that their full original-pixel fields are identical.

## Frozen r2 subgroups

The masks were saved using r2 inputs before r3 or r4 optical reads. The names
describe r2 source support, not a new r4 source classification or a held-out set.

| Frozen subgroup | Native median G | r2 median G | r4 median G | RMSE r2 → r4 |
|---|---|---|---|---|
| Reverse68: r2 unfrosted source G>24 | 11.125 | 46.228 | 27.961 | 35.948 → 16.583 |
| Neutral138: r2 unfrosted source G≤4 | 0.8125 | 13.979 | 0.288 | 16.160 → 2.924 |
| Frost-band222: r2 inset 1.5..7 | 4.25 | 31.204 | 11.694 | 27.263 → 11.173 |

All 68 reverse samples and all 138 neutral samples darken relative to r2.
Reverse68 positive areas become `4.1875 / 3.9375 / 3.625 / 2.75`, compared with
native `3.875 / 3.0625 / 0.625 / 0.0625`. The large residual at thresholds 16
and 24 remains visible despite the improvement.

Neutral138 positive areas become `1.5 / 0.625 / 0.1875 / 0`, compared with native
`0.3125 / 0 / 0 / 0`. Its median is now below native; the remaining upper-tail
false support is retained rather than hidden by the lower median.

## Actual added and removed support, not just net counts

All counts are 0.25 pt world-grid samples; divide by 16 for pt². A false positive
means Android G exceeds the threshold where native does not. A miss means
native exceeds the threshold where Android does not. These are pixel diagnostics
under the opacity-unknown limitation, not a newly defined acceptance test.

At ingress75 target, false-positive counts change from
`154 / 184 / 192 / 156` to `44 / 71 / 84 / 52`. Actual newly added false
positives are zero at every threshold. Native positive-support misses remain zero.

At ingress75 complete ROI, r4 **actually adds** `29 / 30 / 30 / 35` false-positive
samples while removing `180 / 162 / 148 / 146`. Its threshold-4 support adds
three new native-support misses while repairing seven old misses. Thus target
improvement cannot be generalized to every location in the complete ROI.

At full100 complete ROI, false positives change from `88 / 111 / 90 / 109` to
`49 / 79 / 55 / 75`. However, r4 actually adds `1 / 1 / 5 / 8` false positives
while removing `40 / 33 / 40 / 42`. Native-support miss counts change from
`88 / 60 / 49 / 50` to `90 / 63 / 44 / 52`: thresholds 4, 8 and 24 have net
regressions. The actual newly added misses are `5 / 10 / 1 / 7`, while repaired
misses are `3 / 7 / 6 / 5`.

## Cross-channel limitation

Android R/B witness-control finite differences remain exactly zero at every
original capture pixel within the fixed ROI in all six poses. R4 therefore does
not reproduce the native cross-channel response observed with the same G-only
input perturbation. This is coupling evidence, not a two-level proof of
nonlinearity or a uniquely identified internal sampler.

## Reviewable files and hashes

- Official `analysis-android-narrow-shoulder-r4-v1_1/analysis.json`:
  `360cf3d33bbe2a6b57b1950adb3b4f61a46de9b6f2e1478e26b86a2e5f577a3e`.
- `comparison.json`: all six poses, both original-pixel and world-grid metrics,
  all nine existing domains, RGB, positive/negative/neutral support, all thresholds:
  `f68d3923a60c722d83b474295452e745031c87955046ec2053f9348cd7e12ccf`.
- `support-set-differences.json`: actual added/removed support and error sets:
  `1e38fc16b1a36d8e5176767147514901d2f2b8a08a53439d9b7f89c76250566d`.
- Unchanged frozen analyzer:
  `ef475784d5aed32b0dc522ae80c5ff760ad6779a5ef676c5c0de2737307ac2d1`.
- R2-only subgroup freeze JSON:
  `fe269ec10915850ace9319cdab100600b9b879cbcb4b333e554c640c23853177`.

The official output directory also retains original-byte and world-grid NPZs
for each stage. No production source, device, build or Git changes were made
for this analysis task.
