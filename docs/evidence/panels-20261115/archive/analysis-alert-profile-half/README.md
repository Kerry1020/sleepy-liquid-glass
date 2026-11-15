# Alert profile power.5 — frozen historical calibration comparison

Changing only Alert `refractionProfilePower` from1 to.5 does not resolve the native bend. Both stripe scenes have larger left/right RGB error; light stripe bottom bending becomes smaller. The top stripe centroid span increases, but remains far below native. Other background/edge diagnostics are mixed. These calibration results do not support accepting this candidate as a general improvement.

The plan isolates the Alert material role in `GlassControlModifier`. Boundary depth60dp and support20dp remain fixed; Sheet, contour, normals, tint, blur, shine and scrim remain unchanged. The shader already has a nonlinear rise profile. Power.5 changes the interior shoulder, and is not a claim about UIKit's actual formula. Source SHA matched the plan before decoding.

Eight REST inputs use only the four public historical calibration backgrounds in light/dark. They are not an independent test set, production-page proof, or motion validation. The native reference is real SwiftUI Alert on iOS26.5. Original375×667pt/dp displays are750×1334px; actual Android pane is[55,515,695,859]px. No resize, warp, recenter, fitted image translation or source substitution was performed.

The existing final analyzer and every ROI were frozen before decoding this candidate. Straight/corner raw RGB and fixed-smoothing first/second derivatives retain the.5pt sample grid. Derivative smoothing is sigma.75pt,7samples with reflected endpoints. Foreground exclusion is the union of native and actual Android layout boxes expanded2pt. Native AX is not recovered optical alpha. Raw encoded RGB and ICC-normalized sRGB were evaluated independently; all inputs declare PNG sRGB with no ICC, so the tracks are byte-identical. CSVs store one raw track; JSON retains both.

## Exact unchanged controls

|Region|Scenes per color track|Changed pixels, raw / ICC|Maximum channel change|
|---|---:|---:|---:|
|alert_conservative_deep_core_without_foreground|8|0 / 0|0|
|alert_window_outside_pane_bbox|8|0 / 0|0|
|full_sheet_window_rgba|8|0 / 0|0|
|static-alert-cancel_inner8pt|8|0 / 0|0|
|static-alert-confirm_inner8pt|8|0 / 0|0|

Each full Sheet Window is1,000,500pixels and preserves all RGBA values, including color/alpha under transparent pixels. Alert controls are14,088px outside the pane bbox and19,510px in the conservative deep region after foreground exclusion. The deep rectangle [61.5,291.5,313.5,395.5]pt lies beyond every34dp corner extent; it is a guaranteed deep subset, not a recovered full20dp contour-distance mask. Each action inner8pt control is15,872px and is listed separately because the child material samples its parent. All32 body ROI errors remain unchanged.

## Per-scene diagnostic directions

I/R/U means numerical improvement/regression/unchanged at tolerance1e−9, not a significance or acceptance test. All small changes remain listed. Each scene has4body,12straight and72corner raw metrics. Corner scans are horizontal raster slices, include curved coverage/exterior and the unchanged native/Android dark-scrim difference, and do not measure physical thickness in isolation.

|Scene|Body I/R/U|Straight I/R/U|Corner I/R/U|
|---|---|---|---|
|color_stripes-dark|0/0/4|0/12/0|25/47/0|
|color_stripes-light|0/0/4|5/7/0|13/59/0|
|fine_grid-dark|0/0/4|5/7/0|13/13/46|
|fine_grid-light|0/0/4|9/3/0|26/31/15|
|synthetic_landscape-dark|0/0/4|6/6/0|32/37/3|
|synthetic_landscape-light|0/0/4|7/5/0|30/30/12|
|tonal_blocks-dark|0/0/4|8/4/0|10/26/36|
|tonal_blocks-light|0/0/4|9/3/0|19/17/36|

## All straight-edge before/after errors

RGB is encoded8bit RGB RMSE; D1 is RGB/pt; D2 is RGB/pt². Entries are baseline → candidate. Scores use inward0..<20pt except bottom0..<10pt, exactly as the baseline analyzer.

|Scene|Edge|RGB RMSE|D1 RMSE|D2 RMSE|
|---|---|---:|---:|---:|
|color_stripes-dark|left|13.570376 → 16.900431|4.527493 → 4.959127|5.592159 → 5.644568|
|color_stripes-dark|right|12.897795 → 15.663720|3.426680 → 4.091178|4.325364 → 4.628855|
|color_stripes-dark|top|4.534915 → 4.546536|2.857997 → 2.860075|2.182839 → 2.184621|
|color_stripes-dark|bottom|5.700054 → 5.710837|3.361559 → 3.363384|2.706161 → 2.706420|
|color_stripes-light|left|16.760114 → 23.648207|3.466664 → 4.173566|5.569267 → 5.419671|
|color_stripes-light|right|10.636204 → 24.153223|2.870104 → 5.643113|4.592249 → 4.987544|
|color_stripes-light|top|7.133249 → 7.188709|1.988219 → 1.981453|3.110362 → 3.108145|
|color_stripes-light|bottom|10.418044 → 10.454897|2.756419 → 2.744482|4.671604 → 4.668626|
|fine_grid-dark|left|10.946213 → 10.947179|4.330784 → 4.335350|4.861954 → 4.866735|
|fine_grid-dark|right|9.367830 → 9.368725|3.724725 → 3.720351|3.930337 → 3.922945|
|fine_grid-dark|top|2.540854 → 2.540588|2.776546 → 2.777722|2.066985 → 2.067104|
|fine_grid-dark|bottom|2.900919 → 2.900332|3.068369 → 3.067606|2.314387 → 2.316374|
|fine_grid-light|left|9.018682 → 9.016678|2.448282 → 2.457071|4.498443 → 4.497519|
|fine_grid-light|right|8.797403 → 8.795104|2.331386 → 2.323061|4.291135 → 4.276237|
|fine_grid-light|top|4.013443 → 4.008469|1.040781 → 1.031287|1.615009 → 1.604409|
|fine_grid-light|bottom|5.705129 → 5.703676|1.273271 → 1.275683|2.722339 → 2.723257|
|synthetic_landscape-dark|left|8.618286 → 8.668760|2.953058 → 2.976705|3.919368 → 3.925628|
|synthetic_landscape-dark|right|7.441553 → 7.588646|2.606574 → 2.660126|3.269395 → 3.275962|
|synthetic_landscape-dark|top|4.364139 → 4.299689|1.888533 → 1.850120|1.700120 → 1.684262|
|synthetic_landscape-dark|bottom|7.106779 → 6.916262|2.419275 → 2.354765|2.403189 → 2.379215|
|synthetic_landscape-light|left|12.393366 → 12.348938|3.695451 → 3.737989|5.988956 → 6.004270|
|synthetic_landscape-light|right|12.060046 → 11.849857|3.581726 → 3.659955|5.729046 → 5.727549|
|synthetic_landscape-light|top|9.900657 → 10.204721|2.773339 → 2.711818|4.514053 → 4.495654|
|synthetic_landscape-light|bottom|14.839564 → 15.038195|4.149533 → 4.031657|6.873573 → 6.819850|
|tonal_blocks-dark|left|8.430946 → 8.431143|2.857799 → 2.857856|4.125983 → 4.126271|
|tonal_blocks-dark|right|8.202746 → 7.633639|3.264103 → 3.226218|3.322023 → 3.347997|
|tonal_blocks-dark|top|3.347474 → 3.326100|1.110683 → 1.105819|1.272786 → 1.264716|
|tonal_blocks-dark|bottom|8.153192 → 8.148779|3.549559 → 3.549405|3.225713 → 3.225669|
|tonal_blocks-light|left|12.717671 → 12.717549|4.061274 → 4.061808|6.079173 → 6.079239|
|tonal_blocks-light|right|13.807332 → 12.592791|3.917385 → 3.859448|6.744484 → 6.751829|
|tonal_blocks-light|top|11.820252 → 11.785980|3.750665 → 3.741514|5.542938 → 5.528248|
|tonal_blocks-light|bottom|6.533509 → 6.531134|1.238728 → 1.238505|2.165740 → 2.165051|

## All body ROI errors

These diagnostics do not change under this isolated edge-shoulder candidate. The two side gutters have620px each; lower gaps have1,800px each. Native backing controls differ from the Android fixture, so body RGB discrepancy is not a unique material-transfer estimate.

|Scene|left_gutter RMSE|right_gutter RMSE|left_gap RMSE|right_gap RMSE|
|---|---:|---:|---:|---:|
|color_stripes-dark|6.121968 → 6.121968|7.979106 → 7.979106|3.959494 → 3.959494|5.172595 → 5.172595|
|color_stripes-light|12.082290 → 12.082290|3.445661 → 3.445661|6.748004 → 6.748004|3.431067 → 3.431067|
|fine_grid-dark|1.758696 → 1.758696|2.079082 → 2.079082|1.702776 → 1.702776|2.002175 → 2.002175|
|fine_grid-light|0.628619 → 0.628619|0.655006 → 0.655006|0.586578 → 0.586578|0.658843 → 0.658843|
|synthetic_landscape-dark|4.158357 → 4.158357|4.190363 → 4.190363|4.651205 → 4.651205|4.674081 → 4.674081|
|synthetic_landscape-light|2.888706 → 2.888706|2.777599 → 2.777599|3.019688 → 3.019688|2.689899 → 2.689899|
|tonal_blocks-dark|2.446085 → 2.446085|2.377651 → 2.377651|4.491082 → 4.491082|5.022173 → 5.022173|
|tonal_blocks-light|3.620061 → 3.620061|5.831551 → 5.831551|2.289671 → 2.289671|2.616755 → 2.616755|

## Fixed blue-feature centroid response

|Trait|Band|Native span pt|Baseline span pt|Power.5 span pt|
|---|---|---:|---:|---:|
|dark|top|2.975029|0.314626|0.620474|
|dark|body|0.009494|0.000000|0.000000|
|dark|bottom|2.657694|0.229896|0.294525|
|light|top|3.133626|0.417003|0.618389|
|light|body|0.020388|0.001361|0.001361|
|light|bottom|2.732946|0.358107|0.202547|

The frozen window is x60.25..<96pt with positive `B−(R+G)/2` weights. This is color-response bending in original world coordinates, not identified stripe correspondence or physical ray displacement. The top/bottom/body bands and all masks match baseline. A larger span alone cannot accept a profile because coverage, color and blur can also change it.

![Unshifted fixed blue-feature centroid paths](blue-feature-bend-comparison.png)

## Complete corner data and limits

[corner-comparison.md](corner-comparison.md) retains all192corner/depth rows with RGB/D1/D2 baseline → candidate, including every regression and unchanged metric. `analysis.json` records all1,408raw/ICC before-after metrics, all controls, input hashes and unchanged sample counts. CSVs retain fixed raw RGB/smoothed/D1/D2 samples; foreground gaps remain masked and derivatives never cross those gaps. Existing phase diagnostics are marked unidentified and never shift either image.

Dark exterior response remains native≈.52 and Android≈.40; power.5 leaves this unchanged. The narrower/wider color-centroid response and mixed error changes do not establish physical thickness, universal optics, or a reproduction percentage. No noise holdouts were read and no dynamic or other-control work was performed.

## Provenance

- Analyzer SHA256 `e2caa294988003f81f150fc2295d2fe89710210d0ca260598e4fb88c0850ec8b` (reused in place).
- Baseline analysis SHA256 `cd0b6088b597fa93045ae73417410d8457104e416a363a5c4fbc9350f4f9ac38`.
- Candidate analysis SHA256 `ff69c037c355665808cfccefcf24aaa53fc34b66830394c79381dc45122b3961`.
- Predecode freeze SHA256 `3a69b3c36db95dd0d98d33c137d05046b2902ebf3fdc382670fcaadf78499bec`.
- Plan SHA256 `9d16ceaadbda637358fef8fc83b81142c521bef371f8582760c236b4bb096a5c`.
- Candidate source SHA256 `5ebd28c626e7baea243f4e51fafad1f38694c2970d7fdb295f148f979c0eb7d2`.

The original baseline and rejected frost8 artifacts were not modified. The report/figure builder reads only existing analyzer CSV/JSON output.
