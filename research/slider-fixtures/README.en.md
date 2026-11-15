# Slider research fixtures: fixed-source export

[简体中文](README.md) · [Per-file source and SHA-256 map](SOURCE-MAP.json) · [Checksums](SHA256SUMS) · [Calibration report](../../docs/glass-slider-star-calibration.md)

This directory exports Git-tracked author sources and project files from Sleepy Android commit **`db1e2470db900d4642b27339c9cef31523ab75f3`**. It uses that fixed Git tree rather than working-tree content. All **19 files, 566,220 bytes** retain their original paths and bytes: 17 native-reference project files and two Android instrumentation sources. `SOURCE-MAP.json` records every source/export path, Git mode, blob OID, byte count and SHA-256.

![Existing public comparison: native and Android r2 at six settled held poses](../../docs/design/evidence/glass-slider-star-20261115/figures/six-pose-comparison.png)

The figure reuses published evidence; no new screenshot was captured. r2 remains an unaccepted checkpoint with retained failures. Publishing these fixtures establishes neither optical acceptance, independent-backend parity, nor a complete native control adapter. Scope and failures remain in the [calibration](../../docs/glass-slider-star-calibration.md) and [six/eight-point reports](../../docs/glass-slider-holdout-validation.md). Seven-point data remain unconsumed.

## Native reference project

The complete tracked [tools/native-glass-reference](tools/native-glass-reference/README.md) project includes `App`, `UITests`, a shared Xcode scheme, project files and the author's capture/checking scripts. The Slider shares its application, tracing and test host, so the complete native project is preserved, including other pre-existing reference cases. Its nested README is the unmodified document from the fixed commit and retains its historical directory context.

This is a research observation application, not a runtime component. Running it requires macOS, Xcode and the corresponding iOS 26.5 native-reference environment. The tracked Xcode project is included; `project.yml` declares an iOS 26.0 deployment minimum. XcodeGen is only needed when changing that yml and regenerating the project. Supply source inputs and capture/output directories in the actual research environment as documented. No screenshots, videos, traces, DerivedData or build outputs are copied here, and this export performs no build or acquisition.

## Android host dependencies

The original `app/src/androidTest/java/com/lingion/sleepy/ui/component/` paths contain:

- [NativeSliderOpticalWorldRenderTest.kt](app/src/androidTest/java/com/lingion/sleepy/ui/component/NativeSliderOpticalWorldRenderTest.kt): external source worlds, fixed shape/flat pairs, mappings and original-pixel capture.
- [GlassSliderRailEndpointRenderTest.kt](app/src/androidTest/java/com/lingion/sleepy/ui/component/GlassSliderRailEndpointRenderTest.kt): single/range rail endpoints and held-state observations.

These files require the corresponding Sleepy Android application instrumentation host, Gradle/Compose test dependencies, `SleepyThemeProvider`, `LocalUiStyle`, and production `GlassSlider`/`GlassRangeSlider` and `GlassHost`/`GlassBackground` adapters. Both sources require API 33+. Those application dependencies are not ported here, and neither test is registered with this repository's runtime or sample builds. They are not a public standalone Compose Slider API.

## Integrity and continuing research

From this directory:

```sh
shasum -a 256 -c SHA256SUMS
```

A machine holding the source Sleepy repository can also compare `git show db1e2470db900d4642b27339c9cef31523ab75f3:<source_path>` against the export. The map retains all paths and blob OIDs. Scoped `.gitattributes` preserves SHA-bound source bytes and historical whitespace without modifying source content.

This export moves research source ownership and navigation only. It changes no material, runtime provenance, theme, layout, or acceptance conclusion. The six existing evidence packets remain under [docs/design/evidence](../../docs/design/evidence) and are not duplicated. A new color-response acquisition still requires its separately frozen protocol; the presence of these fixtures is not a new capture or validation result.
