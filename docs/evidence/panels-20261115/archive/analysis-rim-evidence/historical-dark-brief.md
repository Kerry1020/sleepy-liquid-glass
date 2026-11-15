# Dark historical rim: first-two-row check

The source is the unchanged raw fixed profiles in `../analysis-alert-baseline/straight-profiles.csv`; every scene remains public historical calibration. Native source/delivery mapping is in `../native-alert-map.md`. Inside-pane equivalence after the scrim correction is established in `historical-dark-reuse.json`; no screenshot is analytically rescrimmed.

The side highlighter defect is also present in dark appearance. On fine-grid left, native RGB at inset0.25→0.75pt is[98.84,98.84,103.47]→[80.84,80.84,84.34], whereas Android is[36.02,36.02,36.74]→[57.48,57.48,58.31]. On the right, native is[93.31,93.31,95.90]→[78.06,78.06,79.71] versus Android[40.08,40.08,40.94]→[57.40,57.40,58.34]. The native outer row is brighter; Android instead rises inward from a dark first row.

Tonal-blocks repeats the sign: native left[70.03,70.03,73.48]→[55.05,55.06,57.44], Android[22.03,22.03,22.87]→[34.52,34.52,35.84]. The right behaves similarly. Existing dark factory CPU side opacity0.75 is stronger than light0.35, while the additive side shine still reaches zero. These observations are consistent with the identified line/side-shine mechanism but do not isolate their relative contribution in dark rendering; no dark removal/floor experiment has been performed.

Do not globally strengthen the dark rim: tonal-blocks bottom first-row native[83.19,83.34,83.69] is already below Android[93.85,93.85,92.57], and colored sources show unequal channel signs. The proposed next light-only candidate should leave the dark factory unchanged as an exact control. All four backgrounds ×four edges ×two rows are retained in `historical-dark-first-two-rows.json`; this brief does not select the neutral-looking examples as a replacement dataset.
