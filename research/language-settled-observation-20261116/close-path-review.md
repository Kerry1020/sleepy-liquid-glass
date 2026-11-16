# Language menu close-path review

Read-only review of Sleepy baseline `ac646d9b11c9455690ea805f56270ff4cf4ba874` (PR #446). This note changes no runtime behavior and does not establish dismissal acceptance. #446 fixes integer carrier placement versus floating optical contours; no rendered exit-frame evidence establishes that it fixes the reported dismissal symptoms. No build, test run, device operation or new capture accompanies this review.

## Pinned product sources

Paths are relative to the application repository. SHA-256 values identify the reviewed file bytes.

| Source | SHA-256 |
| --- | --- |
| `app/src/main/java/com/lingion/sleepy/ui/component/liquidglass/GlassLanguageMenu.kt` | `b321e93c9250c6c07e8cff12efc62198ca31f4ed888d1c5877ec6b85e8db1f6c` |
| `app/src/main/java/com/lingion/sleepy/ui/component/liquidglass/LanguageMenuMotion.kt` | `40209fed12de60e9876fb17f876fd6ef1a6f16e5f0b21d043515109a1a6ba3f0` |
| `app/src/main/java/com/lingion/sleepy/ui/screen/mine/GeneralSettingsScreen.kt` | `9c6c4b64e748ea9140b4ac207aef2d9e3bdc93ae79d81b5089183f55ff096c5f` |

## What the code proves

On the normally animated close path in `GlassLanguageMenu.kt:368–380`, the close loop stops ticking as soon as `sourceReadyForHandoff(..., 1f)` succeeds, then restores the source window. `LanguageMenuMotion.kt:194–204` requires nearly opaque source content, nearly transparent material, and at most one physical pixel of painted-edge error. It does not require mathematical rest or exact geometry. No subsequent tick or exact-source snap is performed during that handoff.

`LanguageMenuMotion.kt:37,64–68` restores the original card to alpha 1. The popup replacement remains drawn with `motion.anchorContentAlpha` and the stopped geometry (`GlassLanguageMenu.kt:435–445`). It is retained until the source draw/submission callback completes (`:111–115,169–174,235–258`); completion removes the session and defers the dismissal callback by a frame (`:93–102`). Thus there is a stopped-motion handoff and a period of overlapping source/replacement ownership. Their anti-aliased edges may be composited twice, with up to the accepted edge mismatch. Whether that becomes a visible pause or border requires rendered-frame evidence. A HWUI commit callback is not a compositor presentation fence; the legacy/software fallback is explicitly only a posted draw callback.

## Why a rectangular border is not established

The morph supplies `Outline.Generic` from the union of two current contours (`GlassLanguageMenu.kt:512–528`). Its material uses `placementLayer=false` plus an explicit shape clip (`:421–429`). That does not disable the backdrop's default draw-time path clipping: `third-party/kyant-backdrop/src/commonMain/kotlin/com/kyant/backdrop/BackdropRenderOptions.kt:15–17` and `DrawBackdropModifier.kt:445–472` retain it. The front rim dispatches a Generic outline through `drawPath`, not the rectangular fallback (`app/src/main/java/com/lingion/sleepy/ui/component/liquidglass/GlassControlModifier.kt:262–268`). This is path-level evidence, not a GPU proof. Simply deleting clips is not a justified fix.

## Actual language-change boundary

`GeneralSettingsScreen.kt:96–106` stores a changed language immediately, then calls `Activity.recreate()` from `onDismissed`. Cancellation and reselecting the current language do not set that recreation flag. This adds a separate possible interruption after menu dismissal.

Existing `LanguageMenuMotionTest.kt:43–99` checks handoff state, opacity exchange and the visible-source threshold. `GlassLanguageMenuTest.kt:226–273` checks immediate selection and callback-after-popup-removal ordering, using the software-window rule at `:50–54`. Those component tests do not exercise the real settings screen's Activity recreation or establish hardware exit-frame smoothness. Test paths share the product's `app/src/test/java/com/lingion/sleepy/ui/component/liquidglass/` prefix.

## Minimum next GPU observations

Using the existing observation infrastructure, compare cancellation, reselecting the current option, and selecting another language. Observe source-card edge pixels and geometry immediately before restoration, during source/replacement overlap, and after popup removal. Correlate the final moving frame, source draw/submission, window removal, dismissal callback and any Activity recreation. Distinguish stationary waiting from missed presented frames; do not infer either from model ticks alone. Record edge changes against the same background before attributing a rectangular rim.

No new fixture is proposed here. Capture, analysis and any later comparison belong in the asset repository. The [existing expanded-menu GPU study](../control-regression-diagnostics-20261116/language-gpu/results/language-triplet-20261115T222128Z/README.md) is historical, failed its settled-geometry control, and does not observe this close sequence or establish exit acceptance.
