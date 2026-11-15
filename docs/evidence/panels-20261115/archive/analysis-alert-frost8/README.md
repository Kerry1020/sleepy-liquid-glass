# Alert rimBlur8 candidate — all8 conditions

These are public historical calibration REST captures, not independent validation or motion proof. Original display pixels share375×667pt/dp world at2px per unit; no image warp, resize, recenter, synthetic render or fitted translation. Geometry assertions require actual Android Alert[55,515,695,859]px. Native AX is not recovered optical alpha. Native backing controls differ from Android. Scrim, body, straight edge and corner appearance remain separate.

Raw encoded RGB and ICC-normalized sRGB were evaluated independently. Every decoded input declares PNG sRGB and has no ICC; the two tracks are pixel-identical. CSV stores one raw track to avoid duplicate data; JSON keeps both metric tracks. Derivatives use the frozen.5pt grid and fixed.75pt Gaussian sigma,7samples; raw RGB is retained. Units are encoded8bit RGB, RGB/pt and RGB/pt², never physical thickness.

The only requested runtime variable was Alert rimBlur8 in both theme branches. This analysis uses the current baseline's already fixed ROIs, algorithms and original native references. `candidate-comparison-freeze.json` preserves the comparison script SHA before candidate image decoding. A lag field label was corrected from Android to native offset before decoding; no sampling or numerical phase algorithm changed.

The candidate has mixed edge results. It reduces stripe-light left-edge RGB and derivative error but worsens that scene's right-edge results. Landscape-light has four improved/eight regressed straight-edge diagnostics. The blue-feature bend is still far below native and becomes smaller in light mode. Thus this isolated blur candidate does not resolve the visible thickness/bending issue.

## Exact pixel controls

| Region | Conditions | Changed pixels | Maximum absolute channel change |
|---|---:|---:|---:|
|alert_conservative_deep_core_without_foreground|8|0|0|
|alert_window_outside_pane_bbox|8|0|0|
|full_sheet_window_rgba|8|0|0|
|static-alert-cancel_inner8pt|8|0|0|
|static-alert-confirm_inner8pt|8|0|0|

Raw and ICC controls are both zero. Full Sheet Window comparison preserves all RGBA bytes, including transparent pixels. Alert deep-core control uses a conservative central region beyond34dp corner extents and excludes direct foreground; it is a guaranteed deep subset, not a complete recovered contour-distance20 mask. Each action's inner8pt region is separate because child optics may sample parent material. All four body ROIs are unchanged in all8 conditions.

## Every group, including regressions

Counts compare every declared raw metric with baseline: four body RGB metrics,12straight RGB/D1/D2 metrics,72corner RGB/D1/D2 metrics per condition. “Improved” is only numerical delta<−1e−9, not a significance or acceptance claim. Tiny grid changes are included; no threshold removes them. Masked corner samples remain identical between runs. Corner scans include curved coverage/exterior response and dark-scrim mismatch, so their error is not a pure material-thickness score.

| Scene | Body I/R/U | Straight I/R/U | Corner I/R/U |
|---|---|---|---|
|color_stripes-dark|0/0/4|9/3/0|47/25/0|
|color_stripes-light|0/0/4|8/4/0|60/12/0|
|fine_grid-dark|0/0/4|7/5/0|23/30/19|
|fine_grid-light|0/0/4|8/4/0|29/26/17|
|synthetic_landscape-dark|0/0/4|11/1/0|55/17/0|
|synthetic_landscape-light|0/0/4|4/8/0|46/26/0|
|tonal_blocks-dark|0/0/4|7/5/0|42/27/3|
|tonal_blocks-light|0/0/4|7/5/0|38/34/0|

All straight-edge errors below retain original coordinates (baseline → candidate).

|Scene|Edge|RGB RMSE|D1 RMSE|D2 RMSE|
|---|---|---:|---:|---:|
|color_stripes-dark|left|13.5704 → 13.0206|4.5275 → 4.5915|5.5922 → 5.5704|
|color_stripes-dark|right|12.8978 → 12.3005|3.4267 → 3.4666|4.3254 → 4.5522|
|color_stripes-dark|top|4.5349 → 4.2757|2.8580 → 2.7147|2.1828 → 2.0903|
|color_stripes-dark|bottom|5.7001 → 5.4045|3.3616 → 3.1857|2.7062 → 2.6288|
|color_stripes-light|left|16.7601 → 13.8148|3.4667 → 3.0035|5.5693 → 5.1737|
|color_stripes-light|right|10.6362 → 10.7974|2.8701 → 3.2978|4.5922 → 4.6417|
|color_stripes-light|top|7.1332 → 6.5677|1.9882 → 1.9373|3.1104 → 2.9311|
|color_stripes-light|bottom|10.4180 → 9.6595|2.7564 → 2.8065|4.6716 → 4.4375|
|fine_grid-dark|left|10.9462 → 10.9452|4.3308 → 4.3323|4.8620 → 4.8624|
|fine_grid-dark|right|9.3678 → 9.3666|3.7247 → 3.7246|3.9303 → 3.9303|
|fine_grid-dark|top|2.5409 → 2.5403|2.7765 → 2.7756|2.0670 → 2.0671|
|fine_grid-dark|bottom|2.9009 → 2.9011|3.0684 → 3.0677|2.3144 → 2.3165|
|fine_grid-light|left|9.0187 → 9.0192|2.4483 → 2.4461|4.4984 → 4.4929|
|fine_grid-light|right|8.7974 → 8.7992|2.3314 → 2.3233|4.2911 → 4.2841|
|fine_grid-light|top|4.0134 → 3.9954|1.0408 → 1.0092|1.6150 → 1.5792|
|fine_grid-light|bottom|5.7051 → 5.7067|1.2733 → 1.2754|2.7223 → 2.7220|
|synthetic_landscape-dark|left|8.6183 → 8.6118|2.9531 → 2.9436|3.9194 → 3.9141|
|synthetic_landscape-dark|right|7.4416 → 7.4257|2.6066 → 2.6175|3.2694 → 3.2629|
|synthetic_landscape-dark|top|4.3641 → 4.3636|1.8885 → 1.8769|1.7001 → 1.6886|
|synthetic_landscape-dark|bottom|7.1068 → 7.0945|2.4193 → 2.4017|2.4032 → 2.3965|
|synthetic_landscape-light|left|12.3934 → 12.4488|3.6955 → 3.6971|5.9890 → 6.0000|
|synthetic_landscape-light|right|12.0600 → 11.9368|3.5817 → 3.5898|5.7290 → 5.7043|
|synthetic_landscape-light|top|9.9007 → 9.9328|2.7733 → 2.7752|4.5141 → 4.5259|
|synthetic_landscape-light|bottom|14.8396 → 14.8578|4.1495 → 4.1057|6.8736 → 6.8426|
|tonal_blocks-dark|left|8.4309 → 7.9886|2.8578 → 2.9352|4.1260 → 4.0489|
|tonal_blocks-dark|right|8.2027 → 8.2463|3.2641 → 3.5429|3.3220 → 3.3787|
|tonal_blocks-dark|top|3.3475 → 3.1053|1.1107 → 1.1745|1.2728 → 1.2426|
|tonal_blocks-dark|bottom|8.1532 → 7.4740|3.5496 → 3.4041|3.2257 → 3.0823|
|tonal_blocks-light|left|12.7177 → 11.8827|4.0613 → 4.1481|6.0792 → 5.8576|
|tonal_blocks-light|right|13.8073 → 13.9942|3.9174 → 4.0042|6.7445 → 6.6035|
|tonal_blocks-light|top|11.8203 → 11.2114|3.7507 → 3.7184|5.5429 → 5.3226|
|tonal_blocks-light|bottom|6.5335 → 5.5451|1.2387 → 1.3544|2.1657 → 2.1956|

## Fixed blue-feature bending

|Trait|Band|Native centroid span pt|Baseline span pt|rimBlur8 span pt|
|---|---|---:|---:|---:|
|dark|top|2.975029|0.314626|0.422725|
|dark|body|0.009494|0.000000|0.000000|
|dark|bottom|2.657694|0.229896|0.265750|
|light|top|3.133626|0.417003|0.306947|
|light|body|0.020388|0.001361|0.001361|
|light|bottom|2.732946|0.358107|0.198823|

This is a frozen color-window centroid, not optical correspondence. A wider/narrower centroid span can also depend on color/blur/coverage; no claim of unique physical displacement is made. The candidate modifies edge frosting and does not supply the missing native bend response. Static stripe excitation alone cannot select a universal profile.

![Fixed first-blue feature trajectories](blue-feature-bend-comparison.png)

`analysis.json` contains all scene/metric before-after deltas, controls, hashes and both color tracks; the CSVs contain every fixed RGB/D1/D2 curve, including masked bottom-corner positions. No native source was changed and no output screenshot was transformed. Existing dark exterior discrepancy remains untouched. The reusable analyzer is ../analysis-alert-baseline/analyze_alert_baseline.py.
