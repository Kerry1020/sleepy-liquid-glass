# Source support excerpts

Recorded r2 material/shader hashes are in profile.json. These excerpts are explanatory source evidence; no optical thickness is measured.

## LiquidGlassStyle.kt

Repository path: `libraries/liquid-glass/runtime/src/androidMain/kotlin/com/lingion/sleepy/ui/component/liquidglass/LiquidGlassStyle.kt`

```text
116:         darkLowTone = darkLowTone?.copy(blend = darkLowTone.blend * amount),
117:     )
118: }
119: 
120: /** Optional edge-only channel separation. Blend controls continuous transitions from the inherited profile. */
121: data class LiquidGlassDispersionProfile(val widthDp: Double, val blend: Double = 1.0)
122: 
123: /** Finite quadratic inward sampling shoulder; null keeps the inherited circular section. */
124: data class LiquidGlassRefractionShoulder(val widthDp: Double, val blend: Double = 1.0)
125: 
548:          * The tint is the 8-bit representation of the native26.5 tonal-light fit;
549:          * its multi-background GPU comparison is recorded in alignment notes73.
550:          * The RGB-star/native26.5 calibration constrains a finite inward shoulder;
551:          * it changes common sampling rather than widening channel separation.
552:          * This is an engineering fit, not an identified physical thickness.
553:          */
554:         fun sliderLens(dark: Boolean): LiquidGlassStyle =
555:             sliderLensCheckpoint(dark).copy(
556:                 refraction = 7.8,
557:                 refractionShoulder = LiquidGlassRefractionShoulder(7.5),
558:             )
559: 
560:         private fun sliderLensCheckpoint(dark: Boolean): LiquidGlassStyle =
561:             LiquidGlassStyle(
562:                 tint = Color(0x21C5C5C3),
563:                 blur = 0.0,
564:                 refraction = 2.15,
565:                 frostBand = LiquidGlassFrostBand(1.5, 7.0, .5, 1.1),
566:                 bevel = 5.5,
567:                 saturation = 1.0,
568:                 brightness = 1.0,
569:                 rim = if (dark) 0.3 else 0.6,
570:                 rimWidth = 1.1,
571:                 endShade = 0.045,
572:                 dispersion = 5.0,
573:                 dispersionProfile = LiquidGlassDispersionProfile(widthDp = 6.5),
574:                 rimBlur = 1.5,
575:                 hairline = 0.42,
576:             )
577: 
578:         /**
579:          * Keep the range checkpoint until the smaller lenses have their own
580:          * source-transport verification. Single-slider calibration cannot identify it.
581:          */
582:         fun rangeSliderLens(dark: Boolean): LiquidGlassStyle = sliderLensCheckpoint(dark)
583: 
```

## liquid_glass.agsl

Repository path: `libraries/liquid-glass/runtime/src/androidMain/assets/shaders/liquid_glass.agsl`

```text
925:         * (1.0 - smoothstep(bevel, halfMinor, inset));
926:   } else {
927:     // A bevel of circular profile, fitted to small panes: flat where it meets
928:     // the face and steepening toward the rim, which reads from so far inside
929:     // that its outermost band shows the content squeezed and mirrored.
930:     float depth = min(uOptics.x, max(uRefractionLimit, 0.0) * halfMinor) * (1.0 - sqrt(1.0 - rise * rise));
931:     // Keep the legacy expression above at power1, avoiding a pow rounding change.
932:     // The host binds a strictly positive finite exponent for the flat endpoint.
933:     if (uRefractionProfilePower != 1.0) {
934:       float profile = 1.0 - sqrt(max(1.0 - rise * rise, 0.0));
935:       depth = min(uOptics.x, max(uRefractionLimit, 0.0) * halfMinor) * pow(profile, uRefractionProfilePower);
936:     }
937:     if (uRefractionShoulder.y > 0.0) {
938:       float width = max(min(uRefractionShoulder.x, halfMinor * 0.5), 1e-3);
939:       float remaining = max(1.0 - inset / width, 0.0);
940:       float shoulderDepth = min(uOptics.x, max(uRefractionLimit, 0.0) * halfMinor)
941:           * remaining * remaining;
942:       depth = uRefractionShoulder.y >= 1.0 ? shoulderDepth
943:           : mix(depth, shoulderDepth, uRefractionShoulder.y);
944:     }
945:     shift = -normal * depth;
946:     if (uLateralRefractionGain > 0.0) {
947:       shift.x += panelLateralShift(centered.x, halfSize.x, depth, normal.y, uLateralRefractionGain);
948:     }
```

## LiquidGlassShader.kt

Repository path: `libraries/liquid-glass/runtime/src/androidMain/kotlin/com/lingion/sleepy/ui/component/liquidglass/LiquidGlassShader.kt`

```text
334:             if (profilePower.isFinite()) {
335:                 profilePower.coerceIn(1e-3, Float.MAX_VALUE.toDouble()).toFloat()
336:             } else 1f,
337:         )
338:         val shoulder = style.refractionShoulder
339:         val validShoulder = shoulder != null && shoulder.widthDp.isFinite() &&
340:             shoulder.widthDp >= 1e-3 && shoulder.blend.isFinite()
341:         put("uRefractionShoulder",
342:             if (validShoulder) checkNotNull(shoulder).widthDp.coerceAtMost(32.0).toFloat() else 0f,
343:             if (validShoulder) checkNotNull(shoulder).blend.coerceIn(0.0, 1.0).toFloat() else 0f)
344:         val frostBand = style.frostBand
345:         val validFrostBand = frostBand != null && listOf(frostBand.startDp, frostBand.endDp,
346:             frostBand.featherDp, frostBand.blurDp, frostBand.blend).all { it.isFinite() } &&
347:             frostBand.startDp >= 0.0 && frostBand.endDp <= 32.0 &&
```
