package com.lingion.sleepy.ui.component.sliderlayerresearch

import android.graphics.Bitmap
import android.os.SystemClock
import android.view.View
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.width
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.LayoutInfo
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.platform.LocalView
import androidx.compose.ui.platform.testTag
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
import com.lingion.sleepy.ui.component.liquidglass.GlassSlider
import com.lingion.sleepy.ui.component.liquidglass.LocalDockInputTimeNanos
import com.lingion.sleepy.ui.theme.LocalUiStyle
import com.lingion.sleepy.ui.theme.SleepyThemeProvider
import com.lingion.sleepy.ui.theme.ThemePresets
import com.lingion.sleepy.ui.theme.UiStyle
import java.io.File
import java.security.MessageDigest
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Assume.assumeTrue
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

/** One explicitly enabled diagnostic group. No native parity or optical acceptance is asserted. */
@RunWith(AndroidJUnit4::class)
@SdkSuppress(minSdkVersion = 33)
class SliderLayerObservationTest {
    @get:Rule val compose = createComposeRule()

    @Test fun observeOneRestHeldDragCancelGroup() {
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        val arguments = InstrumentationRegistry.getArguments()
        assumeTrue("Enable glassSliderLayerObservation=true", arguments.getString("glassSliderLayerObservation") == "true")
        val runId = requireNotNull(arguments.getString("glassSliderLayerRunId")) { "Supply a new glassSliderLayerRunId" }
        require(runId.matches(Regex("[A-Za-z0-9][A-Za-z0-9._-]{0,79}")))
        val root = File(instrumentation.targetContext.getExternalFilesDir(null), "slider-layer-observation-20261116")
        check(root.mkdirs() || root.isDirectory)
        val directory = File(root, runId)
        check(directory.mkdir()) { "Refusing to reuse or overwrite an existing run: $directory" }
        val samples = JSONArray(); val events = JSONArray(); val screenshots = JSONArray()
        val report = JSONObject().put("schema", 1).put("status", "running").put("run_id", runId)
            .put("study", "slider-layer-observation-20261116").put("optical_acceptance", false)
            .put("sampling", "One light flat128 production GlassSlider; quarter REST; center DOWN;1600ms HELD;4 MOVE steps across60dp, each input delay advances the main clock16ms before delivery, then observe without another clock advance; CANCEL;1600ms settle. Compose synthetic clock, not natural-motion parity.")
            .put("move_clock_policy", "Compose UI1.12.1 AndroidInputDispatcher flush advances mainClock by the event-time delta before delivery. Each moveTo(delayMillis=16) is the sole16ms advance; snapshots have no post-delivery animation-frame advance.")
            .put("samples", samples).put("input_events", events).put("screenshots", screenshots)
        var value by mutableFloatStateOf(.25f)
        var changes = 0; var finishes = 0; var activePointer = false
        var fixtureView: View? = null
        var density = 0f
        lateinit var observer: SliderLayerObserver1121
        fun save() { File(directory, "observation.json").writeText(report.toString(2)) }
        fun event(action: String, point: Offset? = null): JSONObject {
            val row = JSONObject().put("action", action).put("compose_ms", compose.mainClock.currentTime)
                .put("wall_uptime_ms", SystemClock.uptimeMillis())
                .put("requested_holder_local_px", point?.let { JSONArray(listOf(it.x, it.y)) } ?: JSONObject.NULL)
            events.put(row)
            return row
        }
        fun frameFence() {
            val committed = CountDownLatch(1)
            compose.runOnUiThread {
                val view = checkNotNull(fixtureView)
                check(view.isHardwareAccelerated) { "Hardware-accelerated fixture required" }
                view.rootView.viewTreeObserver.registerFrameCommitCallback { committed.countDown() }
                view.rootView.postInvalidateOnAnimation()
            }
            check(committed.await(5, TimeUnit.SECONDS)) { "HWUI commit did not complete" }
        }
        fun observe(phase: String, screenshot: Boolean = false) {
            compose.waitForIdle()
            frameFence()
            val nodes = linkedMapOf("holder" to "layer-observation-holder", "owner" to "glass-slider-end",
                "carrier" to "glass-slider-thumb-carrier").mapValues { (_, tag) ->
                compose.onNodeWithTag(tag, useUnmergedTree = true).fetchSemanticsNode()
            }
            val row = compose.runOnIdle {
                val layouts = linkedMapOf<String, LayoutInfo>()
                nodes.forEach { (role, node) -> layouts[role] = node.layoutInfo }
                JSONObject().put("phase", phase).put("compose_ms", compose.mainClock.currentTime)
                    .put("wall_uptime_ms", SystemClock.uptimeMillis()).put("active_pointer", activePointer)
                    .put("value", value).put("changes", changes).put("finishes", finishes)
                    .put("node_bindings", JSONArray(nodes.map { (role, node) ->
                        JSONObject().put("role", role).put("semantics_id", node.id)
                            .put("semantic_bounds_root_px", node.boundsInRoot.let { JSONArray(listOf(it.left, it.top, it.right, it.bottom)) })
                    })).put("layer_observation", observer.observe(layouts))
            }
            samples.put(row)
            if (screenshot) {
                val bitmap = checkNotNull(instrumentation.uiAutomation.takeScreenshot()) { "Composited display unavailable" }
                try {
                    check(bitmap.width > 0 && bitmap.height > 0)
                    val file = File(directory, "$phase-display.png")
                    file.outputStream().use { check(bitmap.compress(Bitmap.CompressFormat.PNG, 100, it)) }
                    screenshots.put(JSONObject().put("phase", phase).put("file", file.name)
                        .put("sha256", MessageDigest.getInstance("SHA-256").digest(file.readBytes()).joinToString("") { "%02x".format(it) })
                        .put("size_px", JSONArray(listOf(bitmap.width, bitmap.height)))
                        .put("binding", "Composited display after the sample's HWUI fence; node coordinates are screen pixels; not atomic with the sample"))
                } finally { bitmap.recycle() }
            }
            save()
        }
        save()
        compose.mainClock.autoAdvance = false
        try {
            observer = SliderLayerObserver1121()
            compose.setContent {
                val actualDensity = LocalDensity.current
                val view = LocalView.current
                SideEffect { fixtureView = view; density = actualDensity.density }
                CompositionLocalProvider(LocalDensity provides Density(actualDensity.density, 1f),
                    LocalLayoutDirection provides LayoutDirection.Ltr,
                    LocalDockInputTimeNanos provides { compose.mainClock.currentTime * 1_000_000L }) {
                    SleepyThemeProvider(darkTheme = false, themeKey = ThemePresets.KEY_DEFAULT) {
                        CompositionLocalProvider(LocalUiStyle provides UiStyle.LiquidGlass) {
                            GlassHost(Modifier.fillMaxSize(), background = Color(0xFF808080)) {
                                GlassBackground(0f, Modifier.fillMaxSize()) {
                                    Box(Modifier.fillMaxSize().background(Color(0xFF808080)))
                                }
                                Box(Modifier.offset(20.dp, 200.dp).width(335.dp).testTag("layer-observation-holder")) {
                                    GlassSlider(value, { next -> value = next; changes++ }, Modifier.fillMaxWidth(),
                                        onValueChangeFinished = { finishes++ })
                                }
                            }
                        }
                    }
                }
            }
            compose.mainClock.advanceTimeBy(1600); compose.waitForIdle()
            report.put("density", density).put("font_scale", 1).put("layout_direction", "LTR")
            observe("rest", screenshot = true)
            val holder = compose.onNodeWithTag("layer-observation-holder", useUnmergedTree = true)
            val bounds = holder.fetchSemanticsNode().boundsInRoot
            val carrier = compose.onNodeWithTag("glass-slider-thumb-carrier", useUnmergedTree = true).fetchSemanticsNode().boundsInRoot
            val downPoint = carrier.center - bounds.topLeft
            val end = downPoint + Offset(60f * density, 0f)
            require(end.x < bounds.width && downPoint.x > 0f && downPoint.y > 0f && downPoint.y < bounds.height)
            holder.performTouchInput { down(downPoint) }; activePointer = true; event("DOWN", downPoint)
            compose.mainClock.advanceTimeBy(1600); compose.waitForIdle()
            assertEquals("Center hold must preserve quarter value", .25f, value, 0f)
            assertEquals("Center hold must not publish a value", 0, changes)
            assertEquals("Center hold must not finish", 0, finishes)
            observe("held", screenshot = true)
            for (step in 1..4) {
                val point = downPoint + (end - downPoint) * (step / 4f)
                val beforeInput = compose.mainClock.currentTime
                // AndroidInputDispatcher.flush advances mainClock by16ms before delivery.
                // Do not advance it again: observe the realized state at this input boundary.
                holder.performTouchInput { moveTo(point, delayMillis = 16) }
                val afterInput = compose.mainClock.currentTime
                event("MOVE-$step", point).put("requested_event_delay_ms", 16)
                    .put("main_clock_before_injection_ms", beforeInput)
                    .put("main_clock_after_injection_ms", afterInput)
                    .put("observed_main_clock_delta_ms", afterInput - beforeInput)
                    .put("explicit_post_delivery_advance_ms", 0)
                check(afterInput - beforeInput == 16L) { "MOVE input clock delta differs from16ms: ${afterInput - beforeInput}" }
                observe("drag-$step", screenshot = step == 4)
            }
            assertTrue("Drag must reach the real value callback", changes > 0 && value > .25f && value < 1f)
            holder.performTouchInput { cancel() }; activePointer = false; event("CANCEL")
            compose.mainClock.advanceTimeBy(1600); observe("cancelled")
            assertEquals("CANCEL must not publish completion", 0, finishes)
            report.put("status", "observed").put("sample_count", samples.length()).put("screenshot_count", screenshots.length())
        } catch (failure: Throwable) {
            report.put("status", "failed").put("failure", "${failure.javaClass.name}: ${failure.message}")
            throw failure
        } finally {
            if (activePointer) {
                try {
                    compose.onNodeWithTag("layer-observation-holder", useUnmergedTree = true).performTouchInput { cancel() }
                    activePointer = false; event("CANCEL-cleanup")
                } catch (cleanup: Throwable) {
                    report.put("cleanup_failure", cleanup.toString()).put("status", "failed")
                }
            }
            report.put("active_pointer_after_cleanup", activePointer)
            save()
        }
    }
}
