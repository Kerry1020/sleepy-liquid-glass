package com.lingion.sleepy.ui.component.sliderlayerresearch

import android.os.Looper
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Matrix
import androidx.compose.ui.graphics.layer.GraphicsLayer
import androidx.compose.ui.layout.LayoutCoordinates
import androidx.compose.ui.layout.LayoutInfo
import java.lang.reflect.Field
import java.util.Collections
import java.util.IdentityHashMap
import org.json.JSONArray
import org.json.JSONObject
import kotlin.math.abs

/** Read-only, version-specific instrumentation. No layer setter or product hook is used. */
internal class SliderLayerObserver1121 {
    private val coordinatorType = Class.forName("androidx.compose.ui.node.NodeCoordinator")
    private val ownedType = Class.forName("androidx.compose.ui.node.OwnedLayer")
    private val ownerType = Class.forName("androidx.compose.ui.platform.GraphicsLayerOwnerLayer")
    private val layerField = field(coordinatorType, "layer", ownedType)
    private val positionField = field(coordinatorType, "position", java.lang.Long.TYPE)
    private val layoutField = field(coordinatorType, "layoutNode", Class.forName("androidx.compose.ui.node.LayoutNode"))
    private val graphicsField = field(ownerType, "graphicsLayer", GraphicsLayer::class.java)
    private val originField = field(ownerType, "transformOrigin", java.lang.Long.TYPE)
    private val underlying = ownerType.getDeclaredMethod("getUnderlyingMatrix-sQKQjiQ").apply {
        check(returnType == FloatArray::class.java)
        isAccessible = true
    }
    private val rendererId = ownerType.getDeclaredMethod("getLayerId").apply {
        check(returnType == java.lang.Long.TYPE); isAccessible = true
    }
    private val identities = IdentityHashMap<Any, String>()

    private fun id(value: Any): String = identities.getOrPut(value) { "object-${identities.size + 1}" }

    /** Call once on the main thread at a declared Compose-clock sample, with unique tagged nodes. */
    fun observe(targets: LinkedHashMap<String, LayoutInfo>): JSONObject {
        check(Looper.myLooper() == Looper.getMainLooper()) { "Layer observation must be atomic on main" }
        check(targets.keys == linkedSetOf("holder", "owner", "carrier")) { "Missing or reordered target roles" }
        val owners = IdentityHashMap<Any, LayoutCoordinates>()
        val orderedLayers = mutableListOf<Any>()
        val references = IdentityHashMap<Any, MutableList<JSONObject>>()
        val targetRows = JSONArray()
        val layouts = identitySet<LayoutInfo>()
        val layoutRows = JSONArray()

        targets.forEach { (tag, layout) ->
            check(layout.isAttached && layout.isPlaced) { "$tag is detached or unplaced" }
            val chain = mutableListOf<LayoutCoordinates>()
            val seen = identitySet<LayoutCoordinates>()
            var next: LayoutCoordinates? = layout.coordinates
            while (next != null) {
                val current = next
                check(seen.add(current) && chain.size < 256) { "Cyclic or excessive coordinator ancestry" }
                check(coordinatorType.isInstance(current) && current.isAttached) { "Unknown/detached coordinates" }
                chain += current
                layerField.get(current)?.let { layer ->
                    check(layer.javaClass == ownerType) { "Unsupported OwnedLayer: ${layer.javaClass.name}" }
                    val previous = owners[layer]
                    check(previous == null || previous === current) { "One OwnedLayer belongs to multiple coordinators" }
                    if (previous == null) { owners[layer] = current; orderedLayers += layer }
                }
                next = current.parentCoordinates
            }
            val own = chain.filter { layoutField.get(it) === layout }.mapNotNull { layerField.get(it) }
            if (tag != "holder") check(own.isNotEmpty()) { "$tag has no actual own layer" }
            val ancestry = chain.mapNotNull { layerField.get(it) }
            targetRows.put(JSONObject().put("role", tag).put("layout_identity", id(layout))
                .put("coordinates_identity", id(layout.coordinates))
                .put("own_layer_ids", JSONArray(own.map(::id)))
                .put("ancestor_layer_ids_inner_to_outer", JSONArray(ancestry.map(::id)))
                .put("total_alpha_product", ancestry.fold(1.0) { alpha, layer -> alpha * graphics(layer).alpha })
                .put("total", total(layout.coordinates)))

            val seenLayouts = identitySet<LayoutInfo>()
            var ancestor: LayoutInfo? = layout
            while (ancestor != null) {
                val current = ancestor
                check(seenLayouts.add(current) && seenLayouts.size <= 256) { "Cyclic/excessive LayoutInfo ancestry" }
                if (layouts.add(current)) {
                    check(current.isAttached && current.isPlaced)
                    val modifiers = current.getModifierInfo()
                    layoutRows.put(JSONObject().put("identity", id(current)).put("modifier_count", modifiers.size))
                    modifiers.forEachIndexed { index, modifier ->
                        modifier.extra?.let { extra ->
                            check(ownedType.isInstance(extra)) { "Unexpected non-layer ModifierInfo.extra" }
                            references.getOrPut(extra) { mutableListOf() }.add(JSONObject()
                                .put("layout_identity", id(current)).put("modifier_index", index)
                                .put("modifier_class", modifier.modifier.javaClass.name)
                                .put("reported_coordinates_identity", id(modifier.coordinates)))
                        }
                    }
                }
                ancestor = current.parentInfo
            }
        }
        check(orderedLayers.isNotEmpty()) { "No observable layers" }
        references.keys.forEach { check(owners.containsKey(it)) { "ModifierInfo layer has no unique coordinator owner" } }
        val rows = JSONArray()
        orderedLayers.forEach { layer ->
            val coordinates = checkNotNull(owners[layer])
            val graphics = graphics(layer)
            check(!graphics.isReleased) { "Released GraphicsLayer" }
            val sx = finite(graphics.scaleX); val sy = finite(graphics.scaleY)
            val tx = finite(graphics.translationX); val ty = finite(graphics.translationY)
            val alpha = finite(graphics.alpha)
            check(sx > 0f && sy > 0f && alpha in 0f..1f)
            check(graphics.rotationX == 0f && graphics.rotationY == 0f && graphics.rotationZ == 0f) {
                "This observer only validates the production slider's 2D scale/translation layers"
            }
            val position = intPair(positionField.getLong(coordinates))
            check(position[0] == graphics.topLeft.x && position[1] == graphics.topLeft.y) {
                "Coordinator placement and GraphicsLayer.topLeft differ"
            }
            check(graphics.size == coordinates.size) { "Layer/coordinator sizes differ" }
            val fractions = floatPair(originField.getLong(layer)).also { it.forEach(::finite) }
            val unspecified = graphics.pivotOffset == Offset.Unspecified
            val px = if (unspecified) graphics.size.width / 2f else finite(graphics.pivotOffset.x)
            val py = if (unspecified) graphics.size.height / 2f else finite(graphics.pivotOffset.y)
            near(px, graphics.size.width * fractions[0], "pivot x")
            near(py, graphics.size.height * fractions[1], "pivot y")
            val raw = affine(sx, sy, tx, ty)
            val pivoted = (underlying.invoke(layer) as FloatArray).copyOf()
            same(pivoted, affine(sx, sy, px + tx - sx * px, py + ty - sy * py), "pivot compensation")
            val parent = coordinates.parentCoordinates
            val localToParent = parent?.let {
                Matrix().also { matrix -> it.transformFrom(coordinates, matrix) }.values.copyOf()
            }
            localToParent?.let { actual ->
                val expected = pivoted.copyOf().also { it[12] += position[0]; it[13] += position[1] }
                same(actual, expected, "placement + pivoted versus public transformFrom")
            }
            rows.put(JSONObject().put("layer_identity", id(layer)).put("graphics_identity", id(graphics))
                .put("renderer_layer_id", rendererId.invoke(layer).toString()).put("owner_class", layer.javaClass.name)
                .put("coordinator_identity", id(coordinates)).put("layout_identity", id(checkNotNull(layoutField.get(coordinates))))
                .put("modifier_references", JSONArray(references[layer] ?: emptyList<JSONObject>()))
                .put("coordinator_only", !references.containsKey(layer))
                .put("raw_layer_transform", JSONObject().put("scale", array(sx, sy)).put("translation_px", array(tx, ty))
                    .put("rotation_degrees", array(0f, 0f, 0f)).put("alpha", alpha)
                    .put("transform_origin_fraction", JSONArray(fractions.toList()))
                    .put("pivot_offset_unspecified", unspecified).put("effective_pivot_px", array(px, py))
                    .put("size_px", JSONArray(listOf(graphics.size.width, graphics.size.height)))
                    .put("placement_px", JSONArray(position.toList())).put("matrix_without_pivot_or_placement", matrix(raw)))
                .put("pivoted", JSONObject().put("matrix_without_placement", matrix(pivoted))
                    .put("m41_m42_include_pivot_compensation", true)
                    .put("matrix_with_placement", localToParent?.let(::matrix) ?: JSONObject.NULL))
                .put("total", total(coordinates)))
        }
        return JSONObject().put("schema", 1).put("compose_contract", "1.12.1")
            .put("matrix_storage", "Compose Matrix.values: row-major, row vectors; x'=x*m[0]+y*m[4]+m[12], y'=x*m[1]+y*m[5]+m[13]")
            .put("identity_scope", "Stable object identities within this observer session; renderer IDs are strings")
            .put("alpha_scope", "Per-layer alpha and ancestry product only; excludes paint alpha, clipping and compositing effects")
            .put("targets", targetRows).put("layouts", layoutRows).put("layers", rows)
    }

    // Public API: https://developer.android.com/reference/kotlin/androidx/compose/ui/layout/LayoutCoordinates
    private fun total(coordinates: LayoutCoordinates): JSONObject {
        val totalMatrix = Matrix().also { coordinates.transformToScreen(it) }
        check(totalMatrix.values.size == 16 && totalMatrix.values.all { it.isFinite() }) { "Nonfinite total transform" }
        val points = listOf(Offset.Zero, Offset(1f, 0f), Offset(0f, 1f),
            Offset(coordinates.size.width.toFloat(), coordinates.size.height.toFloat()))
        points.forEach { point ->
            val actual = coordinates.localToScreen(point); val mapped = totalMatrix.map(point)
            near(actual.x, mapped.x, "total x"); near(actual.y, mapped.y, "total y")
        }
        return JSONObject().put("space", "local_to_screen_px").put("matrix", matrix(totalMatrix.values))
            .put("basis_on_screen_px", JSONArray(points.take(3).map { p -> coordinates.localToScreen(p).let { array(it.x, it.y) } }))
    }

    private fun graphics(owner: Any): GraphicsLayer = graphicsField.get(owner) as GraphicsLayer
    private fun field(owner: Class<*>, name: String, type: Class<*>): Field = owner.getDeclaredField(name).apply {
        check(this.type == type) { "Compose 1.12.1 field signature differs: $name" }; isAccessible = true
    }
    private fun finite(value: Float): Float = value.also { check(it.isFinite()) { "Nonfinite layer property" } }
    private fun near(a: Float, b: Float, label: String) = check(a.isFinite() && b.isFinite() && abs(a - b) <= .02f) {
        "$label mismatch: $a versus $b (instrumentation consistency tolerance .02px)"
    }
    private fun same(a: FloatArray, b: FloatArray, label: String) {
        check(a.size == 16 && b.size == 16); a.indices.forEach { near(a[it], b[it], "$label[$it]") }
    }
    private fun intPair(bits: Long) = intArrayOf((bits shr 32).toInt(), bits.toInt())
    private fun floatPair(bits: Long) = floatArrayOf(Float.fromBits((bits ushr 32).toInt()), Float.fromBits(bits.toInt()))
    private fun affine(sx: Float, sy: Float, tx: Float, ty: Float) = floatArrayOf(
        sx, 0f, 0f, 0f, 0f, sy, 0f, 0f, 0f, 0f, 1f, 0f, tx, ty, 0f, 1f)
    private fun matrix(values: FloatArray) = JSONArray(values.map(::finite))
    private fun array(vararg values: Float) = JSONArray(values.map(::finite))
    private fun <T : Any> identitySet(): MutableSet<T> = Collections.newSetFromMap(IdentityHashMap<T, Boolean>())
}
