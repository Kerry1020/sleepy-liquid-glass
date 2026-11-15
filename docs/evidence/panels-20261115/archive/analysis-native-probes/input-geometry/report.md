# Input-raster geometry repair: exact Window control

The four accepted REST actual Window images are raw RGBA pixel-identical to Alert-body8. The two plain-background actual Window images are also pixel-identical. This is an unchanged-rendering control in the fixed calibration fixture, not a material improvement or parity acceptance.

| Input | Carrier | Actual Window size (px) | Changed Window pixels |
|---|---|---:|---:|
| coordinate | Alert | 658 × 356 | 0 |
| shapes | Alert | 658 × 356 | 0 |
| coordinate | Sheet | 750 × 1334 | 0 |
| shapes | Sheet | 750 × 1334 | 0 |

Observed Window placement, canvas mapping and unit basis, pane bounds, foreground slot rectangles and content density/font scale are unchanged. Runtime object identities and capture timestamps differ. The exported Sheet measurements differ only in their composited-display statistics; these statistics were not used to override the actual Window control.

The composited full displays are **not** globally pixel-identical. All changed pixels fall in y35..60 or y1312..1319, within the declared top and navigation system-bar insets (0..79 and 1302..1333 respectively). Every display is exactly unchanged throughout y80..1301. Exact counts and exclusive-coordinate boxes are retained in `system-overlay-differences.json`; no overlay was removed, fitted, corrected, or silently ignored. The two Alert panes are also unchanged in their complete composited-display pane bounds. A narrow part of the Sheet bottom intersects the navigation overlay; use the observed actual Window for the unchanged-rendering control there.

Raw decoded RGB equals ICC-normalized sRGB for all compared screenshots, so the equality is not an ICC-conversion artifact. File hashes were bound before the candidate's first pixel decode. Only matrix-declared accepted captures and their declared backgrounds were decoded; rejected-display attachments were not decoded. No registration, resize, recentering, warp, source substitution, new ROIs, or parameter fits were used. No duplicate screenshot files or repeated material charts were generated.

The Alert-body8 optical findings and limitations remain unchanged: apparent transition widths improve relative to the original baseline, while source-correspondence positions, local contrast and the overbright outer highlight still mismatch native. The Sheet12 baseline limitation also remains. This geometry repair does not establish a corrected optical model, independently identifiable physical sigma/thickness, dynamic parity or whole-product appearance parity.
