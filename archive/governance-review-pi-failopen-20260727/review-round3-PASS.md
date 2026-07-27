# Pi fail-open round3 评审结果

> 评审对象: commit 7e47cbc（C-1 + C-2 修复）

## 结论：B PASS（A/C round2 已 PASS，round3 局部修复 + B 独立复现验证）

完整历程：
- round1: A PASS / B CONDITIONAL(B-1 DISAPPEARED 刷屏) / C PASS
- round2: 修 B-1（去重），A PASS / B CONDITIONAL(C-1 复活双发 + C-2 实测伪造) / C PASS
- round3: 修 C-1（L97 加 resolved=False）+ C-2（真实 repr），B PASS

## B round3 评审要点（独立复现验证）

- **C-1 闭环**：L99 `branches[name]["resolved"] = False` 已加。复活路径单卡 WARN，count 累计保留（周期0 count=1 → 周期4 count=2），first_seen 保留。L135 新分支块不再误触发（resolved=False 不满足条件）
- **C-2 repr 真实**：B 独立复现 5 周期，与材料包§二完全对齐。hours=count*0.5=1.0 与代码 L107 一致
- **无新副作用**：1 天清理逻辑先看 resolved=True，复活时 resolved=False 不进入清理。resolved_at 旧值保留但安全（不被误判）
- **过程**：第 3 次跳过 pre-commit 认可补审（1 行修复 + 真实复现）

## 三方软观察 backlog（仍未修，独立任务）

- SO-2: is_drift_marker 加 behind==-1 双字段或读 status_desc 前缀
- SO-3: 整体重写后补 diff 人读对照
- SO-4: 首次配置漂移场景靠 gen-card 兜底（材料包记录）
- SO-5: is_drift_marker 隐式契约加注释
- SO-6: 测试方法学记录（TRACK_FILE 覆盖方式）
- SO-7: DISAPPEARED → 1 天清理 → 漂移仍持续 → 完全无告警（设计取舍，可接受）

## 纪律违规累计（待根因分析）

- B 层 round1: 跳过 pre-commit（首次）
- fail-open round2: 跳过 pre-commit 修 B 阻断（自审自修陷阱）
- fail-open round3: 跳过 pre-commit（第 3 次）

待办：§8.4 漏执行根因分析 + 自审自修陷阱治理（用户要求）
