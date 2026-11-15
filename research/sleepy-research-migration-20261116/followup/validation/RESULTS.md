# 仓库边界清理验证 · 2026-11-16

本记录只验证研究迁移与剩余产品测试的状态，不是光学验收。Sleepy 本轮提交 `daabde9ac3b7c421345e6a710fcde1ccd82c475b`。

## 最终范围

累计 PR #443 为 66 文件、+383/-25,967；其中删除 52 个研究文件，12 份产品测试／辅助文件去掉研究职责，另有简短接入 README 和一条文档注释链接。此前 #442 已以 8 文件、+542/-27 合并。

原 52 份文件共 1,774,394 bytes，补充 13 份原文共 253,339 bytes，均已用固定来源 Git blob、SHA-256 和大小逐字节核对。原文保存于资产库；产品仓库不保存本记录、收据或采集协议。真正的行为、几何、分层、GPU 误差门限及必要 shader instrumentation 保留。标准产品路线／布局／指针回归中的诊断截图保留；存在文件输出不等于研究入口。

本次补充清理仅改变 `androidTest`。生产实现、材质参数、业务布局、CI 和 Gradle 没有改变。累计 PR 对生产源码唯一变化是一条文档注释的链接。独立复核另外删除 130 张没有像素断言用途的逐帧全窗口采样，实际色散断言图继续内存采样，并在 finally 中回收。

## 构建与真机结果

- [最后一轮默认构建收据](post-review-build.json)：`assembleDebugAndroidTest --offline --console=plain` 成功，16 秒；13 份改动源码构建期间哈希稳定，无外置 source overlay／init script。
- [真机结果收据](post-review-device-regressions.json)与[完整日志](post-review-device-regressions.txt)：API 36，8 项测试，5 通过、3 失败。安装的是该构建生成的测试 APK，SHA-256 `d0d1819a34d26a0d5b7f65fdfcebe89afb1ed159b22504037d11a5484f574911`，未重复归档 APK。
- [范围核对](scope-verification.json)：66 个累计改动文件，52 删除；13 个补充改动路径全部在 `androidTest`，与补充来源清单一致。

通过项为语言选择／取消／长按行为、持按菜单四角、三背景 × 三材质采样，以及两项前景源坐标／遮罩／颜色误差回归。

未通过项：语言菜单自然展开后 `zh-CN` 行平均像素差 4.305，未达到既有 ≥6 门限；Tab 中间升起帧未达到既有高度断言；Floating 控件持按场景因持续重组发生等待空闲超时。前一轮完整执行也出现同样三类失败，日志保留在 `final-device-regressions.*`。本轮没有降低门限、删除失败断言、修改产品或声称全部通过；没有对拆分前测试做设备 A/B，因此尚未证明这三项失败的归因。

`default-*`、`final-default-*`、`final-device-*` 是中间版本的历史收据，绑定各自源码哈希；以 `post-review-*` 作为本提交最终验证。所有构建输出都只保留日志及身份，不复制 APK、缓存或设备数据。

## 云端检查与合并状态

最新 Sleepy head `daabde9ac3b7c421345e6a710fcde1ccd82c475b` 的 10 项云端检查全部 SUCCESS，CI run `43755312069` 与 Debug APK run `43755310402` 均已完成。这不改变上面的三项真机失败。

普通 squash 合并实际被 GitHub 拒绝：`the base branch policy prohibits the merge`。PR #443 仍为 OPEN/BLOCKED，merge commit 为空。规则 `protect-main`（24128365）的 update restriction 仍 active，当前账号 `current_user_can_bypass=never`；没有使用 admin/bypass、修改规则或删除检查。完整收据：[云端检查与普通合并尝试](remote-ci-and-merge.json)。

## 使用边界

旧外置研究 fixture 仍依赖已经迁出的辅助框架，后续应由资产库在外置 host 显式供给；本轮没有完成这项集成。冻结原图与历史采集身份不改写。光学 goal 继续 active，滑杆 r2 未验收。
