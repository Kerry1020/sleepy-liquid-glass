# Next stage: dynamic controlled shapes — draft v4

Status: **protocol proposal only, not frozen, generated, captured, or validated**. Complete and preserve the current static experiment before starting this stage. This draft does not modify the product, generate inputs, operate a device, decode test outputs, or establish native/Android parity. Exact v2 and v3 bytes/hashes are preserved in `protocol-history/` before this amendment. The v4 checker verifies protocol math and MD/JSON consistency only; it does not implement or validate the future dynamic tracker. The accompanying JSON is the machine-readable plan; implementation/source hashes and capture capability measurements must be registered before test capture.

The aim is to follow known internally multicolor circles, equilateral triangles, five-point stars, and asymmetric special polygons as a genuine native glass surface approaches them, passes over them, and leaves them. Measure visible shape changes and the native selected lens separately. Do not infer native renderer internals, physical IOR/thickness, or universal per-millisecond equality from these observations.

## Two experiments that must remain separate

| Arm | What moves | What it can establish | What it cannot establish |
| --- | --- | --- | --- |
| T: controlled optical transport | A public container carrying the original system-rendered TabView Dock moves over a stationary known source field. The fixture commands the container trajectory. | Conditional optical response of that retained native surface at measured positions/velocities, subject to capture limits. | A freely draggable native Dock, a native gesture/spring law, or native internal lens motion. |
| I: native internal interaction | The owning carrier stays fixed. Actual native inputs operate each of seven registered families: Dock, segmented Tab, Toggle, single slider, single-choice menu, dialog/half sheet and button. The system owns their actual body/thumb/track/fill/highlight/popup/sheet/button responses. | Family-specific selection, highlight, shape/corners, opacity/fill, opening/dismissal, settling, interruption and delivered-input timing, with every actual frame and component retained. | A Dock-only proxy for every family, optical equivalence to T, a freely prescribed internal trajectory, or fictitious unsupported components. |

Move only the public owning container in arm T; preserve the same native controller/view identities, selection, content geometry, styling, traits, and glass implementation. Never animate a manually drawn capsule and call it native. The fixture's carrier animation is an intervention, and every trace must label `motion_origin=fixture_container_command`. A stop or reversal of that carrier is not a native spring response. A separately observed glass/lens response may be native, but its origin and measurement support must remain explicit.

Before freezing the test, the calibration feasibility check must establish whether a public carrier can move the retained native Dock while sampling the stationary external background. Check model/presentation geometry and a no-glass control; retain stale sampling, clipping, forced relayout, fallback material, or loss of the native parent as failures. Do not manipulate private internals to make the experiment work. If it is infeasible, mark arm T unavailable. A fixed native Dock with a moving source field may be registered as a separate source-transport arm, but it is not an interchangeable substitute. A movable public glass specimen also needs its own parent/material identity and must not be described as the TabView Dock.

## Immutable source fields: size, aspect, orientation and color

Keep the baseline world contract: 375×667 logical points, 750×1334 opaque RGB pixels, 2 pixels/point, top-left image-edge origin, frozen embedded sRGB ICC. Pixel `(i,j)` has center `(i+.5,j+.5)`. Use the declared4×4 subpixel area sampler in sRGB code values and preserve PNG/pixel hashes. A genuinely different native viewport/pixel scale requires separately generated analytic sources and a registered world manifest; never stretch an old source or screenshot to fit it.

Register **108 geometric conditions =4 families ×3 base scales ×3 aspect ratios ×3 orientations**, spread over **18 plates with six nonoverlapping landmarks each**. Do not put108 or216 large markers in one canvas. Six internal palette classes are fixed with the family and geometry-factor marginal balance below, not fully crossed with every geometric condition or independent of the assigned background blocks. The initial eight-plate screen covers48 conditions; it does not establish the remaining60.

| Factor | Registered levels |
| --- | --- |
| Base family | circle, equilateral triangle, five-point star, asymmetric polygon |
| Base radius `r` |6,12,18points before anisotropy |
| Aspect factor `q` |1,1.5,2 |
| Orientation `theta` |0,pi/4,pi/2 |
| Ordered palette classes | Fixed deterministic class per geometry; global18/class, family4or5/class, each source-factor level6/class |

For unit base coordinate `v`, transform source geometry by `world=c+R(theta)*r*diag(sqrt(q),1/sqrt(q))*v`. The determinant is `r²`, so aspect changes preserve a given family's continuous area at a fixed base scale. These are three distinct aspect levels with orientation treated separately. For circle-family instances `q` is the principal-axis ratio; compute actual world-axis bounds/width-height ratio and principal axes for every transformed polygon instead of mistaking the affine factor for its final bounding-box ratio. **These transforms apply only to the source landmarks and their color regions. Never nonuniformly stretch a native control.** The declared base radius is not the final circumradius: compute and preserve actual transformed support, ideal bounds and moments. A circle-family source with `q!=1` is its ellipse instance, not a circle. Its conic and orientation remain registered even when a circular outline itself is rotation-invariant.

The base circle is a unit disk. Triangle vertices have angles `−pi/2+2*pi*j/3`; the five-point star has ten vertices at `−pi/2+pi*j/5`, alternating radius1 and.45. The asymmetric polygon has ordered base vertices `[(-.95,-.15),(-.30,-.90),(.45,-.70),(.95,.15),(.20,.95),(-.55,.45)]`, normalized by their maximum Euclidean vertex norm. Preserve base vertices, affine matrix/inverse, transformed world/pixel vertices or conic, actual maximum radius, orientation, continuous ideal area/moments, raster area/moments and every generation failure.

The six RGB palette entries remain `(24,24,24)`, `(232,232,232)`, `(232,48,48)`, `(48,232,48)`, `(48,48,232)`, `(232,232,48)`. Class `k` assigns ordered internal colors `[k,(k+2) mod6,(k+4) mod6]`. In unit base coordinates the regions are left `u<−.25`, middle `−.25<=u<.25`, right `u>=.25`, intersected with the ideal base shape. Apply the same full affine transform to both shape and color partition. All families retain three internal colors. Preserve each region's exact base/transformed boundary coordinates, adjacent RGB identities, signed source-code contrast and persistent boundary/feature IDs.

Enumerate geometry by `i=(((orientation_index*3+aspect_index)*3+scale_index)*4+family_index)`, `i=0..107`. Set `plate=floor(i/6)` and `slot=i mod6`. Let `j=9*orientation_index+3*aspect_index+scale_index`. Assign `k=(scale_index+2*aspect_index+3*orientation_index+family_offset[family_index]) mod6`, with fixed offsets `[0,3,1,4]`. The JSON preserves the explicit4×27 class table and108 condition rows. No random palette permutation or output selection is used. Each class occurs18times globally; each family has every class4or5times; each scale/aspect/orientation level has every class6times. A six-landmark plate need not contain all six classes. With the preserved `plate mod3` background assignment, palette counts per background are `[3,12,3,3,12,3]`, `[3,3,12,3,3,12]`, `[12,3,3,12,3,3]`; both source-seed blocks have9/class. Thus these are geometry-factor marginal balances, not within-background balance or color/background independence. This disclosed limitation adds no captures. Six slots are row-major on a3×2 constellation centered at `(187.5,333.5)`points, with x offsets `[-72,0,72]` and y offsets `[-36,36]`. Each coordinate receives independent seeded jitter in `[-2,+2]`points. The maximum source-radius bound is `18sqrt(2)=25.456…`points; the72point slot spacing leaves more than4points of clearance even with that jitter. Verify actual ideal bounds/nonoverlap, retain failed generation and never substitute a seed. For a separately registered genuine viewport, center the constellation at `(width/2,height/2)` while preserving point-scale offsets and geometry; do not scale the field. No unregistered peripheral landmarks are added.

For each output pixel evaluate the16 declared subpixel centers, retaining integer membership counts for all three regions. Their sum/16 is exact sampled shape coverage. Compose the16 shape/background code values and round half-up with `(integer_sum+8)//16`, without normalization. Preserve lossless per-region coverage RLE, continuous/raster geometry, source PNG/pixel hashes, mask bytes/hashes, generator/protocol/ICC/dependency hashes. These masks describe the sampler, not measured physical alpha.

Three background families remain: neutral RGB128, broad smooth chromatic gradient, and multiscale chromatic texture. Exact nonneutral formulas, amplitudes and filter boundary conditions remain implementation tasks and must be frozen before generation. Each captured plate is assigned one background; three backgrounds are not silently crossed with every geometry, direction and configuration. Paired source identities are not independent scene samples.

| Split | Source-layout seeds | Background seeds | Trajectory-order seed |
| --- | --- | --- | --- |
| Calibration |4196218401,4196218402 |4196218657,4196218658 |4196218913 |
| Test |2794113001,2794113002 |2794113257,2794113258 |2794113513 |

Use NumPy PCG64. `plate_index mod2` selects its split's source-layout seed; this does not replicate every condition under both seeds. Freeze instrumentation, tracker, candidate, groups and analysis on calibration before test outputs open. An output-driven revision turns opened test cases into calibration for that revision and requires new test seeds. Frames, themes, repeats, source colors and paired renderers are not independent source realizations.

## Carrier trajectories and the initial bounded screen

Measure native Dock rest geometry without restyling. Preserve genuine native size/corners and retained public parent identities. Eight directions remain E,W,N,S,NE,NW,SE,SW, in screen x-right/y-down coordinates. For direction `u` use measured rest-box projection `h=abs(u.x)*W/2+abs(u.y)*H/2` and source bound `a=74*abs(u.x)+38*abs(u.y)+18sqrt(2)`. The latter includes the new3×2 slots, bounded jitter and largest transformed source. Centers run from `center−(h+a+16)u` to `center+(h+a+16)u`. Preserve edge clipping and actual visible support; do not resize the Dock to avoid it. Classify approach/passage/leave using achieved geometry and source support, not only planned phases or an assumed capsule alpha.

First use one paired calibration feasibility condition: native and Android, plate0, neutral, light, eastward. Check retained native identity, live sampling of the stationary background, no-glass control, presentation geometry, source support, actual PTS/clock behavior, full-frame ledger and throughput. If the public carrier cannot retain native material sampling/parent behavior, stop that arm and preserve failure. A moving source or other native specimen is a separately registered arm, never an interchangeable native Dock replacement.

The fixture's planned4.65second carrier trajectory remains below. With local `z` in each moving segment use `q(z)=10z³−15z⁴+6z⁵`. It is a carrier intervention, not a native gesture/rebound law.

| Planned seconds | Normalized progress |
| --- | --- |
|0–.30 |Hold0 |
|.30–1.40 |0→.25 |
|1.40–1.55 |Pause.25 |
|1.55–2.15 |.25→.55 |
|2.15–2.35 |Reverse.55→.50 |
|2.35–3.65 |.50→1 |
|3.65–4.65 |Observe rest at1 |

Keep actual commands, input callbacks, presentation positions, velocity/acceleration uncertainty and missed intervals. A fixture pause/reversal/rebound is never called native response. A planned rest interval does not prove observed settling.

The **initial** screen remains62planned clips plus2diagnostic reserves, at most64clips across native/Android and calibration/test, initially at most6seconds each:60coverage clips are `(8T+7I)×2renderers×2splits`, plus the2feasibility clips. Failed originals and reserves stay in the ledger. **64×6=384seconds is the initial acquisition budget, not full-size/full-action completion.** No six-second truncation may be labeled a complete action.

Map E,W,N,S,NE,NW,SE,SW to source plates `[0,2,4,7,10,13,15,17]`. Source seed index is plate mod2; background index plate mod3; themes are `[light,dark,light,dark,dark,light,dark,light]`. These eight plates include all three scale/aspect/orientation levels but only48of108 geometric conditions. Native/Android use identical assigned conditions. All I cases use stable family/configuration rows in JSON. Each family starts with `body_size.base` at configuration index0; family-order prefix offsets give `configuration_global_index=0..46`. Set `g=configuration_global_index*7+suite_index`, source plate `g mod18`, source seed index `plate mod2`, background `g mod3`, and theme `floor(g/2) mod2`. Initial Dock baseline has global configuration index0, so its seven cases are exactly `g=0..6` and can be reused with identical source/background/theme/configuration identities. Unsupported rows retain their original IDs and are never compacted or reindexed. This is deterministic blocking, not independent/full Cartesian sampling. Each paired renderer uses the same frozen case identity with its own actual input/response trace.

## Genuine native configurations and mandatory coverage extension

Source size variation is not native-control size variation. Separate **body_size**, **layout** and **content**. A variable-body family must provide genuinely measured **small/base/large** dimensions from supported public sizing while holding content/layout baseline where possible. Three requests with equal realized bounds do not satisfy the size gate. Freeze size-distinctness tolerance against measured uncertainty on calibration. Record actual width/height, which extent varies, intrinsic/model/presentation bounds, actual thumb/track/fill/popup bounds/corners, API/constraints, viewport/world/raster, safe area, traits, item count/content IDs, parent/material and coupled axes. No label/count substitution, nonuniform transform or screenshot scaling creates a native size sample.

| Native family | Body-size levels | Layout variants | Content variants | Max planned configurations |
| --- | --- | --- | --- | ---: |
| Dock | small/base/large | baseline +2 | baseline +2 |7 |
| segmented_Tab | small/base/large | baseline +2 | baseline +2 |7 |
| Toggle | base (fixed intrinsic) | baseline +2 | baseline +2 |5 |
| single_slider | small/base/large | baseline +2 | baseline +2 |7 |
| single_choice_menu | small/base/large, public support to verify | baseline +2 | baseline +2 |7 |
| dialog_or_half_sheet | small/base/large, actual subtype labeled | baseline +2 | baseline +2 |7 |
| native_button | small/base/large | baseline +2 | baseline +2 |7 |

The baseline counts once: configuration index0 is `body_size.base`; variable families then register small, large, two layout alternatives and two content alternatives, totaling at most7; Toggle has no extra body-size rows, totaling at most5. This is47 planned configurations, not a3×3×3 cross. Layout variants retain baseline body request/content; content variants retain baseline body request/layout. Preserve actual coupled changes and do not present them as independent sizing evidence. Every row remains **unmeasured draft** until actual calibration support is recorded. A real fixed/discrete public sizing limitation needs evidence, explicit unsupported rows and a narrower claim/revised ledger; it does not pass the three-size gate.

Dock sizing keeps the same4 items/labels while genuinely supported public viewport/parent widths target320/375/414pt; item-count3/5 variations belong to content. Segmented Tab keeps3 short segments while public sizing targets distinct actual bodies; changing count/title does not count. Single slider keeps range/value/ticks/labels fixed while public rail constraints target160/240/320pt; intrinsic thumb dimensions can stay equal and are separately recorded. Toggle retains its one true UISwitch/Toggle body size; long-label, RTL and accessibility layouts are not three switch sizes.

Menus retain the same five language labels while probing genuine public presentation/viewport sizing; no undocumented popup-width API or guaranteed three widths is presumed. If requests are ignored, retain unavailable sizes and narrow the claim instead of substituting long labels. Dialog/half-sheet sizing uses a registered actual native subtype and supported public detent/presentation constraints with text/actions held fixed; a sheet does not stand in for a dialog. Buttons hold title/image/state/style fixed while supported controlSize or constraints vary real body size. All use distinct layout/content rows and preserve actual component/corner measurements.

Do not presume a system dual-head slider API. Two actual native single sliders must be labeled a paired-single-slider composition, with both component IDs and full-frame traces; the app dual-head goal remains separately labeled. A different genuine viewport/pixel scale needs a separately frozen analytic source/world raster, never stretching an old source or375pt screenshot.

The full request requires staged expansion before corresponding completeness claims:

| Stage | Additional nominal suite slots across2renderers×2splits | Required implication |
| --- | ---: | --- |
| T source-size coverage |40 |Add the10unseen plates `[1,3,5,6,8,9,11,12,14,16]`; all18plates/108geometry conditions get one full varying-motion profile per split. Unseen direction is `plate mod8`; initial plates keep their directions. Not every geometry×direction is covered. |
| I core controls |700 |Dock7+Tab7+Toggle5+single-slider7=26 configurations ×7suites=182 per renderer/split. Reuse exactly the7 baseline Dock `g=0..6`, leaving175×4 slots. Every supported config receives every applicable complete suite. |
| I remaining families |588 |Menu7+dialog/half-sheet7+button7=21 configurations ×7 family-specific suites ×4. Mandatory before an all-controls claim; unsupported actions/sizes remain explicit. |

Including the initial64 slots gives **1392 nominal suite slots**, **8352 nominal seconds if each fits6seconds**, conditional on exact reuse of all28 initial I slots (7×2renderers×2splits). Without any valid I reuse, the conservative bound is **1420 nominal suite slots** before atomic splits/follow-up; at most28 are added under the finite stage ledger. No initial observation is forced to count as usable coverage. These are conditional staged bounds, **not authorization to launch1392 captures or an absolute raw-recording cap**. A suite requiring multiple independently complete recordings needs a finite amended count/storage/duration ledger before capture; no hidden clips. Finish static, feasibility, then small calibration batches with measured throughput/storage. Unsupported rows preserve IDs/reasons and cannot satisfy missing coverage. No Cartesian multiplication by every palette/source size/direction/acceleration/background is implied. One paired<=12s incomplete-condition follow-up remains separately counted; difficult originals stay preserved.

### Exact initial-case reuse gate

Reuse refers to the same canonical `I/{split}/{renderer_id}/Dock.body_size.base/{suite_id}` and original evidence, not merely equal `g`. Before subtracting any initial slot, compare every required frozen identity field exactly: split/renderer/configuration/body/layout/content/item count; source plate/condition/PNG/pixels/layout seed/background seed/palette-mask/world/generator-protocol-ICC bindings; background/theme/traits/native style/parent/expected-semantic-component manifests; requested suite and full input-intent parameters; driver/build/candidate freeze; preinput/settle/capture policy. The JSON enumerates32 fields. All pre-capture condition hash bindings must resolve to real frozen artifacts; `expected_semantic_component_manifest_sha256` binds the expected semantic/layout target plan. Actual native object IDs, instance union/generation and late discovery are independently observed capture evidence bound afterward before analysis/reuse. Reuse retains the same original evidence; actual object IDs need not match across renderers or independent captures. Draft placeholders are not evidence. Missing/null/mismatched/incomplete/unsupported evidence cannot silently satisfy the full gate.

Native and Android preserve independently delivered input/response traces. Requested input, driver and condition identities must match; actual delivery times/paths and observed response are measured independently and are never forced equal. Changed input hold duration, source/world/palette/content/layout/build/theme or split invalidates reuse even when `g` stays equal. Keep original failures; lost reuse uses the finite conservative addition above.

## Native input cases and complete action lifecycle

Keep each owning carrier fixed for native internal interaction. Seven core Dock/Tab/Toggle/slider suites adapt to supported behavior: selected/unselected and adjacent/first-to-last taps; short120ms/long600ms holds and release; slow120pt/s drag; fast480pt/s drag; accelerated3840pt/s² intent with pause/reversal;24point endpoint overtravel/release; rapid interruption/cancellation where the public driver supports it. Retain actual event delivery, initial selection/item bounds, no-change/ignored input and unsupported forms. The JSON registers seven explicit family-specific suites each for menu, presentation and button: actual open/close/select/outside-dismiss/cancel/press/release/interrupt forms as supported. Every configuration uses its own suites and every component/frame field; no Dock-only proxy. Do not pretend every family supports every drag.

Use actual native interactions for preparation/reset and label them. Never set internal selection/lens geometry to imitate touch. Android receives the same intentions and records independent delivery/response, not the native lens trajectory. Requested speed/acceleration is not actual achieved timing. Preserve overshoot, extension/compression, native release-to-settle and any absent rebound honestly.

Every action's measurement begins with a target.30seconds of observed pre-input baseline, then includes all delivered subevents, release/cancellation, fall/rebound/dismissal and **observed settle**. Freeze a stability criterion/uncertainty on calibration, including at least.5seconds of stable observed support; unavailable geometry or clock support cannot silently count as settled. Bundled subevents wait for prior settle unless an intentional interruption is registered. If the suite cannot fit6seconds, split it into independently complete registered clips or use the bounded continuation below; never truncate and call it complete.

If not settled or cut off at6seconds, preserve `incomplete/right-censored`. Before a completion claim, register at most one paired native/Android repeat of the entire same sequence including baseline with a12second cap, or an independently labeled continuation whose clock/phase continuity limits are retained. A separate recording is not secretly a continuous action. If still unsettled/unidentifiable at12seconds, retain incomplete and stop automatic repeats. Continuation counts/actual footage/storage have their own finite ledger beyond64×6, reviewed per small batch. This is not an unlimited retry loop or a way to replace difficult results.

## Seven-family component and layer contract

The I-arm geometry/frame contract covers every registered family and configuration, from pre-input through actual settle or explicit incomplete end. Observe real native components read-only; the following are measurement targets, not assertions of separate exposed glass nodes or permission to use private APIs.

| Family | Component IDs to retain on every actual frame |
| --- | --- |
| Dock | body, selected_lens, selection_fill, glyphs_labels |
| segmented_Tab | body, track, thumb_or_selection_lens, selection_fill, glyphs_labels |
| Toggle | body, track, thumb, thumb_opaque_core, on_fill, glyphs_labels |
| single_slider | body, track, thumb, active_fill, ticks, glyphs_labels |
| single_choice_menu | anchor, trigger_button, popup_body, row_body, row_highlight, selection_mark, glyphs_labels |
| dialog_or_half_sheet | presentation_body, presentation_backdrop, grabber, action_button_body, action_button_fill, glyphs_labels |
| native_button | body, highlight_fill, glyphs_labels |

Every component row records family/configuration/axis/body-size identity; original PTS and sequence; decode/gap status and app-clock support; existence/visibility status; actual world bounds, model/presentation transform, measured edge/corners, thumb/track/fill/popup geometry; opacity/fill/highlight response; actual parent/z-order/material ancestors; clipping/occlusion; selection/input phase; method/uncertainty/null reasons. Public geometry and pixel-derived geometry stay separately labeled. Lists include absent/unexposed/nonrefractive components honestly: preserve `not_in_native_api`, `not_exposed`, `not_visible`, `occluded`, `clipped`, `unidentified` or `decode_failed`, with null geometry as needed. Never manufacture a component, curved edge or radius from a candidate assumption.

Measure each present body/thumb/track/fill/highlight/popup/sheet/button boundary and corner separately when identifiable. Retain all intervening frosted backplates and actual ancestor layers: a foreground lens must be compared against the composite material/content actually beneath it, not a bare scene sampled through the backing panel. Opaque/no-refraction components retain geometry/appearance evidence and no invented optical deformation. All seven families use source-feature correspondence and the supported local edge normal/tangent contract when optical support exists; unsupported evidence remains null.

### Repeated native component instances

The37 category templates above are not37 actual component instances. Expand an explicit native/semantic instance registry before capture. A five-language menu needs five separately bound row targets; multiple action buttons, Tab/Dock items, glyph/label targets and slider ticks retain separate persistent instance IDs and parent/item/action/tick/content bindings. Every geometry/corner/pose/opacity/fill/material and source-feature row carries the actual instance ID, generation/episode, parent instance ID and clock support. A generic `row_body` or `action_button_body` row cannot stand in for every instance.

Freeze an independent controlled-content semantic target manifest with target/template/item/action/tick bindings and subtype applicability before capture. Actual object identities, lifetime/generation multiplicities and instance union are observed during/after capture and independently reconciled/versioned/hash-bound before analysis/reuse; no future native object ID is presumed at freeze. The observed registry must cover that manifest; it cannot define away a missing language/Tab item or duplicate one binding to replace another. Unknown multiplicity remains unresolved. Bind a separate nonempty acquisition ledger of original actual-frame sequence IDs/PTS; the analyzed rows must match every ledger sample in order, including failure/repeat rows. Every actual frame enumerates exactly the clip's registered instance union, including `not_created_yet`, `present`, `not_in_native_api`, `not_exposed`, `not_visible`, `occluded`, `clipped`, `unidentified`, `ended` and `decode_failed` statuses. Menu dismissal does not delete rows. Version late discovery/creation intervals; destroying/recreating an element starts a new generation, never inferred continuity from a class/index alone. `ended` is terminal within an ID/generation; it cannot later become present. Unknown/decode-failed samples never erase an already observed terminal state. If public object identity is unavailable, preserve null plus semantic correspondence method/uncertainty. These are inventory/measurement targets, not a claim each semantic row has its own exposed native view. Separate verified structural `not_applicable`/nonexistence for the registered native subtype (for example, a dialog without a sheet grabber) from expected-present but unidentified/unexposed/null. Register applicable instances and structural exclusions separately. True precreation/ended/not-visible lifecycle absence remains honest inventory evidence. Unknown applicable expected-present instances cannot count as completed measurements; verified N/A is a scoped exclusion, never a fabricated or successfully measured node.

## Presentation geometry and clocks

Log one monotonic process clock for commands, delivered touch/event callbacks, display-link callbacks, and geometry sampling. For iOS record `CACurrentMediaTime()` at sample start/end, display-link `timestamp` and `targetTimestamp`, model bounds/transform, and available `CALayer.presentation()` geometry converted into the same root/world coordinate system. The presentation tree is an approximation of in-flight animation state and may be unavailable; record null and the reason, never silently substitute model geometry as presentation. Public view/controller identities, transforms, clipping, effective traits, selected item, and parent configuration accompany each clip. Observe native-generated subview geometry read-only; no private getter or geometry mutation is authorized by this protocol.

Bracket each geometry read with monotonic times. A display-link target is a predicted display time, its callback is not proof a frame was shown, and a source `draw(_:)` or screenshot request timestamp is not compositor presentation time. Maintain these separate fields. Derive velocity and acceleration from measured positions at their actual irregular sample times using a method frozen on calibration, with gap/uncertainty flags. Never label a planned easing curve as measured native motion.

Analyze **every actually recorded frame** in original PTS order, from pre-input to observed settle or explicit incomplete end. Keep one frame-ledger row and all registered source/feature/control statuses for each actual sample, including repeated/undecodable frames, drops/gaps, failed captures and unidentified/clipped/occluded states. Keyframes are visualization selections only, never the analyzed sample. Keep original video sample PTS, duration, sequence index, codec, dimensions, color metadata, and capture-callback brackets where exposed. Do not equate video PTS or an external screenshot's host time to the application clock without a documented mapping. Register a visible synchronization patch away from the measurement region and its application draw brackets; retain the mapping fit, residual, offset/drift uncertainty, and occluded/ambiguous markers. Do not assume a fixed one-frame latency. Host and device clocks, and clocks on two devices, are separate domains. Compare elapsed intervals relative to independently observed input markers rather than wall-clock dates.

If screenshots are only obtainable intermittently, preserve request/completion brackets, planned and actual sampling times, and missing frames. Report actual sample count, minimum/median/p95/maximum PTS spacing, repeated/dropped frame indicators, and geometry-to-pixel synchronization uncertainty. A 60fps recording resolves frames roughly16.7ms apart, a120fps recording roughly8.3ms apart; neither measures every millisecond. Requested refresh/capture rate is not achieved sampling rate. Do not interpolate unobserved shapes and present them as measured keyframes. Any interpolation used only to resample a comparison must be labeled with its support and uncertainty, and raw frames must remain available.

## Source identity, morphology, and timing analysis

Create an explicitly new frozen dynamic tracker; the static v2 local-translation tracker is not automatically valid for rotating triangles/stars, strong non-affine warps, temporal blur, or topology changes. Build and verify its synthetic cases before reading test captures. Source identity comes from registered geometry/color/context, not forced nearest-neighbor or an assumed single image. Save zero/one/multiple lobes, fusion, occlusion, clipped support, blur, and unresolved identity. Keep every source ID at every supported sample. If contrast or correspondence fails, retain `unidentified`; top-ranked weak templates alone never prove disappearance.

Report observed weighted centroid, support area, axes/angle, boundary/coverage, source-normalized area and anisotropy, color/contrast, and several-component topology. When boundary correspondence is supported, report vertex/curvature changes for polygons; do not force a triangle/star boundary fit onto an unresolved blob. A star's blurred tips can become invisible without any physical change of topology. Preserve segmentation-threshold sensitivity. Shape-family/base-scale/aspect/orientation comparisons must distinguish pre-affine base radius, actual transformed support radius and source area; preserve the registered condition/plate/native-configuration identities.

Separate global carrier displacement, each registered family/component boundary and each refracted source component. Use source coordinates outside glass, component-relative coordinates and world coordinates together. Foreground icons/labels, the selected thumb/lens over its body/track/fill, menu/sheet/button surfaces and backdrop behind a frosted panel are distinct layers. Do not pool them into one bare-glass score or accidentally sample behind an intervening backplate. Any mask is declared and versioned; actual component/template overlap and layer ambiguity remain in the report.

### Supported local image stretch

Give the outer boundary, polygon vertices, each clipped internal color-boundary segment, and its sampled feature positions persistent IDs derived from the shape ID. Freeze feature sampling density/caps, correspondence gates, neighborhood support, residual limits and uncertainty estimation on calibration before opening dynamic test outputs. Retain every registered feature at every supported sample, including `unidentified`, fused, occluded, clipped and below-contrast states; do not infer a contour correspondence solely from a plausible centroid or a whole-shape ellipse fit.

Only reliable source-to-observed boundary/internal-color-boundary correspondences support local measurements. A resolved one-dimensional contour neighborhood can yield **tangent length ratio and direction only**; its unsupported normal stretch remains null. Fit a local2D source-to-observed Jacobian `J` only when a sufficiently supported non-collinear feature neighborhood, conditioning and residual pass the calibration-frozen gates. It estimates apparent local image deformation, not physical material strain. Do not call a single contour's tangential evidence a full2D deformation field or substitute global area/anisotropy for local strain.

For every present supported body/thumb/track/fill/highlight/popup/sheet/button component of all seven native families separately, retain measured edge polyline/curve, local corner shape, acquisition method, time support and uncertainty. At a confidently located edge neighborhood, define unit edge normal `n`, tangent `tau`, signed normal distance `d_edge` and edge arc position `s_edge`, all in the shared world frame. Never replace an unknown curved native edge with a bounding-box side or the candidate's assumed capsule and label it measured. For a supported `J` and edge frame, report `||J*n||`, `||J*tau||`, their observed directions and uncertainty; otherwise the unavailable quantities stay null with rejection reasons. Keep this family/component edge frame distinct from the source contour's own tangent. Ambiguous multiple components must not be collapsed into one stretch measurement.

Output per-shape/per-feature curves at the actual observed times: source and observed positions, boundary overlays, color response, supported local tangent/normal length ratios and directions, `d_edge/s_edge`, layer/edge identity, correspondence status, fit residual and uncertainty. Attach original video PTS, app monotonic sample brackets, clock-mapping uncertainty, achieved carrier pose and approach/edge/thick-region/leave phase. Show entry into the thin edge, passage through the body and exit without time stretching or filling unobserved gaps. These curves locate supported nonuniform **image-response** changes; they do not uniquely recover native lens thickness or renderer internals. Analyze all actual frames from retained clips without keyframe-only subsampling. This analysis does not itself add captures;64×6 is only the initial screen, while mandatory source/control-size coverage and bounded incomplete-action continuation use the separately registered ledgers above.

Compare native and candidate only on supported common world regions and recorded phases. Arm T may compare optical response conditional on matched measured carrier pose; that does not validate motion timing. Arm I additionally compares response to delivered input, with start delay, travel, lift/fall, overshoot, interruption, and settle intervals. Report any pose/time alignment transformation. No arbitrary per-frame shifts, dynamic time warping, or time stretching may hide a timing mismatch. Aggregate by source seed/clip with the direction/background/theme block structure, not by treating correlated pixels/frames as independent trials.

No numerical parity threshold or pass claim is defined by this draft. First establish native capture repeatability, temporal/color/geometry uncertainty, and tracker failure behavior on calibration; then predeclare metrics and tolerances with the candidate and analysis hashes. Preserve failures instead of excluding difficult frames, clipped paths, dark themes, or background families after inspection.

## Evidence packet and start gate

Each clip needs the original source PNG and geometry table, all108 geometry identities grouped into18plates of6, exact affine/color coordinates and three-region coverage masks/hash bindings, persistent boundary-feature identities, source/generator/protocol/profile hashes, native/candidate build identity, device/OS/API/display configuration, arm/parent/material identity, requested schedule, actual event and geometry trace, original recording/PTS metadata, color/synchronization diagnostics, every-actual-frame PTS/status ledger, per-shape/feature result rows and local-stretch curves including rejections, actual separate-axis native configuration registry and true-size support evidence, seven-family per-component/frame geometry and layer status, fixed palette/marginal tables, stable global case IDs, protocol coverage-check report, action completeness/continuation ledger, and acquisition-failure records. Hash files as files, not as evidence of optical correctness. Preserve raw originals; stream-decode and analyze every actual frame on demand; retain compact full-frame analysis/status rows and declared lossless visualization ROIs/keyframes plus the complete source recording. Keyframes supplement the full-frame analysis and never replace it. Lossy video frames and screenshot PNGs must be labeled separately; do not compare codec-distorted color as though it were a lossless screen sample.

Start gates are: static packet completed/preserved; native carrier feasibility resolved on calibration; source formulas/generator implemented and frozen; input driver capabilities and timing resolution documented; dynamic tracker and uncertainty/metrics frozen; calibration/test separation confirmed; bounded capture/storage plan registered, including mandatory geometry/control-size coverage and complete-action continuation; separate body_size/layout/content support verified with actual distinct variable-body dimensions or a documented narrower support limit, without artificial scaling; seven-family component/layer/all-frame registry and stable initial-reuse schedule frozen; every-actual-frame analysis and incomplete-end policy frozen. A passing protocol checker alone does not satisfy these capture/tracker gates. Until these are satisfied, this document remains a draft and no dynamic test capture is authorized by it alone.

API references for later implementation: Apple's `CALayer.presentation()`, `CADisplayLink.timestamp`, `CADisplayLink.targetTimestamp`, and ReplayKit screen-capture sample-buffer callbacks. Their timestamps and observations must retain their documented meanings; no callback supplies a guaranteed per-pixel compositor time.

## Protocol-only consistency and coverage self-check

Run `python3 protocol-history/check_dynamic_v4.py --self-test` from this packet, or use its absolute path. It reads only the MD/JSON, preserved v3 protocol and preservation receipt; it never opens PNG/video/capture outputs or operates devices. It independently recomputes108 geometry identities, palette formula/table and all marginals, seven-family components/axis rows, baseline reuse and finite slot arithmetic, and compares the mirrored contract/table below. Mutation self-checks must reject deliberately damaged protocol copies. Pure synthetic metadata checks also exercise exact frozen-case reuse fields and repeated-instance/frame cardinality; these do not validate actual native geometry. This checks protocol consistency and coverage declarations, not actual native-size availability, pixel correctness, dynamic tracking, capture capability or parity.

<!-- dynamic-v4-contract:start -->
```json
{
  "revision": 4,
  "status": "draft_unfrozen_ungenerated_uncaptured",
  "geometry_conditions": 108,
  "plates": 18,
  "landmarks_per_plate": 6,
  "palette_formula": "k=(scale_index+2*aspect_index+3*orientation_index+family_offset[family_index]) mod6",
  "palette_global_counts": [
    18,
    18,
    18,
    18,
    18,
    18
  ],
  "palette_family_counts": [
    [
      5,
      4,
      5,
      4,
      5,
      4
    ],
    [
      4,
      5,
      4,
      5,
      4,
      5
    ],
    [
      4,
      5,
      4,
      5,
      4,
      5
    ],
    [
      5,
      4,
      5,
      4,
      5,
      4
    ]
  ],
  "palette_each_factor_level_counts": [
    6,
    6,
    6,
    6,
    6,
    6
  ],
  "palette_background_counts": [
    [
      3,
      12,
      3,
      3,
      12,
      3
    ],
    [
      3,
      3,
      12,
      3,
      3,
      12
    ],
    [
      12,
      3,
      3,
      12,
      3,
      3
    ]
  ],
  "native_families": [
    "Dock",
    "segmented_Tab",
    "Toggle",
    "single_slider",
    "single_choice_menu",
    "dialog_or_half_sheet",
    "native_button"
  ],
  "native_configuration_caps": {
    "Dock": 7,
    "segmented_Tab": 7,
    "Toggle": 5,
    "single_slider": 7,
    "single_choice_menu": 7,
    "dialog_or_half_sheet": 7,
    "native_button": 7
  },
  "baseline_configuration_index": 0,
  "fixed_intrinsic_family": "Toggle",
  "variable_body_size_required_levels": [
    "small",
    "base",
    "large"
  ],
  "component_contract": {
    "Dock": [
      "body",
      "selected_lens",
      "selection_fill",
      "glyphs_labels"
    ],
    "segmented_Tab": [
      "body",
      "track",
      "thumb_or_selection_lens",
      "selection_fill",
      "glyphs_labels"
    ],
    "Toggle": [
      "body",
      "track",
      "thumb",
      "thumb_opaque_core",
      "on_fill",
      "glyphs_labels"
    ],
    "single_slider": [
      "body",
      "track",
      "thumb",
      "active_fill",
      "ticks",
      "glyphs_labels"
    ],
    "single_choice_menu": [
      "anchor",
      "trigger_button",
      "popup_body",
      "row_body",
      "row_highlight",
      "selection_mark",
      "glyphs_labels"
    ],
    "dialog_or_half_sheet": [
      "presentation_body",
      "presentation_backdrop",
      "grabber",
      "action_button_body",
      "action_button_fill",
      "glyphs_labels"
    ],
    "native_button": [
      "body",
      "highlight_fill",
      "glyphs_labels"
    ]
  },
  "initial_clip_cap": 64,
  "initial_target_s": 6,
  "initial_Dock_global_cases": [
    0,
    1,
    2,
    3,
    4,
    5,
    6
  ],
  "additional_T_slots": 40,
  "additional_core_I_slots": 700,
  "additional_other_I_slots": 588,
  "combined_nominal_suite_slots": 1392,
  "nominal_seconds_if_each_slot_fits6s": 8352,
  "settle_support_min_s": 0.5,
  "incomplete_followup_max_per_condition": 1,
  "incomplete_followup_cap_s": 12,
  "all_actual_frames_required": true,
  "new_capture_authorized": false,
  "conservative_nominal_suite_slots_without_initial_I_reuse": 1420,
  "component_entries_are_templates_not_instance_count": true,
  "initial_reuse_exact_identity_field_count": 32
}
```
<!-- dynamic-v4-contract:end -->
