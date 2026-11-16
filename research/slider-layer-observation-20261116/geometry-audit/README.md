# Geometry audit, 2026-11-16

[当前图文与证据索引 / Current illustrated evidence index](../../../docs/current-evidence-20261116.md#slider-android)

This audit does not establish a product bug. Original `GEOMETRY_CONFOUNDED` bounds/matrix gates still fail; no optical acceptance.

From the asset root, set `APP_ROOT` to the Android checkout:

```sh
python3 -B research/slider-layer-observation-20261116/geometry-audit/audit.py --app-root "$APP_ROOT"
# Recompute an existing output:
python3 -B research/slider-layer-observation-20261116/geometry-audit/audit.py --app-root "$APP_ROOT" --check
```

Standard library; creates only `audit.json`. Seven source/vendor hashes must match `FREEZE.json`; unique basenames identify them. This is not whole-checkout identity.

JSON separates `observed` original geometry/values, `calculated` decomposition checked against the prior report, and `hypothesis` interpretation.

Android dp and native pt retain the frozen study's 1:1 design-coordinate convention; this does not establish equal physical dimensions on the two devices.

| Width / height | dp |
| --- | ---: |
| Ideal37×24 ×1.55 | 57.35 /37.2 |
| Owner quantization | +0.128990 /+0.110923 |
| Carrier−owner | +0.007708 /−0.005008 |
| Carrier−native | +0.136697 /+0.105915 |

Density2.9750001 gives170.616255735×110.67000372px →171×111px, matching the owner. Mathematical constants, not Kotlin Float simulation; JSON retains residuals. Gates remain0.10pt /0.001 per element.

Offset(−0.003858823,+0.002487395)dp nearly fits opposite half-size residuals. **Not raw translation measurement.** Pivot, placement, raw transforms and opacity remain unknown.

![Existing full100 context](../../slider-android-response-20261116/evidence/rounds/control-pre/android-r2/trace/st01_rgb_star_d16-light-full100-held-screen.png)

`full100` is source coverage, business value0.50064063; no domain-endpoint or rail-bug evidence.

Next: run the unmodified [observer](../README.md) once when a device returns, using a new run ID; preserve failures. Its raw/pivoted/total transforms and alpha ancestry address these unknowns, not optical/endpoint acceptance. Material, size or rail changes lack evidence.
