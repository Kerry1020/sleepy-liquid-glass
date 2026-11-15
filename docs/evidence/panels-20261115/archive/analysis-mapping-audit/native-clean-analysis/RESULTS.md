# Native clean panel r2: feasibility results

The frozen analyzer completed with exit code 0. Its original overall decision remains **false**, with exactly one failed gate: embedded ICC availability. No frozen file, threshold, region, gate or decision was changed after observing the results.

## Observed geometry and accessibility

All eight REST/repeat observations have **exactly zero numeric difference** from the old fixture in recorded AX pane coordinates, all foreground coordinates, and public controller x/y/width/height. This is stronger than merely passing the declared 0.1pt AX / 0.01pt public tolerances.

| Native panel | Actual AX ltrb (pt) | Actual public controller xywh (pt) |
| --- | --- | --- |
| Alert | 27.5, 257.5, 347.5, 429.5 | 27.5, 257.5, 320, 172 |
| Sheet | 8, 317.7, 367, 659 | 8, 317.71066666666667, 359, 341.28933333333333 |

All sixteen AX dumps exclude show-sheet, show-alert and show-menu. The expected system modal remains exposed during REST and absent before/after. The original launch/test title gate, delivered title DOWN/UP, one relay/state-set pair, source identities, world mapping, session traits and operation/capture/AX time bindings all pass. The AX repair therefore did not hide the system modal in this run.

These are public/AX measurements. They do not establish an optical material contour or thickness.

## Full-image REST repeat

The comparison is the entire 750×1334 decoded RGBA image, with no crop, mask, tolerance, registration or warp. Original PNGs are RGB8; converting to RGBA supplies opaque alpha.

| Source | Panel | Pixels per pair | Changed RGBA pixels | Max channel delta |
| --- | --- | ---: | ---: | ---: |
| panel_probe_coordinate | alert | 1,000,500 | 0 | 0 |
| panel_probe_coordinate | sheet | 1,000,500 | 0 | 0 |
| panel_probe_shapes | alert | 1,000,500 | 0 | 0 |
| panel_probe_shapes | sheet | 1,000,500 | 0 | 0 |

Every raw pair has strict zero difference. The script's normalized-labelled fallback values are also numerically zero, but the screenshot ICC availability gate is false; they are not independent ICC conversion evidence.

## Fixed clean-source footprints

Each row covers both sources and both clean-before/dismiss-after phases: four exact comparisons. All listed pixels match the original raw source exactly. The same declared cores/collars and original S07 support were used without adjustment.

| Fixed region | Comparisons | Pixels each | Changed pixels total |
| --- | ---: | ---: | ---: |
| alert:alert_source_core | 4 | 18,720 | 0 |
| alert:alert_source_core_collar2pt | 4 | 20,992 | 0 |
| alert:alert_source_core_collar8pt | 4 | 28,576 | 0 |
| alert:alert_source_core_collar24pt | 4 | 54,432 | 0 |
| alert:alert_source_core_collar60pt | 4 | 142,560 | 0 |
| alert:old_show-sheet | 4 | 16,415 | 0 |
| alert:old_show-alert | 4 | 15,410 | 0 |
| alert:old_show-menu | 4 | 16,415 | 0 |
| sheet:sheet_source_core | 4 | 18,720 | 0 |
| sheet:sheet_source_core_collar2pt | 4 | 20,992 | 0 |
| sheet:sheet_source_core_collar8pt | 4 | 28,576 | 0 |
| sheet:sheet_source_core_collar24pt | 4 | 54,432 | 0 |
| sheet:sheet_source_core_collar60pt | 4 | 136,080 | 0 |
| sheet:S07_original_frozen_support | 4 | 55,696 | 0 |
| sheet:old_show-sheet | 4 | 16,415 | 0 |
| sheet:old_show-alert | 4 | 15,410 | 0 |
| sheet:old_show-menu | 4 | 16,415 | 0 |

The 60pt collar is a frozen stress test, not a native blur-support upper bound. Source exactness here does not prove that the unknown native sampling support cannot extend outside these regions.

## Full context differences retained

The complete before/after image is separately reported and was never replaced by a cropped zero comparison.

- coordinate / Alert: 836 changed pixels, bbox [691,8,739,31]px.
- coordinate / Sheet: 836 changed pixels, bbox [691,8,739,31]px.
- shapes / Alert: 0 changed pixels.
- shapes / Sheet: 848 changed pixels, bbox [31,11,721,1329]px; all exact connected components are retained in the supplement. Differences occur in the top and bottom context, while the fixed source-footprint checks remain exact.

These differences do not change the full REST-repeat result. They also prevent claiming that every full clean-before/after image is identical.

## Separate colour-metadata evidence

The two original sources contain sRGB ICC profiles. All sixteen native screenshots contain exactly one **sRGB chunk with payload00**, no iCCP chunk, and valid CRCs for every PNG chunk. W3C PNG Third Edition §11.3.2.5 defines this sRGB declaration. Therefore the screenshots have an explicit standardized colour-space declaration; the frozen code's ICC-only test fails because it checks Pillow icc_profile exclusively.

The original ICC gate and overall false result remain intact. The supplement records this metadata for a separate review. No screenshot was relabelled, rewritten, converted, or recaptured, and no unmarked-image colour assumption was introduced.

## What this permits

The native clean fixture now has measured source exactness in the fixed regions, stable full-image REST captures, unchanged public/AX geometry, and no residual trigger controls. This supports preparing a **new, separately registered paired-slope feasibility stage** after root review of the colour declaration.

It does **not** approve an inverse fit or a unique two-dimensional source map. Native central optical contour/tangent invariance, actual blur/source support, and identifiability under tone/material adaptation remain unestablished. The clean condition cannot be pooled with old polluted optical pixels. New paired-slope inputs must stay a distinct feasibility observation set; no physical-thickness, optical-parity or 99.99% similarity claim follows.

The original failed native round, this run's input freeze, the frozen algorithm, every gate result, and the nonzero context evidence are preserved.
