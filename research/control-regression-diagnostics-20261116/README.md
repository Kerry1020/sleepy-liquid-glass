# 控件回归诊断 · 2026-11-16

这些是资产库内的诊断、外置研究入口和运行记录，不属于 Sleepy 产品 PR。本文保留失败结果，没有修改材质或通过门限。

![既有滑杆六姿态对照；不是本轮诊断的新结果](../../docs/design/evidence/glass-slider-star-20261115/figures/six-pose-comparison.png)

图复用既有研究对照。本轮没有新增原生截图，不能用这张图证明下面的测试假设。

## 已执行的时钟与轨道诊断

| 条件 | 构建及设备结果 | 仍失败的断言 |
| --- | --- | --- |
| 只将输入时钟接到 Compose 虚拟时钟 | 构建成功；设备 2 项、0 通过、2 失败 | Toggle 移动宽度与持按几乎相同；Tab 比较的是外层触控容器 |
| 再改为实际 `segment-track` 节点 | 构建成功；单项设备测试失败 | 实际轨道上下溢出已通过；字形宽度仍为静止 106、持按 106 像素 |

[时钟单项构建](floating-clock-only-build.json)、[完整设备结果](floating-clock-only-device.json)、[轨道修正构建](floating-clock-track-build.json)和[单项设备结果](floating-clock-track-held-device.json)分别绑定实际源码和测试 APK 哈希。instrumentation 命令退出码 0 不表示断言通过。没有把 APK 或设备导出复制到本库。

两处测试修正暂存于[补丁](floating-clock-track-proposed-regression.patch)及[身份记录](floating-clock-track-patch.json)，已从 Sleepy 工作区撤回，未混入仓库清理 PR。原动作、断言和门限均未改。它们只修采样时钟与比较节点，不是产品表现修复或已验收方案。

Toggle 左移可能出现横向压缩，现有最大宽度测量不足以区分压缩与无形变。`moveTo(...,16)` 本身推进测试时钟，再显式推进一帧会改变实际节奏。字形至少 1.1 倍的旧断言来源是历史 Android 预放大实现，当前缺少同位置 iOS 26.5 REST/HELD 像素配对；不能据此直接调产品参数或降低断言。

## 外置入口的独立构建记录

[语言菜单 C/U/恢复 C/E 诊断](language-gpu/README.md)与[滑杆外置研究 host](../slider-android-host/README.md)已通过一次显式组合构建：[收据](host-integration-20261116/build.json)、[公开日志](host-integration-20261116/build.log)。固定 Sleepy `e935c5e3`，七份外置输入哈希不变，`:app:assembleDebugAndroidTest --offline --console=plain` 成功，9.232s；普通应用源码与配置未改。随后复用该包执行了[语言菜单首轮 GPU 诊断](language-gpu/results/language-triplet-20261115T222128Z/README.md)：五行数据完整，但精确静止几何控制失败，JUnit 为失败；这不是材质验收或行为通过结论。此次未执行新的滑杆入口。

滑杆 schema2 双文件入口由资产库显式提供冻结 fixture 与完整辅助文件；此次收据验证该版本可编译，不能用旧单文件记录代替。普通 Sleepy 构建不加载任一入口；新的产品回归清理亦未把它们重新放回应用仓库。

公开日志的序列号与本机路径按 [PUBLICATION.json](PUBLICATION.json) 脱敏；原始字节仅保留于本机忽略目录。原始哈希与公开文件哈希分别记录，不能把公开副本当作原始日志。

## 精确终态与实际层观察入口

[新组合构建记录](host-integration-observed/README.md)保留首次外置版本检查失败与修正后的成功构建；语言终态几何和滑杆层观察均已实际编译。只改资产库 init script 的版本检查方式，应用源码、配置与主 APK 字节不变。当前尚未安装或执行，不能把构建成功写成几何、材质或光学通过。

[普通 Toggle 原生点击](../toggle-tap-native26-20261116/README.md)另保存 iOS 26.5 的八次零移动点击输入及完整观察窗口。它不复用450ms持按拖动冒充普通点击，也不把记录层 opacity 当作光学透明度。
