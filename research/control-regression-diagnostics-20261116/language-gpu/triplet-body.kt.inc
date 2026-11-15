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
