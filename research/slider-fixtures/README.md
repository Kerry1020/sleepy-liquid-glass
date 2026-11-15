# Slider 研究夹具：固定源码镜像

[English](README.en.md) · [逐文件来源与 SHA-256](SOURCE-MAP.json) · [校验清单](SHA256SUMS) · [研究报告](../../docs/glass-slider-star-calibration.md)

本目录从 Sleepy Android 的固定 Git 提交 **`db1e2470db900d4642b27339c9cef31523ab75f3`** 导出。只读取该提交的 Git 跟踪作者源码及工程文件，不使用工作区临时内容。17 份原生工程文件和两份 Android instrumentation 源码保持原路径、原 Git blob 与原始字节，共 **19 份、566,220 bytes**。完整清单、mode、Git blob OID、SHA-256 与源路径逐项保存在 `SOURCE-MAP.json`。

![既有公开对照图：原生与 Android r2 六个静态 held 姿态](../../docs/design/evidence/glass-slider-star-20261115/figures/six-pose-comparison.png)

此图复用既有公开证据，没有新截图。r2 是保留已知失败的未验收检查点；研究夹具的发布不等于光学通过、独立后端验收或完整原生控件移植。图和数据的原始口径见[标定报告](../../docs/glass-slider-star-calibration.md)及[六／八角星报告](../../docs/glass-slider-holdout-validation.md)，七角星未消费。

## 原生参考工程

完整跟踪工程保留于 [tools/native-glass-reference](tools/native-glass-reference/README.md)，包含 `App`、`UITests`、共享 Xcode scheme、project 文件及作者捕获／检查脚本。Slider 依赖同一 App、trace 和测试宿主，因此保留整个原生工程，其他已有 reference case 也原样保留。其内嵌 README 是固定提交的原文，沿用原研究目录的路径与历史上下文。

它是独立研究观察 App，不是本库运行时控件。运行需要 macOS、Xcode 及对应的 iOS 26.5 原生参考环境；已跟踪 Xcode 工程在包内，`project.yml` 声明最低 iOS 26.0。只有修改该 yml 并重新生成工程时才需 XcodeGen。输入 source、采集目录与结果输出需按内嵌说明在实际研究环境提供，本次没有复制截图、视频、trace、DerivedData 或构建产物，也没有执行新构建或采集。

## Android 宿主依赖

两份文件在原 `app/src/androidTest/java/com/lingion/sleepy/ui/component/` 路径：

- [NativeSliderOpticalWorldRenderTest.kt](app/src/androidTest/java/com/lingion/sleepy/ui/component/NativeSliderOpticalWorldRenderTest.kt)：外部 source world、固定 shape/flat、采样映射与原像素采证。
- [GlassSliderRailEndpointRenderTest.kt](app/src/androidTest/java/com/lingion/sleepy/ui/component/GlassSliderRailEndpointRenderTest.kt)：single/range 轨道端点与持有状态研究。

它们需要对应 Sleepy Android App 的 Gradle instrumentation 宿主、Compose 测试依赖、`SleepyThemeProvider`、`LocalUiStyle`、`GlassSlider`／`GlassRangeSlider`、`GlassHost`／`GlassBackground` 等生产适配器，且源码标记为 API 33+。本目录没有移植这些 App 宿主依赖，也没有把测试加入本库 runtime 或 sample。不能直接把这两个测试文件当作公开 Compose Slider API。

## 完整性与继续研究

在本目录运行：

```sh
shasum -a 256 -c SHA256SUMS
```

可另在持有原 Sleepy 仓库的设备用 `git show db1e2470db900d4642b27339c9cef31523ab75f3:<source_path>` 核对导出；所有路径和 Git blob OID 均在映射表。限定的 `.gitattributes` 只保护 SHA 绑定作者源码的原字节与历史空白，不重写源码。

本次只迁移源码所有权与研究入口，不改材质、运行时来源清单、主题或布局，也不改变已有实验的验收状态。既有六份证据包留在 [docs/design/evidence](../../docs/design/evidence)，不重复复制。后续新颜色诊断仍须先冻结单独 protocol；本目录的存在不表示新增采集或新的验证结果。
