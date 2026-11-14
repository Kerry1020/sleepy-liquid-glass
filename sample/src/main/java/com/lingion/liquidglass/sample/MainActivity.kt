package com.lingion.liquidglass.sample

import android.os.Bundle
import android.os.SystemClock
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.onClick
import androidx.compose.ui.semantics.role
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.toggleableState
import androidx.compose.ui.state.ToggleableState
import androidx.compose.ui.unit.dp
import com.kyant.backdrop.Backdrop
import com.kyant.backdrop.backdrops.layerBackdrop
import com.kyant.backdrop.backdrops.rememberLayerBackdrop
import com.kyant.backdrop.drawPlainBackdrop
import com.lingion.sleepy.ui.component.liquidglass.*

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { GlassLab() }
    }
}

@Composable
private fun GlassLab() {
    var dark by remember { mutableStateOf(false) }
    var background by remember { mutableIntStateOf(0) }
    val scene = rememberLayerBackdrop()
    MaterialExpressiveTheme(colorScheme = if (dark) darkColorScheme() else lightColorScheme()) {
        val colors = MaterialTheme.colorScheme
        val context = LocalContext.current
        Box(Modifier.fillMaxSize()) {
            Canvas(Modifier.fillMaxSize().layerBackdrop(scene)) {
                drawRect(if (dark) Color(0xff1e2030) else Color(0xffeef0fa))
                when (background) {
                    0 -> {
                        val step = 18.dp.toPx()
                        var x = 0f
                        while (x < size.width) { drawLine(Color.Gray.copy(alpha=.45f), Offset(x,0f),Offset(x,size.height),1f);x+=step }
                        var y = 0f
                        while (y < size.height) { drawLine(Color.Gray.copy(alpha=.45f), Offset(0f,y),Offset(size.width,y),1f);y+=step }
                    }
                    1 -> {
                        val palette=listOf(Color(0xffff526a),Color(0xff1fe0af),Color(0xff4268ff),Color(0xffffdf45))
                        val step=24.dp.toPx();var x=0f;var i=0
                        while(x<size.width) {drawRect(palette[i++%4],Offset(x,0f),Size(step,size.height));x+=step}
                    }
                    2 -> {
                        drawRect(Color(0xfffafafa),Offset.Zero,Size(size.width/2,size.height/2))
                        drawRect(Color(0xff171717),Offset(size.width/2,0f),Size(size.width/2,size.height/2))
                        drawRect(Color(0xffec8168),Offset(0f,size.height/2),Size(size.width/2,size.height/2))
                        drawRect(Color(0xff334faa),Offset(size.width/2,size.height/2),Size(size.width/2,size.height/2))
                    }
                    else -> {
                        drawRect(Color(0xff80a9ce))
                        for(i in 0..5) {
                            val base=size.height*(.35f+i*.09f)
                            val path=Path().apply {moveTo(0f,base);cubicTo(size.width*.3f,base-160f,size.width*.55f,base+160f,size.width,base-40f);lineTo(size.width,size.height);lineTo(0f,size.height);close()}
                            drawPath(path,Color(.08f+i*.035f,.20f+i*.035f,.29f+i*.04f))
                        }
                    }
                }
            }
            Column(Modifier.fillMaxSize().statusBarsPadding().navigationBarsPadding().padding(24.dp),verticalArrangement=Arrangement.spacedBy(20.dp),horizontalAlignment=Alignment.CenterHorizontally) {
                Text("Sleepy Glass Lab", color=colors.onSurface, style=MaterialTheme.typography.headlineSmall,modifier=Modifier.background(colors.surface.copy(alpha=.9f),RoundedCornerShape(16.dp)).padding(12.dp))
                Row(horizontalArrangement=Arrangement.spacedBy(12.dp)) {
                    Button({background=(background+1)%4}, shapes=ButtonDefaults.shapes()) {Text("Background")}
                    FilledTonalButton({dark=!dark}, shapes=ButtonDefaults.shapes()) {Text(if(dark) "Light" else "Dark")}
                }
                Spacer(Modifier.weight(1f))
                val style=LiquidGlassStyle.regular(colors,dark)
                Box(Modifier.fillMaxWidth().height(180.dp).drawPlainBackdrop(scene,{RoundedCornerShape(28.dp)},effects={liquidGlass(context,style)}),contentAlignment=Alignment.Center) {
                    Text("Runtime material preview",color=if(dark) Color.White else Color.Black,style=MaterialTheme.typography.titleLarge)
                }
                MotionPreview(scene,dark)
                Text("Experimental runtime preview. Full Sleepy controls are still being extracted.",color=colors.onSurface,modifier=Modifier.background(colors.surface.copy(alpha=.92f),RoundedCornerShape(16.dp)).padding(12.dp))
                Spacer(Modifier.weight(1f))
            }
        }
    }
}

@Composable
private fun MotionPreview(scene: Backdrop, dark: Boolean) {
    var checked by remember {mutableStateOf(false)}
    val driver=rememberTimedGlassControlMotion(if(checked) 1f else 0f,true,spec=GlassControlMotionSpec.Native,travelDistanceDp=22f)
    val context=LocalContext.current
    val colors=MaterialTheme.colorScheme
    val style=LiquidGlassStyle.controlLens(colors,dark)
    val motion=driver.motion
    val lift=motion.geometryLift
    fun toggle():Boolean {checked=!checked;driver.select(if(checked) 1f else 0f,System.nanoTime());return true}
    Box(Modifier.size(96.dp,60.dp).semantics {role=Role.Switch;contentDescription="Motion preview";toggleableState=if(checked) ToggleableState.On else ToggleableState.Off;onClick {toggle()}}.pointerInput(driver) {
        detectTapGestures(onPress={
            val epoch=driver.begin(true,false,System.nanoTime(),SystemClock.uptimeMillis())
            if(epoch!=null) {
                if(tryAwaitRelease()) {checked=!checked;driver.release(epoch,if(checked)1f else 0f,true,System.nanoTime(),SystemClock.uptimeMillis())}
                else driver.cancel(epoch,System.nanoTime())
            }
        })
    },contentAlignment=Alignment.Center) {
        Box(Modifier.size(64.dp,28.dp).background(colors.surfaceVariant,RoundedCornerShape(50)))
        Box(Modifier.size(64.dp,28.dp).background(colors.primary.copy(alpha=motion.position.value.coerceIn(0f,1f)),RoundedCornerShape(50)))
        Box(Modifier.offset(x=(-11f+22f*motion.position.value).dp).size((37f+21f*lift).dp,(24f+14.3333f*lift).dp).drawPlainBackdrop(scene,{RoundedCornerShape(50)},effects={liquidGlass(context,style.scale(motion.lift.toDouble()))}).background(Color.White.copy(alpha=1f-motion.lift),RoundedCornerShape(50)))
    }
}
