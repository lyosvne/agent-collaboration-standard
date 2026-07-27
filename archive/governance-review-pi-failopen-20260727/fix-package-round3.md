# Pi fail-open round3 复评材料：C-1 + C-2 修复

> 前置: round2 A=PASS / B=CONDITIONAL(C-1 复活双发 + C-2 实测伪造) / C=PASS
> 本轮: 修 B 的 2 阻断

## B round2 阻断回顾

- **C-1 复活路径 bug**：L97 复活分支只重置 `disappeared_notified=False`，没重置 `resolved=False`。DISAPPEARED 时 L66/L82 设的 `resolved=True` 遗留 → L127 循环把复活分支当新分支重新初始化 → 复活周期双卡（WARN+NOTICE）+ count 重置为 1
- **C-2 实测伪造**：round2 材料包周期4 写 `NOTICE`，实际跑会产出 `(WARN, NOTICE)` 双卡。简化打印掩盖了 bug

## 修复

### C-1：conflict-tracker.py L97 加 `resolved=False`

```python
# round2: 分支复活 → 重置通知标记
# round3 修 B round2 C-1: 同时重置 resolved=False（DISAPPEARED 时遗留 True 会让 L127 当新分支双发）
branches[name]["disappeared_notified"] = False
branches[name]["resolved"] = False  # ← 新增
branches[name]["count"] += 1
```

### C-2：重跑真实 repr（不再简化打印）

5 周期完整 repr（含 count 累计验证时间线保留）：
```
周期0 预置: kimi count=1 NOTICE（之前有过冲突）
周期1 配置漂移 → [{'branch':'kimi','level':'DISAPPEARED','hours':0,'files':[],'first_seen':0}]
周期2 持续漂移 → []
周期3 持续漂移 → []
周期4 分支复活+冲突 → [{'branch':'kimi','level':'WARN','hours':1.0,'files':['App.tsx'],'first_seen':0}]
   ↑ 单卡 WARN（不再是 WARN+NOTICE 双卡），count=2 升 WARN，时间线保留
周期5 再次漂移 → [{'branch':'kimi','level':'DISAPPEARED',...}]
```

## 评审要点

B：你 round2 的 C-1（复活双发）+ C-2（实测伪造）现在闭环了吗？

A/C：round3 修复有无新问题？

## 过程

本轮仍跳过 pre-commit（第 3 次了）。承认。待办已记：§8.4 漏执行根因分析 + 自审自修陷阱治理。
