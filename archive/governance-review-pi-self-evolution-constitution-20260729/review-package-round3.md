# Round3 评审材料包 — Pi 精简工具集 + 全维度观测方案

> 评审日期：2026-07-29
> 项目：pi-self-evolution-constitution round3（前两轮审宪法 v0.2，本轮审实施细则）
> 范围：给 Pi 外接工具集 + 全维度观测看板 + 额度规划

## 一、用户需求原话

用户（林于炜）2026-07-29 提出：
1. 观测"只有一个报告，是否有数据看板从全维度分析"——用了哪些模型/做了多少任务/生产了多少类型能力（skill/插件/代码/外部查询/开源库引入）/ECS 实时健康
2. "这些数据依赖于 Pi 下意识地必然记录，不要依赖主观记录"——观测必须是工具链路强制副产物
3. "给 Pi 除了模型 token 以外的工具调用次数的能力"——工具调用也要预算
4. "把我们的智能体远程调用方式和使用矩阵给他使用手册，看看他能干出什么"——给通道工具集，让他探索
5. "给他一个通向外接的通道工具集，而非成品的交付物使用"——从消费成品→有工具箱的探索者
6. 后续澄清："工具不需要原来那套庞大的列表，就是联网工具 github 工具 关键的几个智能体的调度方式，参考智能体协作矩阵再给他增加一些 tokenplan 中附带的工具集就可以了。然后这些工具给他限定使用额度让他规划使用"

## 二、核验真相（纠正三个假设）

经代码库 + 协作矩阵核验：

| 假设 | 真相 |
|---|---|
| tokenplan 套餐附赠工具 | ❌ 4 provider（智谱/MiniMax/Kimi/火山）纯模型路由，联网/生图/代码执行都得自造 |
| 现有 zhipu-search 是联网 | ❌ 假联网（LLM 问答，名字误导，无真实 web_search） |
| 现有 git 工具能操作 GitHub | ❌ 只跑本地 git commit/push，无 GitHub API（无 gh/octokit） |
| Mira/Kimi 可给 Pi 调度 | ⚠️ 需迁 CLI+凭证到 ECS（cookie/OAuth 红线阻塞） |
| Qoder 可给 Pi 调度 | ✅ 唯一 Pi(ECS) 能直接用的（纯 REST+SSE，PAT 注入即用） |

## 三、方案（精简 4 件工具 + 双层额度 + 全维度观测）

### 3.1 工具集（4 件，非庞大列表）
| 工具 | 实现 | 额度 |
|---|---|---|
| webfetch | Node fetch 抓指定 URL，域名白名单，响应进 ledger | 按次 |
| web_search | 复用智谱 API web_search 工具调用（glm 模型支持） | 按 token |
| github_readonly | 现有 git 扩展：clone 公开 repo 到沙箱只读分析，不操作 PR/Issue | 按次 |
| qoder_dispatch | 调 Qoder Cloud REST API（建 session + SSE 接收），PAT 注入 | 按次 |

不做：mira/kimi 调度（凭证红线）/ gh CLI 完整 GitHub / tool_factory 动态注册 / 看板前端 / ProactiveRunner 主动 tick

### 3.2 额度（双层）
- **总额度池**：每日工具调用 N 次（占位 200）+ 复用现有 QuotaTracker 的 token 预算。Pi 自主分配，日报透出"今日额度分配"
- **每工具硬上限**（防耗尽）：webfetch 50/天、web_search 100/天、github_readonly 20/天、qoder_dispatch 10/天
- 实现：ToolBudgetPool + 扩 ToolCallLedgerService 按 toolId 聚合

### 3.3 全维度观测（数据层是根基）
- **扩 tool_call_ledger 字段**：+ model_id / tokens_in / tokens_out / cost_cny / capability_produced / session_id + idx_ledger_called_at 索引
- **修 bug**：agent-loop.ts:372 写裸 SQL 只填 5/11 字段 → 改用 toolCallLedgerService.record()
- **dashboard API**：/api/dashboard/{overview,tools,models,capabilities,budget}，聚合查询（按时间窗 group by）
- **呈现**：JSON API + 飞书多维表格接（不建前端页）

### 3.4 能力产出审计（capability_produced）
工具调用产出物化记录：
- webfetch → {type:'webfetch', url, bytes}
- github_readonly → {type:'dependency_research', repo, stars}
- qoder_dispatch → {type:'code_artifact', session, lines}
- 看板按 capability_produced.type 聚合统计

## 四、实施顺序（4 阶段独立 commit + 验证）
1. 阶段A 数据层修复（扩字段 + 修 bug）— 根基
2. 阶段B 预算层（ToolBudgetPool + pricing-table + AlertService 接飞书）
3. 阶段C 观测层（dashboard API）
4. 阶段D 工具集（4 件 + 注册）

## 五、宪法影响（需同步修订 v0.2 → v0.3）
- §五：补"主动信息获取"（webfetch/web_search 作为 observe 补充）
- §六：三维断路器补"工具调用次数预算"维度
- 新增 §十七（观测层）：埋点强制化 + 看板只读

## 六、给评审方的问题

### A（架构级）请回答：
1. 工具集 4 件是否最小必要？有没有该给没给的？webfetch 域名白名单 + qoder PAT 注入的安全边界够不够？
2. 观测层"强制埋点"（扩 ledger + 修 bug）是否真守得住 M2（agent 之外代码强制）？Pi 有没有绕过 ledger 写入的路径？
3. 额度双层（总额度池 + 每工具硬上限）有无绕过路径？Pi 能不能通过某种方式耗尽总额度池刷某个工具？

### B（逻辑/覆盖）请回答：
1. 预算双层有无逻辑矛盾？capability_produced 字段覆盖度（webfetch/github/qoder 3 类）够不够？skill 产出怎么记？
2. 与宪法 v0.2 §四（只读区：tool_call_ledger 进只读？）/ §六（预算）有无冲突？
3. dashboard API 5 个端点字段合理性？有没有该聚合没聚合的维度？

### C（架构契合）请回答：
1. Qoder REST+SSE 接法是否对齐架构真值的 pi-qoder-dispatch 设计？
2. 工具集是否真复用现有资产（zhipu-search/FeishuNotificationService/CliBridge）而非重造？
3. 与已建的 SelfGrowthLoop 是融合还是并行？ProactiveRunner 留 L2 合理吗？
