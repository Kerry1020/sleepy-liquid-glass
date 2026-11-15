# 孤立形状静态校准结果

本报告描述 iOS 26.5 原生 SwiftUI TabView Dock 与当前 Android 候选实现，在四种孤立彩色源、浅深两种请求主题下的静止画面。八个场景全部列出。结果显示：局部条件差分与绝对外观误差必须分别看；当前候选的绝对底色、选中层，以及三角形源的幅度和扩散仍存在差异。这组校准不提供综合相似度、验收阈值或逐帧交互结论。

## 数据与方法

方法、采样区域和分析代码在读取实际结果前已冻结，见[分析协议](analysis-protocol.json)、[采样定义](sampling-spec.json)和[方法说明](README.md)。本报告直接摘录既有 CSV，没有重新拟合、配准、归一化或更改生产参数。分析冻结标识为 `2474b50cf772f4e01f077d259c62b162597e755035b8659dd3630eb6cc251331`。

每个系统分别以彩色形状画面减去同灰底对照：`D = shape − control`，保留 RGB 正负号。跨系统残差为 `D_Android − D_native`。`条件残差 MAE` 是残差在指定区域内、对像素和 RGB 通道取绝对值后的均值；单位为 0–255 sRGB 码值。全局或远场变化没有被居中或减去。另单独比较两个系统的 control 与 shape，得到`绝对 control MAE`和`绝对 shape MAE`。共同的底色误差可能在条件差分中抵消，因此条件残差小不能代替绝对外观接近。

主表固定使用既有 `nominal_boundary_offset_px=0.0`、`channel=rgb`，数值四舍五入到三位小数。−1、0、+1 物理像素边界敏感性结果仍完整保留在原 CSV，未按结果挑选偏移。

| 源场景 | 源覆盖面积 px² | 源中心 128 px 圆盘实际像素数 | 名义基底实际像素数 |
|---|---:|---:|---:|
| `ic01_circle_top`，上边缘圆 | 1,256.750 | 51,433 | 47,286 |
| `ic02_triangle_body`，内部三角形 | 628.625 | 48,928 | 47,286 |
| `ic03_star_right`，右边缘星形 | 761.625 | 34,197 | 47,286 |
| `ic04_asymmetric_lower`，下边缘不对称形状 | 881.125 | 36,385 | 47,286 |

名义基底为 `nominal_base_excluding_selected_and_glyph_neighborhoods`，排除名义选中胶囊和较宽的名义字形邻域。它不是恢复出的光学边界或 alpha 分割，模糊前景仍可能影响该区。源附近为 `source_center_disk_128px`，圆盘在画布边缘截断，包含材料、可见背景和源本身；不变像素会稀释均值，不能称为材料独占区域。四类源面积也不相等，不能直接用跨形状的像素数比较材料优劣。

**两个 fixture 的渲染上下文也不相同。** 原生 `App/main.swift` 的参考页面包含真实 ScrollView、标题、`Synthetic scroll row` 文字、SF Symbols 和原生父级；Android `NativeDockOpticalWorldRenderTest` 提供背景源世界及其记录，没有复现同一套滚动文字、SF Symbols 和原生父级。绝对图中可以直接看到这一差别。`shape − control` 能抵消恒定加性项，但不能证明消除了背景文字、前景与材料适应之间的非线性交互；名义区域排除也不能完全消除这些影响。因此底色、选中区乃至条件响应的差异都属于当前整套 fixture／候选输出的比较，不能全部归因于材料厚度、折射或单一实现参数。此限界也已写入[冻结方法说明](README.md)的前景和名义区域约束。

## 八个场景的结果

名义基底，47,286 像素／141,858 个 RGB 标量样本：

| 场景 | 请求主题 | 条件残差 MAE | 绝对 control MAE | 绝对 shape MAE |
|---|---|---:|---:|---:|
| `ic01_circle_top` | light | 0.150 | 13.838 | 13.805 |
| `ic01_circle_top` | dark | 0.154 | 33.874 | 33.960 |
| `ic02_triangle_body` | light | 0.844 | 13.838 | 14.338 |
| `ic02_triangle_body` | dark | 1.186 | 33.874 | 34.208 |
| `ic03_star_right` | light | 0.098 | 13.838 | 13.836 |
| `ic03_star_right` | dark | 0.086 | 33.874 | 33.882 |
| `ic04_asymmetric_lower` | light | 0.114 | 13.838 | 13.808 |
| `ic04_asymmetric_lower` | dark | 0.086 | 33.874 | 33.938 |

源中心 128 px 圆盘，像素数见上一表：

| 场景 | 请求主题 | 条件残差 MAE | 绝对 control MAE | 绝对 shape MAE |
|---|---|---:|---:|---:|
| `ic01_circle_top` | light | 0.198 | 12.961 | 12.931 |
| `ic01_circle_top` | dark | 0.177 | 22.188 | 22.273 |
| `ic02_triangle_body` | light | 0.822 | 15.615 | 16.090 |
| `ic02_triangle_body` | dark | 1.155 | 26.929 | 27.260 |
| `ic03_star_right` | light | 0.293 | 11.016 | 11.078 |
| `ic03_star_right` | dark | 0.247 | 18.020 | 18.078 |
| `ic04_asymmetric_lower` | light | 0.317 | 18.283 | 18.286 |
| `ic04_asymmetric_lower` | dark | 0.238 | 31.587 | 31.675 |

原始精度、其余冻结分层及重复差异见 [native-android-differential.csv](calibration-results/native-android-differential.csv)。正负 RGB、Y′ 和独立在线性光下计算的 Y 响应见 [signed-response-strata.csv](calibration-results/signed-response-strata.csv)。本报告不把八个不同场景混合成一个分数。

## 状态、重复与采集限制

八个场景的六个公开状态字段均等于请求的 light 或 dark：原生 control、shape、两次 repeat，以及 Android control、shape，没有公开有效主题不匹配。公开字段不能揭示原生材料内部的适应状态。完整采集来源、系统信息、原始文件路径和哈希见 [capture-sources-and-state.json](calibration-results/capture-sources-and-state.json)。

全部 2,016 条差分统计记录的 `native_response_repeat_abs_mean` 为 0。同一会话内 REST 与 repeat 的条件响应在这些冻结统计上相同；这只说明本次会话的采集重复性，既不是独立统计样本，也不是跨会话稳定性。所供 Android 采集没有 repeat。原生严格来源索引覆盖 16 个会话，拒绝有触摸输入的会话，见[原生索引](../native-calibration-r2/native-dock-index.json)。

32 条裸源守卫记录的 mean、abs_mean、rms、min、max、abs_p95 均为 0，说明本组已知原始源与世界裁切在这些检查中逐像素一致；这不证明经过控件渲染后的材料一致，见 [bare-source-guards.csv](calibration-results/bare-source-guards.csv)。

保存数组经过[独立数值审计](../numeric-audit/calibration-numerics-audit.json)：24 个系统／场景／主题组合、72 个字段均为有限数；RGB 与原始成对图像精确一致，Y′ 和从原图分别解码得到的线性 Y 均落在对应 float32 舍入区间内。审计验证的是保存数值的一致性，不是视觉表现。原分析环境的矩阵乘法路径曾产生浮点告警，其[合成复现](../numeric-audit/synthetic-repro.json)和[独立审计脚本](../numeric-audit/audit_response_numerics.py)一并保留；冻结分析器未改动。

还有一个可见的采集混杂：三角形两主题的原生 control 时钟为 **20:56**，shape 为 **20:57**。其全画布有符号图在屏幕顶部显示前景差分；远于源中心 128 px 的原生阈值计数均为 `626 / 605 / 581 / 539 / 484`（阈值依次为 1、2、4、8、16），Android 对应 light 为 `34 / 0 / 0 / 0 / 0`、dark 全为 0。这些变化按冻结方法完整保留，但不能解释为材料远场传播、整体适应或反推出物理参数。control 与 shape 跨会话，单会话 repeat 为 0 不能消除该混杂。主表的基底和源附近区域不包含顶部时钟。

## 有数据支持的两项差异与后续静态校准方向

1. **绝对外观基线仍有偏差。** 名义基底的 control MAE 在所有 light 场景均为 13.838，dark 均为 33.874。名义选中透镜诊断区的 control／shape MAE 分别为 light 65.616、dark 84.865，同时该区的条件响应和条件残差均为 0。该区包含两系统不同的图标、文字等前景，不能把误差全部归因于材料；源刺激也没有引起该区变化，所以零条件残差不说明选中透镜已对齐。后续静态校准应先核对上下文一致性，再分别检查基底、选中层和前景的绝对画面，避免只以差分调整材料。
2. **内部三角形的响应幅度与空间扩散不同。** 源附近平均绝对 RGB 响应，原生／Android 为 light `0.985 / 0.494`、dark `1.361 / 0.690`。以 `max(|ΔR|,|ΔG|,|ΔB|) ≥ τ` 计数，同一区域在低阈值下 Android 涉及更多像素，在高阈值下原生涉及更多像素，见下表。它同时支持幅度和扩散存在差异，不能只调一个强度数值。后续应联合检查完整阈值序列、正负响应和固定区域图；不从单一阈值推导可见性或保真率。

| 三角形主题／系统 | ≥1 | ≥2 | ≥4 | ≥8 | ≥16 |
|---|---:|---:|---:|---:|---:|
| light 原生 | 2,845 | 2,294 | 1,969 | 1,601 | 1,263 |
| light Android | 10,127 | 5,472 | 1,785 | 815 | 754 |
| dark 原生 | 3,066 | 2,400 | 2,033 | 1,678 | 1,337 |
| dark Android | 11,652 | 7,417 | 2,983 | 865 | 827 |

这里的阈值单位为 RGB 码值，数字是像素数，不是通道数、感知可见面积或新设的通过标准。原始所有场景及冻结分层见 [threshold-sensitivity.csv](calibration-results/threshold-sensitivity.csv)。

## 全部图像与复核入口

[完整图册](calibration-visualizations/README.md)包含全部八个场景，每场景三张，共 24 张图，没有按误差挑图。绝对图并排列出源、原生 REST 和 Android 的 control／shape；有符号图列出源、原生 REST、原生 repeat、Android 的 R、G、B、Y′、线性 Y。完整画布为 750×1334；所有 Dock 细节统一裁切 `[24,1144,726,1312)`，使用同一世界坐标，不按输出重新定位。

全画布有符号图固定为码值 ±255／线性值 ±1；细节图固定为 ±32／±0.125，越界颜色饱和并有标记。图像采用最近邻显示，没有自动增益；细节图颜色饱和不能当作数值截断。原数组和 CSV 仍为数值依据。图文件与来源的绑定见 [visualization-manifest.json](calibration-visualizations/visualization-manifest.json)，该清单 SHA-256 为 `d51ab0a54520ea673abbc8904cd1b37a8abb64cb2e98c214d7a19dd29b3410e3`。

三角形浅色绝对画面：

![三角形浅色：源、原生与 Android 的绝对画面对照](calibration-visualizations/ic02_triangle_body-light-absolute.png)

三角形深色固定 Dock 区域有符号响应；完整量程和顶部时钟差异见其[全画布图](calibration-visualizations/ic02_triangle_body-dark-signed-full.png)：

![三角形深色：统一尺度下的 Dock 有符号响应](calibration-visualizations/ic02_triangle_body-dark-signed-dock-detail.png)

本报告只覆盖上述静态校准数据。它没有读取独立留出数据，没有评估 Toggle、滑杆或 Dock 交互的速度、形变和逐帧节奏，也不能据此作出动态完成或原生等价的声明。[机器可读结果清单](calibration-results/report.json)保留了本次结果的全部文件哈希。
