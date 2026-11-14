// Upstream: Kyant0/AndroidLiquidGlass bebb11a91bd97bf1dabde479f3b332ad9898731f, Apache-2.0.
// Modifications Copyright (c) 2026 Sleepy contributors, GPL-3.0-or-later.
// Original upstream portions retain their Apache-2.0 license.
package com.kyant.backdrop

import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.RenderEffect
import androidx.compose.ui.graphics.Shape
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.unit.Density
import androidx.compose.ui.unit.LayoutDirection

sealed interface BackdropEffectScope : Density, RuntimeShaderCache {

    val size: Size

    /** Pane origin before recording padding; this upstream layout uses local geometry. */
    val effectOffset: Offset get() = Offset.Zero

    val layoutDirection: LayoutDirection

    val shape: Shape

    var padding: Float

    /** Optional preprocessing completed in a separate layer before [renderEffect]. */
    var inputRenderEffect: RenderEffect?

    var renderEffect: RenderEffect?
}

internal abstract class BackdropEffectScopeImpl : BackdropEffectScope, RuntimeShaderCache {

    override var density: Float = 1f
    override var fontScale: Float = 1f
    override var size: Size = Size.Unspecified
    override var layoutDirection: LayoutDirection = LayoutDirection.Ltr
    override var padding: Float = 0f
    override var inputRenderEffect: RenderEffect? = null
    override var renderEffect: RenderEffect? = null

    private val runtimeShaderCache = RuntimeShaderCacheImpl()

    override fun obtainRuntimeShader(key: String, string: String): RuntimeShader {
        return runtimeShaderCache.obtainRuntimeShader(key, string)
    }

    fun update(scope: DrawScope): Boolean {
        val newDensity = scope.density
        val newFontScale = scope.fontScale
        val newSize = scope.size
        val newLayoutDirection = scope.layoutDirection

        val changed = newDensity != density ||
                newFontScale != fontScale ||
                newSize != size ||
                newLayoutDirection != layoutDirection

        if (changed) {
            density = newDensity
            fontScale = newFontScale
            size = newSize
            layoutDirection = newLayoutDirection
        }

        return changed
    }

    fun apply(effects: BackdropEffectScope.() -> Unit) {
        padding = 0f
        inputRenderEffect = null
        renderEffect = null
        effects()
    }

    fun reset() {
        density = 1f
        fontScale = 1f
        size = Size.Unspecified
        layoutDirection = LayoutDirection.Ltr
        padding = 0f
        inputRenderEffect = null
        renderEffect = null
        runtimeShaderCache.clear()
    }
}
