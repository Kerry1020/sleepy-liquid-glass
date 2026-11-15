# Native clean panel fixture source receipt

Implemented only in the two authorized App files. **Not compiled, launched or
captured.** `native-clean-fixture-source.json` records before/after hashes and
source-only invariants; `.patch` contains the exact isolated delta. The two
`.before-*.swift` files preserve the complete pre-edit sources.

## Launch and trigger

Use the existing `ReferenceViewController` path with:

```text
-ReferenceScene presentations
-ReferenceBackground grid
-ReferenceInterfaceStyle light
-ReferenceStaticOptics
-ReferenceExternalInputFile <registered-input-id>.png
-ReferencePanelPlainBacking
-ReferencePanelCarrier alert
```

Use `sheet` in place of `alert` for a separate Sheet run. The existing external
loader still validates the source manifest, original PNG bytes, profile and
world geometry. New panel options reject missing/duplicate/unknown panel flags,
non-static launches, a scene other than `presentations`, missing external input,
Dock parent/content options, native size probes, and invalid carriers before
selecting a root. No scene or parent is silently substituted.

The original `reference-title` UILabel keeps its frame, font and text. Only in
this mode it receives a tap recognizer and AX value `panel-plain-backing:alert`
or `panel-plain-backing:sheet`. First capture the actual clean before context in
the same run. Then tap that existing label to request the selected system panel.
There is no automatic/timed presentation. `relay-requested`, the existing
`presentation/requested`, and `state-set` trace events share a request ID; actual
controller presentation geometry continues through the existing public-context
sampling. Requests during an active/unavailable presentation are logged and
ignored rather than toggling state or queuing a delayed command.

Only the original presentation trigger VStack gets opacity0, AX-hidden and hit
testing disabled. Its three original controls, spacing26 and layout remain in
source. The host root is not hidden or made transparent. Existing `.alert`,
`.sheet`, roles/messages, NativeReferenceSheet, detents/indicator, frame function,
external loader and parent installation compare byte-for-byte with the preserved
source sections. No UITests were edited.

Root still needs to add the narrow test launch/capture call, perform the unified
native build, freeze that binary and obtain clean before/after receipts. Check
both source sides and required plateau/blur support for residual paint, actual
controller/foreground geometry, and native central contour/tangent invariance.
The old polluted observations remain a separate rejected fixture condition; this
source change alone does not make the paired-slope proposal eligible and does
not establish any physical lens/blur/thickness result.
