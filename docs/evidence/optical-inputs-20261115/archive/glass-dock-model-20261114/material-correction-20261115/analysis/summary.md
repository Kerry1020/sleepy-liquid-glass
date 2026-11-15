# Fixed Dock material diagnostics

64 scene/jobs; seven valid metadata packets. Default versus old baseline is exactly zero changed pixels in all 16 scenes, both before and after ICC conversion.

Only fixed-size REST calibration. Values are sRGB code values after the frozen ICC helper. No combined fidelity score, parity acceptance, dynamic conclusion, or private-material claim.

Center order: native / default / tone / adaptive. Removing raw edges does not change this point. Rim order: default / tone / tone without raw edges / adaptive. Rim RGB MAE averages the three per-channel absolute errors over the frozen base mask at 0<=depth<4px. Interior Yprime MAE uses depth>=32px with the same exclusions. Point index is (375,1230).

## Requested light

| Background | Actual native bar | Center RGB: N / D / T / A | Rim RGB MAE: D / T / U / A | Interior Yprime MAE: D / A |
|---|---|---|---|---|
| ms01_gray_26 | light | 36,36,36 / 189,189,189 / 152,152,152 / 35,35,35 | 110.033 / 93.011 / 137.373 / 65.354 | 146.642 / 11.904 |
| ms02_gray_77 | light | 176,176,176 / 193,193,193 / 175,175,175 / 175,175,175 | 67.366 / 61.281 / 13.616 / 13.616 | 24.585 / 9.073 |
| ms03_gray_128 | light | 198,198,198 / 201,201,201 / 198,198,198 / 198,198,198 | 52.792 / 52.028 / 9.955 / 9.955 | 12.152 / 9.271 |
| ms04_gray_179 | light | 220,220,220 / 216,216,216 / 221,221,221 / 221,221,221 | 39.994 / 41.097 / 6.260 / 6.260 | 13.820 / 11.299 |
| ms05_gray_230 | light | 247,247,247 / 238,238,238 / 244,244,244 / 244,244,244 | 33.694 / 31.129 / 2.773 / 2.773 | 19.515 / 14.275 |
| ms06_red | light | 255,139,139 / 255,168,168 / 255,138,138 / 255,138,138 | 52.468 / 46.622 / 17.667 / 17.667 | 29.334 / 7.992 |
| ms07_green | light | 82,255,82 / 100,255,100 / 82,255,82 / 82,255,82 | 37.866 / 32.747 / 42.521 / 42.521 | 13.210 / 8.291 |
| ms08_blue | light | 155,155,255 / 184,184,255 / 154,154,255 / 154,154,255 | 57.238 / 51.286 / 12.940 / 12.940 | 33.527 / 8.371 |

## Requested dark

| Background | Actual native bar | Center RGB: N / D / T / A | Rim RGB MAE: D / T / U / A | Interior Yprime MAE: D / A |
|---|---|---|---|---|
| ms01_gray_26 | dark | 36,36,36 / 39,38,42 / 35,35,35 / 35,35,35 | 44.108 / 40.912 / 32.755 / 32.755 | 13.116 / 11.896 |
| ms02_gray_77 | dark | 73,73,73 / 66,65,68 / 77,77,77 / 77,77,77 | 25.845 / 32.693 / 27.241 / 27.241 | 15.934 / 12.880 |
| ms03_gray_128 | dark | 126,126,126 / 93,92,95 / 119,119,119 / 119,119,119 | 15.255 / 11.571 / 12.584 / 12.584 | 38.938 / 13.287 |
| ms04_gray_179 | dark | 158,158,158 / 109,108,112 / 161,161,161 / 161,161,161 | 34.884 / 14.925 / 15.788 / 15.788 | 52.487 / 7.520 |
| ms05_gray_230 | light | 247,247,247 / 117,115,120 / 203,203,203 / 244,244,244 | 97.259 / 35.487 / 37.977 / 6.786 | 127.666 / 14.228 |
| ms06_red | dark | 255,44,44 / 217,31,34 / 252,41,41 / 252,41,41 | 41.749 / 36.669 / 30.300 / 30.300 | 24.087 / 9.544 |
| ms07_green | dark | 0,223,0 / 0,152,1 / 11,222,11 / 11,222,11 | 59.506 / 48.910 / 42.219 / 42.219 | 51.876 / 4.636 |
| ms08_blue | dark | 42,42,255 / 44,43,231 / 49,49,255 / 49,49,255 | 37.158 / 34.009 / 28.280 / 28.280 | 9.827 / 14.802 |

## Material regressions that remain

- Light gray26: the adaptive center is close (35 versus 36), but the rim MAE remains 65.354. Turning off raw edges alone worsens the rim from 93.011 to 137.373.
- Light green: removing raw edges worsens rim MAE from 32.747 to 42.521, above the original 37.866.
- Dark gray77: tone without raw edges has rim MAE 27.241, still above original 25.845.
- Dark blue: interior Yprime MAE worsens from 9.827 to 14.802. An improved central clipped RGB sample is not sufficient evidence.
- Dark green: candidate center is (11,222,11), while native is (0,223,0); clipped native channels remain constraints, not fitted exact values.
- Requested dark gray230 has actual native bar light. Preserve this difference; do not infer private material state from requested theme.

Full all-62-bin metrics are in metrics.csv; center/top samples in points.csv; exact default preservation in default-minus-old-baseline.json; source traits and ICC provenance in frames.json.
