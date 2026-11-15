# Screen-floor headroom normalization: mathematical and source review

Status: read-only mechanism review, 2026-11-15. This is a proposed next intervention, not an amendment to an already captured candidate. No runtime source was edited, no candidate image or pixel array was read, and no build, test, device action or Git operation was performed. Only this Markdown and the companion JSON are new outputs.

## Finding

The current incremental floor uses a normalized lighting signal as a screen opacity. That changes the old additive floor's target increment into an increment multiplied by remaining brightness headroom. The loss is strongest on bright material. A shared headroom normalization can restore the old **weighted working-RGB increment**, while remaining bounded in each channel, only while enough headroom exists. Exact target preservation for all inputs and strictly avoiding new saturation are incompatible requirements. No algebraic simplification removes that tradeoff.

## Definitions and the reviewed source path

Let `c = coverage`, and let `G` be `glass` **after** the unchanged inherited additive shine at AGSL line1146. Let `d = addedFloor >= 0` be the already frozen angular-table delta times the already frozen depth-band response. The former additive floor would add the neutral vector `E * (1,1,1)`, where:

```text
E = c * d
H = max(c * (1,1,1) - G, 0)     // componentwise nonnegative remaining headroom
Y = dot(H, w), w = (.2126, .7152, .0722), sum(w) = 1
```

`E` is premultiplied. It is a scalar budget expressed in the shader's working RGB coordinates; calling it physical radiance is not established by this source inspection. Likewise, `Y` is weighted working-RGB headroom. The existing `kLuma` coefficients are reused, so there is no new fitted weight or runtime parameter.

The CPU creates eight original and floored angular knots, exporting only their delta in `uShineFloorLit`; AGSL interpolates that delta with the original knots and uses the unchanged `shineAcross` depth bands. `screenMinimumShine` defaults false. The current wrapper enables it only for the light Alert, with minimumShine.08 and inherited shine.16. Its current light Alert blur8, light Sheet blur10, original geometry and the CPU line configuration are independent source facts, not permission to retune them.

The current branch is:

```text
G = previousGlass + c * (flooredAngular * depthBand - d)
out = G + clamp(d, 0, 1) * H
```

In the frozen range where `0 <= d <= 1`, its increment is `d*H`. Per channel this is `E*(1-G_i/c)` for positive `c` and in-range `G_i`. Its weighted increment is `d*Y = E*(Y/c)`, rather than `E`. For a neutral normalized base .90 and d.08, the current increment is .008; for .95 it is .004. This attenuation is built into the compositing equation and cannot be repaired by describing d as an additive budget.

## Hard normalization: exact feasible budget, explicit saturation

The parent's hard proposal is:

```text
alphaHard = E / max(Y, E)       // evaluate only when E > 0
outHard = G + alphaHard * H
```

For finite `E >= 0` and `H >= 0`, `0 <= alphaHard <= 1`, so the new increment never exceeds a channel's remaining headroom. Its weighted increment is exactly `min(E,Y)` in real arithmetic. Thus if `Y >= E`, it delivers the frozen neutral additive budget E without a new exposure or strength parameter. If `Y < E`, no bounded positive operation can deliver E: the total remaining weighted headroom is only Y.

This is a meaningful redistribution. A channel already near white receives less of the increment; other channels with more headroom receive more. If `Y >= E`, the weighted total is conserved, but the original equal per-channel increment is **not** conserved. A low-weight channel may receive more than E. This is not a reconstruction of an unknown native reflection color.

Its unavoidable cost is severe near the ceiling: whenever `E >= Y`, alphaHard is1 and every channel that still has headroom reaches c. The result is white after the existing output cap. For neutral G this is exactly the old clamped additive result `min(G+E,c)`, including its white plateau. The `E=Y` join is continuous but has a derivative kink. A spatial region crossing that threshold can acquire a flat white region and an abrupt derivative change. Therefore the hard formula does **not** guarantee the previous no-new-255 clipping gate, natural highlight rolloff, or the user's soft iOS boundary appearance. It can pass a structural upper-bound check while failing those optical gates.

## Soft normalization: smallest smooth rational alternative, reduced budget

The parent's soft proposal is:

```text
alphaSoft = E / (Y + E)         // evaluate only when E > 0
outSoft = G + alphaSoft * H
```

For positive Y and finite E, `0 <= alphaSoft < 1`; with an initially in-range channel having positive headroom, its real-arithmetic value stays strictly below c. Exact white has H=0 and does not change. Its weighted increment is:

```text
deltaWeightedSoft = E*Y/(E+Y)
deltaWeightedSoft/E = Y/(E+Y)
```

It approaches the target E only when E is small relative to Y. At `E=Y`, it delivers exactly half the target, and when E is much greater than Y it approaches available headroom Y. Relative to hard normalization, its delivered weighted increment lies between one half and one times the hard result (for positive E,Y). It is smooth for positive E+Y and has no hard saturation join.

This is more brightness than current screen in the intended near-white regime, but **not universally** more. Against current unclamped d, the ratio is `c/(Y+E)`, so soft is larger only when `Y+E<c`; on a very dark neutral base below d it can be slightly smaller. Describing it as exact preservation of the old floor would be false. Float/half rounding and 8-bit output can still quantize a value below c to the maximum display code, so even soft's strict real-number inequality cannot substitute for the existing measured clipping gates.

## Exponential normalization: first-order budget, asymptotic neutral ceiling

The additional parent proposal is:

```text
alphaExp = 1 - exp(-E/Y)        // evaluate only when E>0 and Y>0
outExp = G + alphaExp*H
```

Because all three weights are positive and H is nonnegative, Y0 means every H component is0; skip the increment rather than divide. For E0, also skip it. For finite positive E/Y, `0<alphaExp<1` in real arithmetic. It shares both rational proposals' premultiplied scale covariance, neutral preservation, channel-difference scaling and existing-overrange limitations.

Its weighted increment and small-budget expansion are:

```text
deltaWeightedExp = Y*(1-exp(-E/Y))
                 = E - E^2/(2Y) + E^3/(6Y^2) - ...
```

Thus it preserves the frozen target to first order when E/Y is small, while avoiding a finite hard saturation threshold in real arithmetic. Soft rational also has first-order E but expands as `E-E^2/Y+...`; its second-order deficit is twice as large. For positive E,Y, the complete structural ordering is:

```text
E*Y/(E+Y) < Y*(1-exp(-E/Y)) < min(E,Y)
soft                    exponential                   hard
```

The lower inequality follows from `exp(r)>1+r` for r=E/Y>0; the upper one follows from `1-exp(-r)<min(r,1)`. This order is a mathematical relation along the same H direction, not a native-accuracy ranking. At E=Y, exponential delivers `(1-exp(-1))*E`, approximately.63212E, versus.5E soft and E hard. It still does not conserve the full feasible scalar budget at finite positive E/Y.

For a neutral normalized base `g` and `h=1-g>0`, with d fixed positive, the three relevant output forms are:

```text
hard:        min(g+d,1)
soft:        1 - h^2/(h+d)
exponential: 1 - h*exp(-d/h)
```

Exponential's slope with respect to g is `exp(-d/h)*(1+d/h)`, which approaches0 near white and stays between0 and1. Soft's slope is `h*(h+2d)/(h+d)^2`, likewise approaching0. Both have a gradual neutral shoulder; hard changes derivative abruptly at g=1-d. At fixed d>0, the exponential extension to h0 is smooth, with no real-arithmetic plateau below white. This is not a claim of joint differentiability at the degenerate E=Y=0 origin or a match to iOS's nonlinear rim optics.

Numerical care remains necessary. Direct `1-exp(-x)` cancels precision for small x; at large x the subtraction may round to1 even before the exponential underflows. The reviewed shader already contains `dockOneMinusExp(x)`, which uses the fixed fourth-order series `x-x^2/2+x^3/6-x^4/24` below its existing.01 numerical join, and the direct expression above it. Reusing that existing helper adds no fitted parameter or new curve strength. Its existing comment correctly makes no exact C1 join claim. Guarding Y>0 avoids0/0; an extremely large E/Y may still overflow the ratio and yield a numerical saturated limit. Half and final display quantization remain separate clipping risks even with a stable exponential implementation. Do not advertise an exact no-255 guarantee.

The minimal conceptual exponential fragment after the unchanged inherited addition is:

```glsl
float E = coverage * addedFloor;
if (E > 0.0) {
  float3 H = max(float3(coverage) - glass, 0.0);
  float Y = dot(H, kLuma);
  if (Y > 0.0) glass += H * dockOneMinusExp(E / Y);
}
```

This reuses existing numerical machinery but has more operations and a second zero guard than the rational formula. No performance comparison was run. The function remains a model choice; its existence in another shader path does not identify it as Apple's reflection transfer function. The parent-reported approximate124-point calibration simulation was not reproduced here and is not used to select or fit a curve. It is neither a GPU render nor independent validation.

## Premultiplication, zero, neutrality and color

- **Premultiplied covariance.** Scale both c and G by any positive factor t. Then E,H,Y scale by t, alphaHard and alphaSoft stay the same, and the output scales by t. Neither proposal needs a division by c or an arbitrary epsilon, so partial-coverage behavior is coherent in real arithmetic. This is a statement about the increment's algebra, not proof that every upstream source value is valid premultiplied color.
- **Zero-safe evaluation.** The existing `d>0` branch alone is insufficient: at c0 and valid G0, E=Y=0 gives0/0 in both proposals. Guard `if (E > 0)` before either division. For E0, apply no new increment. For E>0,Y0, both alpha values are1 but H0, so the output is unchanged. For hard and rational-soft, a second Y guard is optional, not necessary for division safety. Exponential requires the Y>0 guard because Y is its divisor. No new threshold or tunable epsilon is needed.
- **Existing overrange.** With valid `0 <= G_i <= c`, the new output stays within that upper bound and remains nonnegative. The inherited additive stage may already exceed c; H then becomes0 for that channel, so neither proposal repairs its existing excess. The unchanged final `min(glass,c)` still clips it. Neither the headroom clamp nor the final upper clamp proves a lower bound if upstream G is negative. Do not add a new pre-clamp to repair this silently, because it changes the inherited branch and attribution.
- **Neutral preservation.** Equal RGB components produce equal H, so both operations stay neutral. For valid in-range colored G, the common scalar gives `out = (1-alpha)*G + alpha*c*white`; pairwise channel differences are multiplied by the same nonnegative scalar. Channel order and ratios of nonzero channel differences are preserved in that working RGB space. It moves color toward white and reduces chroma; it does not preserve the old per-channel additive increment, arbitrary perceptual saturation, or a physical hue under an unverified transfer/color space.
- **Scope and color coordinates.** The generic added-floor branch contains no explicit transfer decode/encode; the shader has separate decode helpers used by specific Dock paths. This inspection does not establish that generic rim math runs in linear-light sRGB on every target. Reusing kLuma is internally consistent but does not make Y measured photometric luminance. Adding color conversion would be a separate intervention and is outside this frozen floor-only change.

## Is there a smaller parameter-free formula?

The two rational proposals already reduce to a scalar and one headroom vector. The following is the smallest useful **source-level** soft fragment after the existing inherited addition, without a new uniform, strength, exponent or epsilon:

```glsl
float E = coverage * addedFloor;
if (E > 0.0) {
  float3 H = max(float3(coverage) - glass, 0.0);
  glass += H * (E / (dot(H, kLuma) + E));
}
```

For the exact feasible-budget variant replace only the denominator by `max(dot(H,kLuma),E)`. The inherited reconstruction, default/zero-delta expressions, branch opt-in, knot interpolation, band response and final cap must remain untouched. Division by normalized headroom `H/c` is algebraically equivalent for c>0 but adds an unnecessary zero-coverage problem. `min(1,E/Y)` is equivalent to the hard formula with a Y guard, not a softer solution.

The even shorter componentwise `G + min(E,H)` is merely the old clamped additive floor for valid G. It caps channels independently, creates exact per-channel plateaus and changes channel-difference ratios; it is not a remedy for the rejected additive behavior. The exponential variant above is also parameter-free, with stronger first-order budget retention than rational-soft at its second-order term, but requires its Y guard and stable exponential machinery and still surrenders the exact target. There is no unique native curve implied by any of these normalizations.

An impossibility statement makes the decision concrete: for any bounded positive increment Delta satisfying `0 <= Delta_i <= H_i`, `dot(Delta,w) <= Y`. Demanding weighted increment E when E>Y is impossible. At E=Y, equality with all positive weights forces Delta=H, hence white. Therefore no formula can both preserve that full target in all cases and strictly avoid new saturation. Hard chooses exact feasible energy and permits saturation; rational-soft and exponential choose asymptotic headroom and explicitly sacrifice finite-budget energy.

## Native RGB limitations and next-step decision

These proposals express a compositing mechanism, not a measured iOS optical law. For a native target N to be represented by the shared-alpha headroom model at a given pixel, each nonzero-H channel would need the same `(N_i-G_i)/H_i` in[0,1], and a zero-H channel would need zero new increment. A native response that darkens one channel, changes channel ratios differently, has a colored highlight or uses a different backing sample cannot be deduced or reproduced from E and H alone. The empirical minimumShine.08 is not an identified Apple parameter.

Do not infer pane thickness, rim taper, blur, transmission, refraction, native RGB matching, motion behavior or held-out generalization from boundedness, a conserved scalar or these numerical examples. Actual inherited overflow, output quantization, material layering, ICC/working-space differences and source geometry remain separate concerns. Preserve every original fixed ROI, raw/ICC report, delta-zero top, body/dark/Sheet control, and per-channel clipping gate for a newly identified candidate; do not rewrite the prior frozen plan or accept a pooled mean.

Recommendation: if the next probe's explicit objective is exact feasible weighted increment, hard normalization is the direct no-new-parameter implementation, but preregister its white-plateau risk. For a declared objective of recovering the frozen floor at first order while retaining a gradual neutral ceiling, exponential is a defensible separate next mechanism probe using the existing stable helper. Rational-soft remains the smaller source fragment; both must declare their finite-budget loss in advance. This recommendation follows their structural properties, not the parent's approximate calibration MAEs. None is presently an accepted native match, and choosing between captured outputs after inspection requires separate candidate identities rather than a silently changed probe.
