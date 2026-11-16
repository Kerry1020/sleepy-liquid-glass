# Sleepy 研究内容迁出记录

[English](README.en.md) · [逐文件来源、哈希与存储位置](SOURCE-MAP.json) · [外置 Android 研究入口](../slider-android-host/README.md)

本目录保全 Sleepy `5c604e83cc5ccbc6c5ab622568eae0c99265dfc4` 中明确属于液态玻璃研究的 52 份文件，共 1,774,394 bytes，随后从应用仓库迁出。它补齐较早已合并提交中的残留；PR #442 本身已缩减为四个生产文件及四个 JVM 回归测试。

当前清理状态（2026-11-16）：[PR #443](https://github.com/lingion/sleepy/pull/443) 已合并为 `2a0e4aeaf5029e7168fb15f49ca445a7481934b5`，其 10 项检查均成功。合并主树与清理分支逐树比较一致；七份清单的 98 个原文版本再次对照固定历史来源通过。[合并收据](seventh-pass/validation/merged-20261116.json)记录实际云端状态；更早的 OPEN/BLOCKED 收据仅保留其采集时刻含义。本次只核对仓库范围，没有新增产品改动或设备实验。

![独立资产库已有的四背景示例；本次迁移没有新增光学实验](../../docs/images/sample-backgrounds-light.png)

图复用资产库已发布的独立示例，来源见[图片记录](../../docs/images/sources.json)。迁移不改变运行时、参数、验收状态或这张图的解释。

## 迁移边界

- 原生参考工程 17 份：Swift、Xcode 工程、采集脚本与原说明。
- Android 研究专用入口 8 份：原生运动、Dock／单双头世界、统一外观、面板机制及语言材质诊断。它们不是日常产品回归入口。
- 研究报告与交接记录 7 份。
- 应用内嵌资产包的研究／提取档案 20 份，包含旧 README、catalog、提取计划、图和数值观察；应用保留简短 runtime 接入说明。

15 份字节在本库已经存在，清单直接指向已有文件；37 份缺失版本保存在 `sources/`，不覆盖既有冻结镜像。特别是原生工程的五份旧文件与此前 slider fixture 版本不同，两版均保留。所有映射都带原 Git blob、SHA-256 与字节数。

应用保留生产 `runtime`、确定性 JVM 回归、真正验证行为／采样的 GPU 回归及其共享辅助代码，以及产品布局说明和来源许可审计；历史研究报告另按下述第三批清单迁出。没有复制 APK、DerivedData、Gradle 缓存、trace 或设备数据。

再次排查发现 13 份含有研究职责的测试或辅助文件，原文另存于[补充迁移清单](followup/SOURCE-MAP.json)，共 253,339 bytes，来源固定为 `d38e9d1a92adcde69264bdd50313948bdd29ab0e`。语言菜单的逐帧录制、可配采集协议和反射 shader 诊断、采样／运动／轮廓／背板／窗口回归中的成功路径 PNG／CSV／JSON 研究导出，以及不设性能通过阈值的 exact-contour A/B 采集器，都属于研究职责。应用保留真正的行为、呈现交接、运动与 GPU 误差断言及其内存采样；用于这些断言的 shader instrumentation 也保留。原 52 份清单不改写；补充 13 份完整原文保留拆分前的全部职责。

补充范围也包含 `BackdropAwareForegroundRenderTest` 的成功路径 PNG／JSON 导出，以及产品回归已无调用的背景、布局、采集就绪和指标辅助框架。它们的完整原文保存在本库；Sleepy 只保留必要的 `OpticalCaptureWindow` 截图辅助及实际前景遮罩、颜色误差等内存断言。

[第三批迁移清单](third-pass/SOURCE-MAP.json)另保全 18 份历史研究文件，共 1,450,206 bytes，固定来源为 `daabde9ac3b7c421345e6a710fcde1ccd82c475b`：11 月 9 日的[控件运动报告](third-pass/sources/docs/design/glass-control-motion-20261109.md)及 6 份附件、[PR #299 浮动控件报告](third-pass/sources/docs/design/pr299-floating-controls-20261109.md)及 5 张证据图，以及 5 份 FLClash 控件覆盖、对齐、实现核验和参考版本盘点记录。18 份在本库均无相同字节的已有版本，因而按原目录关系归档到 `third-pass/sources/`，报告与附件的相对链接保持可读。原文中的实验结论、尺寸和参数仅作为历史保留，不代表当前运行时设置或当前验收状态；来源许可由应用的致谢和许可审计独立保留，原 52 份和补充 13 份清单不改写。

## 校验与使用

[第四批迁移清单](fourth-pass/SOURCE-MAP.json)保全另外两份未接入生产的层序原型与自测，共 7,134 bytes，来源固定为 `9cc97649147bd2f4b9a57cb6ddce805d412902cf`。`OrderedGlassScenePrototype` 只被同目录的原型自测引用，不保护现有应用实现，应与研究一起保存。四批累计保全 **85 份、3,485,073 bytes**；原三份清单不改写。

[第五批迁移清单](fifth-pass/SOURCE-MAP.json)另存 10 份产品回归的完整原件，共 95,943 bytes，来源固定为 `e935c5e3b9bc3308930fcf2fe79bbd4f95aab7f6`。这些文件仍夹带无读取方的成功路径 PNG／JSON／TXT 研究导出、录制目录参数或只供附件使用的采集代码。应用仅剥离这些职责，保留原有行为、几何、分层、GPU 像素断言及门限。五批累计 **95 份、3,581,016 bytes**；旧清单与冻结原文均不改写。

[第六批迁移清单](sixth-pass/SOURCE-MAP.json)保全选中色 JVM 回归的完整原件，7,798 bytes，来源固定为 `1b6b96834765412f5a34658c3e459c01f3b75d71`。该测试在成功路径额外导出 9 张 PNG，没有后续读取方；应用移除文件写入和仅供导出的截图，保留四项产品测试、像素断言、手势和时钟步骤。六批累计 **96 份、3,588,814 bytes**；这只是研究职责迁出，不是控件或光学修复。

[第七批迁移清单](seventh-pass/SOURCE-MAP.json)保全两份回归在 `ee1f28fb3c81057f1924cde1ad33ae2f3f49c5b0` 的完整版本，共 13,640 bytes。它们删除导出后仍采集并立即回收无读取方的 Bitmap；应用去掉无用途像素采集，保留帧提交同步及全部实际断言。七批累计 **98 份原文版本、3,602,454 bytes**；同一文件的历史版本分别保存，不覆盖早期原件。

```sh
python3 research/sleepy-research-migration-20261116/verify.py
python3 research/sleepy-research-migration-20261116/verify.py --source /path/to/sleepy
python3 research/sleepy-research-migration-20261116/verify.py --manifest research/sleepy-research-migration-20261116/followup/SOURCE-MAP.json --source /path/to/sleepy
python3 research/sleepy-research-migration-20261116/verify.py --manifest research/sleepy-research-migration-20261116/third-pass/SOURCE-MAP.json --source /path/to/sleepy
python3 research/sleepy-research-migration-20261116/verify.py --manifest research/sleepy-research-migration-20261116/fourth-pass/SOURCE-MAP.json --source /path/to/sleepy
python3 research/sleepy-research-migration-20261116/verify.py --manifest research/sleepy-research-migration-20261116/fifth-pass/SOURCE-MAP.json --source /path/to/sleepy
python3 research/sleepy-research-migration-20261116/verify.py --manifest research/sleepy-research-migration-20261116/sixth-pass/SOURCE-MAP.json --source /path/to/sleepy
python3 research/sleepy-research-migration-20261116/verify.py --manifest research/sleepy-research-migration-20261116/seventh-pass/SOURCE-MAP.json --source /path/to/sleepy
```

第一条逐字节校验本库原 52 个映射；第二条另外使用 `git show` 对照固定来源提交；第三、四条分别校验补充批次与第三批，不要求来源工作区恢复被迁出的文件。归档源码与原文不改写，旧文档中的相对路径、机器路径与历史状态仅保留来源，不能当作当前可执行说明；执行研究使用外置入口并显式选择所需源码。

旧版外置研究 fixture 依赖上述已从 Sleepy 移出的辅助框架，不能假定它仍由应用仓库提供。后续构建外置 Android 研究入口时，必须从本资产仓库显式提供所需辅助源码并完成外置集成；这里记录的是依赖限制，不表示该集成已经完成。不得为恢复旧入口而把研究框架放回 Sleepy。

**永久发布边界：Sleepy 只接收生产应用改动与必要回归。研究入口、协议、报告、图像、曲线、坐标数据与复放工具仅在本资产仓库发布；禁止为方便采集重新放回应用源码树或默认构建。**

[本轮范围、构建和真机验证记录](followup/validation/RESULTS.md)：最终默认构建通过；真机 8 项中 5 项通过、3 项失败，完整保留原门限与失败日志，不构成光学验收。
