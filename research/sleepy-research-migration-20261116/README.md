# Sleepy 研究内容迁出记录

[English](README.en.md) · [逐文件来源、哈希与存储位置](SOURCE-MAP.json) · [外置 Android 研究入口](../slider-android-host/README.md)

本目录保全 Sleepy `5c604e83cc5ccbc6c5ab622568eae0c99265dfc4` 中明确属于液态玻璃研究的 52 份文件，共 1,774,394 bytes，随后从应用仓库迁出。它补齐较早已合并提交中的残留；PR #442 本身已缩减为四个生产文件及四个 JVM 回归测试。

![独立资产库已有的四背景示例；本次迁移没有新增光学实验](../../docs/images/sample-backgrounds-light.png)

图复用资产库已发布的独立示例，来源见[图片记录](../../docs/images/sources.json)。迁移不改变运行时、参数、验收状态或这张图的解释。

## 迁移边界

- 原生参考工程 17 份：Swift、Xcode 工程、采集脚本与原说明。
- Android 研究专用入口 8 份：原生运动、Dock／单双头世界、统一外观、面板机制及语言材质诊断。它们不是日常产品回归入口。
- 研究报告与交接记录 7 份。
- 应用内嵌资产包的研究／提取档案 20 份，包含旧 README、catalog、提取计划、图和数值观察；应用保留简短 runtime 接入说明。

15 份字节在本库已经存在，清单直接指向已有文件；37 份缺失版本保存在 `sources/`，不覆盖既有冻结镜像。特别是原生工程的五份旧文件与此前 slider fixture 版本不同，两版均保留。所有映射都带原 Git blob、SHA-256 与字节数。

应用保留生产 `runtime`、确定性 JVM 回归、真正验证行为／采样的 GPU 回归及其共享辅助代码。11 月 9 日的原有设计档案和来源审计不在本次范围。没有复制 APK、DerivedData、Gradle 缓存、trace 或设备数据。

## 校验与使用

```sh
python3 research/sleepy-research-migration-20261116/verify.py
python3 research/sleepy-research-migration-20261116/verify.py --source /path/to/sleepy
```

第一条逐字节校验本库所有 52 个映射；第二条另外使用 `git show` 对照固定来源提交，不要求来源工作区恢复被迁出的文件。归档源码与原文不改写，旧文档中的相对路径、机器路径与历史状态仅保留来源，不能当作当前可执行说明；执行研究使用外置入口并显式选择所需源码。

**永久发布边界：Sleepy 只接收生产应用改动与必要回归。研究入口、协议、报告、图像、曲线、坐标数据与复放工具仅在本资产仓库发布；禁止为方便采集重新放回应用源码树或默认构建。**
