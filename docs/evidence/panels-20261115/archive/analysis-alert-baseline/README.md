# Alert current baseline — fixed-coordinate evidence

These are public historical calibration REST captures, not independent validation or motion proof. Original display pixels share375×667pt/dp world at2px per unit; no image warp, resize, recenter, synthetic render or fitted translation. Geometry assertions require actual Android Alert[55,515,695,859]px. Native AX is not recovered optical alpha. Native backing controls differ from Android. Scrim, body, straight edge and corner appearance remain separate.

Raw encoded RGB and ICC-normalized sRGB were evaluated independently. Every decoded input declares PNG sRGB and has no ICC; the two tracks are pixel-identical. CSV stores one raw track to avoid duplicate data; JSON keeps both metric tracks. Derivatives use the frozen.5pt grid and fixed.75pt Gaussian sigma,7samples; raw RGB is retained. Units are encoded8bit RGB, RGB/pt and RGB/pt², never physical thickness.

The fixed protocol is in analyze_alert_baseline.py and ../native-alert-map.md. Four body ROIs use a common union of native/Android text/action exclusions expanded2pt. Straight sides retain source phase, with left/right0..24pt, top0..20pt and bottom0..10pt; negative samples are shadow/AA diagnostics. Corners use horizontal raster scans at six fixed depths, with direct content masked. They are not contour-normal scans.

| Scene | Native exterior gain | Android exterior gain | Left gutter RGB RMSE | Left edge0..20 RGB RMSE |
|---|---:|---:|---:|---:|
|color_stripes-dark|0.520043|0.399838|6.122|13.570|
|color_stripes-light|0.800070|0.800070|12.082|16.760|
|fine_grid-dark|0.519706|0.400200|1.759|10.946|
|fine_grid-light|0.800012|0.800012|0.629|9.019|
|synthetic_landscape-dark|0.519927|0.399995|4.158|8.618|
|synthetic_landscape-light|0.800004|0.800004|2.889|12.393|
|tonal_blocks-dark|0.519094|0.399989|2.446|8.431|
|tonal_blocks-light|0.800006|0.800006|3.620|12.718|

Light exterior matches~.80. Current Android Alert dark exterior retains~.40, native~.52; this differs from the historical Sheet~.68 Android observation and must not be fitted away as a thickness defect. The exterior source-before and source-Android-background fixed ROI have zero RGB mismatch in all8 scenes.

The fixed first-blue feature window is x60..96pt. Top y259.75..277.25, body350.25..358.75 and bottom415.75..427.25 avoid the expanded content boxes. Its positive B−(R+G)/2 weighted centroid measures color-response bending, not a recovered source-point path. Native top centroid spans3.134pt light/2.975pt dark; Android spans.417/.315pt. Body centroid is nearly constant. This confirms the visible bend-response mismatch without selecting a unique physical refraction explanation.

`analysis.json` includes file/color metadata and per-scene metrics; `straight-profiles.csv` and `corner-profiles.csv` preserve RGB plus smoothed first/second derivatives. `blue-feature-tracks.csv` retains every fixed feature observation. Three left-edge plots show all8 scenes, including failures. No pooled pass score is used.

Reproduce or evaluate another identically captured candidate:

```sh
/usr/bin/python3 -B /absolute/path/analysis-alert-baseline/analyze_alert_baseline.py --android /absolute/path/candidate-matrix-directory --output /absolute/path/new-analysis --compare-to /absolute/path/analysis-alert-baseline/analysis.json
```

Candidate captures must preserve all8 source identities, actual coordinates, font/density, foreground sample counts and declared color. The interface rejects geometry/mask changes rather than silently fitting them. A numerical lag of the1D derivative curve is labelled `native_sample_offset_pt`: native samples are offset relative to Android. These are appearance correlations with periodic/content ambiguity; no image is shifted and `identified` is always false.
