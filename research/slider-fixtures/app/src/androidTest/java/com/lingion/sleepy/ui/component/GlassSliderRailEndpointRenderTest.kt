package com.lingion.sleepy.ui.component

import android.graphics.Bitmap
import android.os.Build
import android.os.SystemClock
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.absoluteOffset
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
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
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.LayoutCoordinates
import androidx.compose.ui.layout.onGloballyPositioned
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.platform.LocalView
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.test.hasAnyAncestor
import androidx.compose.ui.test.hasTestTag
import androidx.compose.ui.test.junit4.v2.createComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performTouchInput
import androidx.compose.ui.unit.Density
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.dp
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.filters.SdkSuppress
import androidx.test.platform.app.InstrumentationRegistry
import com.lingion.sleepy.ui.component.liquidglass.GlassBackground
import com.lingion.sleepy.ui.component.liquidglass.GlassHost
import com.lingion.sleepy.ui.component.liquidglass.GlassRangeSlider
import com.lingion.sleepy.ui.component.liquidglass.GlassSlider
import com.lingion.sleepy.ui.component.liquidglass.LocalDockInputTimeNanos
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
import java.util.concurrent.ConcurrentLinkedQueue
import kotlin.math.abs

/**
 * Opt-in production endpoint-rail evidence, never a native visual-parity gate.
 * Enable glassSliderRailEndpoints=true; optionally select comma-separated
 * glassSliderRailScenes and set glassSliderRailRunId. The six default scenes
 * rotate ordinary gray and the existing optical backgrounds without a matrix.
 */
@RunWith(AndroidJUnit4::class)
@SdkSuppress(minSdkVersion = 33)
class GlassSliderRailEndpointRenderTest {
    @get:Rule val compose = createComposeRule()

    private enum class Kind { SINGLE_MAX, SINGLE_MIN, SINGLE_RTL_MAX, RANGE, HUE }
    private data class Scene(
        val id: String,
        val kind: Kind,
        val initial: Float,
        val background: OpticalBackground?,
    ) {
        val rtl get() = kind == Kind.SINGLE_RTL_MAX
        val backgroundName get() = background?.name ?: "color_gray"
        val singleDrag get() = kind in listOf(Kind.SINGLE_MAX, Kind.SINGLE_MIN, Kind.SINGLE_RTL_MAX)
        val physicalSign get() = if (kind == Kind.SINGLE_MIN || rtl) -1f else 1f
        val endpoint get() = if (kind == Kind.SINGLE_MIN) 0f else 1f
        fun json() = JSONObject().put("id", id).put("kind", kind.name)
            .put("initial_value", initial).put("initial_range", if (kind == Kind.RANGE) JSONArray(listOf(0, 1)) else JSONObject.NULL)
            .put("rtl", rtl).put("background", backgroundName)
            .put("background_input", background?.metadata() ?: JSONObject().put("input", "Compose Color.Gray, opaque ordinary backing"))
            .put("finished_callback_exposed", kind != Kind.RANGE)
    }
    private data class DisplayScene(val scene: Scene, val showControl: Boolean)
    private data class Thumb(
        val owner: OpticalLayoutGeometry,
        val carrier: OpticalLayoutGeometry,
        val carrierSemanticRoot: Rect,
    )
    private data class Geometry(
        val source: OpticalLayoutGeometry,
        val host: OpticalLayoutGeometry,
        val holder: OpticalLayoutGeometry,
        val holderSemanticRoot: Rect,
        val rail: OpticalLayoutGeometry,
        val thumbs: Map<String, Thumb>,
        val windowOrigin: Offset,
        val screenOrigin: Offset,
    ) {
        fun root(layout: OpticalLayoutGeometry) = layout.screenRect.translate(-screenOrigin)
        fun world(layout: OpticalLayoutGeometry) = layout.screenRect.inWorld(source)
        val evidenceRoot get(): Rect {
            val all = listOf(root(holder), root(rail)) + thumbs.values.map { root(it.carrier) }
            return Rect(all.minOf { it.left }, all.minOf { it.top }, all.maxOf { it.right }, all.maxOf { it.bottom })
        }
        fun json(): JSONObject {
            val handles = JSONObject()
            thumbs.forEach { (name, thumb) ->
                handles.put(name, JSONObject().put("owner", thumb.owner.json()).put("carrier", thumb.carrier.json())
                    .put("owner_actual_root_rect_px", root(thumb.owner).json())
                    .put("carrier_actual_root_rect_px", root(thumb.carrier).json())
                    .put("carrier_semantic_root_rect_px", thumb.carrierSemanticRoot.json())
                    .put("carrier_world_rect_dp", world(thumb.carrier).json()))
            }
            return JSONObject().put("fixed_source_world", source.json()).put("glass_background_host", host.json())
                .put("outer_holder", holder.json()).put("holder_semantic_root_rect_px", holderSemanticRoot.json())
                .put("holder_actual_root_rect_px", root(holder).json()).put("holder_world_rect_dp", world(holder).json())
                .put("actual_rail", rail.json()).put("rail_world_rect_dp", world(rail).json())
                .put("rail_left_minus_holder_left_dp", world(rail).left - world(holder).left)
                .put("rail_right_minus_holder_right_dp", world(rail).right - world(holder).right)
                .put("thumbs", handles).put("optical_evidence_root_rect_px", evidenceRoot.json())
                .put("content_origin_in_window_px", windowOrigin.json()).put("content_origin_on_screen_px", screenOrigin.json())
                .put("geometry_policy", "Actual attached LayoutCoordinates map all four corners and unit basis. Owner and affine carrier are separate; semantic bounds are retained independently. Rectangles are not alpha contours. Evidence includes the whole holder, rail and carriers, without claiming an unbounded shadow fits the viewport.")
        }
    }

    private var surface: OpticalCaptureWindow? = null
    private var sourceCoordinates: LayoutCoordinates? = null
    private var hostCoordinates: LayoutCoordinates? = null
    private var density = 1f
    private var fontScale = 1f
    private var systemFontScale = 1f
    private var currentValue = 0f
    private var currentRange: ClosedFloatingPointRange<Float> = 0f..1f
    private var pointerDown = false
    private var pointerStream = 0
    private var downComposeMs: Long? = null
    private var downUptimeMs: Long? = null
    private val valueEvents = ConcurrentLinkedQueue<JSONObject>()
    private val finishEvents = ConcurrentLinkedQueue<JSONObject>()
    private val inputEvents = JSONArray()

    @Test fun captureProductionEndpointRails() {
        val arguments = InstrumentationRegistry.getArguments()
        assumeTrue("Enable with glassSliderRailEndpoints=true", arguments.getString("glassSliderRailEndpoints") == "true")
        val available = listOf(
            Scene("single_max", Kind.SINGLE_MAX, .75f, null),
            Scene("single_min", Kind.SINGLE_MIN, .25f, OpticalBackground.fine_grid),
            Scene("single_rtl_max", Kind.SINGLE_RTL_MAX, .75f, OpticalBackground.color_stripes),
            Scene("range_endpoints", Kind.RANGE, 0f, OpticalBackground.tonal_blocks),
            Scene("hue_0", Kind.HUE, 0f, OpticalBackground.synthetic_landscape),
            Scene("hue_360", Kind.HUE, 360f, null),
        )
        val selectedIds = arguments.getString("glassSliderRailScenes")?.split(',')?.map(String::trim)?.distinct()
            ?: available.map { it.id }
        require(selectedIds.isNotEmpty() && selectedIds.all { id -> available.any { it.id == id } }) {
            "glassSliderRailScenes must select from ${available.map { it.id }}"
        }
        val scenes = selectedIds.map { id -> available.single { it.id == id } }
        val runId = (arguments.getString("glassSliderRailRunId") ?: System.currentTimeMillis().toString())
            .replace(Regex("[^A-Za-z0-9_-]"), "_")
        val directory = File(InstrumentationRegistry.getInstrumentation().targetContext.getExternalFilesDir(null),
            "slider-rail-endpoints/$runId").apply { check(isDirectory || mkdirs()) }
        val captures = JSONArray()
        val baselines = JSONArray()
        val cleanups = JSONArray()
        val result = JSONObject().put("schema", 1).put("status", "running").put("run_id", runId)
            .put("sdk", Build.VERSION.SDK_INT).put("model", Build.MODEL).put("fingerprint", Build.FINGERPRINT)
            .put("selected_scenes", JSONArray(scenes.map { it.json() }))
            .put("scope", "Actual production GlassSlider, GlassRangeSlider and HueSlider endpoint rail coverage on ordinary backing. Hardware Window PixelCopy and independently composited display screenshots; no software captureToImage or replica rail.")
            .put("world_policy", "375x667dp source at actual GlassBackground top-left, 335dp unmodified control at physical(20,406)dp, fontScale1; RTL is applied only to the production control. No fixture translation, scaling, native alignment or parent glass pane.")
            .put("clock_policy", "Compose autoAdvance=false; LocalDockInputTimeNanos reads Compose mainClock. Advance32ms before each injected action, then1600ms synthetic settling for optical holds. MOVE sample delay16ms. Export real uptime independently; this is not a native timing or velocity claim.")
            .put("input_policy", "Actual REST carrier-center DOWN. Single thumb uses one-time10dp slop plus .25*actual335dp holder width to its business endpoint, captures while still DOWN, then another10dp physical overdrive and another DOWN-held capture. Range endpoints and hue0/360 use stationary center holds. Every stream ends with CANCEL, never UP.")
            .put("rail_assertion_policy", "Actual rail left/right equal the full335dp holder endpoints. Export GPU pixels and actual carrier geometry for endpoint inspection; bounding-box coverage alone does not prove lens optics, all pixels, or native1:1.")
            .put("capture_policy", "Existing HWUI commit+PixelCopy and display readiness RGB3/99.5% thresholds. Only observed systemBars/displayCutout may be excluded for readiness. Full screenshots are preserved; all holder, rail and carrier evidence must remain in the compared App region.")
            .put("native_parity_claim", false).put("baselines", baselines).put("captures", captures)
            .put("cleanup_observations", cleanups).put("input_events", inputEvents)
        val report = File(directory, "result.json")
        fun save() {
            result.put("density", density).put("font_scale", fontScale).put("system_font_scale", systemFontScale)
                .put("pointer_down", pointerDown)
                .put("value_events", JSONArray(valueEvents.toList())).put("finish_events", JSONArray(finishEvents.toList()))
            report.writeText(result.toString(2))
        }
        val displayed = mutableStateOf(DisplayScene(scenes.first(), false))
        save()
        try {
            compose.setContent {
                val actual = LocalDensity.current
                SideEffect { systemFontScale = actual.fontScale }
                CompositionLocalProvider(
                    LocalDensity provides Density(actual.density, fontScale = 1f),
                    LocalLayoutDirection provides LayoutDirection.Ltr,
                    LocalDockInputTimeNanos provides { compose.mainClock.currentTime * 1_000_000L },
                ) { Fixture(displayed.value) }
            }
            compose.waitForIdle()
            compose.mainClock.autoAdvance = false
            for (scene in scenes) {
                result.put("active_scene", scene.id).put("active_phase", "background")
                compose.runOnIdle { displayed.value = DisplayScene(scene, false) }
                settle()
                val activity = checkNotNull(surface)
                assertTrue("Actual GPU/HWUI surface is required", activity.root.isHardwareAccelerated)
                validateWorld()
                val baselineWindow = activity.capture()
                var baselineScreen: Bitmap? = null
                try {
                    val stem = "${scene.id}-background"
                    baselineWindow.saveOpticalPng(File(directory, "$stem-window.png"))
                    val ready = awaitOpticalSurfaceScreen(activity, baselineWindow, density, directory, stem, excludeSystemBars = true)
                    baselineScreen = ready.bitmap
                    ready.bitmap.saveOpticalPng(File(directory, "$stem-screen.png"))
                    baselines.put(JSONObject().put("scene", scene.id).put("background", scene.backgroundName)
                        .put("window_png", "$stem-window.png").put("screen_png", "$stem-screen.png")
                        .put("source_geometry", worldJson()).put("window_geometry", activity.geometry())
                        .put("display_readiness", ready.verification))
                    compose.runOnIdle { displayed.value = DisplayScene(scene, true) }
                    settle()
                    val rest = observe()
                    validateGeometry(rest)
                    assertValue(scene, endpoint = false)
                    capture(scene, "rest", rest, directory, captures, baselineWindow, ready.bitmap)
                    save()
                    val endpoints = if (scene.kind == Kind.RANGE) listOf("lower", "upper") else listOf("upper")
                    for (endpoint in endpoints) {
                        val before = observe()
                        val press = before.root(checkNotNull(before.thumbs[endpoint]).carrier).center - before.holderSemanticRoot.topLeft
                        var completedHeldCapture = false
                        try {
                            input(scene, "DOWN", press, report, result) {
                                compose.onNodeWithTag(HOLDER_TAG, useUnmergedTree = true).performTouchInput { down(press) }
                                pointerDown = true
                            }
                            settle()
                            val held = observe()
                            assertTrue("DOWN expands the selected production thumb owner",
                                checkNotNull(held.thumbs[endpoint]).owner.size.width > checkNotNull(before.thumbs[endpoint]).owner.size.width)
                            if (scene.singleDrag) {
                                val threshold = press + Offset(scene.physicalSign * (10f * density + .25f * before.holder.size.width), 0f)
                                input(scene, "MOVE_TO_ENDPOINT_THRESHOLD", threshold, report, result) {
                                    compose.onNodeWithTag(HOLDER_TAG, useUnmergedTree = true)
                                        .performTouchInput { moveTo(threshold, 16) }
                                }
                                settle()
                                assertValue(scene, endpoint = true)
                                val atEndpoint = observe()
                                capture(scene, "endpoint-held", atEndpoint, directory, captures, baselineWindow, ready.bitmap)
                                save()
                                val overdrive = threshold + Offset(scene.physicalSign * 10f * density, 0f)
                                input(scene, "MOVE_10DP_OVERDRIVE", overdrive, report, result) {
                                    compose.onNodeWithTag(HOLDER_TAG, useUnmergedTree = true)
                                        .performTouchInput { moveTo(overdrive, 16) }
                                }
                                settle()
                                assertValue(scene, endpoint = true)
                                val pulled = observe()
                                assertTrue("The still-down production carrier responds beyond the clamped business endpoint",
                                    scene.physicalSign * (pulled.root(checkNotNull(pulled.thumbs[endpoint]).carrier).center.x -
                                        atEndpoint.root(checkNotNull(atEndpoint.thumbs[endpoint]).carrier).center.x) > .5f)
                                capture(scene, "overdrive-held", pulled, directory, captures, baselineWindow, ready.bitmap)
                            } else {
                                assertValue(scene, endpoint = false)
                                assertTrue("A stationary endpoint hold must not publish a value", valueEvents.none { it.getString("scene") == scene.id })
                                capture(scene, "$endpoint-held", held, directory, captures, baselineWindow, ready.bitmap)
                            }
                            save()
                            completedHeldCapture = true
                        } finally {
                            if (pointerDown) {
                                input(scene, "CANCEL", null, report, result) {
                                    compose.onNodeWithTag(HOLDER_TAG, useUnmergedTree = true).performTouchInput { cancel() }
                                    pointerDown = false
                                }
                                settle()
                                if (completedHeldCapture) {
                                    assertValue(scene, endpoint = scene.singleDrag)
                                    assertTrue("CANCEL must not finish or commit", finishEvents.none { it.getString("scene") == scene.id })
                                }
                                cleanups.put(JSONObject().put("scene", scene.id).put("endpoint", endpoint)
                                    .put("pointer_down", pointerDown).put("value", currentValue)
                                    .put("range", JSONArray(listOf(currentRange.start, currentRange.endInclusive)))
                                    .put("geometry", observe().json()).put("compose_ms", compose.mainClock.currentTime)
                                    .put("wall_uptime_ms", SystemClock.uptimeMillis()))
                                save()
                            }
                        }
                    }
                } finally {
                    baselineScreen?.recycle()
                    baselineWindow.recycle()
                }
            }
            result.put("status", "collected_endpoint_rail_evidence_not_native_acceptance")
        } catch (failure: Throwable) {
            result.put("status", "failed").put("exception", "${failure.javaClass.name}: ${failure.message}")
            throw failure
        } finally {
            // Do not synthesize an UP even when a capture/assertion fails.
            if (pointerDown) {
                try {
                    compose.onNodeWithTag(HOLDER_TAG, useUnmergedTree = true).performTouchInput { cancel() }
                    pointerDown = false
                } catch (cleanup: Throwable) {
                    result.put("cleanup_exception", "${cleanup.javaClass.name}: ${cleanup.message}")
                }
            }
            compose.mainClock.autoAdvance = true
            save()
        }
    }

    @Composable private fun Fixture(displayed: DisplayScene) {
        val scene = displayed.scene
        val actual = LocalDensity.current
        val view = LocalView.current
        SideEffect { surface = OpticalCaptureWindow.from(view); density = actual.density; fontScale = actual.fontScale }
        SleepyThemeProvider(darkTheme = false, themeKey = ThemePresets.KEY_DEFAULT) {
            CompositionLocalProvider(LocalUiStyle provides UiStyle.LiquidGlass) {
                GlassHost(Modifier.fillMaxSize(), background = MaterialTheme.colorScheme.background) {
                    GlassBackground(0f, Modifier.fillMaxSize().onGloballyPositioned { hostCoordinates = it }) {
                        Box(Modifier.fillMaxSize().background(Color(0xFFF0F0F5))) {
                            val source = Modifier.align(Alignment.TopStart).requiredSize(375.dp, 667.dp)
                                .clipToBounds().onGloballyPositioned { sourceCoordinates = it }
                            if (scene.background == null) Box(source.background(Color.Gray))
                            else OpticalCaptureBackground(scene.background, source)
                        }
                    }
                    if (displayed.showControl) key(scene.id) {
                        var value by remember { mutableFloatStateOf(scene.initial) }
                        var pair by remember { mutableStateOf<ClosedFloatingPointRange<Float>>(0f..1f) }
                        // Read in this composition group. Reading only inside
                        // SideEffect leaves this observer stale when the child
                        // control's restart scope consumes a value change.
                        val renderedValue = value
                        val renderedRange = pair
                        SideEffect { currentValue = renderedValue; currentRange = renderedRange }
                        Box(Modifier.absoluteOffset(20.dp, 406.dp).width(335.dp).testTag(HOLDER_TAG)) {
                            CompositionLocalProvider(LocalLayoutDirection provides if (scene.rtl) LayoutDirection.Rtl else LayoutDirection.Ltr) {
                                when (scene.kind) {
                                    Kind.RANGE -> GlassRangeSlider(pair, { next ->
                                        valueEvents.add(event(scene, "onValueChange").put("range", JSONArray(listOf(next.start, next.endInclusive))))
                                        pair = next
                                    }, Modifier.fillMaxWidth(), valueRange = 0f..1f, steps = 0)
                                    Kind.HUE -> HueSlider(value, { next ->
                                        valueEvents.add(event(scene, "onHueChange").put("value", next)); value = next
                                    }, Modifier.fillMaxWidth(), onHueCommit = { next ->
                                        finishEvents.add(event(scene, "onHueCommit").put("value", next))
                                    })
                                    else -> GlassSlider(value, { next ->
                                        valueEvents.add(event(scene, "onValueChange").put("value", next)); value = next
                                    }, Modifier.fillMaxWidth(), onValueChangeFinished = {
                                        finishEvents.add(event(scene, "onValueChangeFinished"))
                                    })
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    private fun settle() { compose.mainClock.advanceTimeBy(1600); compose.waitForIdle() }
    private fun event(scene: Scene, action: String) = JSONObject().put("scene", scene.id).put("action", action)
        .put("compose_ms", compose.mainClock.currentTime).put("wall_uptime_ms", SystemClock.uptimeMillis())

    private fun input(scene: Scene, action: String, position: Offset?, report: File,
                      result: JSONObject, inject: () -> Unit) {
        compose.mainClock.advanceTimeBy(32)
        compose.waitForIdle()
        if (action == "DOWN") {
            pointerStream++
            downComposeMs = compose.mainClock.currentTime
            downUptimeMs = SystemClock.uptimeMillis()
        }
        val receipt = event(scene, action).put("pointer_stream", pointerStream).put("status", "requested")
            .put("holder_semantic_local_px", position?.json() ?: JSONObject.NULL)
            .put("pointer_down_before", pointerDown)
        if (position != null) {
            val geometry = observe()
            val root = geometry.holderSemanticRoot.topLeft + position
            receipt.put("actual_injection_root_px", root.json()).put("actual_injection_screen_px", (root + geometry.screenOrigin).json())
        }
        inputEvents.put(receipt)
        result.put("active_scene", scene.id).put("active_phase", action).put("input_events", inputEvents)
        report.writeText(result.toString(2))
        inject()
        receipt.put("status", "injected").put("pointer_down_after", pointerDown)
            .put("after_injection_wall_uptime_ms", SystemClock.uptimeMillis())
    }

    private fun worldJson(): JSONObject = compose.runOnIdle {
        JSONObject().put("source", OpticalLayoutGeometry.read(checkNotNull(sourceCoordinates), density).json())
            .put("host", OpticalLayoutGeometry.read(checkNotNull(hostCoordinates), density).json())
    }

    private fun validateWorld() = compose.runOnIdle {
        val source = OpticalLayoutGeometry.read(checkNotNull(sourceCoordinates), density)
        val host = OpticalLayoutGeometry.read(checkNotNull(hostCoordinates), density)
        assertEquals("Source world width", 375.0 * density, source.size.width.toDouble(), .5)
        assertEquals("Source world height", 667.0 * density, source.size.height.toDouble(), .5)
        assertTrue("Whole fixed world fits actual host", host.size.width >= source.size.width && host.size.height >= source.size.height)
        assertTrue("World starts at actual backing origin", (source.screenOrigin - host.screenOrigin).getDistance() <= .5f)
        unitAxes("source", source); unitAxes("host", host)
        assertEquals("Fixture font scale", 1f, fontScale, 0f)
    }

    private fun observe(): Geometry {
        val activity = checkNotNull(surface)
        val holder = compose.onNodeWithTag(HOLDER_TAG, useUnmergedTree = true).fetchSemanticsNode()
        val rail = compose.onNodeWithTag("slider-track", useUnmergedTree = true).fetchSemanticsNode()
        val owners = listOf("lower" to "glass-slider-start", "upper" to "glass-slider-end").mapNotNull { (name, tag) ->
            val owner = compose.onAllNodes(hasTestTag(tag), useUnmergedTree = true).fetchSemanticsNodes().singleOrNull()
                ?: return@mapNotNull null
            val carrier = compose.onAllNodes(hasTestTag("glass-slider-thumb-carrier") and hasAnyAncestor(hasTestTag(tag)),
                useUnmergedTree = true).fetchSemanticsNodes().single()
            name to (owner to carrier)
        }.toMap()
        val windowOrigin = activity.origin().let { Offset(it[0].toFloat(), it[1].toFloat()) }
        val screenOrigin = activity.screenOrigin().let { Offset(it[0].toFloat(), it[1].toFloat()) }
        return compose.runOnIdle {
            fun read(coordinates: LayoutCoordinates) = OpticalLayoutGeometry.read(coordinates, density)
            Geometry(read(checkNotNull(sourceCoordinates)), read(checkNotNull(hostCoordinates)),
                read(holder.layoutInfo.coordinates), holder.boundsInRoot, read(rail.layoutInfo.coordinates),
                owners.mapValues { (_, nodes) -> Thumb(read(nodes.first.layoutInfo.coordinates),
                    read(nodes.second.layoutInfo.coordinates), nodes.second.boundsInRoot) }, windowOrigin, screenOrigin)
        }
    }

    private fun validateGeometry(g: Geometry) {
        validateWorld()
        assertEquals("Production holder width", 335.0 * density, g.holder.size.width.toDouble(), .5)
        assertEquals("Production touch height", 48.0 * density, g.holder.size.height.toDouble(), .5)
        unitAxes("holder", g.holder)
        assertEquals("Rail covers the actual left holder endpoint", g.root(g.holder).left, g.root(g.rail).left, .5f)
        assertEquals("Rail covers the actual right holder endpoint", g.root(g.holder).right, g.root(g.rail).right, .5f)
        assertTrue("At least the real production upper thumb is present", "upper" in g.thumbs)
        g.thumbs.values.forEach { thumb ->
            val rect = g.world(thumb.carrier)
            assertTrue("Whole affine carrier stays inside recorded backing world", rect.left >= 0 && rect.top >= 0 && rect.right <= 375 && rect.bottom <= 667)
        }
    }

    private fun assertValue(scene: Scene, endpoint: Boolean) = compose.runOnIdle {
        if (scene.kind == Kind.RANGE) {
            assertEquals("Range lower remains at0", 0f, currentRange.start, 0f)
            assertEquals("Range upper remains at1", 1f, currentRange.endInclusive, 0f)
        } else {
            val expected = if (endpoint) scene.endpoint else scene.initial
            assertEquals("Controlled value for ${scene.id}", expected, currentValue, .00001f)
            val upper = if (scene.kind == Kind.HUE) 360f else 1f
            assertTrue("Published values stay in their business domain", valueEvents.filter { it.getString("scene") == scene.id }
                .all { it.getDouble("value").let { value -> value.isFinite() && value in 0.0..upper.toDouble() } })
        }
        assertTrue("No finish/commit before any UP; this fixture only CANCELs", finishEvents.none { it.getString("scene") == scene.id })
    }

    private fun capture(scene: Scene, phase: String, g: Geometry, directory: File, captures: JSONArray,
                        baselineWindow: Bitmap, baselineScreen: Bitmap) {
        validateGeometry(g)
        assertEquals("REST is unpressed and all held captures retain the injected pointer", phase != "rest", pointerDown)
        val activity = checkNotNull(surface)
        val stem = "${scene.id}-$phase"
        val window = activity.capture()
        try {
            window.saveOpticalPng(File(directory, "$stem-window.png"))
            val ready = awaitOpticalSurfaceScreen(activity, window, density, directory, stem, excludeSystemBars = true)
            try {
                val evidenceScreen = g.evidenceRoot.translate(g.screenOrigin)
                val compared = ready.verification.getJSONArray("compared_screen_rect_px")
                assertTrue("Readiness keeps the entire holder, rail and actual carriers",
                    evidenceScreen.left >= compared.getDouble(0) && evidenceScreen.top >= compared.getDouble(1) &&
                        evidenceScreen.right <= compared.getDouble(2) && evidenceScreen.bottom <= compared.getDouble(3))
                contains("Source world in Window", window, g.source.screenRect.translate(g.windowOrigin - g.screenOrigin))
                contains("Source world on display", ready.bitmap, g.source.screenRect)
                contains("Entire evidence in Window", window, g.evidenceRoot.translate(g.windowOrigin))
                contains("Entire evidence on display", ready.bitmap, evidenceScreen)
                ready.bitmap.saveOpticalPng(File(directory, "$stem-screen.png"))
                fun metric(tag: String, rect: Rect) = JSONObject().put("tag", tag).put("actual_root_rect_px", rect.json())
                    .put("window", opticalRegionMetrics(window, baselineWindow, rect.translate(g.windowOrigin)))
                    .put("composited_display", opticalRegionMetrics(ready.bitmap, baselineScreen, rect.translate(g.screenOrigin)))
                val metrics = listOf(metric("holder", g.root(g.holder)), metric("full-width-rail", g.root(g.rail))) +
                    g.thumbs.map { (name, thumb) -> metric("$name-affine-carrier", g.root(thumb.carrier)) }
                captures.put(JSONObject().put("scene", scene.id).put("background", scene.backgroundName).put("phase", phase)
                    .put("theme", "light").put("rtl", scene.rtl)
                    .put("window_png", "$stem-window.png").put("screen_png", "$stem-screen.png")
                    .put("baseline_window_png", "${scene.id}-background-window.png")
                    .put("baseline_screen_png", "${scene.id}-background-screen.png")
                    .put("geometry", g.json()).put("window_geometry", activity.geometry()).put("display_readiness", ready.verification)
                    .put("pointer_down", pointerDown).put("pointer_stream", pointerStream)
                    .put("pointer_down_source", if (pointerDown) "Successful DOWN injection retained across performTouchInput calls; no UP or CANCEL before this held screenshot" else "No active injected pointer")
                    .put("down_compose_ms", if (pointerDown) downComposeMs else JSONObject.NULL)
                    .put("down_wall_uptime_ms", if (pointerDown) downUptimeMs else JSONObject.NULL)
                    .put("compose_ms", compose.mainClock.currentTime).put("wall_uptime_ms", SystemClock.uptimeMillis())
                    .put("value", currentValue).put("range", JSONArray(listOf(currentRange.start, currentRange.endInclusive)))
                    .put("value_events", JSONArray(valueEvents.filter { it.getString("scene") == scene.id }))
                    .put("finish_events", JSONArray(finishEvents.filter { it.getString("scene") == scene.id }))
                    .put("finished_callback_exposed", scene.kind != Kind.RANGE)
                    .put("measurements", JSONArray(metrics)))
            } finally { ready.bitmap.recycle() }
        } finally { window.recycle() }
    }

    private fun unitAxes(label: String, g: OpticalLayoutGeometry) {
        val x = g.screenBasis[1] - g.screenBasis[0]
        val y = g.screenBasis[2] - g.screenBasis[0]
        assertTrue("$label has unscaled, unrotated axes", abs(x.x - 1) <= .001f && abs(x.y) <= .001f && abs(y.x) <= .001f && abs(y.y - 1) <= .001f)
    }

    private fun contains(label: String, bitmap: Bitmap, rect: Rect) {
        assertTrue("$label fits entirely without clamped sampling: $rect in ${bitmap.width}x${bitmap.height}",
            rect.left >= -.5f && rect.top >= -.5f && rect.right <= bitmap.width + .5f && rect.bottom <= bitmap.height + .5f && rect.width > 0 && rect.height > 0)
    }

    private companion object {
        const val HOLDER_TAG = "slider-rail-endpoint-holder"
        fun Offset.json() = JSONArray(listOf(x, y))
        fun Rect.json() = JSONArray(listOf(left, top, right, bottom))
        fun Rect.inWorld(world: OpticalLayoutGeometry) = Rect((left - world.screenOrigin.x) / world.density,
            (top - world.screenOrigin.y) / world.density, (right - world.screenOrigin.x) / world.density,
            (bottom - world.screenOrigin.y) / world.density)
    }
}
