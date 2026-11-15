# Research moved out of Sleepy

[简体中文](README.md) · [File identities and destinations](SOURCE-MAP.json) · [External Android research entry point](../slider-android-host/README.md)

This archive preserves 52 research files (1,774,394 bytes) from Sleepy commit `5c604e83cc5ccbc6c5ab622568eae0c99265dfc4` before removing them from the application repository. It also covers leftovers from earlier merged work. PR #442 itself already contains only four production files and four JVM regression files.

![Previously published standalone sample on four backgrounds; no new optical experiment was performed](../../docs/images/sample-backgrounds-light.png)

The figure reuses the standalone sample with its existing [image provenance](../../docs/images/sources.json). Migration changes neither runtime behavior nor optical acceptance.

## Scope and preservation

The selection contains 17 native-reference project files, eight research-only Android capture or diagnostic entry points, seven research/handoff reports, and 20 embedded extraction/validation archive files. The application retains a short runtime integration README.

Fifteen files reuse identical published bytes; 37 missing versions are stored under `sources/`. No frozen source is overwritten. Five old native-reference files differ from the previously exported slider fixtures, so both versions remain available. The map records each source Git blob, SHA-256, size and destination.

Production runtime, deterministic host regressions, meaningful GPU behavior/sampling regressions and their shared helpers remain in Sleepy, along with product-layout documentation and source/license audits. Historical research reports are preserved in the third batch below. APKs, build caches, DerivedData, traces and device data are excluded.

A second audit found 13 test/helper files containing research responsibilities. Their complete originals (253,339 bytes) are preserved in a separate [follow-up manifest](followup/SOURCE-MAP.json), pinned to `d38e9d1a92adcde69264bdd50313948bdd29ab0e`. Research responsibilities include language-menu frame recording, configurable acquisition protocols and reflective shader diagnostics; success-path PNG/CSV/JSON export in sampling, motion, contour, backing and window regressions; and the opt-in exact-contour A/B collector without a performance pass threshold. The application retains actual behavior, presentation-handoff, motion and GPU error assertions with in-memory sampling, including shader instrumentation necessary for those assertions. The original 52-file map stays unchanged; the 13 full originals preserve all responsibilities before separation.

The follow-up also includes success-path PNG/JSON exports from `BackdropAwareForegroundRenderTest` and the background, layout, capture-readiness and metrics helper framework no longer consumed by product regressions. Their complete originals are preserved here. Sleepy retains only the necessary `OpticalCaptureWindow` capture helper and actual in-memory assertions, including foreground masks and color-error bounds.

A separate [third-pass manifest](third-pass/SOURCE-MAP.json) preserves 18 historical research files (1,450,206 bytes), pinned to `daabde9ac3b7c421345e6a710fcde1ccd82c475b`: the November 9 [control-motion report](third-pass/sources/docs/design/glass-control-motion-20261109.md) with six attachments, the [PR #299 floating-control report](third-pass/sources/docs/design/pr299-floating-controls-20261109.md) with five evidence images, and five FLClash control-coverage, parity, implementation-verification and reference-inventory records. None had an identical existing version in this repository. All 18 are archived under `third-pass/sources/` with their original directory relationships, preserving the reports' relative attachment links. Experimental conclusions, dimensions and parameters remain historical statements, not current runtime settings or current acceptance. Attribution and licensing remain independently documented in the application's acknowledgements and license audit. The original 52-file and follow-up 13-file manifests stay unchanged.

A [fourth-pass manifest](fourth-pass/SOURCE-MAP.json) preserves the unconnected explicit-ordering prototype and its self-test: two files, 7,134 bytes, pinned to `9cc97649147bd2f4b9a57cb6ddce805d412902cf`. Only the prototype's own test consumes it; it does not protect the current application implementation. Across four batches, **85 files / 3,485,073 bytes** are preserved. The three previous manifests remain unchanged.

A [fifth-pass manifest](fifth-pass/SOURCE-MAP.json) preserves the complete originals of ten product regressions (95,943 bytes), pinned to `e935c5e3b9bc3308930fcf2fe79bbd4f95aab7f6`. These files still contained unused success-path PNG/JSON/TXT research exports, recording-directory arguments or attachment-only collection scaffolding. Only those responsibilities are removed from the application; original behavior, geometry, layering and GPU pixel assertions and thresholds remain. The five batches preserve **95 files / 3,581,016 bytes**. Previous manifests and frozen originals remain unchanged.

```sh
python3 research/sleepy-research-migration-20261116/verify.py
python3 research/sleepy-research-migration-20261116/verify.py --source /path/to/sleepy
python3 research/sleepy-research-migration-20261116/verify.py --manifest research/sleepy-research-migration-20261116/followup/SOURCE-MAP.json --source /path/to/sleepy
python3 research/sleepy-research-migration-20261116/verify.py --manifest research/sleepy-research-migration-20261116/third-pass/SOURCE-MAP.json --source /path/to/sleepy
python3 research/sleepy-research-migration-20261116/verify.py --manifest research/sleepy-research-migration-20261116/fourth-pass/SOURCE-MAP.json --source /path/to/sleepy
python3 research/sleepy-research-migration-20261116/verify.py --manifest research/sleepy-research-migration-20261116/fifth-pass/SOURCE-MAP.json --source /path/to/sleepy
```

The default command checks the original 52 mappings. The optional source check reads the pinned commit through Git, even after the working-tree files are removed; the third and fourth commands separately check the follow-up and third-pass manifests. Archived source and text preserve historical paths and status verbatim; they are provenance, not current execution instructions. Use an explicitly enabled external entry point for research.

The old external research fixture depended on the helper framework removed from Sleepy, so it must not assume the application repository still supplies that framework. Future external Android research-host builds must explicitly supply the required helper sources from this asset repository and integrate them in the external host. This is a dependency limitation, not a claim that the integration is already complete. Never restore the research framework to Sleepy to make the old entry point build.

**Publication boundary: Sleepy accepts production application changes and necessary regressions. Research entry points, protocols, reports, images, curves, coordinates and replay tools are published only in this asset repository, never injected into the default application source tree or build.**

[Scope, build and device verification](followup/validation/RESULTS.md): the final default build passed; five of eight device tests passed and three failed. Original thresholds and failure logs remain intact. This is not optical acceptance.
