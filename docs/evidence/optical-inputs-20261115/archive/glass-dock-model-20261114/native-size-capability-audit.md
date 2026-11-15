# Native size and full-action observation audit

Source-only audit recorded 2026-11-14T15:11:49.383479+00:00.

Read-only source/API audit and review of root-added opt-in size probe. This subagent created only the two audit reports; no source edits, build, tests, device/simulator actions or Git operations.

## Conclusion

The fixture can request real public width constraints and SwiftUI controlSize without adding a transform. The new REST methods can collect size capability evidence. This audit establishes neither distinct realized size levels nor optical/motion parity. Current video export and touch driver do not establish every-frame/every-millisecond complete-action equivalence. No dynamic matrix is authorized by this report.

## Separate the axes

- **body_size**: actual measured native body extent changed via supported public sizing under fixed content/layout baseline where possible; actual coupling retained.
- **layout**: parent/viewport/placement/traits/direction or proposal; request is not measured optical size.
- **content**: labels/count/domain/value/state or subtype; cannot substitute for real size support.

A width constraint can produce a genuine changed body extent, but the request alone is only layout input. Record actual coupled positioning and native child/lens/track/thumb extents; AX bounds can describe a hit target or wrapper. No scaleEffect, screenshot scaling or host transform creates an intrinsic/native style-size level.

## Family capability

### Toggle

UIKit UISwitch returns intrinsicContentSize; SDK says initWithFrame size is ignored. SwiftUI controlSize is a public environment request whose realized effect is unmeasured.

Current: small/regular/large environment opt-in; both SwiftUI Toggle and unchanged UIKit intrinsic switch observed. No width or transform added.

Status: one known intrinsic UIKit route; no measured distinct SwiftUI levels in this audit.

Layout: label/Spacer, stage placement, traits and RTL are layout; extra row width is not switch-body size.

Content: labels/state stay fixed in new REST probe.

Evidence: NativeStage.swift:76-90, NativeStage.swift:180-190, NativeStage.swift:302-323, UISwitch.h:44-46.

### segmented Tab

SwiftUI segmented Picker receives exact frame proposal; UIKit representable uses proposal.width and native intrinsic height.

Current: 160/240/320pt constraints applied separately to the two control bodies with unchanged three titles; AX and trace collection pending root run.

Status: public width route implemented; actual distinct native body extents and optical contour not established here.

Layout: stage parent remains min(420,windowWidth-40); width change can couple child alignment/position and must be recorded.

Content: First/Second/Third remain three fixed short titles; alternate count or long titles would be content, not size.

Evidence: NativeStage.swift:92-110, NativeStage.swift:335-355, main.swift:1664-1696.

### single Slider

SwiftUI Slider gets exact width proposal; UIKit representable uses proposal.width and intrinsic height. Native thumb may remain unchanged while rail/body width varies.

Current: 160/240/320pt constraints for both controls, initial value0.25, range0...1, fixed font/tint; sliderLayerProbe enabled for REST test.

Status: width route implemented; no realized dimensions measured by this audit.

Layout: same parent/world; proposed rail width, actual control bounds, actual track travel, thumb dimensions and origin must be separate fields.

Content: domain/value/label/ticks held fixed; adding discrete steps or labels is not body sizing.

Evidence: NativeStage.swift:112-124, NativeStage.swift:368-390, NativeReferenceTests.swift:95-118.

### paired/range Slider

Host composition of two genuine public scalar UISliders plus host-painted shared rail, routing and ordering constraints. Not an Apple range-slider subtype.

Current: ReferenceRangeScale supports1 or0.75, implemented as whole-UISlider CGAffineTransform after public native endpoint calibration.

Status: scale0.75 is transformed native control evidence, not a native controlSize or distinct intrinsic thumb level.

Layout: host desired rail follows bounds.width-40 and calibrated endpoints; host routing fixed at DOWN; record actual coupled geometry.

Content: lower/upper/domain are separate state/content configuration.

Evidence: NativeRangeReference.swift:4-34, NativeRangeReference.swift:199-217, NativeRangeReference.swift:220-305.

### Dock

standalone UITabBar uses public sizeThatFits for height; a separate production-like four-item SwiftUI TabView parent is available.

Current: standalone width is stageWidth+16 with fixed12pt external bottom gap; no new Dock size knob in this patch.

Status: no three-size Dock calibration in this audit; change viewport/parent only under same native parent/content identity and measure actual body.

Layout: standalone UITabBar and SwiftUI TabView/UINavigationController are different parent contexts; viewport/safe areas/placement changes are recorded layout coupling.

Content: three/four tab count and titles are content and cannot substitute for body-size levels.

Evidence: main.swift:1420-1513, main.swift:1664-1696, README.md:78-96.

### Menu

native Menu with inline five-language Picker; host anchor uses padding16 and radius24, selection label maxWidth180. No native popup-width API added or established here.

Current: original fixed composition only; new global controlSize environment could reach SwiftUI scene if explicitly launched there, but REST size methods target toggle/buttons only.

Status: popup small/base/large unsupported/unmeasured; anchor width and long strings are not proof of popup sizing.

Layout: anchor/viewport/direction are separate; popup may choose its own placement/size.

Content: same five language strings kept fixed for size experiments; changing language labels is content.

Evidence: NativeStage.swift:218-259, NativeStage.swift:180, README.md:943-987.

### Dialog / half-sheet

native alert and native sheet are separate subtypes; sheet uses public medium/large detents and visible indicator.

Current: existing system alert/sheet/menu buttons; no custom dialog-body size API or three-size calibration added.

Status: two sheet detents do not establish three dialog sizes; actual bounds/subtype must be recorded.

Layout: viewport, safe areas, presentation context and detent are supported layout/presentation conditions, with actual body change recorded.

Content: message/action count/text cannot replace a native size route.

Evidence: NativeStage.swift:148-168, NativeStage.swift:197-212, NativeStage.swift:276-299.

### Buttons

GlassButtonStyle, GlassProminentButtonStyle, plus circle subtype. Public SwiftUI controlSize small/regular/large exists in local SDK.

Current: same title/image/state/style under3 controlSize environment requests; fixed inherited16pt font retained.

Status: native environment route implemented; actual body sizes/visible contour/corners remain unmeasured by this audit.

Layout: same VStack spacing24 and same parent; fixed font means this is not a completely default-font controlSize comparison.

Content: Glass, Glass prominent and plus are distinct subtype/content identities; compare each across sizes rather than substituting one for another.

Evidence: NativeStage.swift:129-147, NativeStage.swift:180-190, NativeReferenceTests.swift:120-142, SwiftUICore.swiftinterface:7946-7991.

## Root-added probe review

No obvious type/API blocker found by source inspection; root must use its actual compiler result. The four width modifiers apply directly to Slider/Picker/representable bodies. Opt-in parsing validates the160/240/320 request registry; absent width/size stays nil. No new transform, custom thumb/material or timing override was added. UIKit UISwitch still returns intrinsicContentSize.

ControlSize is applied to the NativeStage Group; fixed16pt font remains inherited. This is a fixed-content/font environment experiment, not proof of default text sizing at each controlSize. The local SwiftUICore API exists, but each native subtype may ignore the environment. Equal measured switch bounds are equal samples.

The two REST methods launch fresh sessions, save AX/screenshot attachments and leave staticOptics false so the ordinary frame recorder runs. Their positive/finite rectangle checks only establish usable observations, not requested-width equality, size distinctness or optical contours. No gesture helper is called. Suggested minor hardening: finite rectangle checks in controlSize method, as already present in the width method.

## Full-action / all-frame limits

- **F1 (scope)**: The opt-in width code is a genuine public layout constraint, not a transform; actual distinct native body dimensions still require measurement. Evidence: NativeStage.swift:36-42, NativeStage.swift:103, NativeStage.swift:109, NativeStage.swift:118, NativeStage.swift:124.
- **F2 (measurement)**: The REST tests assert valid positive AX bounds, not equality to the requested width or three distinct optical body levels. Pass means collection completed, not sizing/parity passed. Evidence: NativeReferenceTests.swift:95-142.
- **F3 (measurement)**: controlSize is scoped as an environment on NativeStage Group and fixed16pt font remains. UIKit representables do not consume that environment. Equal realized switch bounds must remain equal samples. Evidence: NativeStage.swift:180-190, NativeStage.swift:302-323, NativeStage.swift:335-355, NativeStage.swift:368-390.
- **F4 (timing)**: CADisplayLink requests60Hz, records actual timestamps/intervals and capture brackets, and reports observer cost/truncation. It cannot establish every-millisecond or every physical display frame observation. Evidence: ReferenceTrace.swift:270-275, ReferenceTrace.swift:285-299, ReferenceTrace.swift:383-398.
- **F5 (capture)**: Video decoder scans all finite encoded sample PTS, then sorts them. PNG export requires explicit requested times and is selected-frame export; no all-decoded-frame pixel export exists. Raw movie + selected PNGs is not an all-frame pixel analysis. Evidence: inspect-video.swift:29-63, inspect-video.swift:66-103.
- **F6 (timing)**: Session/touches share uptime-relative trace clock and retain actual coalesced/delivery samples. No explicit video-PTS-to-trace anchor is implemented in reviewed fixture/scripts; manual simctl recording command alone does not provide exact phase mapping. Evidence: ReferenceTrace.swift:51-99, ReferenceTrace.swift:102-143, README.md:23-27, inspect-video.swift:46-63.
- **F7 (input)**: Public gesture helpers provide tap, hold and one-target straight drag; slow/fast raw requested velocities are not guaranteed achieved trajectories, continuous reversals, arbitrary acceleration, CANCEL or rapid bursts. Inspect actual delivered touch waveform. Evidence: NativeReferenceTests.swift:30-89, NativeReferenceTests.swift:1521-1530, NativeReferenceTests.swift:1638-1648, README.md:44-55.
- **F8 (input)**: export-touches complete includes ended and cancelled; successful release and cancellation must remain separate. Whole-action assessment also needs pre-DOWN rest, post-UP recovery and no clipped ending. Evidence: export-touches.py:38-55.
- **F9 (optics)**: Public model/presentation layer geometry and opacity do not reveal the complete native optical contour, masks, refraction shader or internal material alpha. Actual raw pixel evidence is still required. Evidence: ReferenceTrace.swift:300-365, README.md:920-936, README.md:980-984.
- **F10 (provenance)**: Local installed headers/interfaces are SDK27.2; deploymentTarget26.0 and README historical26.5 run do not certify a new run as26.5. Record session.os and independent selected runtime/build provenance. Evidence: project.yml:1-9, ReferenceTrace.swift:51-65, README.md:938-941.

## Minimum next steps

1. Run only the two new REST capability methods in a separate packet with exact source hashes, SDK/compiler/build identity, launch arguments, actual session.os/world/scale/traits and per-run IDs. Keep legacy source/run identities separate.
2. Offline classify each request using AX rectangle, actual native UIView bounds/transform, trace body/lens/track/fill geometry and full screenshot. Freeze size-distinctness tolerance above measurement uncertainty; equal realized bounds are unchanged/unsupported levels, never invented small/base/large.
3. Label axis body_size only after actual body extents vary under the same content baseline; preserve width/layout coupling. Freeze layout and content alternatives separately. Keep paired-range scale0.75 explicitly host-transformed.
4. Before dynamic width variants, derive fresh actual track/thumb anchors per size. Existing335pt mapping, threshold and quarter-value anchors are historical one-size measurements, not reusable universal coordinates.
5. For all-frame motion work, retain raw video and enumerate each encoded frame with original decode ordinal, PTS/duration/invalid status and pixels or streaming all-frame metrics. Preserve selected PNGs as derived previews, not substitutes. Record explicit video↔trace anchors and uncertainty.
6. Gate each full action on actual touch target/phase (including ended versus cancelled), rest beforeDOWN, full interaction, UP/CANCEL and recovery; inspect actual display/video gaps and trace truncation. Extend or atomically split with preserved originals when action exceeds a clip.
7. Keep REST calibration conclusions independent of motion, optical parity and all-background claims. Do not start the dynamic matrix merely because this source audit or two test methods pass.

## Provenance

API evidence was read from local iPhoneOS SDK27.2 headers/interfaces, not measured26.5 runtime behavior. Official online documentation fetch returned no readable content and is not used as evidence. Runtime OS/world/scale/traits must come from the new session and build receipt. Sources below are the exact bytes read for this report; root may subsequently edit them or compile a later snapshot.

| Source | SHA-256 |
| --- | --- |
| `/Users/kerrylee/.codex/worktrees/android-settings-glass-fixes/sleepy/tools/native-glass-reference/App/NativeStage.swift` | `fa66a5e37570cca07311677e50c28f1e6cec9e7be84e4d370a7f7070dfd48339` |
| `/Users/kerrylee/.codex/worktrees/android-settings-glass-fixes/sleepy/tools/native-glass-reference/App/NativeRangeReference.swift` | `95c1836ca2a9fdc18643b2a0df65914c8518044666ee5361179def7079b4f972` |
| `/Users/kerrylee/.codex/worktrees/android-settings-glass-fixes/sleepy/tools/native-glass-reference/App/ReferenceTrace.swift` | `fd7e74a0763ac4a6bd665698d733586b51db8470eeeff1d267023cfc46dd0988` |
| `/Users/kerrylee/.codex/worktrees/android-settings-glass-fixes/sleepy/tools/native-glass-reference/App/main.swift` | `1dbadf2d915a4a66b80e4b04d08daa516ab5b80f7656f2b496f7c4d9892bed9a` |
| `/Users/kerrylee/.codex/worktrees/android-settings-glass-fixes/sleepy/tools/native-glass-reference/UITests/NativeReferenceTests.swift` | `632d2adf6c65c607ce9b874e2352b14f42860347d2260a3d5640bb336f743355` |
| `/Users/kerrylee/.codex/worktrees/android-settings-glass-fixes/sleepy/tools/native-glass-reference/inspect-video.swift` | `4c1766e717ffe255f05be42068d27aa4ebfd80e9495905da4358db615be378cb` |
| `/Users/kerrylee/.codex/worktrees/android-settings-glass-fixes/sleepy/tools/native-glass-reference/export-touches.py` | `a3c77ddb5669df0394523621a51fcb5e3375e542e0a5cd3f5758abe0aacbb0e7` |
| `/Users/kerrylee/.codex/worktrees/android-settings-glass-fixes/sleepy/tools/native-glass-reference/README.md` | `a67cf4ce0c2452038c7d4a125edc9e2f6ba349204bd06555a71df8f7c9b08fa0` |
| `/Users/kerrylee/.codex/worktrees/android-settings-glass-fixes/sleepy/tools/native-glass-reference/project.yml` | `4a22ab059046d16fac604832e8fb84d16469fc771b18d80ad673e20cd9f9247e` |
| `/Applications/Xcode.app/Contents/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS.sdk/System/Library/Frameworks/SwiftUICore.framework/Modules/SwiftUICore.swiftmodule/arm64e-apple-ios.swiftinterface` | `c5910b74f2398fcb06f695379cb1b2e1c07700a2b73f89ef05cf09d2f58b3d3c` |
| `/Applications/Xcode.app/Contents/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS.sdk/System/Library/Frameworks/UIKit.framework/Headers/UISwitch.h` | `9ce71cfc7014255a33e6f971056c36a2353bd77b231b4a9f6436b019da27966c` |
