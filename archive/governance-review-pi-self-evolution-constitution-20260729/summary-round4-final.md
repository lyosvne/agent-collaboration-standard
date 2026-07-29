# Pi 工具集 + 观测方案 v0.3 — Round 4 最终评审（三方 PASS）

> 评审日期：2026-07-29
> 评审对象：方案 v0.3（吸收 round3 的 5 个 P0 修订）
> 三方判决：**A PASS + B PASS + C PASS** ✅✅✅
> 项目状态：`PASS`（四轮评审闭环）

## 一、四轮评审历程

| 轮次 | 对象 | A | B | C | 结果 |
|---|---|---|---|---|---|
| round1 | 宪法 v0.1 | 条件通过 | 条件通过 | 条件通过 | 修订→v0.2 |
| round2 | 宪法 v0.2 | **PASS** | 条件通过(N1/N2) | **PASS** | L1 启动，N1/N2 作 L2 前置 |
| round3 | 工具集+观测方案 v0.2 | 条件通过 | 条件通过 | 条件通过 | 修订→v0.3（5 个 P0） |
| round4 | 方案 v0.3 | **PASS** | **PASS** | **PASS** | ✅ 可实施 |

## 二、Round4 三方判决

**三方一致 PASS，5 个 P0 全部 ✅ 补齐，零致命缺陷。**

### A (opus4.8p) PASS
- 5 个 P0 逐条 ✅，其中 P0②（LedgerWriterDaemon 独立 uid）评价"比我 round3 建议更狠，加分项"
- 零新矛盾（SelfGrowthLoop 走虚拟工具 emit 不双写；四维 OR 触发尺度混用语义清晰）
- 唯一残留 P2：daemon 挂了怎么办（需 watchdog + fail-closed），上岗后 30 天补
- 原话："三轮补丁走到这里，宪法+实施细则协议闭合，可以让 Pi 上线了"

### B (gpt5.6sol) PASS
- 5 个 P0 逐条 ✅，预算配比"规划语义成立"
- 2 个 P2 微调（不阻塞）：daemon fail-closed 显式化 + 虚拟工具豁免 per-day 断路器
- 原话："结论 PASS，L1 工具集可开工"

### C (cantus) PASS
- qoder 复用 SSE 消费器修订满足要求
- 原话："复用 qoder-bridge.py 不重造、轮询兜底作降级路径、session_id 唯一计费闭合了重复计费风险，v0.3 可进入实现"

## 三、5 个 P0 修订成效（round3 → v0.3）

| P0 | round3 问题 | v0.3 修订 | round4 判定 |
|---|---|---|---|
| ① 预算配比 | sum(180)<total(200)，Pi 无需规划 | sum(380)=1.9×total(200) + 单工具≤40% + 扣减顺序 + web_search inner_calls 归一 | ✅ |
| ② ledger 强制 | 修裸 SQL 只是治标，M2 破产 | LedgerWriterDaemon 独立进程(uid 隔离) + unix socket 单向 + DB trigger + fs hook + network 白名单 | ✅ |
| ③ skill 产出漏埋 | capability_produced 只有外部工具 | skill_evolve/memory_write/policy_update 三虚拟工具走同一 daemon | ✅ |
| ④ qoder lineage | 外部产出可绕 M4 | external-artifacts 隔离区 + lineage_tag + Pi 重写署名 + Verifier 知情 | ✅ |
| ⑤ qoder SSE 复用 | 只写 REST+SSE 缺轮询，可能重造 | 复用 ECS qoder-bridge.py + 轮询兜底 + session 30min + session_id 唯一计费 | ✅ |

## 四、残留 P2（上岗后 30 天补，不阻塞实施）
1. **LedgerWriterDaemon watchdog**（A/B 共识）：daemon 挂了 Pi 必须 fail-closed（拒绝执行工具，不 fail-open）。加 heartbeat + Pi 侧 5s 无响应自我降级 report-only + systemd Restart=always
2. **虚拟工具豁免 per-day 断路器**（B）：skill_evolve/memory_write/policy_update 是 zero-cost 内部产出，不受每日工具预算约束，仅外部工具停
3. **dashboard 加 /lineage 纵向链路**（A round3）：某 skill 从哪次 web_search→qoder→proposal→Adopt 的完整链路

## 五、最终方案 v0.3 要点（可实施）

### 工具集（4 件 + 3 虚拟）
- 外部：webfetch（域名白名单+只读区）/ web_search（智谱工具调用，inner_calls 归一）/ github_readonly（沙箱禁 package manager）/ qoder_dispatch（复用 ECS SSE 消费器+轮询兜底）
- 虚拟：skill_evolve / memory_write / policy_update（纯 ledger 埋点，走 LedgerWriterDaemon）

### 预算（四维 OR 触发）
- 三维 per-cycle（step cap 25 / 尝试上限 3 / 重复检测 n-gram>60%）
- 一维 per-day（工具调用：sum(硬上限)380 ≥ 1.9×总池200，单工具≤40%，超额降 report-only 不停 evolution）
- 虚拟工具豁免 per-day 断路器

### 观测（强制埋点 + 看板）
- LedgerWriterDaemon 独立进程（uid 隔离 + unix socket 单向 + DB trigger + fs hook + network 白名单三层封堵）
- tool_call_ledger 扩字段（model_id/tokens/cost_cny/capability_produced/session_id/lineage_tag）
- dashboard 6 端点（overview/tools/models/capabilities/budget/rejections）+ group_by risk_level/session_id
- capability_produced 6 类聚合（skill/memory/policy/webfetch/dependency/code_artifact）

### 实施顺序（A+B+D 一体化，C 后置）
- A 数据层（扩字段+修 bug+LedgerWriterDaemon）
- B 预算层（ToolBudgetPool+pricing-table+AlertService 接飞书）
- D 工具集（4 外部+3 虚拟+注册）
- 三者合并一体化上线
- C dashboard 后置（数据有了再做聚合）

## 六、ZCode 综合判断

**四轮评审闭环，三方 round4 一致 PASS。** 方案 v0.3 从用户原始诉求（全维度观测+工具集通道+额度规划）出发，经核验纠正三个假设（tokenplan 不附赠工具/zhipu-search 假联网/git 无 GitHub API），吸收两轮共 19 个 P0/P1 修订，最终达成协议闭合。

**用户核心诉求的达成验证**：
- "数据依赖 Pi 必然记录不依赖主观" → LedgerWriterDaemon 独立进程强制埋点（M2 守住）
- "限定额度让他规划使用" → sum(380)≥1.9×total(200) 让总池成为真实约束（规划博弈空间成立）
- "通向外接的通道工具集" → 4 件精简工具（非庞大列表）+ qoder 唯一可用调度
- "生产了多少类型能力" → capability_produced 6 类（含 skill 第一优先级）

**可进入实施阶段。** 按 A+B+D 一体化顺序，从数据层（LedgerWriterDaemon + 扩字段 + 修 bug）开始。

## 附：session_id（全部回填 index）
- A round4: `337332156435`（-r 续接）
- B round4: `337247830035`（-r 续接）
- C round4: `sess_00kpz140sighsri9gs9m`（fresh，极短重试成功）
- 项目 status: **PASS**
