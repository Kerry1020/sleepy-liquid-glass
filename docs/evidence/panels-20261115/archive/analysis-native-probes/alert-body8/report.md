# Alert body radius8 with constant rim

Strong local apparent-edge improvement; contour position, contrast and rim remain mismatched. No parity acceptance.

All four geometry/source/foreground-slot gates pass. All26 main images have identical raw and ICC-normalized RGB. This candidate reuses the fixed source world, masks, segments, bins and local Alert scans. It is a calibration response, not an independent holdout or parity acceptance.

## Alert local diagnostics

All widths below are raw original-pixel10–90% diagnostics in pt. Local gate failures are retained; descriptive values do not override them.

|Feature / y|Native width|Baseline width|Candidate width|Native50%|Candidate50%|Native contrast|Candidate contrast|Candidate gates|
|---|---:|---:|---:|---:|---:|---:|---:|---|
|S02 /261.75|13.76|23.64|11.54|102.71|109.25|18.69|16.98|secondary_peak>0.8primary|
|S02 /265.75|12.60|23.51|13.90|103.74|107.11|45.57|48.81|secondary_peak>0.8primary|
|S02 /269.75|12.53|24.14|13.91|104.59|106.19|49.88|53.61|pass|
|S02 /273.75|12.22|23.72|13.69|105.74|106.38|49.04|53.12|secondary_peak>0.8primary|
|coordinate x77 /261.75|unresolved|unresolved|unresolved|unresolved|68.49|-2.29|2.10|contrast<8; contrast<5x_local_spread_floor1; source_contrast_direction_cosine<0.7|
|coordinate x77 /265.75|12.23|21.04|14.19|73.08|77.35|58.77|70.99|pass|
|coordinate x77 /269.75|12.72|20.66|14.12|75.36|77.56|65.50|69.30|pass|
|coordinate x77 /273.75|12.73|20.70|13.67|76.70|77.66|66.15|70.81|pass|

## Sheet local feasibility

The S07 cross vertical stem right edge is inside the original Sheet top-left region: x84.25..109.75pt, y334.75..341.25pt (depth17.25..23.75). The source edge is x95.5pt; source pink and gray plateaus are known. The horizontal-arm rows are excluded from this specific contour because their opposing gray plateau lies outside the unchanged x110 boundary. This is source-based exploratory operationalization, not movement of the parent ROI. Native passes14/14 local gates. Every failed Android row is retained.

|y|Native raw width|Candidate raw width|Native50%|Candidate50%|Native contrast|Candidate contrast|Candidate gate|
|---|---:|---:|---:|---:|---:|---:|---|
|335.75|9.65|12.58|95.70|97.16|30.01|23.42|contrast<5x_neutral_spread_floor1|
|337.75|9.60|12.08|95.61|96.88|37.17|26.13|secondary_peak>0.8primary|
|339.75|10.02|unresolved|95.71|96.96|40.95|27.78|secondary_peak>0.8primary|
|341.25|9.92|12.13|95.69|96.88|43.76|28.94|secondary_peak>0.8primary|

## Full fixed regions and highlight

`candidate-fixed-roi-delta.json` retains180 separate segment/bin comparisons without an overall winner score. Body, exterior, raw/smoothed straight curves, corner rasters and all masks are saved alongside it. Alert top rim peak occurs at0.25pt for this candidate, but encoded luma excess31.52counts exceeds native22.29; the minimum three-pixel narrow-peak gate does not resolve FWHM. Improved width therefore does not establish a corrected highlight or lens thickness.

No complete2D source map, physical thickness, independent blur kernel, motion trajectory or reproduction percentage is established. Static Dock/panel work remains incomplete.

Sheet is the control. Every frozen Sheet straight/bin sample is unchanged against the original baseline. Shapes entire Sheet pane is pixel-identical. Coordinate entire pane has1379changed pixels confined to[127.5,656,247.5,659]pt (max RGB20, mean absolute pane delta0.024counts); this is retained as a separate context difference and not corrected.
