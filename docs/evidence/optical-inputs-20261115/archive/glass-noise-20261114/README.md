# Fixed noise and source-point inputs

This packet contains two predeclared controlled-stimulus families. Each family has four independently seeded calibration images and four independently seeded test images. Every image is 750×1334 opaque RGB with a frozen embedded sRGB ICC profile, corresponding to a 375×667 point world at 2 pixels per point.

`protocol.json` fixes every seed, frequency, amplitude, dot count, palette and rasterization rule before generation. `freeze.json` records its hash together with the generator, this README, ICC bytes and Python dependency versions. The generator refuses to generate under a changed freeze. It never reads device screenshots or candidate outputs.

The RGB fields mix fine, medium and coarse Gaussian-correlated noise across the full canvas. The dot fields similarly mix three disk sizes over the full canvas; positions are independent uniform draws with no Dock-dependent placement. Each source point has an identity, continuous center coordinates in pixels and points, RGB, source contrast polarity, radius, seed, drawing order, overlap/edge labels and a local-constellation signature. The image top-left edge is (0,0); raster pixel (i,j) has center (i+.5,j+.5). Dot coordinates describe the ideal disk center before clipping or compositing.

Directory contracts:

- `calibration/manifest.json` uses `schema: 1`, `split: calibration` and IDs `c01`–`c08`. Merely generating this set does not mean any training or calibration has occurred.
- `test/manifest.json` uses `schema: 1`, `split: holdout` and the exact `n01`–`n08` IDs accepted by the existing external-input fixture. Every input has `id`, `file`, `sha256`; supplementary fields preserve source-pixel hash, kind, seed and point-table hashes.
- A dot input has `<id>.points.json` and `<id>.points.csv`. Overlapping, hidden or edge-clipped points are retained. The JSON also records source-neighborhood collisions rather than retrying a seed.

Run `python3 generate.py --freeze`, then `python3 generate.py --generate`, then `python3 generate.py --verify`. Freeze once; regenerating byte-identical files is permitted with the frozen dependencies and profile. `--verify` checks bytes, pixels, mode, profile, dimensions, IDs, seeds and source-point tables without displaying images. It does not build either application or operate a device.

Use the test set only to evaluate extrapolation of the unchanged D46.5 candidate in this batch. Do not use test captures to change its parameters. Seed independence does not make the stimulus design blind, random from a meaningful scene population, or representative of natural photographs. The stimuli do not establish that white noise is optimal, nor do they uniquely reveal native thickness, blur, refractive index or rendering internals.

Known source points support point correspondence, while distributed noise supports correlation. Preserve zero/multiple images, merging, disappearance and ambiguity; never force a nearest-neighbor answer. The method context is Rajendran, Bane and Vlachos, *A Dot-Tracking Methodology for Background-Oriented Schlieren*, DOI `10.1007/s00348-019-2793-3`, [author preprint](https://arxiv.org/abs/1812.10870). That work motivates dot priors and a distinction between tracking and correlation; this packet does not transfer its fluid-diagnostic model to a UI renderer.
