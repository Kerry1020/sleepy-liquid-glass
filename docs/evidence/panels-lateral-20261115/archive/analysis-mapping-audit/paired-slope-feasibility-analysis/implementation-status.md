# Paired-slope implementation supplement

The historical plan, schema, preparation freeze and README remain unchanged.
This supplement records a later numerical implementation and synthetic checks.
**No new real capture or original source PNG was decoded. The experiment is
uncollected/unexecuted/not passed.** Original raw RGB records were verified by
regenerating the four analytic rasters in memory and comparing their byte hashes.

`analysis.py` accepts exactly one `handoff.json` path. Its import performs no
file reads or image decoding. The command validates the original frozen plan,
schema, artifact hashes, four-source/eight-session matrix and all four phases.
It records a before-decode manifest and gives an insufficient-evidence result
for malformed or incomplete input. Android may supply incomplete context as
diagnostics, but missing clean-before/dismiss-after remains a schema/gate error;
no context phase is synthesized. Native additionally requires all four AX dumps.

The frozen handoff schema specifies receipt artifact locations and hashes, but
does not specify their raw payloads. The command therefore deliberately stops
before real image decode with `receipt_semantics_unresolved_before_real_decode`.
It cannot establish canvas identity, phase/session linkage, geometry, traits or
foreground merely from adapter booleans or file hashes. Root will register a
separate raw receipt contract before new collection. The required fields are
listed in `receipt-contract-requirements.json`. A future contract/adapter must
be frozen independently; this supplement does not authorize weakening a gate.

Pure analysis entry points implement the fixed scans, both endpoint spreads,
oracle contrast direction, Gaussian7/sigma1.5/reflect3 operator, derivative
peak/tie/secondary rules, every raw/smoothed increasing/decreasing crossing,
raw monotonicity, 2pt foreground expansion and all original scalar gates.
Failures stay attached to each side and row. The area/mass/tensor gates remain
explicitly inapplicable to this 1D diagnostic and never authorize 2D recovery.

Paired apparent W/C/g/U/D is available only when both sides pass independently.
Diagnostic pre-falsification values are retained; fully eligible exports require
all four a20/a24 × normal/reversed conditions at that platform/row to pass their
reverse and width checks. No favorable subset is averaged into eligibility.
Absolute bounds retain the 0.25pt edge raster floor and propagate to the 1pt g
floor. Fixed h4 first secants require eligible endpoints; second secants also
require the center. Boundary derivatives are unavailable. Cross-platform results
are descriptive residuals, with no parity threshold or parameter fit.

PNG validation parses original chunks before Pillow: signature, bounds, order,
singletons, every CRC, RGB/RGBA8 dimensions, alpha declaration, complete IEND and
color precedence. Legal explicit sRGB is supported without an ICC field. Valid
RGB ICC conversion records source/target profile and intent hashes. Unsupported
higher-priority cICP/invalid ICC never falls back to lower sRGB. Lower-priority
metadata and conflicts remain recorded. Unsupported color provenance keeps only
raw diagnostics. Raw and supported normalized tracks run separately.

The nine top50 lines are analytically constant in all four source rasters.
Consequently, their oracle start→end RGB vector is zero: the original plan does
not specify a nonzero independent material contrast direction. The implementation
does not derive a favorable direction from output plateaus. Top50 is unavailable
until such a direction is independently registered. Its gate is separate from
bilateral diagnostics: the synthetic known-warp fixture retains 40/40 eligible
bilateral rows while the missing top direction keeps the overall result not
passed. No top contour, tangent, physical depth or blur-support claim follows.

`synthetic_checks.py` generates all arrays and PNG streams in memory. Its final
report covers known translation/stretch/inversion/blur, weak contrast, both
noisy plateaus, double peaks, all crossing directions, missing edges, foreground,
tie uncertainty, quantization, reverse/width failures, h4 bounds, strict full-RGBA
repeat, named source exactness, top availability, phase/AX completeness and PNG
metadata failures. The report is implementation evidence, not optical evidence.

No device, build, Git, product or library file was changed by this supplement.
No runtime parameter update, unique2D recovery, physical thickness, true blur
support, refraction/power fit or optical parity percentage is enabled.
