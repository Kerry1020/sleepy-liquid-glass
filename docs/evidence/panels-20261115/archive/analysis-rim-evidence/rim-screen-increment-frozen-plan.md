# Frozen screen-only incremental-floor mechanism probe

Status: frozen before decoding any output from the next screen-only-increment candidate. This is a declared bounded-reflection mechanism probe on public calibration inputs. It is not a new intensity fit, an accepted material, an independent test or evidence of native physical lighting equivalence.

## Single intervention and exact decomposition

The reference is the rejected `panels-alert-rim-bounded-20261115` light Alert and its corresponding `panels-alert-rim-bounded-history-20261115` light Alerts. Preserve blur8, genuine radius-dependent input, refraction60/profile1, all tint/brightness/saturation, shape, geometry and CPU side0/corner0/flat.06, shine.16 and minimum angular floor.08. Preserve the original depth bands, interpolation knots, per-pixel coverage and final output clamp. Do not add, select or fit any strength, exponent, exposure, light color, blend or threshold parameter.

Separate the unchanged original directional shine table `L` from its existing floored table `F=max(L,.08)` at each of the same eight nodes. Apply the existing angular interpolation separately to those two node tables. Let `A(turn)` be the original-table angular response, `F(turn)` the floored-table response, `D(edge,pixel)` the unchanged depth-band coverage response, and `coverage` the existing premultiplied alpha. The declared signals are:

```text
original = A(turn) * D(edge,pixel)
delta    = (F(turn) - A(turn)) * D(edge,pixel)
```

Retain the original additive operation and its arithmetic exactly, using the unmodified original table:

```text
glass += coverage * original
```

Replace only the additional floor's former `coverage * delta` addition, after the original addition, with the requested bounded response:

```text
glass += clamp(delta, 0, 1) * (coverage - glass)
```

`delta` is a scalar normalized lighting signal, not premultiplied by coverage a second time. It is computed from the difference of the two interpolated tables, not by applying `max(interpolatedA,.08)` after interpolation; the latter is a different intervention. The headroom is the existing premultiplied `coverage-glass`; neither encoded-RGB fitting nor a new gain multiplies it. Preserve the original final `min(glass,float3(coverage))` clamp. If original shine alone already saturates a channel, this probe does not claim to recover it. Require exact legacy behavior wherever delta is zero and for every non-opted-in role/theme; merely using a numerically similar rewritten original shine expression is insufficient.

Dark Alert stays on its original factory, including blur16, original rim and original input opt-in. Menus, regular controls, Dock and all non-Alert shine compositing stay unchanged. Sheet selection is a separately recorded control decision, described below. No parameters are retuned after candidate output is seen. A future different mechanism needs a new identity and frozen plan.

## Capture and provenance

Capture the same4 new-probe REST observations (coordinate/shapes×light×Alert/Sheet) and16 historical REST observations (fine_grid/color_stripes/tonal_blocks/synthetic_landscape×light/dark×Alert/Sheet). The six source inputs, source bytes, transforms, dimensions and carrier fixtures remain fixed. Use original750×1334px,375×667pt/dp,2px density and font scale1; actual attached Alert pane must remain[55,515,695,859]px and Sheet[16,635,734,1318]px. Use actual Window origins, measured layout/AX boxes, existing background-readiness and displayed-rest convergence checks. Retain rejected/unconverged captures, do not replace source inputs, and do not infer optical results from failed provenance.

Before decoding, save the candidate capture manifest, source/binary/build receipt and all capture-file hashes in a new predecode record. Baseline, original native, analysis plan, masks and previous124-point files are frozen in the companion JSON. The original baseline PNG files remain untouched. No image registration, shift, scaling, fitted contour or ROI adjustment is permitted. Decode original raw RGBA and ICC-normalized sRGB independently; require identical conclusions when tracks differ and retain actual color-transform actions. Full-display system-bar changes remain distinct from actual Window and visible App controls.

## Primary clipping and paired mechanism gates

1. Re-extract exactly124 original pixels: fixed shapes Alert left y307..<338pt (screen rows614..<676), at inset.25/.75pt (screen columns55/56). Preserve every pixel's native, body8, additive-floor baseline and screen-increment candidate RGB, with exact same-tangent8..<12pt shoulder samples (original insets8.25,8.75,9.25,9.75,10.25,10.75,11.25,11.75pt). No tangent trimming or mean-only substitute is allowed.
2. The new candidate's red255 count must be zero for each62-pixel row, and all three channels'0/255 counts must be reported. Native/body8 have zero255 there; rejected additive-floor has62 and30 red255 values. Report edge RGB, shoulder RGB and edge-minus-shoulder response separately. The shoulder must remain strictly RGBA-identical to the additive-floor baseline at each original sample. Loss of the plateau passes a clipping mechanism gate, not native-color acceptance.
3. In every other originally fixed straight, neutral and corner sample, retain per-channel0/255, any-channel and all-channel counts, plus pointwise newly clipped channels against the additive-floor baseline, body8 and native. An improved mean cannot conceal a new plateau. Native existing clipping is recorded, not universally forbidden. Any new unexplained saturation blocks a general clipping-success claim.
4. Preserve the fixed shapes neutral-top x140..<235pt .25/.75/1.25/1.75pt rows, including0 any255 from the bounded reference. Require exact original-Window RGBA equality to the additive-floor baseline across the existing neutral-top tangents and signed-distance range. Require identical raw RGB/smoothed/D1/D2 curves and peak location there, with no recentering. The original top shine arithmetic remains unchanged.

The strict top invariant applies to the fixed central neutral segment where the original light table is already above the floor and delta is zero. It does not incorrectly demand equality for every lateral top segment: the originally declared top_left/top_right tangents can cross angular floor regions and are separately retained as genuine changed measurements. Any supposedly delta-zero pixel that changes fails the invariant and must be investigated rather than excused by raster uncertainty.

## Body, dark and Sheet controls

- Light Alert actual deep80px rectangles and every originally declared unmasked body ROI must remain strictly RGBA-identical to the additive-floor baseline in the new4 and historical matrices. Keep the8px-eroded bounding rectangle only as a non-deep diagnostic; corner coverage does not become an exact normal-distance contour.
- Each historical dark Alert actual Window and visible App region must remain strictly RGBA-identical to the corresponding additive-floor historical capture and actual `panels-dark-scrim-20261115` reference. Full-screen system bars are reported separately.
- The independent Sheet10 experiment has not been accepted by this plan. Its cosine/response decision must be recorded in a separate immutable control-selection receipt before this probe's first output decode. If Sheet12 is retained, use the existing same-source12px-reference batches for strict controls. If Sheet10 is retained, use the completed same-source Sheet10 capture for each source/theme as its own strict unchanged control, recording its batch paths and hashes; this screen-increment probe must not silently attribute Sheet12→10 changes to Alert compositing. A missing matching Sheet control is reported as unavailable and prevents a Sheet-unchanged claim. It does not justify substituting another carrier or altering Alert thresholds.
- The Sheet decision may select the already captured10 or12 baseline according to the separately declared cosine analysis. It cannot alter Alert material settings or optical gates, select a favorable screen-increment result, or merge a Sheet10 outcome into Alert acceptance. Candidate metadata must state the actual choice.

## All fixed curves and regression reporting

Reuse the complete original straight segments, bins[-6,0),[0,2),[2,4),[4,12),[12,20),[20,24), neutral candidates, body ROIs, masked areas and all corner slices in `panel-probes-preparation/analysis-plan.json`. Keep original0.5pt raster spacing, sigma.75pt/seven-sample reflected smoothing and derivatives that never cross a masked gap. Corner derivative interpretation requires the original minimum16 contiguous clear original pixels. Report raw/smoothed RGB and D1/D2 separately, including whole fixed scans and previously retained inward-only diagnostics; do not change scoring scopes to hide regressions.

For new probes, compare screen increment against additive floor (the isolated compositing intervention), against body8 (whole rim stage) and native (observed response). Keep each source/edge/depth/channel, all foreground exclusions, all peaks and every failed visibility gate. For neutral top/left/right0..<2pt keep separate per-channel errors and the next2..<4pt shoulder band. No averaging across neutral segments can conceal expected side dimming.

The screen operation deliberately reduces additional brightening on already bright colors. At neutral sides it may produce far less lift than the additive-floor candidate, lose a positive local peak or worsen native RGB error. Report these outcomes. Do not treat red unclipping as permission to raise.08, tune a new gain, change body brightness or claim the side is matched. The original minimum-three-pixel half-height support gate stays fixed. Native neutral peaks currently have only two original pixels, so native FWHM remains unresolved; do not fit crossings into precise continuous taper or thickness claims. Bottom Alert/Sheet backing-context warnings and masked Sheet-top neutral exclusion remain unchanged.

For historical light Alerts, compare screen increment directly with the already captured additive-floor light reference to isolate this compositing change at constant blur8/rim settings. Also retain comparison with native and original factory for context, explicitly marking the latter as a combined blur+rim+composition outcome. Preserve each source separately, including stripes left and all corner depths known to regress in the previous candidate. Any worsened source/edge/depth blocks an all-background/all-rim-improved claim. No pooled winner, independent-test, production-page or motion-parity claim follows from these public REST calibrations.

## Decision labels

Report independently: provenance valid/invalid;124-point red-clipping gate pass/fail; delta-zero top invariant pass/fail; strict body/dark/Sheet control pass/fail/unavailable; all fixed per-source optical changes; unresolved native matching. Passing mechanism and controls permits the statement that this declared bounded incremental response removed the observed colored-side plateau. A native-appearance acceptance still requires the complete mixed/negative results to support it; no99.99% or final-parity assertion is preauthorized.
