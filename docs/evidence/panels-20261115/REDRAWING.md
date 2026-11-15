# Reproducing the published panel evidence

This package contains the recorded 2026-11-15 static Alert/Sheet calibration analysis. It does not contain an APK, build cache, video, private course data, full status-bar screenshot or unpublished noise/heldout stimulus. The archived source reports preserve failed candidates and negative results. The portable scientific entry point is [the panel study](../../panel-material-study.md); some archived historical reports retain their original working-directory links and paths.

## Verify every copied byte

From this directory:

```sh
python3 -B verify_publication.py
```

Only Python's standard library is needed. `sources.json` records original source SHA-256, original bytes, published SHA-256 and the transform. Numeric JSON/CSV files larger than256KiB are deterministically gzip-compressed (`mtime=0`). Verification decompresses them in memory and checks that their bytes match the original source hash. Repeated arrays were not rounded, dropped or statistically pooled.

The original-file paths are represented by the `panel-study/` source namespace. Individual native historical crops also identify their original filename and source hash. The complete original capture mappings, frozen predecode manifests, build/source hash receipts and all failed-run receipts are retained under `archive/`. Failed or rejected display image batches were neither optically decoded nor republished for this export.

## Redraw the portable figures

Install Python3 with numpy, Pillow and matplotlib, then run:

```sh
python3 -B redraw_figures.py
```

The script reads only this public package's raw CSV files and exact pane crops. It recreates the light/dark all-background screenshot matrices, Sheet12→10 matrix, neutral-edge curves and all historical straight-edge curves. It does not connect to a phone, run a simulator, compile an app, invoke the historical capture scripts, fit a parameter, shift a coordinate, change a mask or select a successful sample. Font/library differences on another computer may change the rasterized plot labels, but do not change the numerical inputs.

The existing `budget-five-way-fixed-comparison.png`, additive clipping figure and other copied research figures are byte-exact archived figures. Their renderer scripts are retained under `archive/analysis-rim-evidence/` or the relevant analysis directory. The original full-display sources are not all republished: the package deliberately exports bounded pane crops and original raw numerical tracks. Therefore reproducing every historical pixel-analysis stage requires the separately preserved capture archive, whose original identities are recorded here. Redrawing the six portable figures requires only this package.

## Restore exact original research files

To inspect the original uncompressed tree in a new destination:

```sh
python3 -B restore_archive.py /path/to/new/panel-study
```

The destination must not exist. The command restores original bytes and verifies their hashes. It does not run any archived scripts. The archived analyzers intentionally retain their historical dependency paths, source hashes, unsuccessful parser outputs and run identities; restoring them alone is not a new device experiment or an assertion that external capture sources are present.

## Figure transformations

All50 pane crops retain the exact original composited-display pixels at the fixed half-open source rectangles:

| Carrier | Original source pixels | Exported crop size |
| --- | --- | --- |
| Alert | `[55,515,695,859]` |640×344px|
| Sheet | `[16,635,734,1318]` |718×683px|

The image files in `original-crops/` are not resized, warped, registered, recolored or retouched. Their hashes and original source hashes are in `sources.json`. Contact-sheet display scaling is presentation only. Native foreground controls differ from Android; none were replaced to make the pictures match. The known Sheet bottom/backing-context limitation remains visible. Strict controls use the recorded actual Window RGBA comparisons, not a claim that complete composited displays were identical.

Raw encoded RGB and ICC-normalized sRGB equality was checked during the original analyses. Plot luma uses the frozen weights `[.2126,.7152,.0722]` in encoded working RGB. These are descriptive color curves, not physical radiance, optical thickness, a recovered blur kernel or every-millisecond motion parity.

## Where the negative results are

- `archive/analysis-rim-evidence/budget-result.json` and its compressed form retain all reference-specific control/clipping summaries.
- `budget-regression-index.csv` and `budget-regressions.json.gz` retain every background/edge/corner/depth/field regression, including overlapping scopes.
- `budget-history-corner16-metrics.json.gz` is the final historical corner smooth/D1/D2 interpretation. The older CSVs preserve7-support derivative columns for provenance; those legacy columns are not the accepted corner derivative interpretation.
- The `screen`, `additive`, `body8`, `outline-zero`, `sigma-unified`, `refraction0`, `clear-edge`, `profile-half`, `rimBlur8` and Sheet mode/radius reports remain in their original archive directories. A passing geometry/control check does not convert a rejected material candidate into native appearance acceptance.
