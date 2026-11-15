# Plain-scroll 原生静态校准

这是独立于旧 synthetic-scroll 实验的新上下文，仍为 calibration，不能作为独立测试或产品验收。输入沿用四对孤立多色形状，Android 侧条件复用此前冻结候选的原始采集；本轮没有重新构建或采集 Android。

原生保留 iOS 26.5 的真实 TabView、四项系统 TabBar、父 controller 和真实 ScrollView。仅将原有页面标题与 24 行文字所在的 VStack 设为透明并从无障碍树隐藏，布局、padding 和滚动内容继续保留。原生系统图标、标签及父层机制仍与 Android 不同。

## 已保留的采集与检查记录

- `build-result.json`：复用已有 DerivedData 构建一次，实际成功；源码和可执行文件哈希均已绑定。
- `native-feasibility/`：scheme 枚举没有启用新测试；在实际测试前停止。保留无效采集说明，不能计作通过。
- `native-feasibility-r2/`：以同一已构建 xctestrun 明确选择新方法，实际执行一个测试、两个 session，导出四张截图、四份 AX 和一份请求清单。
- `feasibility-metadata-gate.json`：第一版 gate 的失败记录。它错误地将整个启动阶段的主题恒定作为必要条件。
- `check_feasibility_v1.py`：第一版检查器原字节。`check_feasibility_v2.py` 保留所有启动事件，全 session 检查实例与几何，另在请求至最后 AX 的完整截图窗口内检查公开主题及父层、滚动状态。
- `check-feasibility-v2-final-self-check.json`：44 项合成元数据检查通过，包含启动主题变化保留、截图期间主题变化拒绝，以及实例替换、缺失输入和零测试拒绝。
- `feasibility-metadata-gate-v2-final.json`：两个实际 session 的元数据检查通过。shape session 的 bar 主题在启动时短暂为 dark，恢复 light 比请求早约 5.830301 秒；该变化未删除。
- `foreground-review.json`：实际查看原始 control/shape 截图；标题与列表文字不可见、原生 TabBar 仍可见。四张图的固定无遮挡页面 ROI `[0,80,750,1000)` 均与 RGB128 源背景相同。这只检查前景移除，不是光学等价证明。
- `feasibility-gate.json`：绑定上述检查，批准运行完整 16 个静态 session；不批准动态采集或产品验收。

状态栏采集前确认没有既有 override，运行中固定 9:41、信号及电池等字段，并在 finally 中清除。完整采集使用新的 `native-matrix-r2/` 目录；必须核对实际测试数量、全部 16 个 session、32 张原始截图与 32 份 AX，不能只依赖命令退出码。

## 分析约束

`analysis-plan.json` 已在完整矩阵图像分析前登记：使用旧实验完全相同的冻结分析器、颜色处理、阈值、ROI 和采样方法，输入新建的独立 plain-scroll index。旧结果与旧 freeze 不改写。两张 light 可行性 REST/repeat 已先行查看，此事实明确披露；本轮属于校准，不能声称盲测。

去掉文字减少了已知混杂，不能保证私有材质适应相同。保留绝对 control/shape 误差、成对条件响应、原生 repeat 差异及实际公开主题。不能将差分曲线直接反推为唯一厚度、折射率或内部 shader，也不能将此单一尺寸、静态实验外推到所有控件与完整动作。
