# Pi 工具集 + 观测方案 三方评审汇总 — Round 3

> 评审日期：2026-07-29
> 评审对象：Pi 精简工具集（4 件）+ 双层额度 + 全维度观测
> A/B 用 `-r` 续接 round2 session（有宪法 v0.2 上下文），C fresh + 内嵌
> 三方判决：**均为「条件通过」**（无 PASS，无 REJECT）

## 一、三方判决

| 评审方 | 判决 | P0 | P1 | P2 | 致命缺陷 |
|---|---|---|---|---|---|
| A (opus4.8p) | 条件通过 | 2 | 4 | 3 | 无 |
| B (gpt5.6sol) | 条件通过 | 3 | 2 | 2 | 无 |
| C (cantus) | 条件通过 | 1（共振①） | 2（共振） | — | 无 |

**三方共振**：方向对（4 工具最小必要 + 强制埋点正解 + 复用到位），但"过度信任写下来的规则，低估运行期物理隔离"的毛病第三次复发——这次是配置数字不对齐 + 进程隔离没写清 + 顺序依赖倒置。

## 二、三方共振的必修问题（必须补）

### 共振 ①：预算双层配比错（sum < total，总池死条款）⚠️ 三方一致 P0
- **A**：50+100+20+10=180 < 200，20 次冗余去向未定义 → Pi 会学会挪用
- **B**：详细推演三种场景，证明当前配置退化为"取 min"，Pi 根本没有规划动机（直接每个跑满上限即可）
- **C**：明确要求"改为 sum(硬上限)≥总池 或 总池为唯一硬约束+上限为软护栏，二选一，不能双硬"
- **共识结论**：改成 `sum(硬上限) ≥ 1.5× 总池`（如每工具 100/200/50/30=380，总池 200），让总池成为真实约束，Pi 必须规划分配。**这是用户"让他规划使用"诉求的核心——当前配置下 Pi 无需规划。**

### 共振 ②：ledger 强制性不够（M2 破产）⚠️ A/B P0
- **A**：修 agent-loop:372 裸 SQL 只是治标。三条绕过路径：代码层（import DB client 直连）、文件层（工具产出落盘不走 ledger）、进程层（child_process curl 代替 webfetch）。要 DB trigger + fs hook + network command 三层封堵。
- **B**：更深——SQLite 文件在可写区，Pi 有 fs 权限就能 `sqlite3 delete`。正确方案是 **LedgerWriterDaemon 独立进程**（systemd 拉起，与 Pi 不同 uid，Pi 通过 unix socket 单向送 JSON，daemon 是唯一有写权限的）。
- **共识结论**：ledger 写入通道必须由 Pi 之外的独立进程持有。agent-loop 改的不是直接调 record()，而是 sendToLedgerDaemon()。**这是 M2 在观测层的硬要求。**

### 共振 ③：capability_produced 漏 skill 产出 ⚠️ B P1（A/C 隐含）
- **B 明确**：方案列了 webfetch/github/qoder 3 类，但 Pi 核心自进化产物是 **skill 迭代**（七步循环 Stage/Adopt），skill 变更根本不经过这 4 个工具，走的是 fs 写入——capability_produced 永远看不到 skill 产出。
- **B 建议**：新增虚拟工具 `skill_evolve`（不接外部 API，纯 ledger 埋点），SelfGrowthLoop 每次 Stage/Adopt 强制 emit。同理补 `memory_write`、`policy_update`。
- **用户原话验证**：用户明确说"生产了多少类型能力（skill/插件/代码/外部查询/开源库引入）"——**skill 是第一优先级，方案恰恰漏了**。

### 共振 ④：qoder 外部产出 lineage 追溯 ⚠️ A P0 / C 附加条件
- **A**：Qoder 返回的 code_artifact 是"另一个 agent 生成的代码"。攻击路径：Pi 通过 qoder_dispatch 让 Qoder 生成"看起来无害的 policy 改动"，Pi 把它作为自己的 proposal 提交——绕过 M4（实现器/验证器不同 provider，因为实现器变成了 Qoder）。
- **A 建议**：外部产出物只能进 `data/vault/external-artifacts/`（隔离区），不得进 staging/memory/proposal；若要进入自进化流程必须 Pi 本人重写并署名，且 Verifier 必须知情该 diff 有外部血统（ledger `lineage_tag: 'external'`）。
- **C 附加条件**：qoder lineage 必须落 Aetheris 审计轨迹，"一切自动化可审计"红线，非可选项。

## 三、C 独家发现（A/B 漏掉）

### C-1：Qoder 接法缺轮询兜底
- 架构真值要求 **REST + SSE + 轮询兜底**（2026-07-26 裁定），方案只写了 REST+SSE。
- SSE 断流时 Pi 会丢任务终态。必须补轮询兜底。
- **关键**：ECS 已有 SSE 消费器 + qoder-bridge.py 生产资产，**qoder_dispatch 必须复用该链路，不得在 Pi 里再写一套 SSE 客户端**（否则两处消费同一 session 事件流，状态分叉）。

### C-2：工具集与 SelfGrowthLoop 并行不融合
- 用户已裁定"现阶段是他进化，自进化后置"。工具集作为 **Pi Extensions 独立接入**（G6 流水线：规格→ZCode 实现→Mira 评审→用户批准），**不进 SelfGrowthLoop 闭环**——否则等于提前开自进化，违反裁定。
- ProactiveRunner 留 L2 合理：主动行为在质量门成熟前不应触发外部副作用。

## 四、A 独家发现（有价值的补充）

- **缺 system_query 工具**：Pi 做 evolution cycle 经常需要"今天几号/当前 UTC/额度重置时间"，没独立工具会 hack（webfetch worldtimeapi 浪费额度/瞎猜时间致 ledger 时间戳错乱）。建一个 zero-cost 的 system_query（时间/剩余额度/当前 tier）。
- **web_search 内部循环**：智谱 web_search 一次调用可能触发多次内部 tool_call（search→summarize→search），ledger 只记外层一次 → 实际 token 是记录的 3-5 倍。必须记 `inner_tool_calls: N`，QuotaTracker 按 N 扣。
- **web_search 绕过 webfetch 白名单**：web_search 返回 snippet 含任意外部域名，Pi 可从 snippet 读信息不需 webfetch。宪法要显式说明这个边界（web_search snippet 视为公开搜索引擎索引，不受白名单约束但受 taint check）。
- **第一性原理的更简路径**：只给 Pi 一个"提问"工具，harness 层路由到 webfetch/web_search/github/qoder，Pi 不知道底层。好处：Pi 学不到"某工具便宜可刷"。建议 L1 强制 Pi 每次工具调用前写 `reason: 为什么用这个工具`，21 天后看 reason 分布，若无意义规划理由则 L2 退化成单一接口。

## 五、B 独家发现

- **实施顺序依赖倒置**：A→B→C→D 表面独立，实际 C（dashboard）上线时 D（工具）数据还没进 → 用户看到空看板以为工具挂了。建议改 A+B+D 一体化上线，C 后置。
- **dashboard 缺拒绝/session/risk 三维度**：5 端点全是"成功调用"视角，缺 `/api/dashboard/rejections`（taint/预算/白名单/gate 四类拒因）+ group_by risk_level/session_id。尤其 M6 taint 命中率是"Pi 是否试图注入策略性记忆"的直接指标。
- **四维断路器尺度不一致**：宪法 §六三层（step cap/尝试上限/重复检测）是 per-cycle，本方案工具调用是 per-day。建议 §六改"每日工具预算超限→当日降 report-only（不停 evolution，只停外部工具）"。

## 六、修订行动项（按优先级）

### 🔴 P0 必修（二审前）
| # | 行动 | 来源 |
|---|---|---|
| 1 | 预算配比改 `sum(硬上限) ≥ 1.5× 总池`（如 380 vs 200） | A/B/C 共振① |
| 2 | LedgerWriterDaemon 独立进程（Pi 单向 emit，daemon 唯一写权限） | A/B 共振② |
| 3 | capability_produced 加 skill_evolve/memory_write/policy_update 虚拟工具埋点 | B 共振③ |
| 4 | qoder 外部产出 lineage_tag='external' + 隔离区 + Verifier 知情 | A/C 共振④ |
| 5 | qoder_dispatch 复用 ECS 现有 SSE 消费器 + 补轮询兜底 | C 独家 |

### 🟡 P1 严重（L1 首周补）
- 加 system_query 工具（时间/额度/tier，zero-cost）
- web_search 记 inner_tool_calls，QuotaTracker 按 N 扣
- webfetch 域名白名单放只读区 + 域名申请 skill 走 G6 人审 24h
- github_readonly 沙箱禁 npm/pip install，chmod 555
- dashboard 加 /rejections 端点 + group_by risk_level/session_id
- 实施顺序改 A+B+D 一体化，C 后置

### 🟢 P2 可上岗后补
- dashboard 加 /lineage/{capability_id} 纵向链路
- capability_produced 加 status(success/failure/partial)
- SelfGrowthLoop tick 前 ping kill-watcher 心跳
- qoder_dispatch 计费按 session_id 唯一（重连同 session 算 1 次）

## 七、ZCode 综合判断

三方质量极高，**全部条件通过，零致命缺陷，高度共振**。这轮评审的价值在于戳破了"方案看起来闭合实际配置不对齐"的表层闭合——尤其是预算双层配比（180<200 导致总池死条款，Pi 无需规划）和 ledger 强制性（代码约定≠M2 的进程隔离）。

用户的核心诉求"限定额度让他规划使用"在当前配置下**完全落空**——sum(180)<total(200) 让 Pi 直接跑满每个上限即可，没有任何规划博弈空间。这是必须修的 P0。

**建议路径**：
1. 修订方案补 5 个 P0（预算配比 / LedgerWriterDaemon / skill 虚拟工具 / qoder lineage / qoder 复用 SSE 消费器）
2. round4 二审（A/B -r 续接，C fresh）
3. PASS → 进实施（A+B+D 一体化，C 后置）

**或**：因 P0 都是"配置数字 + 进程隔离 + lineage 字段"的可直接修订项，不涉及方向推翻，可考虑"修订即实施"（补完 P0 直接开工，round4 与实施并行）。但这需要用户接受"实施时同步审查"的风险。

## 附：session_id
- A round3: `337332156435`（-r 续接）
- B round3: `337247830035`（-r 续接）
- C round3: `sess_00kpxyensjcw0p4asjj5`（fresh，重调成功；首次 timeout）
