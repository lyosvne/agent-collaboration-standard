# Pi fail-open round2 复评材料：DISAPPEARED 去重

> 前置: round1 A=PASS / B=CONDITIONAL(B-1 DISAPPEARED 刷屏) / C=PASS
> 本轮: 修 B-1（conflict-tracker 加 disappeared_notified 去重）

## 修复

conflict-tracker.py 两处 DISAPPEARED 分支加去重：
```python
# 分支本次不在 report 里 → DISAPPEARED
if state is None:
    # round2 去重: 已通知过 DISAPPEARED 且仍 resolved → 不重发（防 30min 刷屏）
    if branches[name].get("disappeared_notified"):
        continue
    branches[name]["resolved"] = True
    branches[name]["resolved_at"] = now
    branches[name]["disappeared_notified"] = True  # 标记已通知
    escalations.append({"branch": name, "level": "DISAPPEARED", ...})
    continue
```

同处配置漂移分支（exists=False）也加同样去重。

**分支复活时重置 disappeared_notified**（允许"漂移→恢复→再漂移"再次告警）：
- 冲突还在分支（count+1 逻辑）：`branches[name]["disappeared_notified"] = False`
- 真解决 RESOLVED 分支：`branches[name]["disappeared_notified"] = False`

## 实测验证（5 周期模拟）

```
周期1 首次漂移 → [('kimi', 'DISAPPEARED')] ✅
周期2 持续漂移 → [] ✅（去重）
周期3 持续漂移 → [] ✅（去重）
周期4 分支复活+冲突 → [('kimi', 'NOTICE')] ✅（disappeared_notified 重置）
周期5 再次漂移 → [('kimi', 'DISAPPEARED')] ✅（重置后再告警）
```

## 评审要点

B：你 round1 的 B-1（DISAPPEARED 刷屏）现在闭环了吗？去重逻辑 + 复活重置是否覆盖所有场景？

A/C：你们 round1 是 PASS + 软观察。本轮加 disappeared_notified 有无新问题？

## 不修的（SO-2~SO-6 软观察，独立任务）

- SO-2: is_drift_marker 加 behind==-1 双字段
- SO-3: 整体重写后补 diff 人读对照
- SO-4: 首次配置漂移场景靠 gen-card 兜底（材料包记录）
- SO-5: is_drift_marker 隐式契约加注释
- SO-6: 测试方法学记录
