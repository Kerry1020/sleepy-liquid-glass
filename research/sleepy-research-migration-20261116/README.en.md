# Research moved out of Sleepy

[简体中文](README.md) · [File identities and destinations](SOURCE-MAP.json) · [External Android research entry point](../slider-android-host/README.md)

This archive preserves 52 research files (1,774,394 bytes) from Sleepy commit `5c604e83cc5ccbc6c5ab622568eae0c99265dfc4` before removing them from the application repository. It also covers leftovers from earlier merged work. PR #442 itself already contains only four production files and four JVM regression files.

![Previously published standalone sample on four backgrounds; no new optical experiment was performed](../../docs/images/sample-backgrounds-light.png)

The figure reuses the standalone sample with its existing [image provenance](../../docs/images/sources.json). Migration changes neither runtime behavior nor optical acceptance.

## Scope and preservation

The selection contains 17 native-reference project files, eight research-only Android capture or diagnostic entry points, seven research/handoff reports, and 20 embedded extraction/validation archive files. The application retains a short runtime integration README.

Fifteen files reuse identical published bytes; 37 missing versions are stored under `sources/`. No frozen source is overwritten. Five old native-reference files differ from the previously exported slider fixtures, so both versions remain available. The map records each source Git blob, SHA-256, size and destination.

Production runtime, deterministic host regressions, meaningful GPU behavior/sampling regressions and their shared helpers remain in Sleepy. Earlier November 9 design documents and attribution audits are outside this migration. APKs, build caches, DerivedData, traces and device data are excluded.

```sh
python3 research/sleepy-research-migration-20261116/verify.py
python3 research/sleepy-research-migration-20261116/verify.py --source /path/to/sleepy
```

The optional source check reads the pinned commit through Git, even after the working-tree files are removed. Archived source and text preserve historical paths and status verbatim; they are provenance, not current execution instructions. Use an explicitly enabled external entry point for research.

**Publication boundary: Sleepy accepts production application changes and necessary regressions. Research entry points, protocols, reports, images, curves, coordinates and replay tools are published only in this asset repository, never injected into the default application source tree or build.**
