package com.lingion.sleepy.ui.component

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.ColorSpace
import android.os.Build
import android.os.SystemClock
import androidx.compose.foundation.background
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.requiredSize
import androidx.compose.foundation.layout.width
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.key
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clipToBounds
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Rect
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.FilterQuality
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.input.pointer.PointerEventPass
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.LayoutCoordinates
import androidx.compose.ui.layout.onGloballyPositioned
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.platform.LocalView
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.test.junit4.v2.createComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performTouchInput
import androidx.compose.ui.unit.Density
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.IntSize
import androidx.compose.ui.unit.dp
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.filters.SdkSuppress
import androidx.test.platform.app.InstrumentationRegistry
import com.lingion.sleepy.ui.component.liquidglass.GlassBackground
import com.lingion.sleepy.ui.component.liquidglass.GlassHost
import com.lingion.sleepy.ui.component.liquidglass.GlassSlider
import com.lingion.sleepy.ui.component.liquidglass.GlassSliderDragMapping
import com.lingion.sleepy.ui.component.liquidglass.GlassSliderThumbMetrics
import com.lingion.sleepy.ui.component.liquidglass.LocalDockInputTimeNanos
import com.lingion.sleepy.ui.component.liquidglass.LiquidGlassCornerRadii
import com.lingion.sleepy.ui.component.liquidglass.LiquidGlassShader
import com.lingion.sleepy.ui.component.liquidglass.LiquidGlassStyle
import com.lingion.sleepy.ui.theme.LocalUiStyle
import com.lingion.sleepy.ui.theme.SleepyThemeProvider
import com.lingion.sleepy.ui.theme.ThemePresets
import com.lingion.sleepy.ui.theme.UiStyle
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Assume.assumeTrue
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File
import java.security.MessageDigest
import java.util.concurrent.ConcurrentLinkedQueue
import kotlin.math.abs
import kotlin.math.roundToInt

/**
 * Opt-in REST/settled-HELD optical evidence at the current native SwiftUI Slider anchor.
 * A single bounded fixture translation aligns background sampling, not product geometry.
 * Production rendering and pointer handling remain unchanged; this is not natural motion.
 */
@RunWith(AndroidJUnit4::class)
@SdkSuppress(minSdkVersion = 33)
class NativeSliderOpticalWorldRenderTest {
    @get:Rule val compose = createComposeRule()

    private data class Scene(val background: String, val dark: Boolean, val showSlider: Boolean,
                             val coverageStageId: String? = null) {
        val name get() = "${background}-${if (dark) "dark" else "light"}" +
            (coverageStageId?.let { "-$it" } ?: "")
    }

    private data class FixedShapeStage(val id: String, val requestedLensCenter: Offset,
                                       val requestedFinger: Offset, val actualCarrierTarget: Offset?,
                                       val source: JSONObject)

    private data class FixedShapePlan(val shapeId: String, val flatId: String,
                                      val stages: List<FixedShapeStage>, val source: JSONObject,
                                      val specFile: String, val sha256: String,
                                      val referenceQuarterCenter: Offset)

    private data class World(val source: OpticalLayoutGeometry, val host: OpticalLayoutGeometry) {
        fun json() = JSONObject().put("source", source.json()).put("glass_background_host", host.json())
            .put("requested_size_dp", JSONArray(listOf(375, 667)))
            .put("outside_world", "opaque neutral #F0F0F5 recorded in the same GlassBackground")
    }

    private data class SliderGeometry(
        val world: World,
        val holder: OpticalLayoutGeometry,
        val owner: OpticalLayoutGeometry,
        val carrier: OpticalLayoutGeometry,
        val holderSemanticRoot: Rect,
        val carrierSemanticRoot: Rect,
        val windowOrigin: Offset,
        val screenOrigin: Offset,
    ) {
        val holderRoot get() = holder.screenRect.translate(-screenOrigin)
        val ownerRoot get() = owner.screenRect.translate(-screenOrigin)
        val carrierRoot get() = carrier.screenRect.translate(-screenOrigin)
        val carrierWorld get() = carrier.screenRect.inWorld(world.source)
        val evidenceRoot get() = Rect(
            minOf(holderRoot.left, carrierRoot.left - 6f * world.source.density),
            minOf(holderRoot.top, carrierRoot.top - 6f * world.source.density),
            maxOf(holderRoot.right, carrierRoot.right + 6f * world.source.density),
            maxOf(holderRoot.bottom, carrierRoot.bottom + 6f * world.source.density),
        )

        fun json() = JSONObject().put("background_world", world.json())
            .put("outer_holder", holder.json()).put("isotropic_thumb_owner", owner.json())
            .put("affine_visual_carrier", carrier.json())
            .put("holder_actual_root_rect_px", holderRoot.json())
            .put("holder_semantic_root_rect_px", holderSemanticRoot.json())
            .put("owner_actual_root_rect_px", ownerRoot.json())
            .put("visual_carrier_actual_root_rect_px", carrierRoot.json())
            .put("visual_carrier_semantic_root_rect_px", carrierSemanticRoot.json())
            .put("visual_carrier_world_rect_dp", carrierWorld.json())
            .put("visual_carrier_world_center_dp", carrierWorld.center.json())
            .put("optical_evidence_root_rect_px", evidenceRoot.json())
            .put("geometry_source", "Actual attached LayoutCoordinates map all four corners and unit basis through the production transform; semantic boundsInRoot are recorded separately. Visual carrier bounds exclude shadow and are not an alpha-mask or a claim of native geometry parity. Six dp around the carrier, union the whole touch holder, is retained as capture/readiness room.")
            .put("content_origin_in_window_px", windowOrigin.json())
            .put("content_origin_on_screen_px", screenOrigin.json())
    }

    private val externalInputs = linkedMapOf<String, Bitmap>()
    private var externalManifest: JSONObject? = null
    private var surface: OpticalCaptureWindow? = null
    private var sourceCoordinates: LayoutCoordinates? = null
    private var hostCoordinates: LayoutCoordinates? = null
    private var coverageHolderCoordinates: LayoutCoordinates? = null
    private var density = 1f
    private var fontScale = 1f
    private var systemFontScale = 1f
    private var currentValue = .25f
    private var pointerDown = false
    private var heldDownComposeMs: Long? = null
    private var heldDownUptimeMs: Long? = null
    private val fixedTranslationPx = mutableStateOf(Offset.Zero)
    private val valueEvents = ConcurrentLinkedQueue<JSONObject>()
    private val finishEvents = ConcurrentLinkedQueue<JSONObject>()
    private val inputEvents = JSONArray()
    private val dispatchedPointerEvents = ConcurrentLinkedQueue<JSONObject>()

    @Test fun captureNativeSliderOpticalWorld() {
        try {
            captureOpticalWorld()
        } finally {
            externalInputs.values.forEach(Bitmap::recycle)
            externalInputs.clear()
            externalManifest = null
        }
    }

    private fun captureOpticalWorld() {
        val arguments = InstrumentationRegistry.getArguments()
        val fixedShapeCoverage = arguments.getString("glassSliderFixedShapeCoverage") == "true"
        assumeTrue("Enable with glassSliderOpticalWorld=true or glassSliderFixedShapeCoverage=true",
            arguments.getString("glassSliderOpticalWorld") == "true" || fixedShapeCoverage)
        fun selected(argument: String, allowed: List<String>): List<String> {
            val result = arguments.getString(argument)?.split(',')?.map(String::trim)?.distinct() ?: allowed
            require(result.isNotEmpty() && result.all { it in allowed }) { "$argument must select from $allowed" }
            return result
        }
        val externalDirectory = arguments.getString("glassSliderOpticalExternalInputsDirectory")
        externalDirectory?.let(::loadMarkerInputs)
        if (fixedShapeCoverage) {
            require(arguments.getString("glassSliderOpticalThemes") in listOf(null, "light")) {
                "First fixed-shape feasibility supports light only"
            }
            val plan = loadFixedShapePlan(checkNotNull(externalDirectory) {
                "Fixed shape coverage requires glassSliderOpticalExternalInputsDirectory"
            }, arguments.getString("glassSliderFixedShapeSpecFile") ?: "shape-spec.json")
            captureFixedShapeCoverage(plan, arguments.getString("glassSliderOpticalRunId"))
            return
        }
        val backgrounds = selected("glassSliderOpticalBackgrounds",
            externalManifest?.getJSONArray("inputs")?.let { rows ->
                (0 until rows.length()).map { rows.getJSONObject(it).getString("id") }
            } ?: OpticalBackground.entries.map { it.name })
        val themes = selected("glassSliderOpticalThemes", listOf("light", "dark")).map { it == "dark" }
        val runId = (arguments.getString("glassSliderOpticalRunId") ?: System.currentTimeMillis().toString())
            .replace(Regex("[^A-Za-z0-9_-]"), "_")
        val directory = File(InstrumentationRegistry.getInstrumentation().targetContext.getExternalFilesDir(null),
            "slider-optical-world/$runId").apply { check(isDirectory || mkdirs()) }
        val captures = JSONArray()
        val baselines = JSONArray()
        val observations = JSONArray()
        val calibration = JSONObject().put("status", "pending").put("maximum_correction_per_axis_dp", 1)
            .put("purpose", "Optical material sampling alignment only; excludes native/product geometry acceptance.")
            .put("policy", "Derive one fixture-only translation from the first raw REST visual center; each axis must be within1dp or abort. Reuse it unchanged across backgrounds, themes, HELD and post-CANCEL REST. Never retune by theme, value or state; never move or stretch the backing world.")
        val result = JSONObject().put("schema", 1).put("status", "running").put("run_id", runId)
            .put("sdk", Build.VERSION.SDK_INT).put("model", Build.MODEL).put("fingerprint", Build.FINGERPRINT)
            .put("scope", "Production GlassSlider + GlassHost/GlassBackground on ordinary backing, value.25, width335dp; fixed375x667dp source world. REST and settled center-HELD before cleanup CANCEL. Optical comparison only; capture/coordinate validity is not material, geometry or natural-motion parity.")
            .put("native_reference", "Measured source72 iOS26.5 SwiftUI Slider held signals across all8 verified optical captures:375x667pt source world; actual targetFramePt(x20,y414,w335,h31), actualDown(113.5,430)pt, selected value25%. Observer screenshots start at least0.65s after actualDown. Older AX-normalized holds are a distinct geometry and must not be relabeled.")
            .put("native_nominal_control_world_xywh_pt", JSONArray(listOf(20, 414, 335, 31)))
            .put("native_quarter_thumb_center_world_pt", NATIVE_CENTER.json())
            .put("android_uncalibrated_touch_holder_world_xywh_dp", JSONArray(listOf(20, 406, 335, 48)))
            .put("placement_policy", "Unmodified production335dp width and48dp touch height; nominal origin(20,406)dp. Production37dp REST thumb yields ideal local quarter center93dp rather than native93.5pt. Export the first actual residual before one bounded translation; preserve production size, rail, ticks, shape and all subsequent state changes.")
            .put("source_world_policy", "Required375x667dp at the observed GlassBackground top-left, fully visible with unit local-to-screen axes. Fixture-only fontScale1 and LTR. Ordinary backing only; no glass parent panel.")
            .put("theme_preset", ThemePresets.KEY_DEFAULT)
            .put("external_input_manifest", externalManifest ?: JSONObject.NULL)
            .put("inputs", externalManifest?.getJSONArray("inputs")
                ?: JSONArray(backgrounds.map { OpticalBackground.valueOf(it).metadata() }))
            .put("selected_themes", JSONArray(themes.map { if (it) "dark" else "light" }))
            .put("clock_policy", "Compose clock supplied to production Slider input through LocalDockInputTimeNanos;1600ms settle before REST/HELD. Real uptime exported independently. This synthetic clock demonstrates stable optical states and is not native real-time dynamics.")
            .put("capture_policy", "Actual Activity PixelCopy after HWUI commit plus composited display; existing>=99.5% RGB3 readiness threshold unchanged. Exclude only actual systemBars/displayCutout for control-screen readiness and require the entire holder, carrier and6dp carrier shadow room inside the compared region. Save full Window/display PNGs independently.")
            .put("input_policy", "DOWN at the actual mapped REST visual-carrier center, no MOVE or UP, capture while held; cleanup CANCEL afterwards. Quarter value and empty callbacks required throughout. No release dynamics or UP commit evidence.")
            .put("calibration", calibration).put("baselines", baselines).put("captures", captures)
            .put("geometry_observations", observations).put("input_events", inputEvents)
        val report = File(directory, "result.json")
        fun save() {
            result.put("density", density).put("font_scale", fontScale).put("system_font_scale", systemFontScale)
                .put("fixed_translation_px", fixedTranslationPx.value.json())
                .put("value_events", JSONArray(valueEvents.toList())).put("finish_events", JSONArray(finishEvents.toList()))
            report.writeText(result.toString(2))
        }
        save()
        val scene = mutableStateOf(Scene(backgrounds.first(), themes.first(), false))
        try {
            // Fail before acquisition if compilation or production uniform packing
            // would silently send the control down its blur fallback path.
            val shader = android.graphics.RuntimeShader(LiquidGlassShader.shaderSource(
                InstrumentationRegistry.getInstrumentation().targetContext))
            listOf(false, true).forEach { dark ->
                listOf(LiquidGlassStyle.sliderLens(dark), LiquidGlassStyle.rangeSliderLens(dark)).forEach { material ->
                    listOf(0.0, .5, 1.0).forEach { lift ->
                        LiquidGlassShader.build(size = Size(58f, 38f),
                            corners = LiquidGlassCornerRadii(19f, 19f, 19f, 19f), style = material.scale(lift),
                            atlasSizePx = Size(375f, 667f),
                            sampling = LiquidGlassShader.sampling(Offset.Zero, 1f, Rect(0f, 0f, 375f, 667f)))
                            .forEach { (name, values) -> shader.setFloatUniform(name, values) }
                    }
                }
            }
            result.put("production_shader_compile_and_bind", "passed: single/range, two themes, lift0/0.5/1; not exhaustive GPU-driver introspection")
            compose.setContent {
                val actualDensity = LocalDensity.current
                SideEffect { systemFontScale = actualDensity.fontScale }
                CompositionLocalProvider(
                    LocalDensity provides Density(actualDensity.density, fontScale = 1f),
                    LocalLayoutDirection provides LayoutDirection.Ltr,
                    LocalDockInputTimeNanos provides { compose.mainClock.currentTime * 1_000_000L },
                ) { Fixture(scene.value) }
            }
            compose.waitForIdle()
            compose.mainClock.autoAdvance = false
            for (dark in themes) for (background in backgrounds) {
                val current = Scene(background, dark, false)
                result.put("active_scene", current.name).put("active_stage", "plain-background")
                compose.runOnIdle { scene.value = current; valueEvents.clear(); finishEvents.clear() }
                settle()
                val activity = checkNotNull(surface)
                assertTrue("Hardware accelerated capture required", activity.root.isHardwareAccelerated)
                val world = observeWorld()
                observations.put(JSONObject().put("scene", current.name).put("phase", "background").put("world", world.json()))
                validateWorld(world)
                save()
                val stem = "${current.name}-background"
                val baselineWindow = activity.capture()
                baselineWindow.saveOpticalPng(File(directory, "$stem-window.png"))
                var baselineScreen: Bitmap? = null
                try {
                    val ready = awaitOpticalBackgroundScreen(activity, baselineWindow, density, directory, stem)
                    baselineScreen = ready.bitmap
                    ready.bitmap.saveOpticalPng(File(directory, "$stem-screen.png"))
                    val contentWindow = activity.origin().let { Offset(it[0].toFloat(), it[1].toFloat()) }
                    val contentScreen = activity.screenOrigin().let { Offset(it[0].toFloat(), it[1].toFloat()) }
                    assertBitmapContains("Baseline fixed world in actual Window", baselineWindow,
                        world.source.screenRect.translate(contentWindow - contentScreen))
                    assertBitmapContains("Baseline fixed world on actual display", ready.bitmap, world.source.screenRect)
                    baselines.put(JSONObject().put("scene", current.name).put("window_png", "$stem-window.png")
                        .put("screen_png", "$stem-screen.png").put("background_world", world.json())
                        .put("window_geometry", activity.geometry()).put("display_readiness", ready.verification))
                    result.put("active_stage", "rest")
                    compose.runOnIdle { scene.value = current.copy(showSlider = true) }
                    settle()
                    if (calibration.getString("status") == "pending") {
                        val raw = observeSlider(activity)
                        val residual = NATIVE_CENTER - raw.carrierWorld.center
                        calibration.put("source_scene", current.name).put("raw_geometry", raw.json())
                            .put("raw_center_world_dp", raw.carrierWorld.center.json())
                            .put("target_minus_raw_center_dp", residual.json())
                        save()
                        assertTrue("Optical alignment must not normalize a product layout regression: $residual",
                            abs(residual.x) <= 1f && abs(residual.y) <= 1f)
                        compose.runOnIdle { fixedTranslationPx.value = residual * density }
                        calibration.put("status", "fixed").put("translation_px", fixedTranslationPx.value.json())
                            .put("translation_dp", residual.json())
                        settle()
                    }
                    val rest = observeSlider(activity)
                    observations.put(observation(current, "rest", rest))
                    validateSlider(rest, held = false)
                    assertEquals("Optical sample REST center x after one fixed translation", 113.5f, rest.carrierWorld.center.x, .05f)
                    assertEquals("Optical sample REST center y after one fixed translation", 430f, rest.carrierWorld.center.y, .05f)
                    capture(current, "rest", rest, directory, captures, baselineWindow, ready.bitmap)
                    save()
                    val node = compose.onNodeWithTag(HOLDER_TAG, useUnmergedTree = true)
                    // Injection is relative to the semantics touch bounds; actual mapped geometry
                    // supplies the target, and the two coordinate paths are exported separately.
                    val press = rest.carrierRoot.center - rest.holderSemanticRoot.topLeft
                    assertTrue("Measured REST thumb center lies inside the actual touch holder",
                        press.x in 0f..rest.holderSemanticRoot.width && press.y in 0f..rest.holderSemanticRoot.height)
                    heldDownComposeMs = compose.mainClock.currentTime
                    heldDownUptimeMs = SystemClock.uptimeMillis()
                    result.put("active_stage", "held-down")
                    val downEvent = event(current, "DOWN").put("status", "requested")
                        .put("holder_semantic_local_px", press.json())
                        .put("actual_visual_center_root_px", rest.carrierRoot.center.json())
                        .put("actual_visual_center_screen_px", rest.carrier.screenRect.center.json())
                        .put("fixed_translation_px", fixedTranslationPx.value.json())
                    inputEvents.put(downEvent)
                    save()
                    node.performTouchInput { down(press) }
                    pointerDown = true
                    downEvent.put("status", "injected").put("after_injection_uptime_ms", SystemClock.uptimeMillis())
                    try {
                        settle()
                        val held = observeSlider(activity)
                        observations.put(observation(current, "held", held))
                        validateSlider(held, held = true)
                        assertTrue("HELD reaches the real production visual-carrier expansion",
                            held.carrierRoot.width > rest.carrierRoot.width + 1f &&
                                held.carrierRoot.height > rest.carrierRoot.height + 1f)
                        capture(current, "held", held, directory, captures, baselineWindow, ready.bitmap)
                        save()
                    } finally {
                        if (pointerDown) {
                            node.performTouchInput { cancel() }
                            pointerDown = false
                            inputEvents.put(event(current, "CANCEL").put("purpose", "post-capture cleanup; no UP commit evidence"))
                            settle()
                        }
                        save()
                    }
                    val cleanup = observeSlider(activity)
                    observations.put(observation(current, "post-cancel-rest", cleanup))
                    validateSlider(cleanup, held = false)
                    assertEquals("Fixed optical alignment persists after CANCEL x", rest.carrierWorld.center.x,
                        cleanup.carrierWorld.center.x, .05f)
                    assertEquals("Fixed optical alignment persists after CANCEL y", rest.carrierWorld.center.y,
                        cleanup.carrierWorld.center.y, .05f)
                } finally {
                    baselineWindow.recycle()
                    baselineScreen?.recycle()
                }
            }
            assertEquals("Every selected scene has REST and HELD", backgrounds.size * themes.size * 2, captures.length())
            assertEquals("Every selected scene has a plain background baseline", backgrounds.size * themes.size, baselines.length())
            result.put("status", "passed").put("active_stage", "complete")
                .put("acceptance", "Requested optical evidence passed fixed-world, capture-readiness, one bounded fixed sampling translation, quarter-value and no-callback checks. Native material, shape, geometry and natural-motion parity remain unverified by this fixture.")
        } catch (failure: Throwable) {
            result.put("status", "failed").put("exception", "${failure.javaClass.name}: ${failure.message}")
            throw failure
        } finally {
            compose.mainClock.autoAdvance = true
            save()
        }
    }

    /** Separate static optical protocol: fixed source; real production DOWN/MOVE/HELD. */
    private fun captureFixedShapeCoverage(plan: FixedShapePlan, requestedRunId: String?) {
        val runId = (requestedRunId ?: System.currentTimeMillis().toString())
            .replace(Regex("[^A-Za-z0-9_-]"), "_")
        val directory = File(InstrumentationRegistry.getInstrumentation().targetContext.getExternalFilesDir(null),
            "slider-optical-world/$runId").apply { check(isDirectory || mkdirs()) }
        val captures = JSONArray()
        val baselines = JSONArray()
        val observations = JSONArray()
        val coverageStages = JSONArray()
        val calibration = JSONObject().put("status", "pending").put("maximum_correction_per_axis_dp", 1)
            .put("reference_quarter_center_world_dp", plan.referenceQuarterCenter.json())
            .put("policy", "One fixture-only translation from the first actual quarter REST carrier center to the recorded native public quarter lens center; each axis <=1dp or abort. Reused unchanged for all stages, both sources and cleanup. Background, holder dimensions and production transforms are never fitted or retuned.")
        val result = JSONObject().put("schema", 1).put("status", "running").put("run_id", runId)
            .put("sdk", Build.VERSION.SDK_INT).put("model", Build.MODEL).put("fingerprint", Build.FINGERPRINT)
            .put("mode", "fixed-shape-coverage").put("shape_id", plan.shapeId).put("flat_input_id", plan.flatId)
            .put("scope", "First light fixed-object static optical feasibility. Six fresh production GlassSlider scenes, each independently repeated with the original shape and pose-matched flat source. Real DOWN, slop-establishing MOVE, inverse-mapped target MOVE, settled HELD capture, cleanup CANCEL. No setValue, source motion, UP commit, release-dynamics or parity claim.")
            .put("shape_plan", plan.source).put("shape_plan_file", plan.specFile).put("shape_plan_sha256", plan.sha256)
            .put("external_input_manifest", checkNotNull(externalManifest))
            .put("inputs", checkNotNull(externalManifest).getJSONArray("inputs"))
            .put("selected_themes", JSONArray(listOf("light"))).put("theme_preset", ThemePresets.KEY_DEFAULT)
            .put("source_world_policy", "Original opaque750x1334 sRGB PNG, fixed375x667dp world at the actual GlassBackground origin; no background movement or image fitting; fontScale1 and LTR.")
            .put("input_policy", "The requested carrier center is converted analytically through the unchanged production relative drag mapping. DOWN starts at the observed quarter REST carrier. A real MOVE11dp crosses the production10dp slop, then a second real MOVE requests the inverse-mapped fraction. Actual pointer dispatch, values and carrier LayoutCoordinates are exported. Nominal source overlap is not actual optical coverage.")
            .put("clock_policy", "LocalDockInputTimeNanos uses the Compose clock;1600ms settling after DOWN and each MOVE. Requested event delays and actual dispatch uptime are recorded independently. This is settled static evidence, not a millisecond motion measurement.")
            .put("capture_policy", "Actual Window PixelCopy and independent composited display PNGs, unchanged>=99.5% RGB3 readiness and whole-holder/carrier6dp shadow room requirements. Each pose has its own unchanged-source background baseline.")
            .put("calibration", calibration).put("baselines", baselines).put("captures", captures)
            .put("coverage_stages", coverageStages).put("geometry_observations", observations).put("input_events", inputEvents)
        val report = File(directory, "result.json")
        fun save() {
            result.put("density", density).put("font_scale", fontScale).put("system_font_scale", systemFontScale)
                .put("fixed_translation_px", fixedTranslationPx.value.json())
                .put("value_events", JSONArray(valueEvents.toList())).put("finish_events", JSONArray(finishEvents.toList()))
                .put("dispatched_pointer_events", JSONArray(dispatchedPointerEvents.toList()))
            report.writeText(result.toString(2))
        }
        fun observe(scene: Scene, phase: String, geometry: SliderGeometry) {
            observations.put(observation(scene, phase, geometry)
                .put("coverage_stage_id", scene.coverageStageId)
                .put("reference_anchor_world_dp", plan.referenceQuarterCenter.json())
                .put("center_minus_native_anchor_dp", (geometry.carrierWorld.center - plan.referenceQuarterCenter).json()))
        }
        val scene = mutableStateOf(Scene(plan.shapeId, false, false, plan.stages.first().id))
        save()
        try {
            val shader = android.graphics.RuntimeShader(LiquidGlassShader.shaderSource(
                InstrumentationRegistry.getInstrumentation().targetContext))
            listOf(LiquidGlassStyle.sliderLens(false), LiquidGlassStyle.rangeSliderLens(false)).forEach { material ->
                listOf(0.0, .5, 1.0).forEach { lift ->
                    LiquidGlassShader.build(size = Size(58f, 38f),
                        corners = LiquidGlassCornerRadii(19f, 19f, 19f, 19f), style = material.scale(lift),
                        atlasSizePx = Size(375f, 667f),
                        sampling = LiquidGlassShader.sampling(Offset.Zero, 1f, Rect(0f, 0f, 375f, 667f)))
                        .forEach { (name, values) -> shader.setFloatUniform(name, values) }
                }
            }
            result.put("production_shader_compile_and_bind", "passed: light single/range, lift0/0.5/1; not exhaustive driver introspection")
            compose.setContent {
                val actualDensity = LocalDensity.current
                SideEffect { systemFontScale = actualDensity.fontScale }
                CompositionLocalProvider(
                    LocalDensity provides Density(actualDensity.density, fontScale = 1f),
                    LocalLayoutDirection provides LayoutDirection.Ltr,
                    LocalDockInputTimeNanos provides { compose.mainClock.currentTime * 1_000_000L },
                ) { Fixture(scene.value) }
            }
            compose.waitForIdle()
            compose.mainClock.autoAdvance = false
            for (stage in plan.stages) {
                val stageCaptures = JSONArray()
                val stageRow = JSONObject().put("stage_id", stage.id).put("shape_id", plan.shapeId)
                    .put("flat_input_id", plan.flatId).put("requested_stage", stage.source)
                    .put("requested_lens_center_world_pt", stage.requestedLensCenter.json())
                    .put("actual_carrier_target_center_world_pt", stage.actualCarrierTarget?.json() ?: JSONObject.NULL)
                    .put("captures", stageCaptures)
                coverageStages.put(stageRow)
                val actualPoses = mutableListOf<Pair<SliderGeometry, Float>>()
                for (background in listOf(plan.shapeId, plan.flatId)) {
                    val current = Scene(background, false, false, stage.id)
                    result.put("active_scene", current.name).put("active_stage", "plain-background")
                    compose.runOnIdle {
                        scene.value = current
                        valueEvents.clear(); finishEvents.clear(); dispatchedPointerEvents.clear()
                    }
                    settle()
                    val activity = checkNotNull(surface)
                    assertTrue("Hardware accelerated capture required", activity.root.isHardwareAccelerated)
                    val world = observeWorld()
                    validateWorld(world)
                    observations.put(JSONObject().put("scene", current.name).put("coverage_stage_id", stage.id)
                        .put("phase", "background").put("world", world.json()))
                    val stem = "${current.name}-background"
                    val baselineWindow = activity.capture()
                    baselineWindow.saveOpticalPng(File(directory, "$stem-window.png"))
                    var baselineScreen: Bitmap? = null
                    try {
                        val ready = awaitOpticalBackgroundScreen(activity, baselineWindow, density, directory, stem)
                        baselineScreen = ready.bitmap
                        ready.bitmap.saveOpticalPng(File(directory, "$stem-screen.png"))
                        val contentWindow = activity.origin().let { Offset(it[0].toFloat(), it[1].toFloat()) }
                        val contentScreen = activity.screenOrigin().let { Offset(it[0].toFloat(), it[1].toFloat()) }
                        assertBitmapContains("Fixed baseline world in Window", baselineWindow,
                            world.source.screenRect.translate(contentWindow - contentScreen))
                        assertBitmapContains("Fixed baseline world on display", ready.bitmap, world.source.screenRect)
                        baselines.put(JSONObject().put("scene", current.name).put("coverage_stage_id", stage.id)
                            .put("input_id", background).put("shape_id", plan.shapeId)
                            .put("window_png", "$stem-window.png").put("screen_png", "$stem-screen.png")
                            .put("background_world", world.json()).put("window_geometry", activity.geometry())
                            .put("display_readiness", ready.verification))
                        compose.runOnIdle { scene.value = current.copy(showSlider = true) }
                        settle()
                        if (calibration.getString("status") == "pending") {
                            val raw = observeSlider(activity)
                            val residual = plan.referenceQuarterCenter - raw.carrierWorld.center
                            calibration.put("source_scene", current.name).put("raw_geometry", raw.json())
                                .put("raw_center_world_dp", raw.carrierWorld.center.json())
                                .put("target_minus_raw_center_dp", residual.json())
                            save()
                            assertTrue("Fixed-shape calibration cannot normalize a layout regression: $residual",
                                abs(residual.x) <= 1f && abs(residual.y) <= 1f)
                            compose.runOnIdle { fixedTranslationPx.value = residual * density }
                            calibration.put("status", "fixed").put("translation_px", fixedTranslationPx.value.json())
                                .put("translation_dp", residual.json())
                            settle()
                        }
                        val rest = observeSlider(activity)
                        observe(current, "rest", rest)
                        validateSlider(rest, held = false)
                        assertEquals("Fixed calibration x", plan.referenceQuarterCenter.x, rest.carrierWorld.center.x, .05f)
                        assertEquals("Fixed calibration y", plan.referenceQuarterCenter.y, rest.carrierWorld.center.y, .05f)
                        val node = compose.onNodeWithTag(HOLDER_TAG, useUnmergedTree = true)
                        val press = rest.carrierRoot.center - rest.holderSemanticRoot.topLeft
                        val mapping = inverseShapeInput(stage, rest, press)
                        val target = mapping.getJSONArray("android_requested_finger_holder_local_px").offset()
                        val establish = mapping.getJSONArray("slop_establish_holder_local_px").offset()
                        stageRow.put("android_requested_finger_world_pt", mapping.getJSONArray("android_requested_finger_world_pt"))
                        fun inject(action: String, point: Offset? = null, block: () -> Unit) {
                            result.put("active_stage", action)
                            val row = event(current, action).put("status", "requested").put("coverage_stage_id", stage.id)
                                .put("shape_id", plan.shapeId).put("input_id", background)
                                .put("holder_semantic_local_px", point?.json() ?: JSONObject.NULL)
                                .put("fixed_translation_px", fixedTranslationPx.value.json())
                            inputEvents.put(row); save()
                            block()
                            row.put("status", "injected").put("after_injection_uptime_ms", SystemClock.uptimeMillis())
                            save()
                        }
                        heldDownComposeMs = compose.mainClock.currentTime
                        heldDownUptimeMs = SystemClock.uptimeMillis()
                        inject("DOWN", press) { node.performTouchInput { down(press) }; pointerDown = true }
                        try {
                            settle()
                            val downHeld = observeSlider(activity)
                            observe(current, "down-held-before-move", downHeld)
                            validateSlider(downHeld, held = true)
                            assertTrue("Real DOWN expands the production carrier",
                                downHeld.carrierRoot.width > rest.carrierRoot.width + 1f &&
                                    downHeld.carrierRoot.height > rest.carrierRoot.height + 1f)
                            inject("MOVE_ESTABLISH_SLOP", establish) { node.performTouchInput { moveTo(establish, 16) } }
                            settle()
                            observe(current, "slop-established", observeSlider(activity))
                            inject("MOVE_TARGET", target) { node.performTouchInput { moveTo(target, 16) } }
                            settle()
                            val held = observeSlider(activity)
                            observe(current, "held", held)
                            validateSlider(held, held = true, requireQuarter = false)
                            assertTrue("A target MOVE must publish the production value", valueEvents.isNotEmpty())
                            assertTrue("No held MOVE commits a finish callback", finishEvents.isEmpty())
                            assertTrue("Read-only Final-pass observer received actual DOWN and two MOVE dispatches",
                                dispatchedPointerEvents.count { it.optString("scene") == current.name } >= 3)
                            val heldValue = currentValue
                            result.put("active_stage", "held-capture")
                            save()
                            val captureBegin = SystemClock.uptimeMillis()
                            capture(current, "held", held, directory, captures, baselineWindow, ready.bitmap)
                            val captureEnd = SystemClock.uptimeMillis()
                            val captured = captures.getJSONObject(captures.length() - 1)
                            captured.put("coverage_stage_id", stage.id).put("stage_id", stage.id)
                                .put("shape_id", plan.shapeId).put("input_id", background)
                                .put("source_role", if (background == plan.shapeId) "shape" else "flat")
                                .put("requested_stage", stage.source).put("input_mapping", mapping)
                                .put("android_requested_finger_world_pt", mapping.getJSONArray("android_requested_finger_world_pt"))
                                .put("capture_begin_wall_uptime_ms", captureBegin).put("capture_end_wall_uptime_ms", captureEnd)
                                .put("dispatched_pointer_events", JSONArray(dispatchedPointerEvents.toList()))
                                .put("actual_carrier_center_minus_target_dp", (held.carrierWorld.center -
                                    (stage.actualCarrierTarget ?: stage.requestedLensCenter)).json())
                            stageCaptures.put(captured)
                            actualPoses.add(held to heldValue)
                            val afterCapture = observeSlider(activity)
                            observe(current, "held-after-capture", afterCapture)
                            assertRect("Settled carrier remains fixed through capture", held.carrierWorld, afterCapture.carrierWorld, .05f)
                            save()
                        } finally {
                            if (pointerDown) {
                                inject("CANCEL") { node.performTouchInput { cancel() }; pointerDown = false }
                                settle()
                            }
                            save()
                        }
                        val cleanup = observeSlider(activity)
                        observe(current, "post-cancel-rest", cleanup)
                        validateSlider(cleanup, held = false, requireQuarter = false)
                        assertTrue("Cleanup CANCEL never commits a finish callback", finishEvents.isEmpty())
                        stageCaptures.getJSONObject(stageCaptures.length() - 1)
                            .put("post_cancel_geometry", cleanup.json()).put("post_cancel_value", currentValue)
                            .put("post_cancel_dispatched_pointer_events", JSONArray(dispatchedPointerEvents.toList()))
                            .put("post_cancel_value_events", JSONArray(valueEvents.toList()))
                            .put("post_cancel_finish_events", JSONArray(finishEvents.toList()))
                        save()
                    } finally {
                        baselineWindow.recycle(); baselineScreen?.recycle()
                    }
                }
                val shape = actualPoses[0]
                val flat = actualPoses[1]
                stageRow.put("actual_shape_carrier_world_rect_dp", shape.first.carrierWorld.json())
                    .put("actual_flat_carrier_world_rect_dp", flat.first.carrierWorld.json())
                    .put("actual_shape_value", shape.second).put("actual_flat_value", flat.second)
                    .put("pair_carrier_center_delta_dp", (shape.first.carrierWorld.center - flat.first.carrierWorld.center).json())
                    .put("pair_value_delta", shape.second - flat.second).put("pair_tolerance_dp", .05f)
                save()
                assertRect("Shape and flat use the same actual settled carrier pose", shape.first.carrierWorld, flat.first.carrierWorld, .05f)
                assertEquals("Shape and flat use the same production value", shape.second, flat.second, .000001f)
                stageRow.put("pair_position_validation", "passed")
                save()
            }
            assertEquals("Six stages each have shape and flat held captures", plan.stages.size * 2, captures.length())
            assertEquals("Every fresh shape/flat pose has its own unchanged-source baseline", plan.stages.size * 2, baselines.length())
            result.put("status", "passed").put("active_stage", "complete")
                .put("acceptance", "Fixed source/capture validity and matching shape/flat production poses passed. Requested overlap remains geometric and realized coverage must be computed from actual carrier bounds; no optical alpha, material parity or full dynamics claim.")
        } catch (failure: Throwable) {
            result.put("status", "failed").put("exception", "${failure.javaClass.name}: ${failure.message}")
            throw failure
        } finally {
            compose.mainClock.autoAdvance = true
            save()
        }
    }

    private fun inverseShapeInput(stage: FixedShapeStage, rest: SliderGeometry, press: Offset): JSONObject {
        val targetCenter = stage.actualCarrierTarget ?: stage.requestedLensCenter
        val controlWidthPx = rest.holder.size.width.toFloat()
        val productionRestWidthPx = GlassSliderThumbMetrics.width(false) * density
        val travelPx = controlWidthPx - productionRestWidthPx
        require(travelPx > 0f)
        val deltaPx = (targetCenter.x - rest.carrierWorld.center.x) * density
        val requestedFraction = .25f + deltaPx / travelPx
        require(requestedFraction > 0f && requestedFraction < 1f && abs(deltaPx) > .001f) {
            "Fixed-shape target must be an interior MOVE from the fresh quarter state: $targetCenter"
        }
        val direction = if (deltaPx > 0f) 1f else -1f
        val slopPx = GlassSliderDragMapping.START_SLOP_DP * density
        val establish = press + Offset(direction * (slopPx + density), 0f)
        val target = Offset(press.x + direction * slopPx +
            controlWidthPx * (requestedFraction - .25f), press.y)
        fun requireTouch(point: Offset) {
            require(point.x in 0f..rest.holderSemanticRoot.width && point.y in 0f..rest.holderSemanticRoot.height) {
                "The inverse finger request must remain inside the actual touch holder: $point"
            }
        }
        requireTouch(press); requireTouch(establish); requireTouch(target)
        // Pure calculation through the production helper, never a semantic progress/setValue action.
        val forward = GlassSliderDragMapping(press.x, .25f, controlWidthPx, 1f, slopPx, false)
        val establishFraction = forward.valueAt(establish.x)
        val forwardFraction = forward.valueAt(target.x)
        require(abs(forwardFraction - requestedFraction) < .000001f) { "Declared inverse must match production drag mapping" }
        fun inWorld(local: Offset) = (rest.holderSemanticRoot.topLeft + local + rest.screenOrigin -
            rest.world.source.screenOrigin) / density
        return JSONObject().put("requested_lens_center_world_pt", stage.requestedLensCenter.json())
            .put("target_center_world_dp", targetCenter.json())
            .put("target_source", if (stage.actualCarrierTarget == null) "nominal_plan_center" else "actual_carrier_target_center_world_pt")
            .put("native_requested_finger_world_pt", stage.requestedFinger.json())
            .put("android_requested_finger_world_pt", inWorld(target).json())
            .put("android_requested_finger_holder_local_px", target.json())
            .put("down_holder_local_px", press.json()).put("down_world_dp", inWorld(press).json())
            .put("slop_establish_holder_local_px", establish.json()).put("slop_establish_world_dp", inWorld(establish).json())
            .put("actual_rest_carrier_center_world_dp", rest.carrierWorld.center.json())
            .put("actual_holder_width_px", controlWidthPx).put("actual_rest_owner_width_px", rest.owner.size.width)
            .put("production_rest_width_px", productionRestWidthPx).put("production_thumb_travel_px", travelPx)
            .put("production_start_slop_px", slopPx).put("production_start_slop_dp", GlassSliderDragMapping.START_SLOP_DP)
            .put("production_mapping_establish_fraction", establishFraction)
            .put("requested_fraction", requestedFraction).put("production_mapping_forward_fraction", forwardFraction)
            .put("vertical_target_minus_rest_center_dp", targetCenter.y - rest.carrierWorld.center.y)
            .put("formula", "f_target=.25+(targetCenterX-actualRestCenterX)*density/(actualHolderWidthPx-productionRestWidthDp*density); establish=down+sign*11dp; targetFingerX=downX+sign*productionStartSlopPx+actualHolderWidthPx*(f_target-.25). Production relative mapping consumes10dp once, then dx/fullHolderWidth. No feedback fit; integer layout/pointer quantization remains in observed carrier bounds. Vertical finger stays at actual REST center; production horizontal slider does not follow finger y.")
            .put("production_source", "GlassSlider.kt GlassSliderDragMapping.valueAt/START_SLOP_DP; SliderVisuals.kt GlassSliderThumbMetrics; unchanged GlassSliderBody thumb-center travel")
    }

    private fun loadFixedShapePlan(directoryName: String, filename: String): FixedShapePlan {
        require(filename.matches(Regex("[A-Za-z0-9][A-Za-z0-9_.-]{0,127}\\.json")))
        val root = checkNotNull(InstrumentationRegistry.getInstrumentation().targetContext.getExternalFilesDir(null)).canonicalFile
        val directory = File(root, directoryName).canonicalFile
        require(directory.parentFile == root && directory.isDirectory)
        val file = File(directory, filename).canonicalFile
        require(file.parentFile == directory && file.isFile && file.length() in 1..1048576)
        val bytes = file.readBytes()
        val source = JSONObject(bytes.toString(Charsets.UTF_8))
        require(source.getInt("schema") == 1)
        val world = source.getJSONObject("world")
        require(world.getJSONArray("size").offset() == Offset(375f, 667f) &&
            world.getJSONArray("source_size_px").offset() == Offset(750f, 1334f) &&
            world.getInt("pixels_per_world_unit") == 2)
        val shapeId = source.getString("first_input_id")
        val flatId = source.getString("flat_input_id")
        require(shapeId in externalInputs && flatId in externalInputs && shapeId != flatId)
        val manifestRows = checkNotNull(externalManifest).getJSONArray("inputs")
        val registered = (0 until manifestRows.length()).associate {
            val row = manifestRows.getJSONObject(it)
            row.getString("id") to row.getString("sha256")
        }
        val specRows = source.getJSONArray("inputs")
        val shapeRow = (0 until specRows.length()).map(specRows::getJSONObject).single { it.getString("id") == shapeId }
        require(shapeRow.getString("source_sha256") == registered[shapeId]) { "Shape plan and original PNG manifest disagree" }
        require(shapeRow.getJSONObject("shape").getString("source_sha256") == registered[shapeId])
        val flatRow = (0 until specRows.length()).map(specRows::getJSONObject).single { it.getString("id") == flatId }
        require(flatRow.getString("source_sha256") == registered[flatId] && flatRow.isNull("shape"))
        val stages = source.getJSONArray("stages")
        require(stages.length() == 6) { "First feasibility requires the six declared coverage stages" }
        val parsed = (0 until stages.length()).map { index ->
            val stage = stages.getJSONObject(index)
            val id = stage.getString("id")
            require(id.matches(Regex("[A-Za-z0-9][A-Za-z0-9_-]{0,63}")))
            require(stage.getDouble("requested_fraction") in 0.0..1.0)
            val target = stage.optJSONArray("actual_carrier_target_center_world_pt")?.offset()
            FixedShapeStage(id, stage.getJSONArray("requested_lens_center_world_pt").offset(),
                stage.getJSONArray("requested_finger_world_pt").offset(), target, stage)
        }
        require(parsed.map { it.id }.distinct().size == parsed.size)
        val referenceCenter = source.getJSONObject("native_public_geometry_reference")
            .getJSONArray("observed_center_pt").offset()
        val hash = MessageDigest.getInstance("SHA-256").digest(bytes)
            .joinToString("") { "%02x".format(it.toInt() and 255) }
        return FixedShapePlan(shapeId, flatId, parsed, source, filename, hash, referenceCenter)
    }

    /** Separate opt-in marker protocol; legacy procedural scenes are unchanged. */
    private fun loadMarkerInputs(directoryName: String) {
        require(directoryName.matches(Regex("[A-Za-z0-9][A-Za-z0-9_-]{0,63}")))
        val root = checkNotNull(InstrumentationRegistry.getInstrumentation().targetContext.getExternalFilesDir(null)).canonicalFile
        val directory = File(root, directoryName).canonicalFile
        require(directory.parentFile == root && directory.isDirectory)
        val file = File(directory, "manifest.json").canonicalFile
        require(file.parentFile == directory && file.isFile && file.length() in 1..131072)
        val manifest = JSONObject(file.readText())
        val expectedRole = InstrumentationRegistry.getArguments()
            .getString("glassSliderOpticalInputRole") ?: "calibration"
        require(expectedRole in setOf("calibration", "holdout"))
        require(manifest.getInt("schema") == 1 && manifest.getString("split") == expectedRole) {
            "Source role must match the explicitly requested calibration/holdout protocol"
        }
        require(manifest.getString("set_id").matches(Regex("[A-Za-z0-9][A-Za-z0-9_-]{0,63}")))
        val inputs = manifest.getJSONArray("inputs")
        require(inputs.length() in 1..32)
        try {
            for (index in 0 until inputs.length()) {
                val row = inputs.getJSONObject(index)
                val id = row.getString("id")
                require(id.matches(Regex("[A-Za-z0-9][A-Za-z0-9_-]{0,63}")) && id !in externalInputs)
                require(row.getString("file") == "$id.png")
                val png = File(directory, "$id.png").canonicalFile
                require(png.parentFile == directory && png.isFile && png.length() <= 8 * 1024 * 1024)
                val bytes = png.readBytes()
                val hash = MessageDigest.getInstance("SHA-256").digest(bytes)
                    .joinToString("") { "%02x".format(it.toInt() and 255) }
                require(hash == row.getString("sha256")) { "Marker input changed after registration: $id" }
                val bounds = BitmapFactory.Options().apply { inJustDecodeBounds = true }
                BitmapFactory.decodeByteArray(bytes, 0, bytes.size, bounds)
                require(bounds.outWidth == 750 && bounds.outHeight == 1334 && bounds.outMimeType == "image/png") {
                    "Marker PNG must be750x1334 before allocation: $id"
                }
                val options = BitmapFactory.Options().apply {
                    inScaled = false
                    inSampleSize = 1
                    inPreferredConfig = Bitmap.Config.ARGB_8888
                    inPreferredColorSpace = ColorSpace.get(ColorSpace.Named.SRGB)
                }
                val bitmap = checkNotNull(BitmapFactory.decodeByteArray(bytes, 0, bytes.size, options))
                externalInputs[id] = bitmap
                require(bitmap.width == 750 && bitmap.height == 1334 && bitmap.config == Bitmap.Config.ARGB_8888 &&
                    bitmap.colorSpace?.isSrgb == true && options.outMimeType == "image/png")
                bitmap.density = Bitmap.DENSITY_NONE
                val pixels = IntArray(bitmap.width)
                for (y in 0 until bitmap.height) {
                    bitmap.getPixels(pixels, 0, bitmap.width, 0, y, bitmap.width, 1)
                    require(pixels.all { it ushr 24 == 255 }) { "Marker source must be opaque" }
                }
            }
            externalManifest = manifest
        } catch (failure: Throwable) {
            externalInputs.values.forEach(Bitmap::recycle)
            externalInputs.clear()
            throw failure
        }
    }

    @Composable private fun Fixture(scene: Scene) {
        val view = LocalView.current
        val actualDensity = LocalDensity.current
        SideEffect {
            surface = OpticalCaptureWindow.from(view)
            density = actualDensity.density
            fontScale = actualDensity.fontScale
        }
        SleepyThemeProvider(darkTheme = scene.dark, themeKey = ThemePresets.KEY_DEFAULT) {
            CompositionLocalProvider(LocalUiStyle provides UiStyle.LiquidGlass) {
                GlassHost(Modifier.fillMaxSize(), background = MaterialTheme.colorScheme.background) {
                    GlassBackground(0f, Modifier.fillMaxSize().onGloballyPositioned { hostCoordinates = it }) {
                        Box(Modifier.fillMaxSize().background(Color(0xFFF0F0F5))) {
                            val sourceModifier = Modifier.align(Alignment.TopStart)
                                .requiredSize(375.dp, 667.dp).clipToBounds()
                                .onGloballyPositioned { sourceCoordinates = it }
                            val external = externalInputs[scene.background]
                            if (external == null) {
                                OpticalCaptureBackground(OpticalBackground.valueOf(scene.background), sourceModifier)
                            } else {
                                val image = remember(external) { external.asImageBitmap() }
                                Canvas(sourceModifier) {
                                    drawImage(image, srcOffset = IntOffset.Zero, srcSize = IntSize(750, 1334),
                                        dstOffset = IntOffset.Zero,
                                        dstSize = IntSize(size.width.roundToInt(), size.height.roundToInt()),
                                        filterQuality = FilterQuality.Low)
                                }
                            }
                        }
                    }
                    if (scene.showSlider) key(scene.background, scene.dark, scene.coverageStageId) {
                        var value by remember { mutableFloatStateOf(.25f) }
                        SideEffect { currentValue = value }
                        Box(Modifier.offset(20.dp, 406.dp).width(335.dp).graphicsLayer {
                            translationX = fixedTranslationPx.value.x
                            translationY = fixedTranslationPx.value.y
                        }.then(if (scene.coverageStageId != null) fixedShapePointerObserver(scene) else Modifier)
                            .testTag(HOLDER_TAG)) {
                            GlassSlider(value, { next ->
                                valueEvents.add(event(scene, "onValueChange").put("value", next))
                                value = next
                            }, Modifier.fillMaxWidth(), onValueChangeFinished = {
                                finishEvents.add(event(scene, "onValueChangeFinished"))
                            })
                        }
                    }
                }
            }
        }
    }

    private fun settle() {
        compose.mainClock.advanceTimeBy(1600)
        compose.waitForIdle()
    }

    /** Observe delivered Compose pointer changes without consuming or replacing production input. */
    private fun fixedShapePointerObserver(scene: Scene) = Modifier
        .onGloballyPositioned { coverageHolderCoordinates = it }
        .pointerInput(scene.name) {
            awaitPointerEventScope {
                while (true) {
                    val delivered = awaitPointerEvent(PointerEventPass.Final)
                    val changes = JSONArray()
                    for (change in delivered.changes) {
                        val holder = coverageHolderCoordinates?.takeIf { it.isAttached }
                        val world = sourceCoordinates?.takeIf { it.isAttached }
                        val screen = holder?.localToScreen(change.position)
                        val worldPoint = if (screen != null && world != null) {
                            (screen - world.localToScreen(Offset.Zero)) / density
                        } else null
                        changes.put(JSONObject().put("pointer_id", change.id.toString())
                            .put("event_uptime_ms", change.uptimeMillis)
                            .put("holder_local_px", change.position.json())
                            .put("screen_px", screen?.json() ?: JSONObject.NULL)
                            .put("world_dp", worldPoint?.json() ?: JSONObject.NULL)
                            .put("pressed", change.pressed).put("previous_pressed", change.previousPressed)
                            .put("consumed_by_production_at_final_pass", change.isConsumed))
                    }
                    dispatchedPointerEvents.add(event(scene, "COMPOSE_POINTER_DISPATCH")
                        .put("coverage_stage_id", scene.coverageStageId).put("pass", "Final; observer never consumes")
                        .put("type", delivered.type.toString()).put("changes", changes))
                }
            }
        }

    private fun event(scene: Scene, action: String) = JSONObject().put("scene", scene.name).put("action", action)
        .put("compose_ms", compose.mainClock.currentTime).put("wall_uptime_ms", SystemClock.uptimeMillis())

    private fun observation(scene: Scene, phase: String, geometry: SliderGeometry) =
        JSONObject().put("scene", scene.name).put("phase", phase).put("geometry", geometry.json())
            .put("fixed_translation_px", fixedTranslationPx.value.json())
            .put("center_minus_native_anchor_dp", (geometry.carrierWorld.center - NATIVE_CENTER).json())

    private fun observeWorld(): World = compose.runOnIdle {
        World(OpticalLayoutGeometry.read(checkNotNull(sourceCoordinates), density),
            OpticalLayoutGeometry.read(checkNotNull(hostCoordinates), density))
    }

    private fun observeSlider(activity: OpticalCaptureWindow): SliderGeometry {
        val holder = compose.onNodeWithTag(HOLDER_TAG, useUnmergedTree = true).fetchSemanticsNode()
        val owner = compose.onNodeWithTag("glass-slider-end", useUnmergedTree = true).fetchSemanticsNode()
        val carrier = compose.onNodeWithTag("glass-slider-thumb-carrier", useUnmergedTree = true).fetchSemanticsNode()
        val windowOrigin = activity.origin().let { Offset(it[0].toFloat(), it[1].toFloat()) }
        val screenOrigin = activity.screenOrigin().let { Offset(it[0].toFloat(), it[1].toFloat()) }
        return compose.runOnIdle {
            SliderGeometry(
                World(OpticalLayoutGeometry.read(checkNotNull(sourceCoordinates), density),
                    OpticalLayoutGeometry.read(checkNotNull(hostCoordinates), density)),
                OpticalLayoutGeometry.read(holder.layoutInfo.coordinates, density),
                OpticalLayoutGeometry.read(owner.layoutInfo.coordinates, density),
                OpticalLayoutGeometry.read(carrier.layoutInfo.coordinates, density),
                holder.boundsInRoot, carrier.boundsInRoot, windowOrigin, screenOrigin,
            )
        }
    }

    private fun validateWorld(world: World) {
        assertEquals("Fixed source world width", 375.0 * density, world.source.size.width.toDouble(), .5)
        assertEquals("Fixed source world height", 667.0 * density, world.source.size.height.toDouble(), .5)
        assertTrue("A sufficiently wide/tall actual source host is required",
            world.host.size.width >= world.source.size.width && world.host.size.height >= world.source.size.height)
        assertTrue("Source world starts at the actual GlassBackground top-left",
            (world.source.screenOrigin - world.host.screenOrigin).getDistance() <= .5f)
        assertUnitAxes("source world", world.source)
        assertUnitAxes("GlassBackground host", world.host)
        assertEquals("Fixture default native font scale", 1f, fontScale, 0f)
    }

    private fun validateSlider(geometry: SliderGeometry, held: Boolean, requireQuarter: Boolean = true) {
        validateWorld(geometry.world)
        assertEquals("Unmodified production slider width", 335.0 * density, geometry.holder.size.width.toDouble(), .5)
        assertEquals("Unmodified production touch height", 48.0 * density, geometry.holder.size.height.toDouble(), .5)
        assertUnitAxes("Translated slider holder", geometry.holder)
        assertTrue("Actual visual carrier fits inside the fixed world",
            geometry.carrierWorld.left >= 0f && geometry.carrierWorld.top >= 0f &&
                geometry.carrierWorld.right <= 375f && geometry.carrierWorld.bottom <= 667f)
        assertRect("Mapped carrier vs semantic bounds (independent coordinate paths)",
            geometry.carrierRoot, geometry.carrierSemanticRoot, 1f)
        assertRect("Mapped holder vs semantic bounds (independent coordinate paths)",
            geometry.holderRoot, geometry.holderSemanticRoot, 1f)
        if (requireQuarter) {
            assertEquals("Center hold preserves quarter value", .25f, currentValue, 0f)
            assertTrue("Center DOWN/CANCEL must not publish a value", valueEvents.isEmpty())
            assertTrue("Center DOWN/CANCEL must not finish an interaction", finishEvents.isEmpty())
        } else {
            assertTrue("Production MOVE value is finite and within domain", currentValue.isFinite() && currentValue in 0f..1f)
        }
        if (held) {
            assertTrue("HELD capture occurs during active DOWN before cleanup CANCEL", pointerDown)
            assertTrue("HELD completes1600ms of the declared synthetic clock",
                compose.mainClock.currentTime - checkNotNull(heldDownComposeMs) >= 1600)
        }
    }

    private fun capture(scene: Scene, phase: String, geometry: SliderGeometry, directory: File, captures: JSONArray,
                        baselineWindow: Bitmap, baselineScreen: Bitmap) {
        val activity = checkNotNull(surface)
        val stem = "${scene.name}-$phase"
        val window = activity.capture()
        window.saveOpticalPng(File(directory, "$stem-window.png"))
        try {
            val ready = awaitOpticalSurfaceScreen(activity, window, density, directory, stem, excludeSystemBars = true)
            try {
                val compared = ready.verification.getJSONArray("compared_screen_rect_px")
                val evidence = geometry.evidenceRoot.translate(geometry.screenOrigin)
                assertTrue("System-owned insets must not exclude holder, carrier or6dp shadow room",
                    evidence.left >= compared.getDouble(0) && evidence.top >= compared.getDouble(1) &&
                        evidence.right <= compared.getDouble(2) && evidence.bottom <= compared.getDouble(3))
                ready.bitmap.saveOpticalPng(File(directory, "$stem-screen.png"))
                assertBitmapContains("Fixed world in actual Window", window,
                    geometry.world.source.screenRect.translate(geometry.windowOrigin - geometry.screenOrigin))
                assertBitmapContains("Fixed world on actual display", ready.bitmap, geometry.world.source.screenRect)
                assertBitmapContains("Entire optical region in actual Window", window, geometry.evidenceRoot.translate(geometry.windowOrigin))
                assertBitmapContains("Entire optical region on actual display", ready.bitmap, evidence)
                fun metrics(tag: String, root: Rect) = JSONObject().put("tag", tag)
                    .put("actual_root_rect_px", root.json())
                    .put("window", opticalRegionMetrics(window, baselineWindow, root.translate(geometry.windowOrigin)))
                    .put("composited_display", opticalRegionMetrics(ready.bitmap, baselineScreen, root.translate(geometry.screenOrigin)))
                captures.put(JSONObject().put("scene", scene.name).put("background", scene.background)
                    .put("theme", if (scene.dark) "dark" else "light").put("phase", phase)
                    .put("window_png", "$stem-window.png").put("screen_png", "$stem-screen.png")
                    .put("baseline_window_png", "${scene.name}-background-window.png")
                    .put("baseline_screen_png", "${scene.name}-background-screen.png")
                    .put("geometry", geometry.json()).put("window_geometry", activity.geometry())
                    .put("display_readiness", ready.verification).put("fixed_translation_px", fixedTranslationPx.value.json())
                    .put("value", currentValue).put("pointer_down", pointerDown)
                    .put("compose_ms", compose.mainClock.currentTime).put("wall_uptime_ms", SystemClock.uptimeMillis())
                    .put("down_compose_ms", if (phase == "held") heldDownComposeMs else JSONObject.NULL)
                    .put("down_wall_uptime_ms", if (phase == "held") heldDownUptimeMs else JSONObject.NULL)
                    .put("value_events", JSONArray(valueEvents.toList())).put("finish_events", JSONArray(finishEvents.toList()))
                    .put("measurements", JSONArray(listOf(metrics("slider-touch-holder", geometry.holderRoot),
                        metrics("slider-actual-affine-carrier", geometry.carrierRoot),
                        metrics("slider-with-shadow-room", geometry.evidenceRoot)))))
            } finally { ready.bitmap.recycle() }
        } finally { window.recycle() }
    }

    private fun assertBitmapContains(label: String, bitmap: Bitmap, rect: Rect) {
        assertTrue("$label must fit entirely without clamped or skipped coordinates: $rect in ${bitmap.width}x${bitmap.height}",
            rect.left >= -.5f && rect.top >= -.5f && rect.right <= bitmap.width + .5f &&
                rect.bottom <= bitmap.height + .5f && rect.width > 0f && rect.height > 0f)
    }

    private fun assertUnitAxes(label: String, geometry: OpticalLayoutGeometry) {
        val origin = geometry.screenBasis[0]
        val x = geometry.screenBasis[1] - origin
        val y = geometry.screenBasis[2] - origin
        assertTrue("$label has unit unrotated local-to-screen axes; no stretch",
            abs(x.x - 1f) <= .001f && abs(x.y) <= .001f && abs(y.x) <= .001f && abs(y.y - 1f) <= .001f)
    }

    private fun assertRect(label: String, expected: Rect, actual: Rect, tolerance: Float) {
        assertEquals("$label left", expected.left, actual.left, tolerance)
        assertEquals("$label top", expected.top, actual.top, tolerance)
        assertEquals("$label right", expected.right, actual.right, tolerance)
        assertEquals("$label bottom", expected.bottom, actual.bottom, tolerance)
    }

    private companion object {
        const val HOLDER_TAG = "native-slider-optical-holder"
        val NATIVE_CENTER = Offset(113.5f, 430f)
        fun Offset.json() = JSONArray(listOf(x, y))
        fun JSONArray.offset(): Offset {
            require(length() == 2)
            val x = getDouble(0).toFloat()
            val y = getDouble(1).toFloat()
            require(x.isFinite() && y.isFinite())
            return Offset(x, y)
        }
        fun Rect.json() = JSONArray(listOf(left, top, right, bottom))
        fun Rect.inWorld(world: OpticalLayoutGeometry) = Rect(
            (left - world.screenOrigin.x) / world.density, (top - world.screenOrigin.y) / world.density,
            (right - world.screenOrigin.x) / world.density, (bottom - world.screenOrigin.y) / world.density)
    }
}
