# Dock 静态材质响应根因与最小生产修正方案

日期：2026-11-14。范围仅为当前 Android Dock 底座/背板材质的只读审计，以及 M 中已经采集的五灰、三色平坦输入。未操作设备、构建、Git、子代理；未读取 N/holdout；未修改产品源码或冻结方法。本文是供 root 实施和采集的方案，不是修复已完成或原生一致的声明。

## 结论

当前主要偏差有两个可由源码和既有数字明确定位的来源：

1. **主体“暗底越白”的 cover 响应。** `pill(light)` 的大底色覆盖、正 `contrast` 和饱和度处理，直接重现 Android 的五灰和 RGB 中心结果。它把 gray26 的 cover 从约 0.576 提高到 0.746，输出约 189；原生该处为 36。改变 blur 或折射截面无法修正平坦输入中心的这个响应。
2. **边缘绕过主体材质，再叠一次黑边。** AGSL hairline 从原始 `sampleGlass` 算暗线并替换已完成的 `glass`，随后 Compose 的独立黑 border 再压暗。gray128 的 128→约 101.4→约 89.1 与实测顶缘 89 一致。改变 `refractionProfilePower` 无法解除这两个颜色处理步骤。

最小可验证修正应限于 **Dock 底座的专用材质响应**：把主体 tone/chroma 与 rim 分开；停止用主题着色的 tint 和固定 contrast 公式控制所有背景；取消叠加的 raw-source 暗线/独立 border；保留当前采样、haze、几何和折射供独立验证。不能把某张灰底上调好的 alpha 推广成修复。

## 代码位置与受影响层

源码根目录 A：`/Users/kerrylee/.codex/worktrees/android-settings-glass-fixes/sleepy`。行号对应本次读取的 SHA，后续 root 修改后可能变化。

| 位置 | 当前行为 | 修正边界 |
| --- | --- | --- |
| `app/src/main/java/com/lingion/sleepy/ui/component/liquidglass/LiquidGlassNavigationBar.kt:174–193` | `materialDark` 初始取 App 主题；背景外观采样受默认 false 的 `LocalDockBackdropAppearanceEnabled` 控制；lens 使用 `rememberCombinedBackdrop(backdrop, platterBackdrop)` | 主体响应与外观状态分开记录；保留真正的 retained platter 作为上层 lens 输入 |
| 同文件 `:580–624` | 底座依次具有 retained layer、shadow、`surfaceContainer` background、独立 1dp border、`drawPlainBackdrop`/`LiquidGlassStyle.pill` | 改动限此底座的 GL 分支；底座修改应被 retained layer 保留，从而进入上方 lens 的折射输入 |
| `LiquidGlassStyle.kt:168–191` 的 `pill()` | light：`#F4F4F4`、alpha `147/255`、contrast `.4`、saturation `2.1`；dark：`surfaceContainerHighest` alpha `.48`、contrast `-.4`、saturation `1.925`；两者 clear blur `0`、haze `.72`、hazeBlur `15.6` | 使用 Dock 专用响应。当前 app/runtime 主源码仅 Dock 引用该 factory；仍应防止扩大成其他控件的共享改动 |
| `LiquidGlassShader.kt:285–312` 的 `build()` | `uOptics` 绑定 refraction/saturation/brightness；`uTint` 绑定未额外色彩转换的 Color 分量；`uGlow.w` 其实是 contrast | 新响应使用独立模式/参数；不要改变所有旧 style 的 uniform 含义 |
| `liquid_glass.agsl:712–757` | 几何位移、frost、clear/haze 混合、veil | 第一轮保持，避免把 tone 修正与光学参数混在同一次变更中 |
| AGSL `:758–778` | 饱和度与亮度→根据五点背景亮度算 clash→加厚 tint→premultiplied glass | Dock 模式替换此段的颜色响应；不要在新响应后再叠一次旧 tint/clash |
| AGSL `:780–821` | rim screen/add light，随后 raw-source hairline 替换主体颜色 | Dock 用材质空间的一套 rim，不再同时保留 raw-source 暗线与外层 border |
| `LiquidGlassEffect.kt:53–60,73–136,140–149` | API/异常 fallback 使用 blur+vibrancy；GPU 支持时独立 clear/haze atlas 后进入 shader | 本报告的数值归因针对该 GPU 分支；fallback 没有完整执行 tint/contrast shader，不能套用同一数值结论 |

底座的 `.background(alpha=.88/.72)` 不是本轮中心白雾的主要来源：在输入 backdrop 不透明的内部，shader 的 `coverage = alpha*(1-cover)+cover = 1`，其输出已覆盖这层 background。该 background 仍会影响边界、透明输入、fallback 和 retained sibling，不能据此直接全局删除。

上层 raised lens 的自身 style、glyph lens、selection 色块和运动状态本轮不改。底座被上层 lens 折射时，应看到**已完成 tone/haze/rim 的底座**。不能为了亮度匹配把 lens 改成绕开 platter 直接读取最底层背景。

## 主体方程能重现已有 Android 数据

以下只用于不透明常量底色、固定中心、无 glow/rim/端部 shading 影响的既有采集，所有分量归一化为 `[0,1]`：

```text
y = dot(c, [0.2126, 0.7152, 0.0722])
t = 244/255
a = 147/255
s = 2.1
k = 0.4
clash = clamp((t - y - 0.3)/0.5, 0, 1)
cover = a + (1-a)*k*clash
O = clip((1-cover) * (y + s*(c-y)) + cover*t, 0, 1)
```

| 输入 | clash | cover | 当前方程预测 RGB8 | Android 实测中心/内部中位数 | 原生实测中心/内部中位数 |
| --- | ---: | ---: | --- | --- | --- |
| gray26 / light | 1.0000 | .7459 | 188.602 | 189 | 36 |
| gray77 / light | .7098 | .6967 | 193.352 | 193 | 176 |
| gray128 / light | .3098 | .6290 | 200.959 | 201 | 198 |
| gray179 / light | 0 | .5765 | 216.471 | 216 | 220 |
| gray230 / light | 0 | .5765 | 238.071 | 238 | 247 |
| red `[232,48,48]` / light | .6304 | .6833 | `[255,168.293,168.293]` | `[255,168,168]` | `[255,139,139]` |
| green `[48,232,48]` / light | 0 | .5765 | `[99.680,255,99.680]` | `[100,255,100]` | `[82,255,82]` |
| blue `[48,48,232]` / light | .8331 | .7176 | `[184.523,184.523,255]` | `[184,184,255]` | `[155,155,255]` |

小于约一档的差异是这里没有模拟 GPU 量化、编码路径和 rasterization。这个吻合支持“当前主体公式就是主要偏差源”，不证明所有空间像素都没有其他影响。

当前 dark 还把 `surfaceContainerHighest` 的主题色放入中性背板，导致灰底出现例如 `[93,92,95]`、`[109,108,112]`；原生对应中心为中性 126、158。色偏和背景保留过低应分别处理。三色 dark 的 Android→原生主通道分别为 red `217→255`、green `152→223`、blue `231→255`，不能只靠把 RGB tint 变成灰色解决。

## 边缘方程的单独归因

在 straight top/bottom 的 line 完全覆盖处，light hairline `.35` 和 Compose border `31/255` 可写为：

```text
dark = max(x - .298*255, .22*x)
hairlineResult = .65*x + .35*dark
withBorder = hairlineResult * (1 - 31/255)
```

gray26 预测约 `16.60`（实测 17）；gray77 约 `49.17`（实测 49）；gray128 约 `89.08`（实测 89）。这不是主体在边缘连续变薄的结果，而是替换为 raw source 后叠加两次压暗。曲线的空间轮廓、border 覆盖和 shader line 仍须靠 root 的实际单变量采集验证；这里只给出源码可解释的归因。

去掉黑边后也不能直接把当前固定 rim `.6` 当成正确结果。用中性主体颜色 `B` 与白色 screen 混合 `E = B + r*(255-B)`，原生固定点得到的**复合有效 r** 为：

| light 灰底 | 中心 B | 顶缘 E | 有效 r |
| --- | ---: | ---: | ---: |
| 26 | 36 | 67 | .1416 |
| 77 | 176 | 220 | .5570 |
| 128 | 198 | 231 | .5789 |
| 179 | 220 | 242 | .6286 |
| 230 | 247 | 255 | 1.0000，含 clipping，不能识别更大的值 |

这些是同一坐标的复合关系，**不是原生 rim uniform**。它们说明低灰 edge 响应也需背景/材质状态适配。若只去线、保留固定 `.6`，gray26 会从 36 升到约 167，仍明显错误。

## 最小可验证生产方案

建议按两次有界变更实施，避免又产生无法归因的综合调整。

### 1. 先把 tone/chroma 变成 Dock 专用、可解释的响应

在 Style/Shader 增加默认关闭的 Dock 响应模式，只有 NavigationBar 的底座显式启用。其余 style 仍走原路径。对于新模式，保持现有 `base` 的空间采样，取 unpremultiplied `c`，用：

```text
Y = dot(c, kLuma)
O = clip(T(Y, materialState, backdropLuma) + q(materialState, backdropLuma)*(c-Y), 0, 1)
glass = O * coverage
```

`coverage` 与颜色分开，premultiply 一次。新分支应跳过旧 saturation/brightness/clash/tint 色彩处理，不能重复混色。若透明输入需要 veil，veil 仍只应用一次。所有实际采样的 backdrop RGBA、色彩空间约定保持原样，先不要加未经测定的 gamma `pow`。

一个**可立即采集、不是最终值**的 light 高亮分支初值为：

```text
T_light(Y) = .55 + .45*Y
q_light = .45*2.35 = 1.0575
```

等价 style-only 对照是 `tint=White, alpha=.55, contrast=0, saturation=2.35, brightness=1`，保持其他光学参数。这不是单底色拟合：其灰77/128/179/230 预测 `174.9 / 197.85 / 220.8 / 243.75`；RGB 预测 `[255,138.09,138.09] / [81.90,255,81.90] / [153.78,153.78,255]`，同时接近上述已采原生值。root 可用这个简单对照先证明“clash/tint 响应修正”的效果。

但它在 gray26 仍预测 `151.95`，必须把这个失败保留下来，不能靠只展示灰128和三色宣称完成。

现有 light 数据明确要求低亮度非线性或材质状态分支。可以用连续双分支作为生产结构：

```text
w = smoothstep(kneeLow, kneeHigh, paneBackdropLuma)
T = mix(T_low, T_light, w)
q = mix(q_low, q_light, w)
```

优先用 pane-level、已经模糊的 backdrop luma 决定 `w`，不对每个像素做硬状态切换，以免在纹理上产生色阶和闪烁。现有五点 `sampleBehind` 可复用来形成同帧 luma；其采样方式同样只是候选，并未被证明是原生实现。

当前数据仅能要求 gray26 的 `Y=.10196` 在低分支，且最低彩色 blue 的 `Y=.24033` 已能进入亮分支；**无法识别两个 knee 的精确值或过渡曲线**。例如 `.12/.24` 只是满足现有端点的工程初值。它必须标记待验证，不能当 UIKit 常量。也不能把对一个低灰点的修正写成已经确定的通用规律。

dark 的四个未发生 public bar appearance 变化的灰26/77/128/179，可描述性给出复合线性初值：

```text
T_dark(Y) = 14.0392156863/255 + .821568627451*Y
```

相应灰预测 `35.4 / 77.3 / 119.2 / 161.1`，与原生 `36 / 73 / 126 / 158` 仍有残差。它可以作保持中性的初始传递增益，不能当最终 tone curve。dark 的 chroma 增益应独立用 RGB 校准，不要复用 light saturation，也不要从已 clip 的通道反算唯一系数。

gray230 请求 dark 时，原生当前 bar trait 为 light，输出与 light 同为 247；此场景必须继续报告。把它强行并入固定 dark 曲线会污染参数，把它静默删掉也不成立。当前默认关闭的 appearance 适配和它的候选 hysteresis 不能仅凭这些独立重启平坦样本被认定正确。gray26/light 的公开 bar trait 仍为 light，也不能擅自把其低输出命名成已证实的私有 dark 材质。

### 2. 单独解除叠加边线，再校准材质空间 rim

只在 runtime GL Dock 底座上：

- 去掉 NavigationBar 独立的 1dp border。
- 新 Dock 模式不执行从 `sampleGlass(point)` 替换主体的 raw-source hairline。若以 factory 对照实现，至少把 Dock `hairline`、`hairlineSide` 归零，并注意 dark/light 两分支。
- 保留一套与主体响应一致的 rim，颜色从已完成的 `glass` 出发。rim 的强度/屏混合响应与 tone 状态共享连续权重，不能再次用 raw 背景绕过磨砂层。
- 首先报告所有五灰、RGB 的固定中心、边缘与全部既有深度 bin 的变化。低灰 rim 不能直接继承固定 `.6`；其初值可由上述有效 r 约束，但过渡形状与 clipping 后能量不可由这五点唯一识别。

这次材质改动应被 `platterBackdrop` 保留，使上层 lens 自然折射修改后的实际背板，而不增加另一个近似底座。没有必要在这次修正中改 lens 运动、轮廓、profile power 或全局玻璃组件。

## 哪些参数能识别，哪些不能

| 参数/性质 | 当前证据能得到什么 | 当前不能得到什么 |
| --- | --- | --- |
| 主体 RGB 响应 | 每个已测背景/状态/位置的最终 RGB；当前 light 方程重现 baseline；非线性/状态依赖确实存在 | 全背景通用性、唯一原生配方 |
| tone/chroma 的局部线性系数 | 没有 clipping 且假设模型成立时的复合 intercept、gain、chroma gain | 由 intercept 分离唯一 tint RGB 与 alpha；由 gain 分离 brightness 与 alpha；由 clip 通道还原精确 saturation |
| gamma / 色彩工作空间 | 当前 code-space 公式与采集值吻合，现代码没有显式 transfer-function 转换 | 五灰无法区分多种非线性、材质自适应、私有处理与 gamma；也不能从此保证所有 wide-gamut 目标一致 |
| blur/haze | 常量输入内部的 blur 保持常量，现有参数参与采样路径 | 从五灰/RGB 反算 sigma、clear/haze 比例、核形状；因此本轮不要用 blur 补 tone |
| refraction/profile power | 常量图上位移仍读到同色；当前几何公式可读 | 用平坦输入识别位移、非线性截面、物理厚度、IOR、不同尺寸规律 |
| rim/border | 观察到的组合边缘响应；当前两层压暗机制能数值解释 baseline | 从含 rasterization、重叠 stroke 的结果唯一反演各原生光照层 |
| appearance/hysteresis | 相同请求主题可能有不同当前 bar trait；gray230/dark 已记录切为 light | 独立静态重启样本不能识别切换门限、方向记忆、滞后速度和私有材质状态 |

根因修正的第一轮验收必须覆盖现有完整五灰三色，而不是挑选某种底色。flat 数据可先隔离 tone/rim 的错误；磨砂核、真实位移和“中厚边薄”的非线性截面还需 root 使用已有空间校准输入逐项采集。本文没有给出它们已对齐的结论。

## 本次只读输入身份

| 源码 | SHA-256 |
| --- | --- |
| `LiquidGlassNavigationBar.kt` | `5e3a6a1b2b628cd5a1ea177f9d9f22195af027e7c53f1c5f29b185a76a1c8ea5` |
| `LiquidGlassStyle.kt` | `051cacf70fc654c8760708623c19b811f71560eaad637a4469fb989e37e544ce` |
| `LiquidGlassShader.kt` | `dc215ec35b04bef416056060fe16c297eafd02d655af29c700bb791931ae172c` |
| `LiquidGlassEffect.kt` | `17bcec74d13faee03c1c6f16f4c02e3db735253bdf716adc687c0564e58a376a` |
| `liquid_glass.agsl` | `160226f6fead34d819d4eaa233c71372f3050c9d4b620541077c50fd493f808c` |

数据仅来自 M 的 `material-sweep/manifest.json`、`flat-material-analysis/scene-summaries.csv`、`flat-material-analysis/report.json` 与已独立核算的 `flat-material-independent-review-r2.json/.md`。本轮执行了标准库公式计算和 CSV 读取，没有生成新的 UI 采集数据，也没有继续 frame-ledger/scanner 工作。
