# External Android Slider research host

This opt-in entry point prepares one frozen optical fixture and its complete archived helper file for Sleepy's existing `:app` instrumentation host. Research source generation stays in this asset repository. It does **not** provide an independent runtime API or a standalone Android test application.

The selected test needs Sleepy's `GlassSlider` adapters, theme providers, AndroidJUnit/Compose dependencies and `SleepyRenderTestRunner`. The asset overlay supplies the complete capture/geometry helpers in the isolated `com.lingion.sleepy.ui.component.assetresearch` package. Its `OpticalCaptureWindow` is distinct from Sleepy's retained screenshot helper. It remains an SDK 33+ optical research fixture. Compiling it does not establish optical parity or execute a capture.

![Existing native/Android six-pose Slider comparison](../../docs/design/evidence/glass-slider-star-20261115/figures/six-pose-comparison.png)

This is an existing real comparison, not output from this new entry point. It preserves visible differences for investigation; **the material has not passed optical acceptance**. The entry point introduces no stage filter or fixture behavior changes. Existing opt-in runs may acquire six poses; a bounded stage selection would require a separate declared patch.

## Prepare and verify

Run from this repository's root:

```sh
python3 -B research/slider-android-host/prepare-overlay.py
python3 -B research/slider-android-host/prepare-overlay.py --check
python3 -B research/slider-android-host/prepare-overlay.py --self-test
python3 -B research/slider-android-host/test-prepare-overlay.py
python3 -B research/slider-android-host/verify-static.py --record
```

Preparation selects only `NativeSliderOpticalWorldRenderTest.kt` from the two Android exports in `../slider-fixtures/SOURCE-MAP.json`. It also selects the complete `GlassOpticalCaptureFixtures.kt` from `../sleepy-research-migration-20261116/followup/SOURCE-MAP.json`. Both maps, source commits/blobs, byte counts and source SHA-256 values are pinned before transformation. `GlassSliderRailEndpointRenderTest.kt` is not copied or injected. Frozen fixture and archive files remain read only.

The helper changes only its package declaration. The generated fixture keeps its original package, changes its one class declaration to `AssetNativeSliderOpticalWorldRenderTest`, adds 8 explicit import aliases and replaces the corresponding complete identifiers. Alias references bind directly to the asset helper even when Sleepy has a same-named type. Reversing those declared edits must reproduce each original byte for byte; thresholds, capture methods, stage scheduling and fixture behavior remain unchanged.

| Imported helper | Fixture reference count | Explicit alias |
| --- | ---: | --- |
| `OpticalBackground` | 3 | `AssetResearchOpticalBackground` |
| `OpticalCaptureBackground` | 1 | `AssetResearchOpticalCaptureBackground` |
| `OpticalLayoutGeometry` | 14 | `AssetResearchOpticalLayoutGeometry` |
| `OpticalCaptureWindow` | 3 | `AssetResearchOpticalCaptureWindow` |
| `saveOpticalPng` | 6 | `assetResearchSaveOpticalPng` |
| `awaitOpticalBackgroundScreen` | 2 | `assetResearchAwaitOpticalBackgroundScreen` |
| `awaitOpticalSurfaceScreen` | 1 | `assetResearchAwaitOpticalSurfaceScreen` |
| `opticalRegionMetrics` | 2 | `assetResearchOpticalRegionMetrics` |

The schema2 generated sources and receipt live under ignored `.local/v2/`:

```text
.local/v2/preparation.json
.local/v2/sources/com/lingion/sleepy/ui/component/AssetNativeSliderOpticalWorldRenderTest.kt
.local/v2/sources/com/lingion/sleepy/ui/component/assetresearch/AssetGlassOpticalCaptureFixtures.kt
.local/v2/static-verification.json
```

The script is idempotent for matching output and refuses to overwrite a modified or incomplete existing overlay, a changed receipt, extra files or symlinks. If regeneration is needed, remove only `.local/v2/`. The old `.local/sources` and its schema1 receipt remain untouched. Do not copy generated sources into the Sleepy repository.

## Explicit Gradle invocation

Set absolute paths for the asset repository and an existing compatible Sleepy checkout. The source directory must be outside that checkout:

```sh
GLASS_ASSETS=/absolute/path/to/sleepy-liquid-glass
SLEEPY_ANDROID=/absolute/path/to/sleepy

"$SLEEPY_ANDROID/gradlew" -p "$SLEEPY_ANDROID" \
  -I "$GLASS_ASSETS/research/slider-android-host/overlay.init.gradle" \
  -PglassResearchSources="$GLASS_ASSETS/research/slider-android-host/.local/v2/sources" \
  :app:assembleDebugAndroidTest
```

Both `-I` and `-PglassResearchSources` are explicit. A normal Sleepy build does not load this init script and does not inject any asset sources. No host Gradle file, source file, dependency, CI configuration or test discovery setting is changed. When opted in, the script requires exactly the two pinned Kotlin files and the complete pinned schema2 receipt, rejects symlinks, then attaches their directory to `androidTest.kotlin.srcDir` for AGP's built-in Kotlin support. It checks that the test alias is unique across `:app` source sets and that only the generated helper declares the reserved research package.

The command above builds instrumentation only. A later device run must explicitly filter the aliased class, for example by adding these arguments to the same `-I`/`-P` invocation:

```text
:app:connectedDebugAndroidTest
-Pandroid.testInstrumentationRunnerArguments.class=com.lingion.sleepy.ui.component.AssetNativeSliderOpticalWorldRenderTest
```

The fixture's existing opt-in instrumentation arguments and source-image preparation still apply; this entry point does not enable them automatically. Keep device capture and build verification separate from static preparation.

## Frozen provenance

| Item | Identity |
| --- | --- |
| Sleepy source commit | `db1e2470db900d4642b27339c9cef31523ab75f3` |
| Original source | `app/src/androidTest/java/com/lingion/sleepy/ui/component/NativeSliderOpticalWorldRenderTest.kt` |
| Original Git blob | `9d534052fedc25c069cea4fc2f2b7924dbbaba90` |
| Original bytes | `71695` |
| SOURCE-MAP SHA-256 | `4743df6a03b68f30fe5f0071b9d23a23aa5db6042696e60c5cf063cfa9227032` |
| Original source SHA-256 | `1735702b83f009b1bfe2e01af82571b14017edb5f1dec851916b170a978cdb5e` |
| Fixture overlay SHA-256 | `4e25fe39264656134a48958bdd49aeb1506f17815c8610d2de4219042e52f360` |
| Helper source commit | `d38e9d1a92adcde69264bdd50313948bdd29ab0e` |
| Helper original Git blob | `ec3922c4d1651ee5507f1b394b208cd9957c8d9d` |
| Helper original bytes | `30049` |
| Helper SOURCE-MAP SHA-256 | `1bf6f7e90a487470713c86bbc9da0183461198bcf5619d9633c9f876cc8d31d3` |
| Helper original SHA-256 | `3bcee1b8b7d2d4f1d6e452f7ecd8dfa75e9e65329c40dfa7eff3436b9850d8d0` |
| Namespaced helper SHA-256 | `eee6b8de60ca26cc9845dd3ea9a6ecf8b443c8f4bd1cb05589afdd17c7852c8d` |
| Complete schema2 preparation receipt SHA-256 | `f0a77f707968225ebe00c8c55f8ece3fd9aa298c968584456386c21d40818b37` |

Both source-map hashes are pinned. A provenance update requires a reviewed change to the generator and init script pins. The generated receipt separately records both original identities, every deterministic transformation and reference count, output bytes/hashes, and successful inverse byte equality.

## Validation boundary

`verify-static.py --record` writes the v2 result only to `.local/v2/static-verification.json`. It runs preparation checks, inverse-byte contracts, changed/duplicate input rejection and isolated filesystem tests for missing/extra/modified/symlink outputs. It verifies that the Gradle receipt and two output pins match the generator. It does not claim that Gradle configuration, Kotlin compilation, installation or a device capture has passed. Those require a separate explicit host run. The checked-in `static-verification.json` is retained as historical schema1 evidence.

[static-verification-v2.json](static-verification-v2.json) publishes the current static result with the generated source-root path made repository relative. Its publication metadata records the original local report hash; the generated Kotlin and preparation receipt hashes are unchanged.

The current host uses AGP 9.5.1 built-in Kotlin. The `AndroidSourceSet.getKotlin()` and `AndroidSourceDirectorySet.srcDir(Object)` signatures were inspected in its installed Gradle API JAR. Android's [built-in Kotlin migration guide](https://developer.android.com/build/migrate-to-built-in-kotlin) documents the Kotlin source-set requirement; Gradle's [init script documentation](https://docs.gradle.org/current/userguide/init_scripts.html) documents `-I` and `beforeProject`.

## Historical single-file host build checkpoint, 2026-11-16

[host-build-20261116.json](host-build-20261116.json) records a real opt-in build against clean Sleepy commit `d38e9d1a92adcde69264bdd50313948bdd29ab0e`: `:app:assembleDebug :app:assembleDebugAndroidTest --offline --console=plain` completed successfully in34s (100 tasks,14 executed). The receipt binds the external alias, init script and actual arm64 application/test APK hashes. No research source, Gradle configuration or CI file was added to Sleepy.

That checkpoint used the older single-file overlay while the host still contained complete helpers. It does not validate this schema2 two-file integration or the current host after helper migration. The schema2 entry point now has a separate [combined external-host build receipt](../control-regression-diagnostics-20261116/host-integration-20261116/build.json): its two pinned sources and the separately pinned language diagnostic compiled against clean Sleepy `e935c5e3` in 9.232s. No device installation or execution of these new entry points followed; this is compilation evidence only.

The first post-build recorder assumed a nonexistent `app-debug.apk`; this failed after Gradle had succeeded. The corrected receipt selected the real arm64 output from AGP metadata without rebuilding. This is build evidence only. The earlier static receipt remains a static result, and this build receipt does not claim installation, capture or optical acceptance. The separately recorded [Android G-response study](../slider-android-response-20261116/PLAN.md) tracks later device work.
