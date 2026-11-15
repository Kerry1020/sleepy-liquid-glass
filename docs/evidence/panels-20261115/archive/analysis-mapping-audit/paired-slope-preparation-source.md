# Paired-slope native capture source preparation

Only `/Users/kerrylee/.codex/worktrees/android-settings-glass-fixes/sleepy/tools/native-glass-reference/UITests/NativeReferenceTests.swift` was changed. The new `testPanelPairedSlopeMappingFeasibility` wrapper fixes four already requested paired-slope IDs (a20 normal/reversed, a24 normal/reversed), light appearance, calibration split, and Alert only. It invokes the same private `panelPlainBackingFeasibility(inputIDs:carriers:)` cycle as the existing clean-backing test.

The existing `testPanelPlainBackingFeasibility` wrapper fixes the same two original IDs in the same order and the same Alert/Sheet carrier order, retaining four fresh launches. Re-expanding the extracted helper with those constants reconstructs the entire previous function and entire previous UITest file byte for byte. The original loader, launch helper, native-control visibility waits, actual title tap, settle duration, screenshot/AX phases, same-presentation repeat spacing, dismissal controls, trace payloads, geometry assertions and process termination are unchanged. The active XCTest case name still comes from its original wrapper; the helper does not introduce a new run identifier.

Each wrapper is expected to produce four fresh sessions and16 screenshot/AX pairs when later authorized and run. This is source intent only, not an executed result. The manifest loader still requires exactly8 entries; the separate acquisition plan must define the compatibility entries, and only the fixed selected IDs are launched. No PNG or oracle was opened by this task.

Full before/after source hashes, all native Swift/project/plist source hashes and reconstruction checks are in the companion JSON; the narrowly scoped edit is in the companion diff.

- Before full UITest SHA256: `84459663646a8abbd0a81d3138964f7d705ad2f0f2ec772db9399120de483790`
- After full UITest SHA256: `27184ef46d507cd9d8324c7e4d0fa6f205dc8774fb29edcdced73d1d35c1febb`
- Reconstructed old function SHA256: `df732b82611074bb7cfcf50df92ec748ab40518cd573a603e836e330df112a51`
- Extracted helper SHA256: `fc54d22a6e62adc855218af297b77efba86c918dffd076c5e85508966e364d25`

No compiler, build, XCTest execution, device/simulator operation, capture, image decode or Git command was run. New plan/source-footprint/tangent gates remain to be frozen before acquisition is authorized. Old runtime/ICC observations were not reinterpreted, overwritten or used to claim the new entry point passed.
