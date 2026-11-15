package com.lingion.sleepy.ui.component

import android.app.Activity
import android.content.ContextWrapper
import android.graphics.Bitmap
import android.os.SystemClock
import android.view.InputDevice
import android.view.MotionEvent
import android.view.View
import android.view.ViewGroup
import android.view.inspector.WindowInspector
import android.widget.FrameLayout
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.width
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.Recomposer
import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.draw.drawWithContent
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Rect
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.ComposeView
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.LocalView
import androidx.compose.ui.platform.ViewRootForTest
import androidx.compose.ui.platform.createLifecycleAwareWindowRecomposer
import androidx.compose.ui.semantics.SemanticsNode
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.semantics.getOrNull
import androidx.compose.ui.test.junit4.v2.createComposeRule
import androidx.compose.ui.unit.dp
import androidx.lifecycle.LifecycleOwner
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.filters.SdkSuppress
import androidx.test.platform.app.InstrumentationRegistry
import com.lingion.sleepy.ui.component.liquidglass.GlassBackground
import com.lingion.sleepy.ui.component.liquidglass.GlassHost
import com.lingion.sleepy.ui.component.liquidglass.GlassLanguageMenu
import com.lingion.sleepy.ui.component.liquidglass.LanguageMenuPresentationDiagnostics
import com.lingion.sleepy.ui.component.liquidglass.LanguageMenuVisualStateKey
import com.lingion.sleepy.ui.component.liquidglass.LanguageMenuHandoffStateKey
import com.lingion.sleepy.ui.theme.LocalDarkTheme
import com.lingion.sleepy.ui.theme.LocalUiStyle
import com.lingion.sleepy.ui.theme.UiStyle
import org.json.JSONObject
import org.json.JSONArray
import java.io.File
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import java.util.concurrent.ConcurrentLinkedQueue
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger
import kotlin.math.ceil
import kotlin.math.abs
import kotlin.math.roundToInt

/** Product-menu behavior and actual GPU coverage with a real-time composition clock. */
@RunWith(AndroidJUnit4::class)
@SdkSuppress(minSdkVersion = 33)
class AssetLanguageGpuTripletDiagnosticTest {
    @get:Rule val compose = createComposeRule()

    private val instrumentation get() = InstrumentationRegistry.getInstrumentation()
    private val events = ConcurrentLinkedQueue<JSONObject>()
    private val selections = ConcurrentLinkedQueue<String>()
    private val dismissals = ConcurrentLinkedQueue<JSONObject>()
    private val rowSequence = AtomicInteger()
    private val languages = listOf(
        "zh-CN" to "简体中文", "zh-TW" to "繁體中文", "en" to "English",
        "ja" to "日本語", "es" to "Español",
    )
    private val neutral = Color(.94f, .94f, .96f)
    private var selected by mutableStateOf("zh-CN")
    private lateinit var activity: Activity
    private var realView: ComposeView? = null
    private var realRecomposer: Recomposer? = null
    private var density = 1f
    private var cardWidthDp: Float? = null
    private var cardTopDp: Float? = null
    private var activeDownTime = 0L
    private var activePointer = false
    private var lastPointer = Offset.Zero
    private var suppressClosedSourceDrawing by mutableStateOf(false)
    private val sourceDrawSequence = AtomicInteger()
    @Volatile private var lastSourceDrawSuppressed: Boolean? = null

    fun selectionDismissalAndLongPressKeepTheOriginalPointerBehavior() {
        val tapHoldMs = 67L
        val longPressHoldMs = 450L
        val settleMs = 850L
        installRealtimeFixture()
        val priorObserver = LanguageMenuPresentationDiagnostics.observer
        LanguageMenuPresentationDiagnostics.observer = { sessionId, event, _, windowIdentity, windowClass ->
            add("presentation_event").put("session_id", sessionId).put("stage", event)
                .put("window_identity", windowIdentity ?: JSONObject.NULL)
                .put("window_class", windowClass ?: JSONObject.NULL)
        }
        try {
            waitFor("Language card laid out") { findTag("general_language_card")?.bounds?.width?.let { it > 0f } == true }
            open(tapHoldMs, settleMs)
            assertFirstOpenPresentationHandoff()
            tap(tagCenter("general_language#en"), tapHoldMs, "select-en")
            waitFor("English selection is accepted") { selected == "en" }
            waitFor("English popup exit completes") { !menuPresent() && dismissals.lastOrNull()?.optString("code") == "en" }
            SystemClock.sleep(settleMs)
            assertEquals("Initial selection callback", listOf("en"), selections.toList())
            assertSelectionPrecedesDismissal("en")

            open(tapHoldMs, settleMs)
            val callbacksBeforeOutside = selections.size
            val dismissalsBeforeOutside = dismissals.size
            tap(outsidePoint(), tapHoldMs, "outside-dismiss")
            waitFor("Outside click removes popup") { !menuPresent() && dismissals.size == dismissalsBeforeOutside + 1 }
            SystemClock.sleep(settleMs)
            assertEquals("Outside dismissal must not select", callbacksBeforeOutside, selections.size)
            assertEquals("Outside dismissal preserves English", "en", selected)
            assertTrue("Outside dismissal reports no selection", dismissals.last().isNull("code"))

            open(tapHoldMs, settleMs)
            val callbacksBeforeSame = selections.size
            val dismissalsBeforeSame = dismissals.size
            tap(tagCenter("general_language#en"), tapHoldMs, "select-same-en")
            waitFor("Same item removes popup") { !menuPresent() && dismissals.size == dismissalsBeforeSame + 1 }
            SystemClock.sleep(settleMs)
            assertEquals("Same item is accepted once", callbacksBeforeSame + 1, selections.size)
            assertEquals("Same item preserves English", "en", selected)
            assertSelectionPrecedesDismissal("en")

            val callbacksBeforeHold = selections.size
            val dismissalsBeforeHold = dismissals.size
            val heldAnchor = longPressOpen(longPressHoldMs, settleMs, "hold-anchor")
            inject(MotionEvent.ACTION_UP, heldAnchor, SystemClock.uptimeMillis(), "hold-anchor-up")
            SystemClock.sleep(settleMs)
            assertTrue("Stationary long press release keeps menu open", readOnMain { menuPresent() })
            assertEquals("Stationary hold does not select a row beneath the original point", callbacksBeforeHold, selections.size)
            assertEquals("Stationary hold does not dismiss", dismissalsBeforeHold, dismissals.size)
            tap(outsidePoint(), tapHoldMs, "hold-cleanup-outside")
            waitFor("Hold cleanup removes menu") { !menuPresent() && dismissals.size == dismissalsBeforeHold + 1 }
            SystemClock.sleep(settleMs)

            val callbacksBeforeSlide = selections.size
            val dismissalsBeforeSlide = dismissals.size
            val slideAnchor = longPressOpen(longPressHoldMs, settleMs, "slide-ja")
            val japanese = tagCenter("general_language#ja")
            val slideStart = SystemClock.uptimeMillis()
            repeat(12) { index ->
                val fraction = (index + 1) / 12f
                inject(MotionEvent.ACTION_MOVE, slideAnchor + (japanese - slideAnchor) * fraction,
                    slideStart + (index + 1) * 16L, "slide-ja-move")
            }
            inject(MotionEvent.ACTION_UP, japanese, slideStart + 13 * 16L, "slide-ja-up")
            waitFor("Japanese slide selection is accepted") { selected == "ja" }
            waitFor("Japanese slide exit completes") { !menuPresent() && dismissals.size == dismissalsBeforeSlide + 1 }
            SystemClock.sleep(settleMs)
            assertEquals("Long-press slide accepts exactly once", callbacksBeforeSlide + 1, selections.size)
            assertEquals("Long-press slide selects Japanese", "ja", selections.last())
            assertSelectionPrecedesDismissal("ja")

            open(tapHoldMs, settleMs)
            val callbacksBeforeCancel = selections.size
            val inside = tagCenter("general_language#ja")
            val outside = outsidePoint()
            val beganAt = SystemClock.uptimeMillis()
            inject(MotionEvent.ACTION_DOWN, inside, beganAt, "slide-cancel-down")
            repeat(8) { index ->
                sleepUntil(beganAt + (index + 1) * 16L)
                val fraction = (index + 1) / 8f
                inject(MotionEvent.ACTION_MOVE, inside + (outside - inside) * fraction,
                    beganAt + (index + 1) * 16L, "slide-cancel-move")
            }
            inject(MotionEvent.ACTION_CANCEL, outside, SystemClock.uptimeMillis(), "slide-cancel-cancel")
            SystemClock.sleep(settleMs)
            assertEquals("Cancelled pointer must not select", callbacksBeforeCancel, selections.size)
            if (readOnMain { menuPresent() }) {
                tap(outsidePoint(), tapHoldMs, "cleanup-outside-dismiss")
                waitFor("Cleanup removes menu") { !menuPresent() }
            }
            SystemClock.sleep(settleMs)
        } finally {
            try {
                disposeFixture()
            } finally {
                LanguageMenuPresentationDiagnostics.observer = priorObserver
            }
        }
    }

    /** Research-only C/U/E sampling; all measurements are written before assertions. */
    @Test fun closedUnpaintedAndExpandedGpuTriplet() {
        val arguments = InstrumentationRegistry.getArguments()
        assertEquals("Explicit research opt-in is required", "true", arguments.getString("languageGpuTripletCheck"))
        val runId = (arguments.getString("languageRunId") ?: "triplet-${System.currentTimeMillis()}")
            .replace(Regex("[^A-Za-z0-9_-]"), "_")
        val parent = File(instrumentation.targetContext.getExternalFilesDir(null), "language-gpu-triplet")
        assertTrue("Create research capture parent", parent.isDirectory || parent.mkdirs())
        val directory = File(parent, runId)
        assertTrue("Use a new run directory so captures cannot mix", directory.mkdir())
        val report = JSONObject().put("schema", 1).put("research_only", true)
            .put("status", "SAMPLING_NOT_COMPLETE").put("junit_passed", false)
            .put("source_sha256", "94b488726ac48e666160f786c5881c53b960fc948016a74a7235a923be2f9639")
            .put("capture", "Original real-time fixture and UiAutomation composited display; no Compose clock advance")
            .put("background", "Unchanged neutral (.94,.94,.96) and 20dp grid, black alpha .13, width .5dp")
            .put("roi", "Original right-48dp..right-30dp and centerY plus/minus 8dp; rounded pixel edges")
            .put("late_delay_ms", 350).put("original_minimum_mean_abs_delta_8bit", 6.0)
            .put("original_maximum_mean_rgb_distance_from_first_row_8bit", 5.0)
            .put("device", JSONObject().put("fingerprint", android.os.Build.FINGERPRINT)
                .put("sdk", android.os.Build.VERSION.SDK_INT).put("model", android.os.Build.MODEL))
            .put("captures", JSONArray()).put("geometry", JSONObject()).put("comparisons", JSONObject())
            .put("limits", JSONArray(listOf(
                "A frame-commit callback proves HWUI submission, not compositor presentation; original 80ms delay is retained.",
                "stable names the first settled request; stable/late pixels must be examined before claiming temporal stability.",
                "E-U >=6 is a candidate predicate, not a validated material oracle or native optical acceptance.",
                "A no-material/one-row-material fault has not been injected by this fixture."
            )))
        cardWidthDp = 362f
        cardTopDp = 180f
        try {
            installRealtimeFixture()
            waitFor("Language card laid out") { findTag("general_language_card")?.bounds?.width?.let { it > 0f } == true }
            SystemClock.sleep(400)
            val closedBounds = readOnMain { requireNotNull(findTag("general_language_card")).bounds }
            val closedValueBounds = readOnMain { findTag("general_language_value")?.bounds }
            report.getJSONObject("geometry").put("C_before", tripletGeometry())
            val c = captureTripletStage("C", directory, report)
            report.getJSONObject("geometry").put("C_after", tripletGeometry())

            // Draw-phase state only. The wrapper, child composition, size and semantics stay attached.
            val beforeSuppressionDraw = sourceDrawSequence.get()
            instrumentation.runOnMainSync {
                check(!menuPresent()) { "U must be acquired while the menu is closed" }
                suppressClosedSourceDrawing = true
            }
            val u = captureTripletStage("U", directory, report)
            val unpaintedBounds = readOnMain { requireNotNull(findTag("general_language_card")).bounds }
            val unpaintedValueBounds = readOnMain { findTag("general_language_value")?.bounds }
            val suppressionObserved = sourceDrawSequence.get() > beforeSuppressionDraw && lastSourceDrawSuppressed == true
            report.getJSONObject("geometry").put("U_after", tripletGeometry())

            // Restore the real source and submit it before the original public pointer opens the menu.
            val beforeRestoreDraw = sourceDrawSequence.get()
            instrumentation.runOnMainSync {
                check(!menuPresent()) { "Source restoration must precede natural opening" }
                suppressClosedSourceDrawing = false
            }
            val restored = captureTripletStage("C_restored", directory, report)
            val restoredBounds = readOnMain { requireNotNull(findTag("general_language_card")).bounds }
            val restoreObserved = sourceDrawSequence.get() > beforeRestoreDraw && lastSourceDrawSuppressed == false
            report.getJSONObject("geometry").put("C_restored_after", tripletGeometry())

            open(67L, 850L)
            waitFor("All five rows finish natural expansion") {
                val state = findTag("general_language_menu")?.node?.config?.getOrNull(LanguageMenuVisualStateKey)
                state != null && state.alpha >= .999f && abs(state.scaleX - 1f) <= .001f &&
                    abs(state.scaleY - 1f) <= .001f && languages.all { (code, _) ->
                        findTag("general_language#$code")?.bounds?.height?.let { it >= 35f * density } == true
                    }
            }
            val stableRows = tripletRows()
            report.getJSONObject("geometry").put("E_before", tripletGeometry())
            val e = captureTripletStage("E", directory, report)
            val lateRows = tripletRows()
            report.getJSONObject("geometry").put("E_after", tripletGeometry())
            val menuHandoff = readOnMain {
                findTag("general_language_menu")?.node?.config?.getOrNull(LanguageMenuHandoffStateKey)
            }
            val controlValidity = JSONObject()
                .put("suppression_draw_observed", suppressionObserved).put("restored_draw_observed", restoreObserved)
                .put("source_bounds_exactly_retained", closedBounds == unpaintedBounds && closedBounds == restoredBounds)
                .put("value_bounds_exactly_retained", closedValueBounds == unpaintedValueBounds)
                .put("row_bounds_exactly_retained_stable_to_late", stableRows == lateRows)
                .put("expanded_source_alpha", menuHandoff?.sourceCardAlpha ?: JSONObject.NULL)
                .put("expanded_handoff_phase", menuHandoff?.phase ?: JSONObject.NULL)
                .put("fixture_suppression_disabled_for_natural_open", !suppressClosedSourceDrawing)
                .put("captured_without_active_pointer", !activePointer)
            report.put("control_validity", controlValidity).put("density", density)
                .put("source_screen_bounds_px", tripletRect(closedBounds))
                .put("source_value_screen_bounds_px", closedValueBounds?.let(::tripletRect) ?: JSONObject.NULL)
            val rowGeometry = JSONArray()
            stableRows.forEach { (code, bounds) ->
                val roi = tripletRoi(bounds)
                rowGeometry.put(JSONObject().put("code", code).put("stable_screen_bounds_px", tripletRect(bounds))
                    .put("late_screen_bounds_px", tripletRect(requireNotNull(lateRows.firstOrNull { it.first == code }).second))
                    .put("roi_screen_bounds_px", tripletRect(roi)).put("roi_pixel_edges", tripletPixelEdges(roi))
                    .put("roi_fraction_inside_source_rect", tripletOverlapFraction(roi, closedBounds))
                    .put("roi_fraction_inside_value_rect", closedValueBounds?.let { tripletOverlapFraction(roi, it) } ?: JSONObject.NULL))
            }
            report.put("rows", rowGeometry)
            val comparisons = report.getJSONObject("comparisons")
            // The original gpuRowProbe is used unchanged for every pair, including all five rows.
            fun compare(name: String, prior: File, actual: File, materialPredicate: Boolean = false) {
                comparisons.put(name, measureTripletPair(prior, actual, stableRows, materialPredicate))
            }
            compare("E_stable_from_C_stable", c.stable, e.stable, true)
            compare("E_stable_from_U_stable", u.stable, e.stable, true)
            compare("E_late_from_C_late", c.late, e.late, true)
            compare("E_late_from_U_late", u.late, e.late, true)
            compare("C_stable_from_U_stable", u.stable, c.stable)
            compare("C_restored_stable_from_C_stable", c.stable, restored.stable)
            compare("temporal_C", c.stable, c.late)
            compare("temporal_U", u.stable, u.late)
            compare("temporal_C_restored", restored.stable, restored.late)
            compare("temporal_E", e.stable, e.late)
            val sourceRemovalRows = comparisons.getJSONObject("C_stable_from_U_stable").getJSONArray("rows")
            val unoccludedIndices = stableRows.indices.filter { tripletOverlapFraction(tripletRoi(stableRows[it].second), closedBounds) == 0.0 }
            val rawGridUnchanged = unoccludedIndices.isNotEmpty() && unoccludedIndices.all {
                sourceRemovalRows.getJSONObject(it).getDouble("mean_abs_delta_8bit") == 0.0
            }
            val restoredPixelsEqual = comparisons.getJSONObject("C_restored_stable_from_C_stable").getBoolean("all_roi_pixels_equal")
            val temporalControls = JSONObject()
            val temporalNames = listOf("temporal_C", "temporal_U", "temporal_C_restored", "temporal_E")
            temporalNames.forEach { name -> temporalControls.put(name, comparisons.getJSONObject(name).getBoolean("all_roi_pixels_equal")) }
            val temporalPixelsEqual = temporalNames.all { temporalControls.getBoolean(it) }
            report.put("pixel_controls", JSONObject()
                .put("equality_scope", "Only the five sampled row ROIs, with no new numeric tolerance")
                .put("unoccluded_source_removal_row_codes", JSONArray(unoccludedIndices.map { stableRows[it].first }))
                .put("C_U_raw_grid_pixels_equal_in_unoccluded_row_rois", rawGridUnchanged)
                .put("C_restored_C_all_row_roi_pixels_equal", restoredPixelsEqual)
                .put("stable_late_all_row_roi_pixels_equal", temporalControls)
                .put("all_temporal_controls_exactly_equal", temporalPixelsEqual))
            report.put("status", "ALL_FIVE_ROWS_MEASURED_NOT_AN_OPTICAL_ACCEPTANCE")
            writeTripletReport(directory, report)

            // Evidence is complete before any coverage assertion, including the original failing C predicate.
            assertTrue("U actually suppressed source drawing and source drawing was restored", suppressionObserved && restoreObserved)
            assertEquals("U retains source layout", closedBounds, unpaintedBounds)
            assertEquals("Restoring C retains source layout", closedBounds, restoredBounds)
            assertEquals("U retains value layout", closedValueBounds, unpaintedValueBounds)
            assertEquals("Settled row geometry stays unchanged in late capture", stableRows, lateRows)
            assertTrue("C/U raw background stays identical in row ROIs outside the source card", rawGridUnchanged)
            assertTrue("Restored C reproduces C in every sampled row ROI", restoredPixelsEqual)
            assertTrue("Each settled/late pair has identical pixels in every sampled row ROI", temporalPixelsEqual)
            assertTrue("GPU screenshot taken without an active pointer", !activePointer)
            assertTrue("Natural open reaches source-hidden motion phase", menuHandoff != null && menuHandoff.phase == "motion" && menuHandoff.sourceCardAlpha == 0f)
            assertEquals("Opening for pixel verification must not select a language", emptyList<String>(), selections.toList())
            assertTripletOriginalPredicates(comparisons.getJSONObject("E_stable_from_C_stable"), "Original C baseline")
            assertTripletOriginalPredicates(comparisons.getJSONObject("E_stable_from_U_stable"), "Candidate source-unpainted U baseline")
            report.put("junit_passed", true)
        } catch (failure: Throwable) {
            report.put("failure", JSONObject().put("type", failure.javaClass.name).put("message", failure.message ?: JSONObject.NULL))
            throw failure
        } finally {
            try { disposeFixture() } finally { writeTripletReport(directory, report) }
        }
    }

    private data class TripletCapturePair(val stable: File, val late: File)

    private fun captureTripletStage(stage: String, directory: File, report: JSONObject): TripletCapturePair {
        val stable = writeTripletCapture("${stage}_stable", directory, report)
        SystemClock.sleep(350)
        val late = writeTripletCapture("${stage}_late", directory, report)
        return TripletCapturePair(stable, late)
    }

    private fun writeTripletCapture(name: String, directory: File, report: JSONObject): File {
        val before = SystemClock.uptimeMillis()
        val bitmap = captureSettledGpu(name)
        val file = File(directory, "$name.png")
        try {
            file.outputStream().use { assertTrue("Encode GPU capture $name", bitmap.compress(Bitmap.CompressFormat.PNG, 100, it)) }
            val decoded = requireNotNull(android.graphics.BitmapFactory.decodeFile(file.absolutePath))
            val roundtripEqual = try { bitmap.sameAs(decoded) } finally { decoded.recycle() }
            report.getJSONArray("captures").put(JSONObject().put("name", name).put("file", file.name)
                .put("capture_begin_uptime_ms", before).put("capture_end_uptime_ms", SystemClock.uptimeMillis())
                .put("width_px", bitmap.width).put("height_px", bitmap.height).put("bitmap_config", bitmap.config?.name ?: JSONObject.NULL)
                .put("bitmap_color_space", bitmap.colorSpace?.name ?: JSONObject.NULL)
                .put("png_roundtrip_same_pixels", roundtripEqual)
                .put("active_pointer", activePointer).put("requested_source_suppression", suppressClosedSourceDrawing)
                .put("last_draw_source_suppression", lastSourceDrawSuppressed ?: JSONObject.NULL)
                .put("source_draw_sequence", sourceDrawSequence.get()))
            writeTripletReport(directory, report)
            assertTrue("PNG roundtrip retains the original GPU bitmap pixels: $name", roundtripEqual)
            return file
        } finally { bitmap.recycle() }
    }

    private fun measureTripletPair(priorFile: File, actualFile: File, rows: List<Pair<String, Rect>>, materialPredicate: Boolean): JSONObject {
        val prior = requireNotNull(android.graphics.BitmapFactory.decodeFile(priorFile.absolutePath))
        try {
            val actual = requireNotNull(android.graphics.BitmapFactory.decodeFile(actualFile.absolutePath))
            try {
                assertEquals("GPU baseline width", prior.width, actual.width)
                assertEquals("GPU baseline height", prior.height, actual.height)
                val probes = rows.map { (code, bounds) -> gpuRowProbe(code, tripletRoi(bounds), prior, actual) }
                val firstRgb = probes.first().meanRgb
                val records = JSONArray()
                var allPass = true
                var allEqual = true
                probes.forEachIndexed { index, probe ->
                    val bounds = rows[index].second
                    val before = gpuRowProbe(probe.code, tripletRoi(bounds), prior, prior)
                    val distance = probe.meanRgb.indices.sumOf { abs(probe.meanRgb[it] - firstRgb[it]) } / 3.0
                    val record = JSONObject().put("code", probe.code).put("prior_mean_rgb_8bit", JSONArray(before.meanRgb.toList()))
                        .put("actual_mean_rgb_8bit", JSONArray(probe.meanRgb.toList())).put("mean_abs_delta_8bit", probe.meanAbsDelta)
                        .put("actual_mean_rgb_distance_from_first_row_8bit", distance)
                        .put("roi_pixel_edges", tripletPixelEdges(tripletRoi(bounds)))
                    if (materialPredicate) {
                        record.put("original_delta_at_least_6_pass", probe.meanAbsDelta >= 6.0)
                            .put("original_row_distance_at_most_5_pass", distance <= 5.0)
                        allPass = allPass && probe.meanAbsDelta >= 6.0 && distance <= 5.0
                    }
                    allEqual = allEqual && probe.meanAbsDelta == 0.0
                    records.put(record)
                }
                return JSONObject().put("prior", priorFile.name).put("actual", actualFile.name).put("rows", records)
                    .put("all_roi_pixels_equal", allEqual).put("evaluates_original_material_predicates", materialPredicate)
                    .also { if (materialPredicate) it.put("all_rows_pass_original_predicates", allPass) }
            } finally { actual.recycle() }
        } finally { prior.recycle() }
    }

    private fun assertTripletOriginalPredicates(comparison: JSONObject, label: String) {
        val rows = comparison.getJSONArray("rows")
        for (index in 0 until rows.length()) {
            val row = rows.getJSONObject(index)
            assertTrue("$label ${row.getString("code")}: mean absolute delta=${row.getDouble("mean_abs_delta_8bit")}",
                row.getDouble("mean_abs_delta_8bit") >= 6.0)
            assertTrue("$label ${row.getString("code")}: RGB distance=${row.getDouble("actual_mean_rgb_distance_from_first_row_8bit")}",
                row.getDouble("actual_mean_rgb_distance_from_first_row_8bit") <= 5.0)
        }
    }

    private fun tripletRows(): List<Pair<String, Rect>> = readOnMain {
        languages.map { (code, _) -> code to requireNotNull(findTag("general_language#$code")).bounds }
    }

    private fun tripletGeometry(): JSONObject = readOnMain {
        val snapshot = JSONObject().put("uptime_ms", SystemClock.uptimeMillis()).put("menu_present", menuPresent())
        val tags = listOf("general_language_card", "general_language_value", "general_language_menu") + languages.map { "general_language#${it.first}" }
        tags.forEach { tag -> snapshot.put(tag, findTag(tag)?.bounds?.let(::tripletRect) ?: JSONObject.NULL) }
        val state = findTag("general_language_menu")?.node?.config?.getOrNull(LanguageMenuVisualStateKey)
        snapshot.put("visual_state", state?.let { JSONObject().put("alpha", it.alpha).put("scale_x", it.scaleX).put("scale_y", it.scaleY) } ?: JSONObject.NULL)
        snapshot
    }

    private fun tripletRoi(bounds: Rect) = Rect(bounds.right - 48f * density, bounds.center.y - 8f * density,
        bounds.right - 30f * density, bounds.center.y + 8f * density)

    private fun tripletPixelEdges(rect: Rect) = JSONArray(listOf(rect.left.roundToInt(), rect.top.roundToInt(), rect.right.roundToInt(), rect.bottom.roundToInt()))

    private fun tripletRect(rect: Rect) = JSONObject().put("left", rect.left).put("top", rect.top).put("right", rect.right).put("bottom", rect.bottom)

    private fun tripletOverlapFraction(roi: Rect, other: Rect): Double {
        val width = (minOf(roi.right, other.right) - maxOf(roi.left, other.left)).coerceAtLeast(0f)
        val height = (minOf(roi.bottom, other.bottom) - maxOf(roi.top, other.top)).coerceAtLeast(0f)
        return (width * height / (roi.width * roi.height)).toDouble()
    }

    private fun writeTripletReport(directory: File, report: JSONObject) {
        File(directory, "gpu-triplet.json").writeText(report.toString(2))
    }

    private data class CornerProbe(val name: String, val corner: Boolean, val delta: Double)
    private data class HeldRowProbes(val mode: String, val probes: List<CornerProbe>)

    /** A held row must leave all four outside corners untouched for both pointer origins. */
    fun heldLanguageRowKeepsItsFourCornersOutsideTheHighlight() {
        cardWidthDp = 362f
        cardTopDp = 180f
        val results = mutableListOf<HeldRowProbes>()
        installRealtimeFixture()
        try {
            waitFor("Language card laid out") { findTag("general_language_card") != null }
            for (mode in listOf("direct-row", "anchor-drag")) {
                val anchor = if (mode == "anchor-drag") longPressOpen(450L, 850L, mode) else {
                    open(67L, 850L)
                    null
                }
                val before = captureSettledGpu("$mode-before", heldSnapshot = anchor != null)
                try {
                    val bounds = readOnMain { requireNotNull(findTag("general_language#en")).bounds }
                    if (anchor == null) {
                        inject(MotionEvent.ACTION_DOWN, bounds.center, SystemClock.uptimeMillis(), "$mode-down")
                    } else {
                        val beganAt = SystemClock.uptimeMillis()
                        repeat(12) { index ->
                            inject(MotionEvent.ACTION_MOVE, anchor + (bounds.center - anchor) * ((index + 1) / 12f),
                                beganAt + (index + 1) * 16L, "$mode-move")
                        }
                    }
                    SystemClock.sleep(700)
                    val held = captureSettledGpu("$mode-held", heldSnapshot = true)
                    try {
                        val probes = mutableListOf<CornerProbe>()
                        fun probe(name: String, x: Float, y: Float, corner: Boolean) {
                            val px = x.roundToInt(); val py = y.roundToInt()
                            var total = 0.0
                            for (dy in -1..1) for (dx in -1..1) {
                                val prior = before.getPixel(px + dx, py + dy)
                                val actual = held.getPixel(px + dx, py + dy)
                                for (shift in listOf(16, 8, 0))
                                    total += abs(((actual ushr shift) and 255) - ((prior ushr shift) and 255))
                            }
                            probes += CornerProbe(name, corner, total / 27.0)
                        }
                        val insetX = 4f * density
                        val insetY = 3f * density
                        probe("top-left", bounds.left + insetX, bounds.top + insetY, true)
                        probe("top-right", bounds.right - insetX, bounds.top + insetY, true)
                        probe("bottom-left", bounds.left + insetX, bounds.bottom - insetY, true)
                        probe("bottom-right", bounds.right - insetX, bounds.bottom - insetY, true)
                        probe("left-interior", bounds.left + insetX, bounds.center.y, false)
                        probe("right-interior", bounds.right - insetX, bounds.center.y, false)
                        results += HeldRowProbes(mode, probes)
                    } finally { held.recycle() }
                } finally {
                    before.recycle()
                    if (activePointer) inject(MotionEvent.ACTION_CANCEL, lastPointer, SystemClock.uptimeMillis(), "$mode-cancel")
                }
                SystemClock.sleep(250)
                assertEquals("Cancelled held row must not select", emptyList<String>(), selections.toList())
                assertTrue("Cancelled held row leaves menu available", readOnMain { menuPresent() })
                tap(outsidePoint(), 67L, "$mode-dismiss")
                waitFor("Held regression cleanup removes menu") { !menuPresent() }
            }
            results.forEach { result ->
                result.probes.forEach { probe ->
                    if (probe.corner) assertTrue("${result.mode}: ${probe.name} must remain outside highlight, delta=${probe.delta}", probe.delta <= 1.5)
                    else assertTrue("${result.mode}: ${probe.name} must contain a visible highlight, delta=${probe.delta}", probe.delta >= 5.0)
                }
            }
        } finally {
            disposeFixture()
        }
    }

    private fun disposeFixture() {
        if (activePointer) runCatching {
            inject(MotionEvent.ACTION_CANCEL, lastPointer, SystemClock.uptimeMillis(), "cleanup-cancel")
        }
        instrumentation.runOnMainSync {
            realView?.disposeComposition()
            realRecomposer?.cancel()
        }
    }

    /** The rule only bootstraps an Activity; product animation owns a real-time recomposer. */
    private fun installRealtimeFixture() {
        compose.setContent {
            val view = LocalView.current
            SideEffect {
                var context = view.context
                while (context !is Activity && context is ContextWrapper) context = context.baseContext
                activity = context as Activity
            }
        }
        compose.waitForIdle()
        val ready = CountDownLatch(1)
        instrumentation.runOnMainSync {
            val observer = FrameLayout(activity)
            realView = ComposeView(activity).also { view ->
                val parent = view.createLifecycleAwareWindowRecomposer(lifecycle = (activity as LifecycleOwner).lifecycle)
                realRecomposer = parent
                view.setParentCompositionContext(parent)
                view.setContent { Fixture(); SideEffect { ready.countDown() } }
                observer.addView(view, FrameLayout.LayoutParams(-1, -1))
                activity.setContentView(observer)
            }
        }
        assertTrue("Real-time composition initializes", ready.await(5, TimeUnit.SECONDS))
    }

    private fun captureSettledGpu(name: String, heldSnapshot: Boolean = false): Bitmap {
        assertTrue("Only the separate held GPU diagnostic may capture an active pointer", !activePointer || heldSnapshot)
        assertEquals("Held snapshot must have a real active pointer", heldSnapshot, activePointer)
        val roots = readOnMain {
            WindowInspector.getGlobalWindowViews().filter { it.isAttachedToWindow && it.isHardwareAccelerated && it.width > 0 && it.height > 0 }
        }
        assertTrue("Actual hardware-accelerated windows are present", roots.isNotEmpty())
        val committed = CountDownLatch(roots.size)
        instrumentation.runOnMainSync {
            roots.forEach { root ->
                root.viewTreeObserver.registerFrameCommitCallback { committed.countDown() }
                root.postInvalidateOnAnimation()
            }
        }
        assertTrue("HWUI commits all fixture windows before $name", committed.await(5, TimeUnit.SECONDS))
        // Submission precedes compositor presentation. This is a settled GPU diagnostic,
        // and its optional held snapshots are never used as motion-timing evidence.
        SystemClock.sleep(80)
        val bitmap = requireNotNull(instrumentation.uiAutomation.takeScreenshot()) { "Composited display unavailable" }
        assertEquals("Pointer state stays unchanged throughout the static GPU snapshot", heldSnapshot, activePointer)
        return bitmap
    }

    private data class GpuRowProbe(val code: String, val meanRgb: DoubleArray, val meanAbsDelta: Double)

    private fun gpuRowProbe(code: String, roi: Rect, baseline: Bitmap, expanded: Bitmap): GpuRowProbe {
        val left = roi.left.roundToInt()
        val top = roi.top.roundToInt()
        val right = roi.right.roundToInt()
        val bottom = roi.bottom.roundToInt()
        require(left >= 0 && top >= 0 && right <= expanded.width && bottom <= expanded.height && right > left && bottom > top) {
            "$code: foreground-free row probe must remain inside the composited display: $roi"
        }
        val mean = DoubleArray(3)
        var delta = 0.0
        val count = (right - left) * (bottom - top)
        for (y in top until bottom) for (x in left until right) {
            val pixel = expanded.getPixel(x, y)
            val prior = baseline.getPixel(x, y)
            for (channel in 0..2) {
                val shift = 16 - channel * 8
                val value = (pixel ushr shift) and 255
                mean[channel] += value
                delta += abs(value - ((prior ushr shift) and 255))
            }
        }
        for (channel in 0..2) mean[channel] /= count
        return GpuRowProbe(code, mean, delta / (count * 3.0))
    }

    @Composable private fun Fixture() {
        val currentDensity = LocalDensity.current.density
        SideEffect { density = currentDensity }
        val tint = Color(0f, .65f, .75f)
        MaterialTheme(colorScheme = lightColorScheme(primary = tint, background = neutral, surface = neutral,
            surfaceContainer = neutral, onSurface = Color(0xFF123239))) {
            CompositionLocalProvider(LocalUiStyle provides UiStyle.LiquidGlass, LocalDarkTheme provides false) {
                GlassHost(Modifier.fillMaxSize(), background = neutral) {
                    GlassBackground(0f, Modifier.fillMaxSize()) {
                        Box(Modifier.fillMaxSize().background(neutral).drawBehind {
                            val step = 20.dp.toPx()
                            for (x in 0..ceil(size.width / step).toInt()) drawLine(Color.Black.copy(alpha = .13f),
                                Offset(x * step, 0f), Offset(x * step, size.height), .5.dp.toPx())
                            for (y in 0..ceil(size.height / step).toInt()) drawLine(Color.Black.copy(alpha = .13f),
                                Offset(0f, y * step), Offset(size.width, y * step), .5.dp.toPx())
                        })
                    }
                    BoxWithConstraints(Modifier.fillMaxSize()) {
                        val requestedWidth = cardWidthDp?.dp ?: minOf(420.dp, (maxWidth - 40.dp).coerceAtLeast(1.dp))
                        // Keep the fixed product-menu fixture used by the behavior regression.
                        Box(Modifier.align(Alignment.TopCenter).offset(y = (cardTopDp ?: 146f).dp)
                            .width(requestedWidth.coerceAtMost(maxWidth))
                            .drawWithContent {
                                val suppressed = suppressClosedSourceDrawing
                                lastSourceDrawSuppressed = suppressed
                                sourceDrawSequence.incrementAndGet()
                                if (!suppressed) drawContent()
                            }) {
                            GlassLanguageMenu("Language", selected, languages, onSelect = { code ->
                                add("selection_callback").put("code", code)
                                    .put("popup_present_at_callback", menuPresent())
                                selections.add(code)
                                selected = code
                            }, onDismissed = { code ->
                                dismissals.add(add("dismissal_callback").put("code", code ?: JSONObject.NULL)
                                    .put("popup_present_at_callback", menuPresent()))
                            })
                        }
                    }
                }
            }
        }
    }

    private data class TaggedNode(val tag: String, val bounds: Rect, val node: SemanticsNode)

    /** Read public test semantics directly, without Compose rule idling or clock advancement. */
    private fun nodes(): List<TaggedNode> {
        val found = ArrayList<TaggedNode>()
        fun visitNode(node: SemanticsNode, screenOffset: Offset) {
            val tag = node.config.getOrNull(SemanticsProperties.TestTag)
            if (tag?.startsWith("general_language") == true) {
                found += TaggedNode(tag, node.boundsInWindow.translate(screenOffset), node)
            }
            node.children.forEach { visitNode(it, screenOffset) }
        }
        fun visitView(view: View) {
            if (view is ViewRootForTest) {
                val screen = IntArray(2)
                val window = IntArray(2)
                view.getLocationOnScreen(screen)
                view.getLocationInWindow(window)
                visitNode(view.semanticsOwner.unmergedRootSemanticsNode,
                    Offset((screen[0] - window[0]).toFloat(), (screen[1] - window[1]).toFloat()))
            } else if (view is ViewGroup) repeat(view.childCount) { visitView(view.getChildAt(it)) }
        }
        WindowInspector.getGlobalWindowViews().filter { it.isAttachedToWindow }.forEach(::visitView)
        return found
    }

    private fun findTag(tag: String): TaggedNode? = nodes().firstOrNull { it.tag == tag }
    private fun menuPresent() = findTag("general_language_menu") != null
    private fun tagCenter(tag: String): Offset = readOnMain {
        requireNotNull(findTag(tag)) { "Missing $tag" }.bounds.center
    }

    private fun outsidePoint(): Offset = readOnMain {
        val menu = requireNotNull(findTag("general_language_menu")).bounds
        val root = WindowInspector.getGlobalWindowViews()
            .last { it.isAttachedToWindow && it.javaClass.simpleName == "PopupLayout" }
        val location = IntArray(2)
        root.getLocationOnScreen(location)
        val inset = 8f * density
        val middleY = menu.center.y.coerceIn(location[1] + inset, location[1] + root.height - inset)
        listOf(Offset(location[0] + inset, middleY),
            Offset(location[0] + root.width - inset, middleY),
            Offset(location[0] + root.width / 2f, location[1] + inset),
            Offset(location[0] + root.width / 2f, location[1] + root.height - inset))
            .first { !menu.contains(it) }
    }

    private fun inject(action: Int, point: Offset, plannedUptimeMs: Long, label: String) {
        sleepUntil(plannedUptimeMs)
        val before = SystemClock.uptimeMillis()
        if (action == MotionEvent.ACTION_DOWN) activeDownTime = before
        val event = MotionEvent.obtain(activeDownTime, before, action, point.x, point.y, 0)
            .apply { source = InputDevice.SOURCE_TOUCHSCREEN }
        val accepted = try { instrumentation.uiAutomation.injectInputEvent(event, true) } finally { event.recycle() }
        activePointer = action != MotionEvent.ACTION_UP && action != MotionEvent.ACTION_CANCEL
        lastPointer = point
        assertTrue("Public input accepted: $label", accepted)
    }

    private fun tap(point: Offset, holdMs: Long, label: String) {
        val start = SystemClock.uptimeMillis()
        inject(MotionEvent.ACTION_DOWN, point, start, "$label-down")
        inject(MotionEvent.ACTION_UP, point, start + holdMs, "$label-up")
    }

    private fun open(holdMs: Long, settleMs: Long) {
        tap(tagCenter("general_language_card"), holdMs, "open")
        waitFor("Five-language menu appears") { findTag("general_language#es") != null }
        SystemClock.sleep(settleMs)
    }

    /** Keep the same physical pointer down across the real product menu's opening. */
    private fun longPressOpen(holdMs: Long, settleMs: Long, label: String): Offset {
        val anchor = tagCenter("general_language_card")
        val beganAt = SystemClock.uptimeMillis()
        inject(MotionEvent.ACTION_DOWN, anchor, beganAt, "$label-down")
        sleepUntil(beganAt + holdMs)
        waitFor("Held press opens all five language rows") { findTag("general_language#es") != null }
        SystemClock.sleep(settleMs)
        return anchor
    }

    private fun assertSelectionPrecedesDismissal(code: String) {
        val accepted = events.last { it.optString("event") == "selection_callback" && it.optString("code") == code }
        val dismissed = dismissals.last()
        assertTrue("Selection callback still has popup content", accepted.getBoolean("popup_present_at_callback"))
        assertEquals("Dismissal reports accepted code", code, dismissed.getString("code"))
        assertTrue("Dismissal follows popup removal", !dismissed.getBoolean("popup_present_at_callback"))
        assertTrue("Selection callback precedes dismissal", accepted.getInt("sequence") < dismissed.getInt("sequence"))
    }

    private fun waitFor(label: String, condition: () -> Boolean) {
        val deadline = SystemClock.uptimeMillis() + 5_000L
        while (!readOnMain(condition)) {
            assertTrue("Timed out: $label", SystemClock.uptimeMillis() < deadline)
            SystemClock.sleep(10)
        }
    }

    private fun <T> readOnMain(block: () -> T): T {
        var result: Result<T>? = null
        instrumentation.runOnMainSync { result = runCatching(block) }
        return requireNotNull(result).getOrThrow()
    }

    private fun sleepUntil(deadline: Long) {
        while (true) {
            val remaining = deadline - SystemClock.uptimeMillis()
            if (remaining <= 0L) return
            SystemClock.sleep(remaining)
        }
    }

    private fun add(event: String): JSONObject = JSONObject().put("event", event)
        .put("sequence", rowSequence.incrementAndGet()).also(events::add)

    private fun assertFirstOpenPresentationHandoff() {
        val rows = events.filter { it.optString("event") == "presentation_event" }
            .sortedBy { it.getInt("sequence") }
        val prepared = rows.first { it.optString("stage") == "prepared" }
        val sessionId = prepared.getInt("session_id")
        val stages = rows.filter { it.getInt("session_id") == sessionId }
        val expected = listOf("prepared", "popup_positioned", "popup_first_content_draw", "popup_frame_committed",
            "handoff_waiting-source-hidden-frame", "source_hidden_first_content_draw", "source_hidden_frame_committed", "handoff_motion")
        val positions = expected.map { stage -> stages.indexOfFirst { it.optString("stage") == stage }.also {
            assertTrue("First natural open records $stage: ${stages.map { row -> row.optString("stage") }}", it >= 0)
        } }
        assertTrue("Popup submission precedes hiding the source and starting motion", positions.zipWithNext().all { (a, b) -> a < b })
        val popup = stages.first { it.optString("stage") == "popup_frame_committed" }
        val source = stages.first { it.optString("stage") == "source_hidden_frame_committed" }
        assertTrue("Popup and source fences belong to separate content windows", popup.getInt("window_identity") != source.getInt("window_identity"))
        assertTrue("Popup fence is registered by the Popup content window", popup.getString("window_class").endsWith("PopupLayout"))
    }
}
