# Language observed terminal geometry

[当前图文与证据索引 / Current illustrated evidence index](../../docs/current-evidence-20261116.md#menu)

Current integration checkpoint: The generated terminal-observation test compiled successfully in the [combined external build](../control-regression-diagnostics-20261116/host-integration-observed/README.md). Initial preparation statements below describe the earlier handoff. Runtime execution remains pending: no connected ADB device was available, and compilation is not geometry, material or optical acceptance.

The subsequent [carrier-alignment fix](../language-carrier-alignment-20261116/README.md) addresses a separate half-pixel placement error. The [binary inventory](../control-regression-diagnostics-20261116/host-integration-observed/README.md#binary-inventory-after-pr-446) identifies the existing main/test APKs as historical baselines, not builds of that fix. This observer has no post-fix GPU result.

This asset-only derivative replaces the approximate readiness wait in the [C/U/C_restored/E fixture](../control-regression-diagnostics-20261116/language-gpu/README.md). It preserves the real pointer, real-time recomposer, original background, source draw gate, HWUI submission callback and 80ms display delay. It does not observe or claim mathematical motion rest.

The [first run](../control-regression-diagnostics-20261116/language-gpu/results/language-triplet-20261115T222128Z/gpu-triplet.json) failed exact row geometry: its first row moved from binary32 `566.01019287109375` to `566.0` even though both E screenshots were identical. [baseline-trigger.json](baseline-trigger.json) retains the original failure and numeric provenance. No frozen original, old fixture or old result is changed.

Existing semantics expose six visual fields and menu/row bounds, but no motion `isRunning`, velocity or finish event. Handoff `motion` persists while an expanded menu is stationary. This fixture therefore uses the explicit name **observed-terminal-geometry**.

Each main-thread observation traverses the semantics tree once. All six visual fields must exactly match the terminal target: scaleX/scaleY/alpha/contentAlpha are `1f`; translation X/Y come from the existing source anchor's center/top, the observed menu size at unit scale, public window-to-screen offset and density. This target applies to the unchanged centered 362dp-wide, 180dp-top fixture. It intentionally does not emulate the production inset/clamp algorithm; a changed/constrained layout that cannot match this target times out for review.

The exact visual vector, menu Rect, all five row Rects and handoff state must then repeat consecutively at least four times and span at least **350ms of actual uptime**. Polls are separated by up to 50ms of real sleep, within a 5000ms polling deadline. Every observation records time, six actual/target fields, all menu/row coordinates, raw Float bits, matching status and streak/window length. Missing semantics, nonterminal fields or any exact change reset the streak. Timeout writes partial evidence and throws; it never captures a substitute successful E sample. Main-thread scheduling can delay a read beyond the deadline, which is rejected rather than accepted.

The original C/U/C_restored captures precede natural opening, and E follows that observation window. E still has a second capture after 350ms, and the original exact stable/late row assertion and exact ROI pixel controls remain. The original `>=6` delta and `<=5` row-distance predicates are unchanged. This sampling repair neither promises JUnit green nor validates a material oracle; the earlier first-row E−U result was also below 6, and a negative material control remains absent.

Prepare and check from this asset repository:

```sh
python3 research/language-settled-observation-20261116/prepare-fixture.py
python3 research/language-settled-observation-20261116/verify-static.py --record
```

The generator reads only the pinned, already prepared parent source (`ca4d1638…`) and frozen original (`94b48872…`) in the asset repository. It creates exactly one new alias under this study's `prepared/sources`. Eight original sections are checked byte-for-byte, including the C/U/E capture stage, pixel algorithms, predicates, GPU fences, pointer helpers, real-time fixture and background.

Initial preparation build handoff (the later successful compilation is recorded above; device execution remains pending):

```sh
./gradlew -I /absolute/path/to/sleepy-liquid-glass/research/language-settled-observation-20261116/overlay.init.gradle \
  -PlanguageSettledObservationSources=/absolute/path/to/sleepy-liquid-glass/research/language-settled-observation-20261116/prepared/sources \
  :app:assembleDebugAndroidTest --offline --console=plain
```

The overlay is inert unless explicitly selected, rejects a source root inside Sleepy, pins the receipt and output hash, requires exactly one Kotlin file and checks alias uniqueness. It uses a separate property, so the independent slider or previous language overlays need not be edited.

Instrumentation handoff after verifying installed main/test APK identities:

```sh
adb -s DEVICE shell am instrument -w -r \
  -e class com.lingion.sleepy.ui.component.AssetLanguageObservedTerminalGeometryTest#closedUnpaintedAndExpandedGpuTriplet \
  -e languageSettledObservation true -e languageRunId NEW_UNIQUE_RUN_ID \
  com.lingion.sleepy.debug.test/com.lingion.sleepy.SleepyRenderTestRunner
```

Device output is the target app external-files directory under `language-settled-observation/NEW_UNIQUE_RUN_ID/`, with eight PNGs and `gpu-triplet.json` on completed sampling, or a partial report on timeout. Reusing a run directory fails. Pull results only into this asset study and verify device/host hashes. Static preparation checks do not establish Kotlin/Gradle compilation, device behavior, temporal control validity or optical acceptance.
