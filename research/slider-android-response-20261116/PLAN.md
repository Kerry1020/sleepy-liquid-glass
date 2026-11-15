# Android G response: bounded comparison implementation plan

**Goal:** Compare one unchanged Android Slider checkpoint with the published S native global-G and mask-G responses, without identifying colour change as unique displacement.
**Architecture:** Reuse frozen native inputs and arrays; acquire three unique Android source conditions with repeated controls; compare raw encoded responses and conditional common-alpha intervals on a fixed world grid.
**Scope:** Research tooling and evidence stay in this asset repository. The session authorises Android capture; this plan does not imply product or optical acceptance.

## 1. Bind the existing native reference

- [ ] Hash-check S at `../slider-color-response-20261116/evidence/reference-analysis/` before reading arrays.
- `original-pixels.npz` SHA-256: `11b1e76aa2a0a7766b579bdfd8a8fc8e4bceecda1fc996a34f07d9955a78f695`.
- `analysis.json` SHA-256: `5499910555e7aa465f853c2361f55fe4a2300703416a98b82d00de98c393d9ba`.
- Read `raw_global_output_input[...,1,1]` as U_GG and `raw_mask_output_input[...,1,1]` as M_GG: output row G, input column G. Do not substitute the all-output descriptive input-G alpha.
- Native operating state is iOS 26.5/23F77, light, 2 px/pt, world 375×667, full100 HELD, tint `(0,.65,.75,1)`; retain all recorded settings and actual geometry.
- Native public carrier xywh is `[159.04738254547118,410.9,57.35,37.2]` pt; this is measured geometry, not an image-registration target.

## 2. Freeze a bounded Android acquisition before executing it

- [ ] Prepare, review and externally preserve a hash manifest binding this plan, actual runner/analyzer, fixture/adapter, checkpoint parameters, shader, APK/test APK, backend, source PNGs/specs/manifests, device/API/display and operating settings.
- Source conditions are exactly `control-pre`, `global-G`, `mask-G`, `control-post`, in that order. The unchanged fixture acquires all six stages × shape/flat per round: 48 screen endpoints and 196 original files across four rounds. Only the eight full100 screen endpoints enter this bounded native comparison; the other poses remain contextual evidence, without matched S native targets.
- Reuse S round input bytes, including sRGB ICC, original 750×1334 source grid, five-point star diameter16pt and centre `(187.5,419.5)`. The loader consumes all eight compatibility files, but only the five-point star and flat are scheduled. No stage-filter patch is introduced.
- Derived Android specs preserve original PNG bytes and all six pose definitions. They add the historical public-geometry reference and the S actual full100 centre `(187.7223825454712,429.5)`; status/scheduled-stage metadata is corrected to describe the actual six-stage Android acquisition. Original S specs stay unchanged and their identities are bound.
- Control shape SHA-256 is `9757bdb14092023996f2bd46d30b682799aac1fe06c221b7cad256c991e46724`; flat is `6e4291536355bff3dae7dee3957eec96bf4f3efc7566dd4257721a635ad8340b`.
- Global-G adds exactly20 encoded bytes to every source G; mask-G adds `floor((20*coverage16+8)/16)` in the original left_blue coverage mask. R/B remain byte-identical; source G never exceeds252.
- Retain original PNGs, input identities, actual DOWN/MOVE/held/UP and screenshot brackets, source/owner/carrier geometry, producer/readiness evidence and every failed attempt. Requested full100 or a timer alone is insufficient.
- No fallback backend, private native mutation, fixture-specific colour correction, new shoulder parameter or post-result rerun selection. A failed gate retains evidence and stops response inference; a corrected acquisition requires a separately recorded attempt/reason.

## 3. Acquisition, colour and geometry gates

- [ ] Require complete hash/identity matches, all twelve scheduled endpoints and49 original files per round, opaque RGB8/RGBA8 original screenshots, valid delivered held pointer and complete settled screenshot brackets. Analyse only the prespecified full100 shape/flat pair from each round.
- Record decoded source/producer colour space, pixel format/channel order, screenshot output colour-space evidence and actual sRGB handling; do not silently convert profiles, gamma, saturation or white balance. Missing output colour-space evidence means `COLOR_SPACE_UNVERIFIED`, permitting labelled byte diagnostics only.
- Light mode, tint, layout direction/font scale, theme, rail/foreground, backend and declared material parameters stay fixed across all Android observations. Observed effective opacity must be bound; missing opacity means `MAPPING_UNKNOWN_PIXEL_DIAGNOSTICS_ONLY`, not an inferred value of1.
- Within Android's eight observations require each actual owner/carrier bound and centre range≤0.10pt, each presentation-affine element range≤0.001, effective-opacity range≤0.01, source-world origin and world-to-producer matrix element range≤1e-8.
- Require identical actual output mapping/pixel lattice between rounds for direct integer differences. If these differ, stop this bounded comparison rather than introducing per-round image registration.
- Require every flat-minus-pre-flat RGB absolute maximum≤2 bytes on the complete fixed ROI, and post-control-shape-minus-pre-shape maximum≤2; retain all signed residuals and counts. No p99-only gate, averaging, baseline reselection or flat subtraction from U/M.
- Actual holder, carrier plus6pt guard and all required source sampling footprints must be visible and unclipped. Missing/cropped producer support, carrier bounds or screenshot mapping rejects geometry comparison.
- Across systems report each carrier bound/centre difference and observed affine/opacity difference. Differences>0.10pt/0.001/0.01 respectively mark `GEOMETRY_CONFOUNDED`; keep composite pixel differences but make no material-only attribution. Unknown fields remain unknown.

## 4. Map actual coordinates once; preserve outline differences

- [ ] Use recorded source-world-to-screenshot affine B from actual observed source origin/unit basis; screenshot array indices are `B(x,y)−(0.5,0.5)`, not the nominal screen centre or requested density.
- Keep world-to-producer sampling separate: actual producer width/375 and height/667 (or its observed affine) are not automatically screenshot density. Preserve any measured x/y inequality.
- Fixed ROI is world `[165.5,397.5,209.5,441.5)`, native original pixels `[331,795,419,883)`. Native sample centres are `((col+.5)/2,(row+.5)/2)`; keep the native88×88 grid unchanged.
- Compute Android signed differences on its original lattice, retain them, then bilinearly sample each field once onto those fixed native world centres with the same B. Label interpolated values; no registration, centre alignment, contour scaling, phase fit, crop fitting, denoising or colour normalization.
- Report the complete ROI; fixed above-rail `y<422`, rail `422≤y<438`, below-rail `y≥438`; native-capsule primary `y<422,inset≥1`; rim `y<422,0≤inset<1`; exterior `y<422,inset<0`.
- Inset uses S's existing `inset_capsule_assumption`, not optical alpha. Retain Android's independent measured contour/membership; a secondary intersection of independently measured interiors is labelled separately and never replaces the fixed domains.

## 5. Raw response, weak denominators and uncertainty

- [ ] For each platform p, arithmetic baseline is control-pre: `U_p=O_globalG,G−O_pre,G`, `M_p=O_maskG,G−O_pre,G`; retain original endpoint RGB and the complete input-G output column as supporting diagnostics.
- All values are finite encoded-byte responses, not radiance, transmission or infinitesimal derivatives. Raw `alpha_G=M_p/U_p` is descriptive and is never clipped to[0,1].
- Always report endpoint error-box sensitivities E=1,4,8 bytes; E4 is the primary conditional comparison, not a measured error bound or S's old raw finite-difference T4.
- Under a fixed locally affine response and common nonnegative source influence, candidate a∈[0,1] must satisfy `|M_p−a*U_p|≤2E`. The shared pre endpoint is included: coefficients `1,−a,−(1−a)` have absolute sum2; do not treat the two contrasts as independent baselines.
- Solve `A_p(E)=[0,1]∩sort([(M_p−2E)/U_p,(M_p+2E)/U_p])` for nonzero U_p. At U_p=0 use[0,1] if `|M_p|≤2E`, otherwise the empty set. Retain infeasible intervals even for weak denominators.
- Mark denominator weak when `|U_p|≤2E`, since its endpoint-box difference interval contains0; no identified ratio is published for it. Also retain signed U, ratio outside[0,1], negative/reversed responses, interval width and strong/weak counts; never silently discard them.
- With valid gates, empty `A_native(E)∩A_android(E)` rejects the common-alpha surrogate at that pixel/E; nonempty intersection means only bounded compatibility. Primary resolved-ratio summaries require both denominators strong; all-pixel interval failures remain visible.
- Report raw U/M differences, absolute-error quantiles/maxima, signed sums, alpha differences where resolved, interval gaps and every incompatible coordinate on all fixed domains. Do not attach binomial confidence or independent-sample p-values to spatially correlated/interpolated pixels.
- Shared zero support must not dominate a scalar score: alongside full-domain results always report the frozen-native `M_GG>0` subset, and separately the prespecified union `M_native!=0 or M_android!=0`; preserve Android-only false support and sign changes.

## 6. Native basis already observed, before Android acquisition

| Fixed domain | Pixels | U_GG min/median/max | M_GG>0 | Weak at E1/E4/E8 |
|---|---:|---|---:|---|
| Complete ROI | 7744 | 0/19/20 | 316 | 507/516/1642 |
| Primary | 1630 | 13/17/19 | 262 | 0/0/416 |
| Above-rail rim | 186 | 9/14/20 | 20 | 0/0/171 |
| Rail band | 2816 | 0/18/19 | 34 | 507/516/1047 |

- These numbers are direct S-array summaries, not Android outcomes; Android denominator validity must be measured. `(192.75,411.25)` has U_GG14/M_GG0 and is not a positive-mask anchor.
- The selected foreground rail is unchanged by background perturbation and may suppress U, overlay responses or mix layers; rail failures/zeros cannot be assigned to lens refraction. Excluding it from the primary domain does not erase its reported results.

## 7. Falsification boundary and deliverable

- [ ] Preserve counts/maps for literal output0/255, endpoint RGB changes and R/B cross-channel response; absence of endpoint saturation does not exclude internal clamps shifted by tint/offset. Do not remove suspect pixels after viewing results.
- Fixed tint/brightness/affine gains may cancel in a ratio; adaptive cover, transfer/gamma, clipping, changing sampling/gain, layered rail/background responses or haze need not. Compatible alpha with different U is consistent with a gain difference, not proof of that cause.
- Different alpha with strong denominators rejects only the stated surrogate under valid gates; it may arise from transport, blur/haze, geometry/rasterization, nonlinear/clipped colour or layer mixing. One mask does not identify a unique displacement, kernel, opacity, refraction strength or physical thickness.
- The earlier `docs/design/evidence/glass-slider-green-witness-20261115` binds actual source mapping, input ICC, raw pixel colour controls and preserved failures, but uses a G128/+104 baseline and six poses with unknown Android effective opacity. It cannot supply any missing S-condition endpoint or prove the current installed checkpoint.
- Deliver a new immutable analysis package with hashes, gate outcomes/unknowns, original and once-sampled arrays, fixed-domain tables and unclipped maps. No shader/default update, new candidate, animation claim, holdout claim or optical acceptance follows automatically from this finite comparison.
- Before executing, self-check synthetic cases: U=0/M=0; U=0/M>2E; negative U; weak U with contradiction; M/U outside[0,1]; common/empty alpha intersections; shared-baseline factor2; rail-zero suppression; known affine mapping; source/geometry/drift/colour-evidence rejection. Tests validate arithmetic/gates, not native optical parity.
