# Mechanism numerical supplement

All original mechanism outputs contain finite numeric values. The three JSON files were recursively checked; the rendered PNG's decoded samples are finite. All 62 fixed depth bins are nonempty.

The supplement recomputed **15 curves / 930 coordinates** with explicit R×0.2126 + G×0.7152 + B×0.0722. It also recomputed **3720 RGB statistic groups** from the original captures. Maximum disagreement with the original JSON RGB statistics and weighted means: **8.53e-14** code units. Maximum full-frame matmul-versus-explicit difference, including constant synthetic controls: **0**; maximum depth-curve difference: **0**.

The separately saved `mechanism-numerical-review-depth.png` differs from the original rendered figure in **0 RGBA pixels**, with maximum channel difference **0**. The original figure was preserved.

The runtime reports NumPy 2.0.2 with the Accelerate BLAS backend. With ARM64 floating-point exception flags explicitly cleared before the operation, actual and constant-array controls recorded **72 matmul warnings** in this review. Detailed warnings, result ranges, and error-ignore hardware flag observations are retained in `mechanism-numerical-review.json`.

The reviewed numbers and figure show **no observed numerical contamination**. Warning/control evidence is consistent with an issue in the Accelerate-backed matmul floating-point status path. It does **not** uniquely locate a BLAS internal instruction, prove that all warnings in other workloads are harmless, or justify silently suppressing future warnings. The independent multiply/add path provides the checked substitute for these curves.

No frozen script/input/output was changed. This is a numerical supplement to single-size static calibration, not optical acceptance, physical-model identification, or multi-size/dynamic validation.
