# Sigma-unified negative rim blur

Partial static mechanism improvement; do not claim material parity or completion.

All four geometry/source/foreground-slot gates pass. All26 main images have identical raw and ICC-normalized RGB. This candidate reuses the fixed source world, masks, segments, bins and local Alert scans. It is a calibration response, not an independent holdout or parity acceptance.

## Alert local diagnostics

All widths below are raw original-pixel10–90% diagnostics in pt. Local gate failures are retained; descriptive values do not override them.

|Feature / y|Native width|Baseline width|Candidate width|Native50%|Candidate50%|Native contrast|Candidate contrast|Candidate gates|
|---|---:|---:|---:|---:|---:|---:|---:|---|
|S02 /261.75|13.76|23.64|16.08|102.71|108.31|18.69|19.87|secondary_peak>0.8primary|
|S02 /265.75|12.60|23.51|19.14|103.74|106.46|45.57|42.72|secondary_peak>0.8primary|
|S02 /269.75|12.53|24.14|22.13|104.59|105.50|49.88|47.03|secondary_peak>0.8primary|
|S02 /273.75|12.22|23.72|22.78|105.74|105.46|49.04|45.12|secondary_peak>0.8primary|
|coordinate x77 /261.75|unresolved|unresolved|unresolved|unresolved|69.49|-2.29|1.27|contrast<8; contrast<5x_local_spread_floor1; source_contrast_direction_cosine<0.7; secondary_peak>0.8primary|
|coordinate x77 /265.75|12.23|21.04|17.67|73.08|78.39|58.77|62.88|secondary_peak>0.8primary|
|coordinate x77 /269.75|12.72|20.66|19.80|75.36|78.82|65.50|57.04|secondary_peak>0.8primary|
|coordinate x77 /273.75|12.73|20.70|20.05|76.70|78.67|66.15|58.38|secondary_peak>0.8primary|

## Sheet local feasibility

The S07 cross vertical stem right edge is inside the original Sheet top-left region: x84.25..109.75pt, y334.75..341.25pt (depth17.25..23.75). The source edge is x95.5pt; source pink and gray plateaus are known. The horizontal-arm rows are excluded from this specific contour because their opposing gray plateau lies outside the unchanged x110 boundary. This is source-based exploratory operationalization, not movement of the parent ROI. Native passes14/14 local gates. Every failed Android row is retained.

|y|Native raw width|Candidate raw width|Native50%|Candidate50%|Native contrast|Candidate contrast|Candidate gate|
|---|---:|---:|---:|---:|---:|---:|---|
|335.75|9.65|12.48|95.70|96.61|30.01|25.65|secondary_peak>0.8primary|
|337.75|9.60|12.15|95.61|96.41|37.17|29.05|secondary_peak>0.8primary|
|339.75|10.02|12.18|95.71|96.23|40.95|32.13|pass|
|341.25|9.92|12.38|95.69|96.26|43.76|33.78|secondary_peak>0.8primary|

## Full fixed regions and highlight

`candidate-fixed-roi-delta.json` retains180 separate segment/bin comparisons without an overall winner score. Body, exterior, raw/smoothed straight curves, corner rasters and all masks are saved alongside it. Alert top rim peak occurs at0.25pt for this candidate, but encoded luma excess31.52counts exceeds native22.29; the minimum three-pixel narrow-peak gate does not resolve FWHM. Improved width therefore does not establish a corrected highlight or lens thickness.

No complete2D source map, physical thickness, independent blur kernel, motion trajectory or reproduction percentage is established. Static Dock/panel work remains incomplete.
