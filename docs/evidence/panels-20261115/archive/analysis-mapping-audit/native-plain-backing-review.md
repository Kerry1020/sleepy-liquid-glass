# Native panel plain backing: source review and minimal proposal

**Proposal only. No native source was edited or built.** There is no existing
launch mode that clears the presentation scene's three glass triggers while
retaining the same parent and system Alert/Sheet path.

`-ReferenceStaticOptics` exports the bare image and public presentation context;
it does not hide scene content. `-ReferenceDockContent plain-scroll` does preserve
real ScrollViews while setting their inner text stack to opacity zero, but it
only runs under the separate SwiftUI TabView/navigation parent. Using that mode
for panels would change containment and omit the current panel presenters.

The reusable part is the existing opacity-zero layout-preserving pattern. In
`NativeStage.swift`, the three backing trigger controls are one `VStack` at
lines148–169, while the system `.sheet` and `.alert` modifiers are attached outside
it at lines197–213. A proposed static-only `-ReferencePanelPlainBacking` can hide
only that inner stack's drawing/accessibility while retaining its children,
spacing, intrinsic layout, outer stage and the native presentation modifiers.
Do not hide or make transparent the stage root or its hosting controller.

For deterministic triggering, use the already drawn `reference-title` UILabel
as a test-only relay under that flag, with proposed
`-ReferencePanelCarrier alert|sheet`. Its existing frame/appearance remains
unchanged. One tap sends a narrow command to the mounted `NativeStage`, which
sets its existing `showAlert` or `showSheet` Boolean. This adds no drawn control
and allows the test to capture the clean backing before requesting the actual
system presentation in the same run. Do not rely on an opacity-zero SwiftUI
Button remaining hittable, and do not use fixed-delay automatic presentation.
A guarded NotificationCenter message or injected command object is sufficient;
exact transport is an implementation choice still requiring compilation.

Keep the original `ReferenceViewController`, source canvas and layout function,
UIHostingController, heading, selectors, UITabBar, original Alert title/message/
roles and complete `NativeReferenceSheet` content, detents, indicator and tint.
Guard the new flag to external-input static `presentations` launches only. Reject
parent/scene switches. Existing default fixtures and source evidence stay intact.

Before enabling any new capture matrix, freeze the new native binary/source
identity, capture same-run clean before/after context and original-source export,
check both actual source footprints and plateau/blur support for residual trigger
paint, then measure realized public controller/foreground geometry and native
central optical contour/tangent invariance. The old Alert/Sheet coordinates are
comparison gates, not frames to force on the system. Keep every existing visibility
gate unchanged. New clean results form a distinct fixture condition because
removing the backing glass may change native material adaptation.

The paired-slope input proposals remain ineligible until those observations
exist. This review does not recover a physical lens, blur kernel or thickness.
Source paths, hashes, evidence locations, proposed guards and receipt requirements
are in `native-plain-backing-review.json`.
