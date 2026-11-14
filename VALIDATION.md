# Initial experimental source validation

Validated on 2026-11-14 before initial public publication:

- JDK 17 target, Android SDK 37, installed Gradle 9.8.2, no project-local SDK paths committed.
- `:runtime:assemble :runtime:testAndroidHostTest :sample:assembleDebug`: passed.
- Runtime host tests: 38 tests across five classes, zero failures/errors. These cover numerical motion endpoints, parent motion, foreground selection and hysteresis; they do not prove complete visual parity.
- Sample APK installed and launched on a physical PKX110 / Android API 36. Host and installed APK SHA-256 matched. Four synthetic backgrounds (grid, saturated stripes, contrasting blocks, layered hills) were inspected in light and dark themes, with direct and held motion input. The pane visibly responds to the recorded background. A dark-theme title contrast issue found during inspection was fixed and the sample rebuilt.
- Imported runtime manifest: all 34 source/resource hashes match the recorded Sleepy commit. Official backdrop baseline: 30 of 34 files unmodified; four locally documented adaptations.
- Source scan excludes credentials, developer-local paths, build outputs, APKs and device captures.

The initial build exposed and corrected a graphics-layer CompositingStrategy import in the independent backend. The app still uses its separate existing backend. No iOS native equivalence, every-frame timing match, full production-control extraction, API 26 device acceptance, package release or Maven distribution is claimed.

No hosted workflow is configured for this initial source publication. Contributors can run the focused commands in README and CONTRIBUTING; a successful source build is separate from device optics acceptance.
