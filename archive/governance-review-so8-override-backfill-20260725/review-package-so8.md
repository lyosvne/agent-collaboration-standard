# 评审材料包：SO-8 override 补录强制校验

> 评审对象：本方案 4 处改动（hook + 单测 + YAML 注释 + spec）
> 评审性质：§四.步骤0 强制触发（循环闭合：本机制自身变更属强制评审对象）
> 评审日期：2026-07-25
> 触发依据：B round2 标的 SO-8 真阻断（"事后补退化为事后忘"）

## 一、背景

meta-review-gate round3 PASS 后，处理 B 在 round2 标的 SO-8：
> "override 补录强制校验——下次 pre-commit 触发时，hook 应检查上一次 override 是否已补录条目，未补录则 deny。否则'事后补'退化为'事后忘'。"

round3 override 机制仅靠 deny 消息提示，无强制。B 标真 fail-open。

## 二、方案（4 改动）

### 2.1 hook 加 override pending log + 强制校验
- 新增 `OVERRIDE_PENDING_FILE = ~/.zcode/hooks/.review-gate-override-pending.json`（本地状态，不进 repo）
- `append_override_pending(reason, filename, command)`：override 触发时追加 `{used_at_iso, used_at_ts, reason, filename, command_head}`
- `check_override_pending_backfilled()`：读 pending + 查闸门表 verdict=override + override_reason 非空
- `clear_override_pending()`：闸门表已有补录条目时清理
- main 改动：override 分支追加 pending；非 override 分支命中强制触发后先校验 pending

### 2.2 单测 5 case（全部 PASS）
- P1: override 触发 → 放行 + pending 写入
- P2: override 过期 + pending 未补录 → deny
- P3: 闸门表加 verdict=override 条目 → pending 自动清理（命令仍 deny 因 override≠PASS）
- P4: pending 不存在 → 正常放行
- P4b: 非 override 路径不生成 pending

### 2.3 闸门表 YAML 注释
补 `override_reason` / `override_date` 字段说明（verdict=override 时必填）+ hook 读取逻辑更新（SO-8 强制校验）

### 2.4 spec §四.步骤0 override 流程更新
详细说明 SO-8 闭环：pending log → 强制校验 → 补录后清理

## 三、要评审方回答的问题

### Q1：pending log 本地文件设计（不进 repo）
- hook 写本地状态是否合理？副作用？
- 不进 repo 意味着 drift-check 监控不到，覆盖缺口可接受？

### Q2：补录判定粗粒度
- "任意一条 verdict=override + override_reason 非空"就清理全部 pending
- 不要求精确匹配 pending 记录（避免 schema 复杂化）
- 风险：补一条假 override 条目就能清理所有历史 pending
- 防忘记模型下是否可接受？

### Q3：P3 case 语义
- P3 里闸门表加了 override 条目，pending 清理了，但命令仍 deny（因 verdict=override ≠ PASS）
- 这个语义是否正确？还是 override 条目应该算"已审过"放行？

### Q4：fail-closed
- pending log 损坏/丢失/被恶意删除的场景
- 当前：损坏时 deny + 提示清理；丢失时正常流程（P4）
- 是否够？

### Q5：整体
- SO-8 是否真消灭 B 标的 fail-open？
- 有无新引入问题？

## 四、验证证据

- 26/26 单测 PASS（原 21 + SO-8 的 P1/P2/P3/P4/P4b）
- YAML 合法
- 不动 ECS / 不动 ~/.zcode/cli/config.json
- 本地状态文件不进 repo（git status 干净）

## 五、红线遵守

- 改 .zcode/hooks/review-gate-precommit.py（治理基础设施）→ §四.步骤0 强制触发
- 改 spec §四.步骤0 + 闸门表 schema → 同上
- 不动 ECS / 不动全局 config
- pending log 在 ~/.zcode/hooks/ 不进 repo

## 六、调度前校验（§二.2.1，本次严格执行）

1. 档位真值层一致：A=opus4.8p / B=gpt5.6sol / C=cantus（spec §二）
2. 实测可达性：round3 已实测 22 档全可达 + qoder 三档全可达（间隔短不复测）
3. 冲突上报：无冲突
4. 材料内联：本次 prompt 全部内联（不靠文件路径，避免 SO-1 沙箱不可达问题）
