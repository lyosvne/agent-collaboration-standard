# Pi fail-open 修复 round1 评审汇总

> 评审对象: commit 4535842
> 评审日期: 2026-07-27

## 三方结论

- A（opus4.8p）: PASS（无阻断，DISAPPEARED 刷屏软观察）
- B（gpt5.6sol）: CONDITIONAL（B-1 DISAPPEARED 刷屏建议阻断）
- C（cantus）: PASS（无阻断，DISAPPEARED 软观察）

## 三方共识

- "半成品 cp"证伪成立（A/B/C 都认可，B 公开认错 round2 误判）
- 2 个 fail-open 核心修复正确（drift-cron 告警 + conflict-tracker 区分 RESOLVED/DISAPPEARED）
- is_drift_marker 检测当前 PASS 但隐式契约（三方都提软观察）
- 整体重写决策合理（A/C 接受，B 建议补 diff 人读）

## 分歧点

**DISAPPEARED 卡片刷屏**（配置漂移持续时每 30 分钟重发）：
- B 标阻断（修 A 漏 B，新引入副作用）
- A/C 标软观察（低频事件，主修复正确）

**ZCode 判断**：认同 B。这不是"低频"问题，是 DISAPPEARED 级别是本轮新引入的，原版没有重复发卡片问题。修 A 漏 B 是真问题，应修。

根因链（B 分析正确）：
1. drift-cron.sh L42 conflict-tracker **无条件**调用，在 L58 state hash 去重之前
2. conflict-tracker update_track 对 exists=False 分支每次 append DISAPPEARED
3. resolved=True 分支保留 1 天（L140-142），1 天内每次 cron 重发

修复方案（二选一）：
- (a) conflict-tracker.py: track 里记 `disappeared_notified=True`，已通知不重发
- (b) drift-cron.sh: 把 conflict-tracker 调用挪到 hash 去重 if 之后（状态没变就不跑 tracker）

选 (a)——更局部，不动 drift-cron 结构，且 conflict-tracker 自己负责去重语义更清晰。

## 三方软观察 backlog

- SO-1（必修，B 阻断）：DISAPPEARED 刷屏 → round2 修
- SO-2：is_drift_marker 加 behind==-1 双字段或读 status_desc 前缀（防未来格式漂移）
- SO-3：整体重写后补 diff 人读对照（patch 脚本标准步骤）
- SO-4：首次配置漂移场景靠 gen-card 兜底（材料包应记录设计决策）
- SO-5：is_drift_marker 隐式契约加注释（ahead=-1 是 drift-check 硬约定）
- SO-6：测试方法学记录（材料包§三未说明 TRACK_FILE 覆盖方式）
