# SO-8 override 补录强制校验 round1 评审汇总

> 评审对象：SO-8 方案（hook + 单测 + YAML + spec）
> 评审日期：2026-07-25
> 评审方：A（opus4.8p）/ B（gpt5.6sol）/ C（cantus）

## 三方结论

- **A（opus4.8p）**：CONDITIONAL（补录判定 BLOCKER + fail-closed 分级 CONDITIONAL）
- **B（gpt5.6sol）**：CONDITIONAL（含 2 个 BLOCKER：粗粒度清理 + 新 fail-open）
- **C（cantus）**：CONDITIONAL（C1 匹配范围约束必须）

## 三方共识（必修，round2 处理）

### 共识 1：补录判定必须改为精确匹配（真阻断，三方一致）

**问题**：当前"任意 verdict=override + override_reason 非空 就清全部 pending" → SO-8 首次成功使用后**永久失效**（C 的 C1 最透：历史条目永远满足新 pending）。还允许"补一条假条目清 N 条历史欠账"（A/B 共识）。

**修复**（A 方案 A + B 共识）：
- pending 记录新增 `override_id`（uuid 或 used_at_ts 唯一标识）
- 闸门表 override 条目新增 `override_id` 字段（必填）
- 清理时逐条匹配 `override_id`，未匹配的 pending 保留
- 单测钉死：历史已有补录条目 + 新 override → 仍 deny（C1 case）

### 共识 2：override_reason 加 .strip()（B 标次级阻断）

`override_reason=" "` 不能绕过判定。`.strip()` 后非空才算。

### 共识 3：P3 语义正确，文档化即可（A 裁定）

override 条目是审计记录非审批通过，命令仍 deny（因 verdict=override ≠ PASS）。deny 消息要写清"override 条目仅完成审计补录，本次需另行获得 PASS 条目才能放行"。

## 三方分歧（ZCode 裁定）

### 分歧：pending log 缺失时的策略

- **B**：deny（视为未知状态，防恶意 rm 洗白）
- **C**：fail-open + 告警（防忘记机制不应打死正常 commit；新装 hook 首次跑 pending 不存在，B 方案会全员 deny）
- **A**：未直接表态，但提到"文件不存在应视为无 pending 正常放行（P4 case），不能 fail-closed"

**ZCode 裁定**：采用 C/A 方案（fail-open）。
- 理由：P4 case 已钉死"pending 不存在 → 正常放行"，是正确行为（新装 hook 不误伤）
- 缓解：在 spec + deny 消息显式声明"恶意 rm pending 可洗白，是 hook 结构性上限，防恶意靠 server 端 SO-9 兜底"（A 建议）
- B 担心的"恶意 rm"属恶意模型，超出 SO-8 威胁边界（防忘记非防恶意，round3 已声明）

### 分歧：fail-closed 分级（A 建议但未阻断）

A 建议：
- JSON 解析失败/截断 → fail-closed（已是当前实现）
- 文件不存在 → 正常放行（P4 已钉死）
- 权限不可读 → fail-closed + 提示检查权限

ZCode 采纳前两条（已是实现）。权限不可读 case 当前会走"文件不存在"分支（open 抛异常被 except 捕获返回 None）—— 实际行为是 fail-open。可接受（防忘记模型）。

## ZCode 综合判断

三方核心共识明确：精确匹配 + .strip() + 文档化 P3 语义 + 显式声明结构性上限。

### round2 必修
1. **精确匹配**：pending 加 `override_id` + 闸门表加 `override_id` 字段 + 逐条清理
2. **.strip()**：override_reason 判定加归一化
3. **C1 单测**：历史补录条目 + 新 override → 仍 deny
4. **P3 文档化**：deny 消息写清 override ≠ PASS

### round2 软观察（采纳）
5. **原子写**（A 建议）：pending 写入用 tmp + rename，避免断电损坏
6. **0600 权限**（B 建议）：pending log 创建时设 0600（Windows 下 chmod 可能无效，但 Unix 下有效）
7. **结构性上限声明**（A 建议）：spec 显式写"恶意 rm pending / --no-verify / 多机漂移 不在 SO-8 覆盖范围，靠 SO-9 server 端兜底"

### 不做（独立任务）
- B 的 T1-T6 单测里的 T4（pending 缺失 deny）—— 与 C 共识冲突，不采纳
- B 的 flock 并发 —— pre-commit 串行，无并发（A 共识）
- B 的 owner 校验 —— 边角，独立任务

## round2 计划

修 4 必修 + 3 软观察，全部低成本。改完按闸门规则快速复核（无需二轮全量评审）。
