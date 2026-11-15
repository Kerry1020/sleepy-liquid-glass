# Independent review: Alert CPU-line removal plus0.08 shine floor

Scope: read-only source inspection and arithmetic of a proposed engineering candidate. No product code change, build, device operation, fitted coefficient, or parity acceptance is performed.

## Other edge paths

The current `LiquidGlassStyle.alert` factories explicitly set `rim=0`, and inherit `hairline=0`, `hairlineSide=null` (resolved to0). `LiquidGlassShader.build` therefore supplies zero regular screened rim and zero shader dark hairline. The explicit `LiquidGlassRim` additive directional table and `GlassControlModifier.onDrawFront` black0.5dp CPU stroke are the remaining direct pane edge paths. `GlassAlertDialog`/`GlassDatePickerDialog` route the pane through this modifier; no second explicit border was found in those wrappers. Material matching uses tonalElevation0; this inspection does not infer the private Material implementation or arbitrary caller-provided modifiers are border-free.

## Floor distribution and actual invariants

`minimumShine` is an absolute floor on each of the eight angular brightness knots, not a fraction of `shine` and not restricted to exact horizontal normals. For light Alert shine0.16, the original knot brightness values are:

```
[0.1600,0.1088,0.0768,0.0608,0.0272,0.0112,0.0048,0]
```

A0.08 floor makes:

```
[0.1600,0.1088,0.0800,0.0800,0.0800,0.0800,0.0800,0.0800]
```

For dark shine0.22, the values become:

```
[0.2200,0.1496,0.1056,0.0836,0.0800,0.0800,0.0800,0.0800]
```

With the actual320×172dp Alert and34dp corner radius, the first nonzero angular knot is about0.898rad. The fixed top neutral x140..<235 interval spans turns at most about0.503rad. Thus the floor leaves that fixed top **shader additive shine** unchanged; lateral corners and side orientation change. It also retains original shine depth bands, raster coverage integration, contour geometry, refraction, blur, tint and saturation.

However, setting CPU `flat=0` removes the original flat black opacity0.12(light)/0.03(dark) from the top edge. Therefore the total top pixel result is **not** invariant even though its shader shine value is unchanged. The first Android top pixel is currently darker than the next; line removal can shift the peak outward and can also clip it. The candidate must not be described as changing sides only or maintaining top pixels.

For a2px/dp straight side, the first interior pixel integrates the existing shine bands over0..<0.5dp: `(1/3×1 +1/6×0.7)/0.5 =0.9`. At full coverage, an absolute floor0.08 therefore adds about18.36 encoded RGB counts to the first pixel before clamping, and about11.152 counts to the second. This is comparable in scale to the measured native side peak-minus-shoulder16.00/20.00, but does not establish an accepted native coefficient: side body colors, remaining colored halos, raster coverage and the removed CPU line also matter.

## Smallest useful bounded verification

Use the existing same-source Alert baseline and freeze two mechanism conditions rather than silently conflating factors:

1. CPU side/corner/flat0, minimumShine0: isolates dark-line removal and its top/side effects.
2. CPU side/corner/flat0, minimumShine0.08: isolates the added angular floor against condition1.

If one combined candidate is captured first, retain the inability to attribute total changes to either factor; add the line-only condition when a defect needs attribution. Keep Sheet/Dock/MD unchanged. Use existing same geometries and all registered fixed RGB profiles rather than selecting a successful side peak. Light and dark must be checked, because the removed CPU opacities and original shine differ. The present native new-probe data are light only; dark results cannot be called a matched native new-probe acceptance without an appropriate existing dark reference.

Record separately: first four pixels, peak position, RGB maxima/clipping, source/exterior controls, top/side/corner changes, and the existing body/deeper controls. The floor table ends at5dp contour inset; far-body invariance should be checked against the actual contour support, not a nominal rounded rectangle distance. Native FWHM remains unresolved under the original three-pixel gate. Do not invent a narrower support or subpixel contour fit to make the two-pixel peak produce a width.

This review supports a bounded Alert-only mechanism experiment. It does not authorize a default switch based solely on the rough18.36-count arithmetic or extrapolate it to Sheet thickness.
