# Frost sigma 0.55 intervention: reject as a replacement

The single change from Slider frost sigma 1.1 to 0.55 improves several spread
areas but does not improve the captured G response consistently. Restore 1.1
before testing an independent common-transport hypothesis. These are calibration
diagnostics, not held-out validation or a native-parity result.

The frozen v1.1 analyzer was used unchanged. All six accepted shape/flat pairs
have zero original-byte and world-grid flat RGB p99. Across r2 and r3, observed
carrier bounds, presentation matrices, source origin and source sampling matrix
are identical. Android effective opacity is still unobserved, so all six outputs
remain `MAPPING_UNKNOWN_PIXEL_DIAGNOSTICS_ONLY`.

## Ingress75 G positive support

World-grid support areas are in pt². The thresholds remain 4 / 8 / 16 / 24.

| Domain | Native | r2 sigma 1.1 | r3 sigma 0.55 |
|---|---|---|---|
| Frozen 17.6875 pt² target | 7.375 / 3.9375 / 0.625 / 0.0625 | 17 / 15.4375 / 12.625 / 9.8125 | 15.9375 / 13.8125 / 9.8125 / 6.8125 |
| Complete 1936 pt² ROI | 68.5625 / 54.8125 / 41.1875 / 32.625 | 82.75 / 72.8125 / 60.1875 / 50.875 | 71.5625 / 62.4375 / 50.6875 / 42.4375 |

Target median G falls from 27.018 to 18.661, still much higher than native 2.75.
The complete ROI G RMSE against native rises from 3.6313 to 3.6780 even though
its MAE falls from 0.6054 to 0.5764. Area shrinkage alone therefore conceals
stronger local errors.

## Frozen r2 subgroups

The subgroup masks were reconstructed and saved from r2 inputs before reading
r3 optical results. They are explicitly calibration selected.

- In the 138 target samples whose current unfrosted source G is at most 4,
  median G falls 13.979 to 8.781 (native 0.8125). None brightens. G>24 support
  falls 1.3125 to 0.125 pt², while native has zero support there.
- In the reverse68 samples whose current unfrosted source G exceeds 24,
  20 brighten, 44 darken and 4 remain identical. The largest increase is 17.966
  encoded-byte units. Median G falls 46.228 to 40.830, but p90 rises 54.266 to
  63.267 and the maximum rises 61.703 to 73.363. All 68 still exceed G=24;
  native has just one grid sample above that threshold in this subgroup.

## Full100 and unchanged controls

Complete ROI G positive area changes from
`74.875 / 67.5625 / 57.3125 / 50.3125` to
`69.25 / 64 / 56.1875 / 50.75`, compared with native
`74.875 / 64.375 / 54.75 / 46.625`. The previously exact threshold-4 area becomes
too small, while threshold-24 excess grows. G RMSE worsens 2.3060 to 2.4395 and
MAE worsens 0.3783 to 0.4005.

Ingress01, ingress10 and far50 G finite differences are exactly unchanged at
the original Android pixel lattice. Ingress50 G RMSE also worsens, 2.2814 to
2.5194. Android R/B witness-control finite differences remain exactly zero at
every original pixel in every pose. This intervention does not reproduce the
native R/B coupling response.

## Evidence

- Frozen analyzer SHA256:
  `ef475784d5aed32b0dc522ae80c5ff760ad6779a5ef676c5c0de2737307ac2d1`.
- Official r3 analysis SHA256:
  `0ae43663c56dfb6055f4b8df19abc7849f88c64360b7f9dc8a27be41acf734ab`.
- Complete four-threshold comparison JSON SHA256:
  `04e372dc1fa2e84d8d334899f83182032bd5d04ca003dfb8a26878e9e0b0013c`.
- R2-only subgroup freeze JSON SHA256:
  `fe269ec10915850ace9319cdab100600b9b879cbcb4b333e554c640c23853177`.

No registration, input change, altered threshold, photometric gain fit or
new acceptance criterion was used. The full official original-byte and
world-grid results remain in their respective analysis directories.
