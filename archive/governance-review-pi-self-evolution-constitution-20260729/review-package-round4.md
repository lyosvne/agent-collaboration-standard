# Round4 修订对照 — Pi 工具集 + 观测方案 v0.3

> 2026-07-29，吸收 round3 三方评审 5 个 P0 + 关键 P1
> round3 三方均条件通过，零致命缺陷，高度共振
> 本文档是 round3 → v0.3 的逐条修订对照，供 round4 二审

## 逐条修订对照（round3 发现 → v0.3 怎么改）

### P0① 预算双层配比错（sum<total，总池死条款）→ ✅ 已修
**round3 共识**：50+100+20+10=180 < 200，Pi 无需规划（跑满每个上限即可）。用户"让他规划"诉求落空。
**v0.3 修订**：
- 每工具硬上限调到：webfetch 100 / web_search 200 / github_readonly 50 / qoder_dispatch 30 = **sum 380**
- 总额度池：**200 次/天**
- 比例：sum(380) = 1.9× total(200)，总池成为真实约束，Pi 必须规划分配
- 扣减协议明确（A 建议）：`check_tool_cap → check_total_pool → decrement_both`，硬上限第一道门，总池第二道门
- 加"单工具占总池比例上限 40%"（A 建议，防单一工具饿死其他）
- web_search 计量归一（A/B P1）：记 `inner_tool_calls: N`，QuotaTracker 按 N 扣（智谱内部 search→summarize→search 循环）

### P0② ledger 强制性不够（M2 破产）→ ✅ 已修
**round3 共识**：修 agent-loop:372 裸 SQL 只是治标。SQLite 在可写区，Pi 有 fs 权限能 delete。三条绕过路径（代码直连/文件落盘/child_process curl）。
**v0.3 修订**：
- **LedgerWriterDaemon 独立进程**（B 建议）：systemd 拉起，与 Pi 不同 uid，是唯一有 SQLite 写权限的进程
- Pi 通过 **unix socket 单向送 JSON**（sendToLedgerDaemon()），无直接 DB 写权限
- agent-loop.ts:372 改的不是调 record()，而是 sendToLedgerDaemon()
- DB 层 SQLite trigger 强制 INSERT 必须带完整字段（A 建议的兜底）
- fs hook（round2 N1 升级）：工具产出必须落 `data/vault/tool-artifacts/{tool_id}/{ledger_id}/`，无 ledger 行则无目录写权限
- network command 拦截（A 建议）：curl/wget/nc/ssh 走白名单（不只是写命令，读类网络命令也拦）
- **三层封堵**：DB trigger + fs hook + network command，缺一层即破

### P0③ capability_produced 漏 skill 产出 → ✅ 已修
**round3 B 明确**：方案只埋 webfetch/github/qoder，但 Pi 核心产物 skill 走七步循环 fs 写入，不经过工具。用户原话"skill 是第一优先级"恰恰漏了。
**v0.3 修订**：
- 新增 3 个**虚拟工具**（不接外部 API，纯 ledger 埋点）：
  - `skill_evolve`：SelfGrowthLoop 每次 Stage/Adopt 强制 emit，capability_produced = `{type:'skill_change', skill_id, version, diff_hash, gate_scores}`
  - `memory_write`：MemoryGovernance 每次写记忆 emit，`{type:'memory', category:user/agent/world, tokens}`
  - `policy_update`：EvolutionEngine 每次 commit emit，`{type:'policy', matter_type, version, lineage}`
- 这 3 个虚拟工具同样走 LedgerWriterDaemon，同样受预算约束（但不消耗外部额度，内部产出 zero-cost 计 internal 预算）
- dashboard /capabilities 端点按 capability_produced.type 聚合：skill_change / memory / policy / webfetch / dependency_research / code_artifact

### P0④ qoder 外部产出 lineage 追溯 → ✅ 已修
**round3 A/C 共识**：Qoder 返回的 code_artifact 是"另一个 agent 的代码"。攻击路径：Pi 让 Qoder 生成"无害 policy 改动"再自己提交，绕过 M4。
**v0.3 修订**：
- qoder_dispatch 的 ledger 必须带 `lineage_tag: 'external'`
- 外部产出物只能进 `data/vault/external-artifacts/`（**隔离区**，不进 staging/memory/proposal）
- 若要进入自进化流程：必须 Pi 本人重写并署名（lineage_tag 改 'pi_rewritten_from_external'），且 Verifier 必须知情该 diff 有外部血统
- Proposer/Verifier 读到 lineage_tag='external' 触发额外审查（M6 taint check 加强）
- 宪法 v0.3 §四新增 external-artifacts 隔离区定义

### P0⑤ qoder_dispatch 复用 ECS SSE 消费器 + 轮询兜底 → ✅ 已修
**round3 C 独家**：架构真值要求 REST+SSE+轮询兜底，方案只写了前两个。ECS 已有 SSE 消费器 + qoder-bridge.py，不能再写一套（状态分叉）。
**v0.3 修订**：
- qoder_dispatch **不在 Pi 里写 SSE 客户端**，复用 ECS 现有 SSE 消费器（`/opt/pi-orchestrator/extensions/feishu-bridge/qoder-bridge.py` 已验证可达）
- Pi 通过调 qoder-bridge.py（subprocess 或 HTTP）建 session + 接收结果
- 补**轮询兜底**：SSE 断流时，Pi 轮询 `GET /api/v1/cloud/sessions/{id}/events` 兜底取终态
- session 生命周期硬上限 30min（B P2：防"一个 session 挂一天"）
- 计费按 session_id 唯一（同 session 多次 SSE 重连同算 1 次，B P2）

## P1 关键修订（L1 首周补）

### system_query 工具（A 独家）
- 新增 zero-cost 工具：时间/UTC/当前 tier/各 provider 剩余额度/额度重置时间
- 防 Pi hack（webfetch worldtimeapi 浪费额度/瞎猜时间致 ledger 时间戳错乱）

### webfetch 域名白名单归属（A P1）
- 白名单文件放**只读区**
- 配"域名申请 skill"走 G6 人审 SLA 24h（超时 REJECT 不 APPROVE）
- web_search snippet 边界显式说明（B L6）：视为公开搜索引擎索引，不受白名单约束但受 taint check

### github_readonly 沙箱（A P1）
- clone 到沙箱，**禁 npm/pip install / 任何 package manager 执行**
- 只允许 grep/ast-parse/tree 结构分析
- clone 后立即 chmod 555（只读）

### dashboard 加拒绝维度（B P1）
- 新增第 6 端点 `/api/dashboard/rejections`（taint/预算/白名单/gate 四类拒因）
- M6 taint 命中率是"Pi 是否试图注入策略性记忆"的直接指标
- 每端点加 `group_by` 参数支持 risk_level/session_id

### 实施顺序改 A+B+D 一体化（B L3）
- 不再 A→B→C→D 独立 commit（C 上线时 D 数据没进 = 空看板）
- 改：**A+B+D 合并为"数据+预算+工具"一体化上线，C dashboard 后置**
- 或插 backfill 步骤：A→A'(backfill)→B→D(骨架)→D-live→C

## 宪法 v0.2 → v0.3 同步修订

### §六 预算（三维→四维）
- 原三层（step cap 25/尝试上限 3/重复检测）是 **per-cycle**
- 新增第四维"工具调用次数"是 **per-day**
- 交互明确（B 冲突2）：四维 **OR 触发**（任一超限即断路）
- 每日工具预算超限 → 当日降 report-only（**不停 evolution，只停外部工具**）
- 预算配比：sum(硬上限) ≥ 1.5× 总池（让总池成为真实约束）

### §十七 观测层（新增）
- **埋点强制化原则**：ledger 写入由 LedgerWriterDaemon 独立进程持有，Pi 只有单向 emit 权限
- 三层封堵：DB trigger（INSERT 必须完整字段）+ fs hook（工具产出绑 ledger_id）+ network command 白名单（curl/wget/nc/ssh）
- **看板只读**：dashboard API 只读聚合，不写
- capability_produced 覆盖 6 类：skill_change/memory/policy/webfetch/dependency_research/code_artifact
- 拒绝维度必观测：taint/预算/白名单/gate 四类拒因进 dashboard

### §四 新增 external-artifacts 隔离区
- `data/vault/external-artifacts/`：外部 agent（qoder）产出物隔离区
- 不进 staging/memory/proposal，进入自进化流程必须 Pi 重写署名 + Verifier 知情 lineage

## 工具集与 SelfGrowthLoop 关系（C 裁定）
- **并行不融合**：工具集作为 Pi Extensions 独立接入（G6 流水线：规格→ZCode 实现→Mira 评审→用户批准）
- 不进 SelfGrowthLoop 闭环（否则违反"现阶段他进化"裁定）
- ProactiveRunner 留 L2 合理（主动行为在质量门成熟前不触发外部副作用）

## 不变项（round3 已认可）
- 4 件工具选择（webfetch/web_search/github_readonly/qoder_dispatch）—— 三方认可最小必要
- 全维度观测方向（扩 ledger + dashboard）—— 三方认可
- Qoder 作为唯一 Pi 能直接用的调度 —— 三方认可
- 不做 mira/kimi（凭证红线）/ gh CLI / 看板前端 / tool_factory —— 维持

## 给 round4 评审方的问题
1. 上述 5 个 P0 修订是否补齐？逐条标 ✅/⚠️/❌
2. v0.3 有无引入新矛盾？（如 LedgerWriterDaemon 与 SelfGrowthLoop 写日志的冲突？四维预算 OR 触发的尺度一致性？）
3. 最终判决：PASS / 仍条件通过 / REJECT
