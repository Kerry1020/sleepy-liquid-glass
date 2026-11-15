# Dock 静态边缘材质：机制判断与最小候选

审计时间：2026-11-14 15:37 UTC。仅只读 Android 当前 runtime/style、M 已有机制结果，以及 S/C 已公开 calibration 的统计和组件描述。没有设备、构建、Git、产品源码修改或图片解码；没有读取 N 或独立 holdout。以下候选与实验是供 root 实施的方案，不是新渲染结果或验收。

路径缩写：`A=/Users/kerrylee/.codex/worktrees/android-settings-glass-fixes/sleepy`；`M` 为本目录；`S=../glass-isolated-shapes-20261114`；`C=../glass-plain-context-20261114`。

## 结论先行

当前“硬而平”至少有三个不同入口，不能继续只加折射幅度：

1. 正折射的源采样路径有固定的圆弧截面、外缘奇异斜率与内部提前归零；现有 power2 进一步压低内部响应，而外缘斜率仍然奇异。M 实测四个 light 校准源的基底条件误差全部恶化，不能晋级。
2. shader 内的 0.67dp 暗线与外部 1dp border 是独立的颜色覆盖层。它们可盖掉应当显现的折射边带，制造硬描边；改变它们并没有改变 `point + shift` 的采样路径。
3. haze/tint/contrast 控制幅度、扩散和背景适应。M 的 dark-gray light 请求场景仍有巨大主体误差；一个 gray128 上去线有效，不足以决定全背景的最终材质。

最小新模型建议是**只用于正折射、可选的有限边缘斜率截面**，将归一化曲线形状与位移幅度 D、支持宽度 b 分离。第一轮保持 D/b/轮廓/颜色不变，只替换曲线；参数由预先规定的静态校准观测确定，不凭外观指定。默认保留 legacy 路径，任何结果都不能推广到其他控件或动态。

## 1. 实际源码路径与 flat/sharp 的数学来源

当前 `LiquidGlassStyle.kt:29–30,164–190`：pill 继承 `refraction=60, bevel=20`，只将正折射 cap 设为 `refractionLimit=1.5`。`LiquidGlassShader.kt:281–305` 将 bevel、refraction、cap、power 分别绑定为独立 uniform。`liquid_glass.agsl:712–734` 的实际正分支可写为：

```text
m = halfMinor
b = max(min(style.bevel, m/2), 0.001)
D = min(style.refraction, max(style.refractionLimit,0)*m)
u = clamp(inset/b, 0, 1)
Q(u) = 1 - sqrt(2u-u²)
Q_gamma(u) = Q(u)^gamma
shift = -normal * D * Q_gamma(u)
samplePosition = point + shift
```

对于实际 62dp 高的基底，`m=31,b=15.5,D=46.5`。所以 style 的 bevel20 并不代表实际 20dp 的光学带。提高 cap 只是把原 D31 的整条非零位移乘 1.5；没有改变 Q 的形状。d≥15.5dp 后正位移恒为零，中央剩余区没有这条正折射路径。

对 0<u<1，`Q'(u)=-(1-u)/sqrt(2u-u²)`。它在面内端 u→1 时变平，在外缘 u→0 时斜率趋于负无穷。gamma2 保留同一个外缘奇异性，同时把尾部的二次趋零变为四次趋零。数学支持区仍是相同的 b；只是有效位移更集中在很窄的外缘，并非平滑地解决“边缘渐薄”。

| 归一化 inward u | legacy Q | power2 Q² |
| --- | ---: | ---: |
| 0.10 | 0.564110 | 0.318220 |
| 0.25 | 0.338562 | 0.114624 |
| 0.50 | 0.133975 | 0.017949 |
| 0.75 | 0.031754 | 0.001008 |

应同时看采样映射的局部 Jacobian，而不是只看“最大位移”：在一段直边、以朝内 d 为坐标时，源位置 `s(d)=d+D Q(d/b)`，`ds/dd=1+(D/b)Q'(u)`。斜率过零意味着折返、压缩或镜像的分界；无穷斜率与像素采样/遮线叠加可以形成极窄而硬的响应。gamma1 的分界有闭式解 `d*=b[1-b/sqrt(D²+b²)]`。按当前公式，D31 时约为 8.568dp，D46.5 时约为 10.598dp；对应源 inward 约 11.841 与 12.985dp。这些只是当前 shader 公式计算，不是从原生测得的光线或物理厚度。

“原生需要有限斜率”仍是待检验假说。现有数据足以拒绝 power2，尚不能唯一确定原生连续截面、IOR、厚度或边缘导数。

## 2. M 的 power2 实际退化及其含义

数据来自 `mechanism-analysis/profile-power-response.json`，同一已冻结方法，对四个 light 源各自作 shape−control，再比较两系统；没有将不同源合成分数。下列误差及响应均为 0–255 sRGB 码值，px 为原始物理像素，不是 dp。

| 源 | base 条件 MAE γ1 | base 条件 MAE γ2 | source-disk128 条件 MAE γ1→γ2 |
| --- | ---: | ---: | ---: |
| circle top | 0.149896 | 0.297107 | 0.198459→0.334293 |
| triangle body | 0.843604 | 0.855757 | 0.821752→0.833149 |
| star right | 0.098183 | 0.147810 | 0.293330→0.361952 |
| asymmetric lower | 0.113656 | 0.181668 | 0.317090→0.406202 |

triangle 在最外 0–4 物理像素 base 带的 Android 平均绝对响应由 0.363636 降为 0.057473，而原生为 1.292891；条件 MAE 由 1.056619 升为 1.298075。circle/star/lower 在该带原本响应已经超过原生，power2 又略增响应。因此不是“所有源一起少一点/强一点”的单一增益问题：内部源被采到外边的路径与边缘源被采入的路径必须分开检查。

四源在 base inward≥32px 的 γ2−γ1 结果精确为零。这符合当前 b=15.5dp=31px 的截止，不是模型已经修好中央材质；triangle 在该内部区域 Android 响应为 1.074045、原生 2.176064，差异不会被只改这条窄边 Q 自动解决。

gamma<1 会朝更宽尾部的方向改变响应，但本次 γ1/γ2 对照并不证明任意较小指数能通过。尤其 gamma≤0.5 会使面内端导数不再平滑归零，不能为追一个响应幅度盲目下调。若继续探索指数，应作为明确对照，不把某个猜测值变成生产结论。

## 3. S/C 的响应瓣告诉了什么，不能告诉什么

S/C 的 `components.jsonl.gz` 保留的是阈值条件响应组件，不是跟踪得到的一对一光线对应。不同系统/阈值下的 component ID 都是局部标号。`centroid_from_source_center_px` 不应直接被当作采样位移 D；其变化同时受 blur、tint、阈值、遮挡和连通性影响。

在 C 的 triangle-light、`any_abs_RGB≥4` 下，原生有三块落在名义基底的响应，中心瓣 bbox `[513,1204,561,1249)`、上边瓣 `[513,1169,561,1178)`、下边瓣 `[513,1285,561,1292)`；面积分别 1466、238、265px。Android 的三块为 `[509,1205,556,1248)`、`[515,1169,556,1177)`、`[513,1286,554,1291)`，面积 1447、219、119px。它们是分别列出的空间描述，并未按组件 ID 宣称对应。

原生中心/上/下瓣的加权质心相对源中心 y 约为 `+0.111/-58.942/+57.952px`；Android 为 `-1.376/-58.390/+58.416px`。S→C 去掉页面文字之后，这组局部描述保持相同，而旧顶部时钟的无关组件消失。这支持“主要响应路径的位置与幅度/展开程度需要分开校准”，不支持用质心差唯一反演截面。

同一 triangle-light 源附近 128px 圆盘，既有完整阈值序列显示 Android 低阈值覆盖较广而高阈值响应较弱：原生 ≥1/2/4/8/16 为 `2845/2294/1969/1601/1263px`，Android 为 `10127/5472/1785/815/754px`；平均绝对 RGB 响应分别约 0.985 与 0.494。由此只增 D 或统一提高饱和/亮度，都可能放大错误的低幅度尾部。应保留正负 RGB、完整阈值序列与瓣位置，不能按单阈值选参数。

## 4. 独立边线、几何与模糊的贡献

### 外部 border 与 shader hairline

`LiquidGlassNavigationBar.kt:589–600` 的 background 和外部 1dp border 包住后面的材质绘制；既有 C 因果审计已经以实际 Compose 字节码确认 border 最后叠到子内容上。`liquid_glass.agsl:784–816` 先加亮 rim，再由 0.67dp hairline 混入未折射的 `sampleGlass(point)` 并覆盖 rim。后者既是一条暗线，也是对折射结果的局部替换。因此它们可抹去可见的薄边，但不会修正原本 `point+shift` 的映射。

M 已有三灰阶 2×2 GPU 数据，不能再沿用 C 旧文档“未采”的状态。固定名义基底 MAE 及最外 1px 带均值如下；均值覆盖整个固定带，不等同于旧 C 的单个 x375 像素。

| light 请求背景 | 原 baseline base MAE | 去外 border+去 shader hairline base MAE | 最外带 baseline RGB 约值 | 双去线 RGB 约值 | 原生最外带 RGB 约值 |
| --- | ---: | ---: | ---: | ---: | ---: |
| gray26 | 144.685777 | 150.899900 | 27.7/27.5/27.9 | 205.2/204.9/205.4 | 61.5/61.5/61.5 |
| gray128 | 13.257067 | 8.128995 | 97.8/97.6/98.0 | 219.8/219.5/220.0 | 219.3/219.2/219.4 |
| gray230 | 16.739535 | 13.314061 | 182.5/182.3/182.7 | 244.5/244.2/244.7 | 251.0/251.0/251.0 |

gray128 说明去双线能揭示被盖住的亮边，但 gray26 的主体/适应差异完全未解，整区误差还上升。不能据此直接推出全背景、全主题都应该删线或去线后已经对齐。边框、hairline、亮边、主题适应与采样曲线必须各有独立因子记录。

### 轮廓与法线

`DockPlatterShape.kt` 将实际 Continuous Capsule clip 与 retained exact/profile 关联；`LiquidGlassEffect` 可传实际 exact contour，uniform 选择 exact 模式并保留显式 fallback。`signedExactGeometry` 的 inward 是沿径向命中边界后的 normal projection，不是整个面内的 Euclidean SDF。其 zero contour/normal 与深处 inward 的准确性是不同问题。

因此先在真实生产轮廓的直边分析 Q，再检查曲角。不能把 Capsule 换成圆角近似去让某条曲线好看；不能把 fallback 当 exact 成功；也不能把沿角的 inset 误差硬塞进一个 power。新候选必须保留 uOutlined/exactFound、实际 normal/inset 与 source mapping 的诊断身份。如果需要延长 b 到更深处，应先确认该范围的 geometry 有效。

### clear/haze/tint

pill 当前 `blur=0,haze=.72,hazeBlur=15.6`；clear 与 haze 都在 `point+shift` 处采样，haze 不是未移动背景的独立叠层。调 Q 会同时移动两支；改变 haze 比例/半径又会改变响应幅度和尾部。之后还有 saturation、brightness、tint 和全局 clash 覆盖。

这些变量可以解释“低阈值太广、高阈值不足”的一部分，但当前证据不唯一识别谁占多少。先固定它们隔离 Q 候选；再用 M 的平灰/彩色背景研究颜色与传播。均匀输入上的折射位移不产生可辨纹理，不能靠灰底颜色曲线单独拟合 D/b/Q。

## 5. 一个最小、能实际进入 shader 的候选

建议 opt-in 正折射模式 `boundedSlope`，保留 legacy 为默认，新增一个可记录标量 k，而不是再造另一套绘制控件。只在正分支替换 `Q_gamma`：

```text
u = clamp(inset / b, 0, 1)
P(u;k) = (1-u)^2 * (1 + (2-k)*u), 0 <= k <= 3
depth = D * P(u;k)
shift = -normal * depth
```

这是 cubic Hermite 位移截面：`P(0)=1,P(1)=0,P'(0)=-k,P'(1)=0`。其导数 `P'(u)=-(1-u)[k+3(2-k)u]` 在数学区间 k∈[0,3] 内非正，保证有限、单调、不产生负位移；实际镜像/折返由 `J=1+(D/b)P'(u)` 决定。这不是物理厚度场或 Snell 求交。

这个区间来自保持单调的数学约束，不是凭眼选择的外观参数。**本报告不指定生产 k 值。** 首轮 D46.5、b15.5、现有 normal/clip、haze/tint/rim/线条全部保持，比较的变化只有曲线。这样能真正检验“独立外缘斜率/中段形状”是否优于 Qγ，避免又把改善归因于增幅。

需要的最小实现约束：

- 在 style/uniform 中明确记录 mode/k；scale 保留截面身份，lerp 不偷偷将 legacy 切换成另一公式。默认调用、负折射 lens、lensContent、MD 及其他角色保持原行为。
- k 必须 finite，并明确拒绝或记录无效请求；不能静默将失效候选当作成功。AGSL 使用乘法多项式，保持 u=0/1 的有限端点。
- 首先只给 production Dock base 的诊断 copy 提供新模式。玻璃背板后续仍用其实际角色同路径作独立静态校准；不把 Dock 参数广播到所有面板。
- 不同时改 D、b、轮廓、采样层序和颜色。若曲线单因子不足，再以单独注册的 b-only/joint 变体检查，而不是将所有自由度一起拟合。

现有 b 上限为 m/2。若后续纹理证据要求更宽的真实支持区，单改 style.bevel 到20/30仍会被同一上限截断。届时应在 opt-in 正分支中显式表达并记录支持宽度，不影响负镜片；最多扩到有有效 inward/normal 的面内范围，并保留 legacy-b-only 对照。不能隐式取消全局 cap 后把结果说成只改了 k。

## 6. 最小可区分实验与参数来源

仅限当前同尺寸、无输入的 Dock/玻璃背板静态工作，不启动动态、size 或其他控件矩阵。

1. **先保留两个不同问题的证据。** M 的三灰阶 2×2 保留全部四格，计算同 depth-bin 的 border/hairline 主效应与交互；不要只展示双去线。用灰阶/彩色控制检查实际 materialDark、tint/alpha/contrast、原生有效 trait，再决定颜色/线条候选。灰底用于隔离覆盖颜色，不用于反演 refraction。
2. **曲线候选先只改 mode/k，D/b 不变。** 复用四个 S/C 已公开 calibration 源的 shape/control 与完整固定区域，保存绝对图和条件响应。比较所有四源的方向、瓣位置、正负幅度、阈值序列和62个 inward bins。最外源减少过量响应的同时，内部源必须恢复边缘响应；只在其中一源或一个均值上好看不算充分。
3. **若要拟合采样路径，补少量可识别静态标记，而非凭质心认光线。** 在生产真实直边的已知 source inward 位置放多个互不重复的小形状/色码，与同灰对照成对；固定位置和正负对比，避开选中项/图标。至少三个独立位置用于 D/b/k 的识别，还需未用于拟合的位置检验曲线；同时记录可能的一对多折返，不强行最近邻配对。参数从实测的瓣位置/宽度及同一固定误差目标求得。位置数是模型识别的最低条件，实际噪声/遮挡可能需要更多观测；不得在欠定时宣称拟合唯一。
4. **可做一个 shader 内部映射诊断，但不能冒充原生测量。** 将同一真实 AGSL 算得的 point+shift、normal/inset/J 输出到独立诊断通道或已知坐标背景，保留与生产相同轮廓/分支。它验证实际 GPU 路径而非 CPU 重画曲线；颜色、模糊覆盖会污染编码，因此诊断路径与正常材质图必须分别保留。原生仍只以真实公开控件响应检验，不能给原生套 Android 公式。
5. **只有 width 疑点成立才加一个 2×2。** `legacy/新截面 × 旧b/新b` 四格保持 D 和其余材质固定；比较新曲线的贡献与纯改宽度贡献。拟合出的 b/k 没有可辨性时，保留多解和失败，不增加更多参数掩盖问题。

预先写清候选参数、拟合与诊断区域、误差/位置目标、异常数据规则和最大变体数。来源/ICC/世界坐标、原始输入、原始输出及代码/APK身份保持可核；重复/恢复 baseline 用于发现状态漂移，不重试直到颜色满意。本方案不读取或用独立 holdout 选参数。

拒绝条件包括：边缘源过量响应改善但内部源进一步消失；位置/折返结构更差；只通过提高 tint 遮盖纹理差异；b 请求被 cap 忽略却当作不同模型；exact fallback/层序/实际主题发生未控制变化；仅单灰或整区均值改善而固定边带明显退化。若 boundedSlope 不足以解释多位置响应，应保留失败并提出下一模型，不能因为其数学更平滑便认定更像原生。

## 审阅身份

| 来源 | SHA-256 |
| --- | --- |
| A `liquid_glass.agsl` | `160226f6fead34d819d4eaa233c71372f3050c9d4b620541077c50fd493f808c` |
| A `LiquidGlassStyle.kt` | `051cacf70fc654c8760708623c19b811f71560eaad637a4469fb989e37e544ce` |
| A `LiquidGlassShader.kt` | `dc215ec35b04bef416056060fe16c297eafd02d655af29c700bb791931ae172c` |
| A `DockPlatterShape.kt` | `5dd86599853fdeaf57485b2e64d80e5f2618ee7b53aef3e4c90eab6c43f04575` |
| A `LiquidGlassNavigationBar.kt` | `5e3a6a1b2b628cd5a1ea177f9d9f22195af027e7c53f1c5f29b185a76a1c8ea5` |
| M `analyze_mechanism_probes.py` | `90cbb59ba1cf59a97abfc5cfa7f52d3bc4ea235069540908a6d0fd8247d47185` |
| M `mechanism-analysis/profile-power-response.json` | `7f885f9ec8450c6ee0703cfed7cc52e47de426f545e019138bb0308c0cfb3c72` |
| M `mechanism-analysis/border-hairline-depth.json` | `e35afc6e8755d21a5f1a955b7b0540fbcc35e5a19ca78f607e3d0bf4940268ee` |
| S `analysis/calibration-results/components.jsonl.gz` | `b2e3a3c9b71c4ae10e6567d80833a822fbccf9ceb0da67dab05bf82b778d6e1a` |
| C `calibration-results/components.jsonl.gz` | `7176c4d6fa476cbc5ed4d4b64708426ca1eced014bab380499bee9197847869f` |
| C `calibration-results/threshold-sensitivity.csv` | `54852caf71d76d1a3bfc56b43e0cbf36c2628f752ab2d999812d75503194b1df` |
| C `calibration-results/signed-response-strata.csv` | `665f50a1277c394b6e14619c9b424d5ff22d2f840901eecbeff52705e88ddb26` |

此报告没有新增“静态验收完成”“原生等价”或相似度百分比结论。
