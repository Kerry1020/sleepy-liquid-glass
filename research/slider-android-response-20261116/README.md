# Android Slider G 响应采集归档 · 2026-11-16

本目录归档已完成的四轮 Android 原始采集及后续明确标记的采后诊断，不新增采集或调参；**采集成功不代表视觉、交互或光学验收通过**。原始方案和采前身份清单分别见 [PLAN.md](PLAN.md) 与 [FREEZE.json](FREEZE.json)。

## 已保存的采集

已实际读取四轮 receipt、result 和 index：每轮仪器测试 `exit_code=0`、`test_passed=true`；结果状态为 `passed`，冻结索引器状态为 `original_hashes_pointer_and_pair_checks_passed`。每轮含六个姿态 × shape/flat，共 **12 个按住状态端点、49 个原始文件**（48 张 PNG 和一个 `result.json`）；receipt 中各文件的设备/主机哈希匹配标记均为 true。

| 顺序 | 条件 | 按住端点 | 原始文件 | 原始回执 |
| --- | --- | ---: | ---: | --- |
| 1 | control-pre | 12 | 49 | [receipt.json](evidence/rounds/control-pre/android-r2/receipt.json) |
| 2 | global-G | 12 | 49 | [receipt.json](evidence/rounds/global-G/android-r2/receipt.json) |
| 3 | mask-G | 12 | 49 | [receipt.json](evidence/rounds/mask-G/android-r2/receipt.json) |
| 4 | control-post | 12 | 49 | [receipt.json](evidence/rounds/control-post/android-r2/receipt.json) |

合计 48 个按住端点、196 个原始文件。四份 receipt 绑定同一份 `FREEZE.json`：SHA-256 `4cd995935db016027d5c37cb472b53c7ea205a063aa7dc68412a265e2f704e23`。这些是采集完整性记录，不是系统间响应一致性结论。

## 分析状态与仓库边界

采前冻结的 [analyze.py](analyze.py) 虽通过 19 项纯数学/门限自测，实际加载首轮数据时因假设不存在的 `source_manifest` 字段及复制后的 manifest 路径而失败；后续还确认了索引顶层身份、几何记录字段的格式差异。原冻结文件保持不变。

[analyze-compatible.py](analyze-compatible.py) 是**采后 I/O/schema 兼容修复**：读取已绑定的原始 S manifest，以 receipt 哈希、嵌入 manifest、源图身份和实际记录交叉验证。数学、阈值及响应计算不变，四轮各 63 个加载身份检查和原 19 项自测通过；它不属于采前冻结版本，也不意味着完整响应分析已通过。[原冻结版本的四轮拒绝结果](analysis-v1-schema-rejection/analysis.json)与[采后修复核对记录](post-acquisition-schema-repair.json)分别保存。

既有兼容版已完成[采后诊断](analysis-v2-post-acquisition-compatible-20261116/RESULTS.md)，状态为 `DIAGNOSTIC_COMPOSITE_RESPONSE_GEOMETRY_CONFOUNDED`，`optical_acceptance=false`、`inference_allowed=false`。控制漂移为零，但跨系统几何超过冻结门限，有效不透明度仍未知；E4 区间相容不能作为材质一致或光学通过。完整结果与数值数组另存，冻结输入和分析源码未改，也没有新增设备采集或产品修改。

Fixture 与生成源码留在本资产库的[外置研究 host](../slider-android-host/README.md)，仅经显式 opt-in 编译到兼容的 Sleepy 仪器测试宿主；研究源码不进入 Sleepy 产品仓库，普通构建不加载该入口。

## 历史视觉上下文

![历史六姿态 iOS/Android 对照](../../docs/design/evidence/glass-slider-star-20261115/figures/six-pose-comparison.png)

上图来自既有研究，是历史上下文；**不是本轮四条件的配对结果，也不是本轮验收图**。不得用它替代本目录的原始证据或后续分析。
