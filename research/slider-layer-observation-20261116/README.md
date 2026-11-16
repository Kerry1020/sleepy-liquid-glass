# Slider layer observation, 2026-11-16

[当前图文与证据索引 / Current illustrated evidence index](../../docs/current-evidence-20261116.md#slider-android)

Current integration checkpoint: The new observer and test compiled successfully in the [combined external build](../control-regression-diagnostics-20261116/host-integration-observed/README.md). Initial preparation statements below describe the earlier handoff. Runtime execution remains pending: no connected ADB device was available, and compilation is not geometry, material or optical acceptance.

This is a new, small external instrumentation study. It observes the actual production `GlassSlider` on a light flat128 background. It does not edit Sleepy, its renderer, its build configuration, the frozen 71KB optical fixture, or any old capture. The sources are injected only through an explicit external Gradle init script, following the existing [external host](../slider-android-host/README.md) convention. They use a separate `sliderlayerresearch` package and require Compose UI1.12.1.

There is no optical or geometry acceptance result here. At the initial source handoff, implementation checks had not built, installed or run an APK; the later combined build above records successful compilation separately. Device execution remains pending.

The subsequent [geometry audit](geometry-audit/README.md) explains the recorded 171×111px owner through integer-pixel quantization while preserving the original failed 0.10pt / 0.001 gates. It does not establish a product bug or raw layer translation. `full100` records business value 0.50064063, not a domain endpoint. Running this unchanged observer once remains the next device step.

## One bounded group

The new sampling plan deliberately differs from the historical six-pose, two-scene optical acquisition:

1. Start one production slider at quarter value on flat128; use LTR, font scale1, a335dp holder at(20,200)dp, and the actual device density.
2. After1600ms of the Compose clock, observe REST and save one composited display PNG.
3. Inject DOWN at the actual REST carrier center. After1600ms, observe HELD and save one PNG. Assert that the center hold has not published a value or completion.
4. Inject four MOVE events16ms apart over60dp using `moveTo(delayMillis=16)`. In Compose UI1.12.1 on Android, flushing each MOVE advances the main clock by16ms **before** delivering it. Observe after delivery without an additional clock advance. Save a PNG only for the fourth MOVE. Assert that the production callback received a changed value.
5. Inject CANCEL, advance1600ms and observe the final state. Assert no completion callback.

This yields seven JSON samples and at most three PNGs in one group, with no external input images, source fitting, motion override, stage retuning or repeated scene matrix. Requested pointer events, Compose time, wall uptime, value callbacks, semantics IDs and actual screen-coordinate transforms are recorded. The clock is synthetic; this is not a natural-motion trace. Screenshots follow a hardware frame-commit fence but are explicitly **not atomic** with the JSON sample.

The MOVE records include main-clock time before and after injection, the observed delta and an explicit post-delivery advance of0. A delta other than16ms fails the study. These samples describe the realized layers at the input-delivery boundary; they do not promise that an animation target received by that MOVE has already produced a later Compose frame. `waitForIdle` with `autoAdvance=false` and the HWUI fence do not deliberately advance the Compose clock. The separate1600ms REST/HELD/CANCEL settling advances remain unchanged.

Static timing correction before any execution: the first source draft paired `moveTo(delayMillis=16)` with `mainClock.advanceTimeBy(16)`, which would advance32ms per loop on this Android dispatcher. The latter call was removed. There is no acquisition from the earlier draft to reinterpret. Read-only1.12.1 bytecode inspection verified `TouchInjectionScope.move` → event-time advance, and `AndroidInputDispatcher.flush` → main-clock advance by event delta with `ignoreFrameDuration=true`, followed by event delivery and `runCurrent`. [bytecode-contract.json](bytecode-contract.json) binds the inspected test library class JAR. Android documents the event-delay API in its [TouchInjectionScope reference](https://developer.android.com/reference/kotlin/androidx/compose/ui/test/TouchInjectionScope).

## Coordinate contract

Each sample walks the complete public `parentCoordinates` chain from holder, isotropic owner and visual carrier. The chains include modifier coordinators and layout ancestors. It also enumerates `LayoutInfo.getModifierInfo().extra` for each distinct ancestor layout. Repeated modifier references are retained as references; each real `OwnedLayer` is read exactly once per sample by object identity. Coordinator-owned layers that have no modifier reference are included explicitly. Session object IDs remain stable across samples; renderer IDs are stored as strings.

The three transform records have different meanings:

| Field | Meaning |
| --- | --- |
| `raw_layer_transform` | Actual `GraphicsLayer` scale, raw translation, alpha, transform-origin fractions, effective pivot, layer size and coordinator placement. Its `matrix_without_pivot_or_placement` contains only raw scale/translation. |
| `pivoted` | The actual `OwnedLayer` underlying matrix, including pivot compensation. Its m41/m42 are **not** raw translation. A separate public local-to-parent matrix includes coordinator placement. |
| `total` | Public `LayoutCoordinates.transformToScreen(Matrix)` for that coordinator or tagged node, including all ancestor transforms and placement. |

Matrices retain the16 Compose values: row-major storage with row-vector mapping, `x'=x*m[0]+y*m[4]+m[12]`, `y'=x*m[1]+y*m[5]+m[13]`. For the supported2D layers, pivoted translation is `pivot + rawTranslation - scale*pivot`; local-to-parent additionally includes coordinator placement. Neither matrix is back-solved to manufacture raw properties.

The observer checks pivot/size consistency, placement versus `GraphicsLayer.topLeft`, pivoted matrix versus actual raw properties, placement-plus-pivoted versus public `transformFrom`, and total matrix versus public `localToScreen` basis/corner mapping. The fixed0.02px tolerance is only an instrumentation arithmetic consistency tolerance; it is not a product or native-parity threshold. Per-layer alpha and its ancestry product do not describe paint alpha, clipping or final optical opacity.

Unknown `OwnedLayer` implementations, changed reflection signatures, missing owner/carrier layers, duplicate ownership, unresolved modifier layers, cycles, detached nodes, nonfinite data and nonzero3D/rotation properties fail the test. There is no fallback to semantic bounds, nominal animation values or the first matching layer.

The runtime contract was checked against actual cached1.12.1 class files using read-only `javap`. [bytecode-contract.json](bytecode-contract.json) records class-JAR hashes and the verified field/method/bytecode contracts. The public transform API is documented by Android's [LayoutCoordinates reference](https://developer.android.com/reference/kotlin/androidx/compose/ui/layout/LayoutCoordinates). Private reflection is intentionally version-specific.

## Prepare and compile handoff

From the asset repository root:

```sh
python3 -B research/slider-layer-observation-20261116/prepare.py
python3 -B research/slider-layer-observation-20261116/prepare.py --check
```

Preparation verifies the exact two files in [source-pins.json](source-pins.json) and writes only `.local/preparation.json`. It refuses changed sources, symlinks, extra files, a changed receipt or overwriting an existing receipt. The source directory contains only the small test and observer; it does not copy the historical fixture/helper or large data.

A standalone explicit test-APK compilation command is:

```sh
GLASS_ASSETS=/absolute/path/to/sleepy-liquid-glass
SLEEPY_ANDROID=/absolute/path/to/sleepy
STUDY="$GLASS_ASSETS/research/slider-layer-observation-20261116"
"$SLEEPY_ANDROID/gradlew" -p "$SLEEPY_ANDROID" \
  -I "$STUDY/overlay.init.gradle" -PsliderLayerStudy="$STUDY" \
  :app:assembleDebugAndroidTest --offline --console=plain
```

For the parent task's single combined test APK, add this study's `sources/` as another external `androidTest.kotlin` directory and validate it against the same receipt/pins. The prior schema2 slider init script intentionally accepts exactly its own two frozen files; do not place these new files into that old generated directory or relax its pins. Keep the host's1.12.1 Compose UI dependencies. The new standalone init script verifies the resolved Compose UI versions without changing them. No main APK rebuild is required by this study's changes.

After the parent installs the resulting test APK, run only this class once, with these instrumentation arguments:

```text
class=com.lingion.sleepy.ui.component.sliderlayerresearch.SliderLayerObservationTest
glassSliderLayerObservation=true
glassSliderLayerRunId=<new unique run ID>
```

Use the actual installed debug test package and the host's `com.lingion.sleepy.SleepyRenderTestRunner`; confirm the component from the resulting test manifest. The test requires SDK33+ and an awake, hardware-accelerated foreground test window. It does not install or launch anything by itself from this source handoff.

Output is inside the target application's external files directory:

```text
slider-layer-observation-20261116/<run ID>/observation.json
slider-layer-observation-20261116/<run ID>/rest-display.png
slider-layer-observation-20261116/<run ID>/held-display.png
slider-layer-observation-20261116/<run ID>/drag-4-display.png
```

An existing run ID aborts before acquisition. Preserve failed output as evidence and use a new ID for any later attempt; never overwrite or relabel old acquisition. `status=observed` means only that this diagnostic and its consistency checks completed. It does not accept native shape, motion or material parity. The JSON embeds the complete output schema; each layer contains the raw/pivoted/total records and all identity references needed for downstream analysis.
