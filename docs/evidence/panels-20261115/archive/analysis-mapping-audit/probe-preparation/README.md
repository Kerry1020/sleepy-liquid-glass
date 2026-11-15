# Paired-slope Alert inputs — unmeasured, ineligible proposal

The four PNGs are exact deterministic input assets, **not measured optical data**.
They are intentionally not registered in a loader or capture matrix. The proposed
center source footprint overlaps the native `show-sheet` glass button, and the
native central optical contour/tangent invariance has not been established.
The proposal must not be used to claim a recovered normal/tangential map.

The anchor is fixed at `(187.5,257.5)pt`, with `a20/a24`, slope `.25`, support
`u=-64..<128pt`, and gray60/190 normal/reversed contrast. Raster membership is
analytic at pixel centers; exact row spans, centroids, masks, RGB/PNG hashes, and
the reused persisted sRGB profile are recorded in `oracle.json` and
`proposal-manifest.json`. Output rows remain `d=.25..19.75pt`; the last one is
only .25pt above the existing expanded title mask. No original ROI or gate was
moved to make the new center appear eligible.

`before-alert-backing-audit.json` compares only the two existing nonperiodic
calibration sources with their native before-Alert contexts in a fixed corridor.
These differences expose fixture content; they do not certify that hypothetical
new source pixels would remain untouched. `geometry-eligibility.json` distinguishes
native AX, native optical uncertainty, and a CPU-only Android cubic calculation.

No native/Android source, build, device, Git operation, optical-output image, or
heldout image was changed or used by this preparation script.
