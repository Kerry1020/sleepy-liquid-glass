# Predecode implementation clarification and Sheet control receipt

Status: declared before reading any new screen-increment output pixels. The main frozen plan remains byte-unchanged. Its SHA256 is `98ad62d4c92c43a60b8bca15a76ffb2b2faf01821155af24592ff90628ecfb19`.

## Nonnegative headroom clarification

The implementation owner explicitly confirms that the following headroom clamp is intentional:

```text
glass += clamp(delta, 0, 1) * max(coverage - glass, 0)
```

This supersedes only the main plan's unconstrained `(coverage-glass)` headroom term. It prevents the newly introduced floor from applying a negative change when the original inherited additive shine has already exceeded a channel's coverage. It adds no intensity, width, exposure or fitted parameter. The definition of delta, eight original/floored nodes, old additive shine expression, delta-zero/default preservation, original coverage and final output clamp are unchanged. The actual candidate identity is therefore **screen-only increment with nonnegative headroom**. Preserve both formulas in the provenance rather than silently editing the original frozen text.

The parent reports a two-vec4 `uShineFloorLit` separation for the incremental angular signal, with the exact legacy expression retained in non-opted-in and zero-delta branches. This is an implementation report, not yet a decoded-pixel proof. Build/source receipts and actual invariant tests must accompany capture handback. No output-dependent parameter selection occurred.

## Sheet10 selection and comparison scopes

The parent selects the preceding radius10 candidate for the next matrix, preserving its actual existing light Alert additive-floor reference and two light Sheet10 observations at `panels-sheet-radius10-20261115`. Save that complete matrix/capture/source receipt as the new4 same-source Sheet reference before decoding screen-increment output. Require strict actual-Window and visible-App equality for those two Sheet10 controls. Existing bounded-rim Alert images remain the original primary Alert reference; if the radius10 Alert images are also used, first prove their actual Windows are identical to that reference.

For the16 historical observations:

- Four dark Alerts and four dark Sheets retain their original factory controls and require strict actual-Window/visible-App equality against `panels-dark-scrim-20261115` (and the corresponding bounded-rim historical images).
- Four light Sheets at radius10 have no same-source historical radius10 strict reference. Their native and previous radius12 comparisons are explicitly **combined radius-response observations**, not strict zero-difference controls and not the effect of Alert floor compositing. Record the missing like-for-like strict reference; do not claim eight historical Sheets unchanged.
- Historical light Alerts still isolate screen-only incremental composition against their like-for-like bounded-rim light Alert references. All fixed straight/corner/body/clipping data and regressions remain mandatory.

The selection is an orthogonal control choice. It cannot alter the frozen Alert strength,geometry,124-pixel clipping gate, delta-zero top equality, body controls, per-source curve reporting or unresolved-width interpretation. No native appearance acceptance follows from either this receipt or a boundedness proof.
