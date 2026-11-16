    /** Public-semantics observation only; this does not expose mathematical motion rest. */
    private data class ObservedTerminalGeometry(
        val menu: Rect,
        val rows: List<Pair<String, Rect>>,
        val visual: List<Float>,
        val targetVisual: List<Float>,
        val targetMenu: Rect,
        val handoffPhase: String?,
        val sourceAlpha: Float?,
        val pointerActive: Boolean,
    ) {
        fun matchesTarget(): Boolean = visual == targetVisual && menu == targetMenu &&
            handoffPhase == "motion" && sourceAlpha == 0f && !pointerActive
    }

    private data class TerminalGeometryRead(
        val uptimeMs: Long,
        val geometry: ObservedTerminalGeometry?,
        val record: JSONObject,
    )

    private fun exactVisualRecord(values: List<Float>): JSONObject {
        val names = listOf("scale_x", "scale_y", "alpha", "content_alpha", "translation_x_dp", "translation_y_dp")
        return JSONObject().also { record ->
            names.forEachIndexed { index, name ->
                record.put(name, values[index]).put("${name}_float_bits", values[index].toRawBits())
            }
        }
    }

    private fun exactRectRecord(rect: Rect): JSONObject = tripletRect(rect).put("float_bits_ltrb",
        JSONArray(listOf(rect.left.toRawBits(), rect.top.toRawBits(), rect.right.toRawBits(), rect.bottom.toRawBits())))

    private fun readObservedTerminalGeometry(closedBounds: Rect): TerminalGeometryRead = readOnMain {
        val at = SystemClock.uptimeMillis()
        // One main-thread traversal per observation, rather than interleaved independent tag reads.
        val snapshot = nodes()
        val menu = snapshot.firstOrNull { it.tag == "general_language_menu" }
        val state = menu?.node?.config?.getOrNull(LanguageMenuVisualStateKey)
        val visual = state?.let { listOf(it.scaleX, it.scaleY, it.alpha, it.contentAlpha, it.translationXDp, it.translationYDp) }
        val handoff = menu?.node?.config?.getOrNull(LanguageMenuHandoffStateKey)
        val rowNodes = languages.map { (code, _) -> code to snapshot.firstOrNull { it.tag == "general_language#$code" } }
        val record = JSONObject().put("uptime_ms", at).put("menu_present", menu != null)
            .put("active_pointer", activePointer).put("handoff_phase", handoff?.phase ?: JSONObject.NULL)
            .put("source_alpha", handoff?.sourceCardAlpha ?: JSONObject.NULL)
        val rowRecords = JSONArray()
        rowNodes.forEach { (code, node) ->
            rowRecords.put(JSONObject().put("code", code).put("bounds", node?.bounds?.let(::exactRectRecord) ?: JSONObject.NULL))
        }
        record.put("rows", rowRecords).put("menu_bounds", menu?.bounds?.let(::exactRectRecord) ?: JSONObject.NULL)
            .put("visual", visual?.let(::exactVisualRecord) ?: JSONObject.NULL)
        if (menu == null || state == null || rowNodes.any { it.second == null }) {
            record.put("target_visual", JSONObject.NULL)
                .put("target_menu_bounds", JSONObject.NULL).put("all_rows_have_original_minimum_height", false)
            TerminalGeometryRead(at, null, record)
        } else {
            val actualVisual = requireNotNull(visual)
            // This fixed, centered 362dp/180dp fixture has room for the final menu.
            // Use the original source anchor, never an adjusted observed Y.
            // If a future layout clamps the menu, exact target matching times out for review.
            val screenOffset = menu.bounds.topLeft - menu.node.boundsInWindow.topLeft
            val targetLeft = closedBounds.center.x - menu.bounds.width / 2f
            val targetTop = closedBounds.top
            val targetMenu = Rect(targetLeft, targetTop, targetLeft + menu.bounds.width, targetTop + menu.bounds.height)
            val targetVisual = listOf(1f, 1f, 1f, 1f,
                (targetLeft - screenOffset.x) / density, (targetTop - screenOffset.y) / density)
            val rows = rowNodes.map { (code, node) -> code to requireNotNull(node).bounds }
            val minimumHeight = rows.all { it.second.height >= 35f * density }
            record.put("target_visual", exactVisualRecord(targetVisual))
                .put("target_menu_bounds", exactRectRecord(targetMenu))
                .put("popup_screen_offset_px", JSONObject().put("x", screenOffset.x).put("y", screenOffset.y))
                .put("all_rows_have_original_minimum_height", minimumHeight)
            TerminalGeometryRead(at, if (minimumHeight) ObservedTerminalGeometry(menu.bounds, rows, actualVisual,
                targetVisual, targetMenu, handoff?.phase, handoff?.sourceCardAlpha, activePointer) else null, record)
        }
    }

    private fun awaitObservedTerminalGeometry(directory: File, report: JSONObject, closedBounds: Rect): List<Pair<String, Rect>> {
        val timeoutMs = 5_000L
        val intervalMs = 50L
        val windowMs = 350L
        val minimumSamples = 4
        val beganAt = SystemClock.uptimeMillis()
        val deadline = beganAt + timeoutMs
        val samples = JSONArray()
        val observation = JSONObject().put("name", "observed-terminal-geometry")
            .put("status", "OBSERVING").put("mathematical_rest_observed", false)
            .put("timeout_ms", timeoutMs).put("poll_interval_ms", intervalMs)
            .put("required_unchanged_window_ms", windowMs).put("minimum_consecutive_samples", minimumSamples)
            .put("began_uptime_ms", beganAt).put("samples", samples)
        report.put("terminal_geometry_observation", observation)
        var previous: ObservedTerminalGeometry? = null
        var consecutiveStart = 0L
        var count = 0
        while (SystemClock.uptimeMillis() <= deadline) {
            val sample = readObservedTerminalGeometry(closedBounds)
            val current = sample.geometry
            val exactTarget = current?.matchesTarget() == true
            val unchanged = exactTarget && current == previous
            if (!exactTarget) {
                count = 0
                consecutiveStart = 0L
            } else if (unchanged) {
                count++
            } else {
                count = 1
                consecutiveStart = sample.uptimeMs
            }
            previous = if (exactTarget) current else null
            val coveredMs = if (count > 0) sample.uptimeMs - consecutiveStart else 0L
            sample.record.put("all_terminal_fields_exact", exactTarget).put("exactly_equals_previous_candidate", unchanged)
                .put("consecutive_samples", count).put("unchanged_window_ms", coveredMs)
            samples.put(sample.record)
            writeTripletReport(directory, report)
            if (sample.uptimeMs <= deadline && exactTarget && count >= minimumSamples && coveredMs >= windowMs) {
                observation.put("status", "OBSERVED_TERMINAL_GEOMETRY_WINDOW_COMPLETE_NOT_MATHEMATICAL_REST")
                    .put("accepted_uptime_ms", sample.uptimeMs).put("consecutive_samples", count)
                    .put("unchanged_window_ms", coveredMs)
                writeTripletReport(directory, report)
                return requireNotNull(current).rows
            }
            val remaining = deadline - SystemClock.uptimeMillis()
            if (remaining <= 0L) break
            SystemClock.sleep(minOf(intervalMs, remaining))
        }
        observation.put("status", "TIMED_OUT_WITHOUT_OBSERVED_TERMINAL_GEOMETRY")
            .put("ended_uptime_ms", SystemClock.uptimeMillis())
        writeTripletReport(directory, report)
        throw AssertionError("Public semantics did not retain exact terminal visual fields and menu/five-row geometry within $timeoutMs ms")
    }
