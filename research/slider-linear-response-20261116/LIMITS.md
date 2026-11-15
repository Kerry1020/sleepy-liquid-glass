# What the existing colour evidence does and does not reject

The earlier raw-encoded U tests reject particular **unclipped** shared brightness/saturation families. They do not reject a saturation stage followed by internal clipping and a fixed positive gain/offset. The proposed terminal-sRGB diagnostic in `PLAN.md` is paused; no new original output PNG was decoded for it, and no gamma-model result is claimed.

At world `(192.75,411.25)`, the already reported native encoded RGB values are:

| condition | R | G | B |
|---|---:|---:|---:|
| original | 6 | 100 | 96 |
| global R +20 | 32 | 97 | 93 |
| global G +20 | 6 | 114 | 87 |
| global B +20 | 6 | 99 | 114 |

Here is a concrete counterexample to interpreting the output-row asymmetry as requiring row-conditioned gamma or a row-conditioned saturation matrix. Define

`F_i(j) = O_i + clip(X_i + A*1[i=j] + C*w_j, 0, H)`

with `w=(.2126,.7152,.0722)`, `A=30`, `C=-14`, `H=27`, `X=(-1.0236,13,9)`, and `O=(6,87,87)`. The baseline is `O+clip(X,0,H)`. Rounding these predictions to bytes reproduces every value in the table. The common diagonal/offdiagonal coefficients are consistent with an oversaturation-type structure; the R baseline and both negative offdiagonal responses are at a lower platform, while other observations reach an upper platform.

This is an existence counterexample only. The free latent baselines and channel offsets are not inferred native parameters, and their relationship to the actual sampled source has not been established. It is not an Android correction, an actual native-pipeline identification, or proof of a globally shared saturation model. Its purpose is to show why rejecting the earlier **unclipped** family does not exclude a clipped family.

The next signed-G test separates three restricted observable descriptions: ordinary affine, single-channel clipped-affine, and general monotonic response. Each RGB output is retained separately. Passing clipped-affine is only compatibility with a permissive per-channel description at four finite source steps; it does not establish a common saturation matrix, common thresholds, common gain, processing order, geometry, optical thickness, or dynamic behaviour. Rejecting encoded clipped-affine does not reject a clamp acting in linear light followed by encoding, or another monotonic transfer.

The general monotonic test has a broader conditional interpretation: with unchanged nonnegative sampling, fixed-sign colour mixing, channelwise monotonic clipping/transfer, and the collection controls passing, global G must not increase output R/B and must not decrease output G. A violation rejects that fixed-sign description at the stated endpoint tolerance. It does not establish which native stage changed.
