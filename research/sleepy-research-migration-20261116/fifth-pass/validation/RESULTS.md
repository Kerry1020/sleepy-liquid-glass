# 剩余研究导出清理

本批仅从 10 份产品测试剥离无消费者的成功路径 PNG、JSON、TXT 导出、附件目录参数、采集日志和仅服务导出的数据收集。完整原件先在资产库 `629ab8b3d4de0dbbc578b3aae8e0717da3ba79d7` 发布；Git 远端、GitHub API 与云端 10 个 blob/大小均已核对，然后才改写产品测试。

Sleepy 提交 `1b6b96834765412f5a34658c3e459c01f3b75d71` 为 10 文件、+91/-246；追加到清理 PR #443 后累计 96 文件、+472/-27,077。生产实现、材质、布局、Gradle、CI 均未改变。

独立逐项复核：39 个 `@Test` 名称全部保留；90 处 assert/assume 中仅删除 PNG 编码成功检查，其余 89 处产品断言的参数、数值门限及采样语义保留。手势、主时钟、等待、250ms 静置、HWUI/PixelCopy 及原有 5s 超时均保留。8s 全线程栈 watchdog 仅服务文件导出，随导出删除。用于回归的内存截图、CPU/GPU 计算与必要 CSV 参考数据保留。

[默认测试编译收据](compile.json)和[公开日志](compile.log)：单次 `:app:compileDebugAndroidTestKotlin --offline --console=plain` 成功，3.379s；没有加载外置研究 overlay，没有设备操作或新增光学实验。原始日志只在忽略目录保留，收据分别记录原始与公开哈希。

本 head 的云端检查开始运行：CI 43765226389、Debug APK 43765223227。未将旧 head 的成功冒称为本 head 成功。当前 PR 为 OPEN/BLOCKED，主分支 update restriction、账号不能 bypass；未修改保护规则或声称已合并。该清理不修复或隐藏历史光学/设备失败，也不构成光学验收。
