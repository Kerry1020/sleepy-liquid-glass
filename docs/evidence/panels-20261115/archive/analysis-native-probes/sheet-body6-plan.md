# Sheet blur experiment: mode control, then 12 → 10

This plan is frozen before either new Sheet candidate is decoded. The filename preserves the requested handoff name; **radius 6 will not be executed**, fitted, or presented as an optimal value. The final registered experiment has two phases: A isolates enabling the true-radius input mode at radius 12; B changes only the API radius input 12 → 10 in that same mode, with the deterministic execution-route change disclosed below.

The original source supports, regions, sampling, masks and visibility gates remain unchanged. S07's exact local extraction was operationalized after earlier native/baseline review inside the frozen parent support; this new before-candidate plan does not retroactively make that localization an independent confirmatory preregistration. Both selected backgrounds are calibration inputs, not a held-out test set.

## Reason for the experiment

The existing native S07 response passes all 14 rows and has raw 10–90 widths 9.596–10.152 pt. Legacy Sheet12 passes 0/14 rows; where raw crossings are unique, descriptive widths are 11.785–12.867 pt. The earlier corrected-rim candidate passes only 2/14 rows; at y339.75 pt its width is 12.184 pt versus native 10.017 pt, with lower local contrast. These observations support testing a smaller blur input, but do not identify a physical blur kernel, establish radius 6, or determine any optimum. Failing legacy rows are not eligible measurements for fitting a radius.

Enabling a new mode and changing 12 → 6 together would confound the mode and radius effects. Phase A removes that confound. Phase B uses the smaller prespecified local API-input change 12 → 10 to observe the implemented response direction; its magnitude is an engineering perturbation, not an estimate of native sigma or thickness. No result-dependent radius search is authorized by this plan.

## Phase A: isolate the mode

Use the preceding completed rim candidate, at its original light Sheet12 legacy/default mode, as the control. Root must bind its exact directory, capture files, source revision and parameter/configuration evidence before the new phase A images are decoded. Do not read an incomplete rim run.

For phase A, enable true-radius input **only for light Sheet**, retaining the Sheet body blur input at 12 and every other optical and shaping parameter. Alert retains the preceding rim candidate's exact configuration. Dark retains its original factory/null path; it does not opt into the new mode. Retain the input-raster geometry fix and the original source-image mapping.

Capture the same two selected sources × light × Alert/Sheet × REST, with the same accepted actual Window and composited-display outputs, placement, density, slot geometry, scrim and timing protocol. Phase A compares the complete Sheet mode change with legacy Sheet12; it cannot isolate a radius response. Report that mode delta without fitting or silently compensating another parameter.

## Phase B: API radius perturbation with disclosed route change

After phase A is complete and its metadata/geometry/control gates pass, bind the complete phase A outputs before phase B's first pixel decode. Retain true-radius mode and change **only the light Sheet body blur input from 12 to 10**. All other parameters, sources, shaping, masks, geometry and capture conditions stay fixed. The API stays in true-radius mode, but its deterministic blur execution route changes as documented below; do not claim the Gaussian execution path is the same. Alert remains a strict control against phase A and the preceding rim control. Dark remains the original factory/null path.

Capture the identical four REST conditions. The primary API-input response comparison is phase B versus phase A, with native and historical legacy results retained as separately labelled context. This measures the deployed API response including the known shared-band-to-local route transition, not an independently isolated Gaussian-radius effect. Do not use legacy mode12 as the sole radius baseline.

If control evidence is incomplete, Alert actual Window pixels change, the source/shaping changes, or measured geometry/slots differ, stop the causal comparison and report the failed gate. Do not alter the plan after observing candidate pixels. Any later radius would require a separate before-capture plan.

### Known implementation routing limitation (before phase B decode)

Root reports that `GlassHost.filterBand` performs exact radius lookup only for 2.5, 12 and 16. Phase A true-radius12 still reuses shared12. Phase B true-radius10 follows the same public input API but has no matching band, so it uses the local preblurred input fallback. The only configured scalar mutation is 12 → 10, yet the Gaussian execution route differs. These facts must be bound to `GlassHost.kt` and `GlassFilterBands.kt` source hashes in the next build freeze before phase B decode. No new global band or dependency is added.

The phase B result must therefore be labelled **API-input engineering response with a deterministic routing change**. It cannot separate radius magnitude from shared-band versus local-fallback implementation effects, prove equality of Gaussian kernels, or support physical sigma/thickness recovery. If those causes need separation, that requires a separately authorized and preregistered same-execution-route control; this plan does not add one. Radius 10 remains the fixed experiment input and cannot be chosen again after seeing pixels.

## Frozen S07 extraction

Use the right edge of S07's pink cross vertical stem. The source stem is x153.1..190.9 px after the upper arm ends at y668.9 px; the source edge crossing is 95.5 pt. Source RGB is [215,43,154], neutral RGB [184,184,184], and the fixed scalar direction is normalized [31,−141,−30].

The unchanged parent Sheet top-left window is x[48,110) pt and inward depth [−5.75,24) pt from the **raster** top at 317.5 pt. Retain the native AX top 317.7 pt as a distinct observation; never recenter to it. The local x pixel centers are 84.25..109.75 pt at 0.5 pt spacing (52 original pixels). High plateau x[84,90) pt uses source pixel indices [168,180); neutral plateau x[100,110) uses [200,220). No ROI expansion is allowed to complete the upper arm's missing gray plateau.

Analyze **all 14 row centers**, including all failures:

334.75, 335.25, 335.75, 336.25, 336.75, 337.25, 337.75, 338.25, 338.75, 339.25, 339.75, 340.25, 340.75, 341.25 pt.

These correspond to raster inward depths 17.25..23.75 pt. Use unchanged 7-sample Gaussian smoothing with sigma 0.75 pt and reflected ends. Retain both raw and smoothed scalar tracks, separate raw/smoothed unique 10%, 50%, 90% crossings and 10–90 widths, contrast, source-direction cosine, local spread, derivative peak ratio, uncertainty and every failed gate. Raw widths remain unresolved if their crossings are missing/nonunique, even if smoothed crossings exist.

The inherited gates remain: encoded contrast ≥8 counts; contrast ≥5 × max(1 count, robust neutral spread); source direction cosine ≥0.7; at least 12 clear original pixels; secondary derivative peak ≤0.8 of primary; unique relevant crossings and valid source-consistent plateaus; no raw upward transition step above 1 count between the smoothed 90% and 10% crossings. The location floor is ±0.25 pt plus half the tied peak span; uncertainty above 1 pt prevents a fine location comparison. The existing secondary-peak separation rule and quantization handling remain unchanged in the hash-bound script.

Report row-matched native, control and candidate values rather than choosing a better-looking row. Passing-row counts describe identifiability; they are not a parity score. S07 is a scalar local contour and does not establish a two-dimensional source map. No complete-feature centroid is allowed for clipped or foreground-covered features. Existing complete-feature gates (64 pixels, 95% contained contrast mass, source tensor ratio 0.05) remain unchanged and cannot be waived.

## All other fixed analyses and controls

Retain every parent straight segment/bin, corner slice, body/exterior ROI, narrow-rim segment, shape support, foreground union mask and exclusion. The JSON embeds these unchanged definitions and their hashes. Do not add probes, move a plateau, change a threshold, select only successes, fit a translation, warp, resize, recenter or substitute an input. Keep apparent color-edge width, local correspondence, encoded color/contrast, and rim/highlight diagnostics separate. Brightness is not stretch or physical thickness.

Alert actual Window controls must be exactly equal in raw RGBA over their entire observed surfaces. Inspect full composited displays separately and retain exact changed coordinates; never convert a system-overlay difference into a material change or silently erase it. Actual pane/canvas/unit-basis, foreground slots and content density must remain exact. Freeze candidate file hashes before each first decode. Use no new native captures, unselected/hidden/holdout images, or duplicated screenshot files.

Dark is outside this light-only capture matrix. Root must supply implementation/configuration evidence that its original factory/null branch is unchanged; no dark pixel-equivalence claim is permitted without dark screenshots.

The output must include all row values/failures and every fixed ROI comparison, with separate native/control/candidate labels. A width improvement cannot cancel a worse location, contrast, rim or other region. There is no aggregate winner percentage or new acceptance tolerance. These calibration experiments alone cannot establish whole-material, dynamic, multi-size or whole-product parity. No physical sigma/thickness is inferred.

## Binding and execution ownership

The machine-readable companion is `sheet-body6-plan.json`. Its control references are roles until root hands off complete captures and frozen configuration evidence; binding those exact files must happen before the corresponding candidate decode and must not alter any design, region, gate or parameter choice. Root alone implements, builds and captures. This analysis task only writes below `analysis-native-probes`.
