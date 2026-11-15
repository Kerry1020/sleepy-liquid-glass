# Fixed signed-G diagnostic plan

This supersedes the execution portion of the paused terminal-sRGB `PLAN.md`. It is an analysis plan, not a new capture instruction. The parent owns acquisition and the separate `slider-signedG-response-20261116` directory.

## Collection contract

Only four new rounds are scheduled: original five-point RGB-star control-pre; global encoded G −20; global encoded G −40; original control-post. Each uses its unchanged flat pair, real native material, original carrier/rail, original scene geometry and full100 endpoint. The existing +G20 round may be combined only if the collector finds the new original controls and the old original control **byte-for-byte identical**, in addition to all original endpoint/identity gates. A visual match or matching mean is insufficient. The star's G source values range from 48 to 232 (including convex antialiasing with 128), so −40 and +20 do not clip source bytes. The collector must verify the actual prescribed input differences rather than rely on this range argument.

The sole analyzer input is the collector's `signed-output.npz`, containing `t=[-40,-20,0,20]`, `output_rgb` of shape `(4,88,88,3)` and dtype `uint8`, and fixed `x`, `y`, `inset` arrays. `x/y` may be either full grids or 88-element centre vectors; `inset` is an `(88,88)` carrier-capsule approximation. The analyzer does not independently possess pre/post or old-control arrays, so it does not assert their gate outcomes. The collector is responsible for withholding this input if a gate fails. Hash the sole input and report that limitation.

## Questions and fixed endpoint tolerances

At every original pixel and for each output channel independently, test:

1. Ordinary affine with the expected sign.
2. `y(u)=clip(a+b*u,L,U)`, `b>=0`, with arbitrary per-pixel/channel `a,b,L,U` and `0<=L<=U<=255`.
3. General monotonic response.

For output G use `u=t`; for output R/B use `u=-t` and reorder observations by ascending `u`. Normalise the four equally spaced `u` coordinates to `z=0,1,2,3` for exact rational slope bounds, reporting slope per encoded input byte by dividing by 20. Endpoint tolerances are **T=1,4,8 bytes**, interpreted as `|predicted continuous endpoint - observed byte| <= T`. Clip each observation interval to `[0,255]`. No extra half-byte or old finite-difference tolerance is added. These are compatibility bounds, not stochastic confidence levels.

Report the original full ROI; primary `y<422,inset>=1`; above-rail `y<422`; rail band `422<=y<438`; below-rail `y>=438`; the carrier inset bins `[0,1),[1,3),[3,8),[8,infinity)` both across the ROI and above rail; and outside-carrier `inset<0`. These masks do not estimate optical alpha. Do not select a mask from a newly observed anomaly.

## Exact finite clipped-affine test

Enumerate the 15 contiguous branch assignments `(ell,h)` with `0<=ell<=h<=4`: indices before `ell` are on a low platform, indices `[ell,h)` are linear, and indices from `h` are on a high platform. Equality at a branch boundary is allowed. Intersect all low-platform observation intervals to obtain `[Llo,Lhi]`; do the same for high-platform `[Ulo,Uhi]`. Reject empty intersections and, when both platforms occur, reject `Llo>Uhi`.

For the middle observations retain their bounds on `a+m*z`. A low platform also requires `a+m*z_lastLow<=Lhi` and, if a middle exists, `a+m*z_firstMiddle>=Llo`. A high platform requires `a+m*z_firstHigh>=Ulo` and, if a middle exists, `a+m*z_lastMiddle<=Uhi`. If there is no middle but both platforms occur, additionally retain `a+m*z_lastLow<=Uhi` and `a+m*z_firstHigh>=Llo`; these preserve `L<=U` and must not be omitted.

All remaining constraints have the form `a>=lower-m*zLower` or `a<=upper-m*zUpper`. Eliminate `a` analytically: every lower/upper pair requires `m*(zUpper-zLower)<=upper-lower`. Intersect these half-lines with `m>=0`. A nonempty interval is necessary and sufficient for that branch. Its union over the 15 branches is the exact clipped-affine feasible set under this observation model. No SciPy LP sweep, arbitrary parameter cap, iterative fit or arbitrary 3×3 colour fit is used. The ordinary affine test is the branch with all four points linear. General monotonic feasibility follows from the ordered observation intervals.

## Before loading the new NPZ

Run `analyze-signed-g.py --self-test`. Construct cases covering ordinary affine; low/high/both platforms including an empty sampled middle; constant response; monotonic but non-clipped-affine response; nonmonotonic response; the counterexample in `LIMITS.md`; tolerance nesting; generated clipped examples; and explicit witness reconstruction. The self-test must not load original or new output pixels. Save a small self-test receipt binding the script hash. The analysis path also reruns these self-tests before loading its sole NPZ input.

## Decision limits

Affine rejection with clipped-affine compatibility is evidence that the **unclipped encoded** simplification was insufficient. Clipped-affine rejection with monotonic compatibility rejects a single encoded linear segment bracketed by two platforms, while leaving other monotonic transfers possible. Monotonic rejection challenges the fixed-sign description, conditional on collection gates. Non-rejection is not pipeline identification or visual acceptance.

In particular, R remaining at 6 for +20 and recovering on negative G is compatible with an internal floor; it does not uniquely prove one. R staying constant at both −20 and −40 does not exclude an arbitrarily deep latent floor. The original and negative-G responses must be reported even when they are uninformative. Neutral-field signed steps are deferred; no neutral acquisition is authorized by this plan.
