# Analysis implementation v1.1

The acquisition source specs, frozen protocol, analysis-plan and v1 script remain byte-identical. No new witness/control capture was read to make these corrections.

- The old native calibration PNG mode inspection showed opaque RGBA8 rather than RGB8. v1.1 validates every alpha byte is 255, then retains the original R/G/B bytes directly. No color conversion or recompositing.
- An explicitly missing opacity remains unknown in the enriched evidence format, consistent with the frozen protocol. It permits labeled raw diagnostics without mapping acceptance.
- An empty common interior produces a null p99 and an uncertain flat gate, rather than nonfinite JSON.
- Geometry-only connected component results are cached for repeated identical masks. Signal-weighted centroids still use each actual field.
- Synthetic fixtures propagate an explicit SYNTHETIC_ONLY_NO_CAPTURE_EVIDENCE label.

No threshold, domain, support definition, geometry tolerance, frozen target, source identity, or optical decision criterion changed. v1.1 output records both its own SHA and the frozen v1 criteria SHA.

The reviewer identified two additional implementation corrections before v1.1 was used on any new capture: each Android capture's geometry-result path/hash is now required to equal the accepted index.source_result, and the original-pixel flat residual p99 is required alongside the interpolated grid p99. A missing original-byte flat comparison remains uncertain. Neither correction changes the frozen tolerance or interpretation rule.

Source-arithmetic clarification: at antialiased pixels the exact encoded witness G change is integer `floor((104*coverage_count+8)/16)`, as already implemented in the frozen generator and hashes. The protocol's `104*leftBlueCoverage` describes the unquantized coverage quantity; odd coverage counts incur +0.5 encoded byte rounding. Analysis uses the actual hashed source bytes, never the unquantized shorthand.

The actual output screenshot mapping is also cross-checked: native index density/dimensions/origin must agree with strict session scale/window and actual external source canvas; Android full-screen index density/origin must agree with held source LayoutCoordinates. A generic enriched evidence entry additionally requires `actual_screenshot_pixels_per_world_unit`, `actual_world_origin_in_screenshot_px` and `actual_screenshot_dimensions_px`. A missing or inconsistent screenshot mapping cannot silently change the coordinate system.

The protocol's full100 “flat-top” refers to the capsule's straight central top boundary segment, not a proof that the whole star samples a zero-displacement interior. The star's tip is still near that boundary. full100 remains a positive G/contrast reference and a comparison for cap-only changes; it does not isolate an unmodified interior or negative G stimulus.
