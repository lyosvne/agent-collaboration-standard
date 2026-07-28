# 评审材料包 — Pi 自进化宪法 v0.1

> 评审对象：`docs/ground-truth/83-pi-self-evolution-constitution-v0.1.md` + `83-pi-resource-manifest-v0.1.yaml`
> 项目：pi-self-evolution-constitution，round1
> 日期：2026-07-29
> 目的：宪法层先于代码补丁评审。三方一致 PASS 后才允许进阶段 A（补代码缺口）。

---

## 一、目标映射表（governance-review-process §1.2）

| 交付内容 | 对应北极星条款 | 对应路线图 | 第一性原理检验 |
|---|---|---|---|
| Pi 自进化宪法（终极目标 + 边界） | §一终局（用户只定战略+确认，其余自动运转）| O2 执行闭环 | 让 Pi 自主跑，但边界硬隔离——从本质出发，不是堆功能 |
| 元原则 M1-M5（harness 非 weights / agent 外强制 / canonical 单一 / 验证器分离 / 只归档） | §五.1 从本质出发 / §三.3 git 真值 | O1 基座 | 从开源血泪教训提炼，不是凭空设计 |
| L1→L2→L3 渐进自治 | §五.5 执行不偏离 | O2 | 不一上来就 L3 无人值守，渐进式 |
| 可改区/只读区物理隔离 | §三.5 可制动 | O1 | 防 reward hacking 的结构性墙，非靠自觉 |
| kill switch 双层 | §三.5 可制动 | O1 | 用户始终能停，主权在本机 |
| 预算断路器（80%/100%/三层） | §三.5 可制动 / 资源主权 | O1 | 防无限循环烧钱 |
| 自进化日志规范 | §三.3 git 真值 | O1 | 全链路可追溯，防 Comprehension Debt |
| 每日飞书报告 + 失活报警 | §三.5 可制动 | O2 | 用户最少介入但始终知情 |

## 二、项目上下文摘要

### 2.1 用户与目标
- 用户：林于炜，飞书 CSM，非程序员懂架构。用 ZCode 做 AI 系统架构设计。
- 终局：让 Pi（Aetheris backend，ECS 常驻）实现自进化闭环——主动跑、自改能力（白名单内）、每天出报告、失活报警、自稳定进化。**用户不再深度介入成长，只看报告 + 异常时介入**。
- 用户原话（2026-07-29）："你充分调研我们的所有知识库的开源项目，所有的循环智能体设计，所有开源社区的自成长项目，基于Pi设计一个自成长闭环，确定好边界，给到它所有的充足资源，和充分的授权，把ECS的环境治理到最干净，然后让它自闭环就好，每天只需要出一份报告告诉我它成长了多少，更新了什么，有哪些忧虑。"

### 2.2 为什么现在做
- 用户判断：所有障碍（调度规则/数据通道/认证/凭证）已解决，但 Pi 还没"自己跑"——缺一个自进化闭环驱动它主动 tick。
- 之前的方案卡在"他进化优先 vs 自进化优先"的反复。用户 2026-07-29 明确推翻"他进化优先"，**现在就开自进化**。

### 2.3 真实问题
- Pi 的 `EvolutionEngine.runCycle()` 是孤儿方法，全仓非测试 0 调用——evolution 从未真正发生。
- `Proposer.generateImprovedPolicy()` 只产注释不产可执行 TS，且占位校验反向卡死占位提案（恒被拒）。
- 没有 SelfGrowthLoop 驱动 tick。Pi 只能被动响应 `handleUserIntent`。
- 飞书推送无 channel（AlertService 只推 console+file）。

### 2.4 本次评审范围
**仅宪法层**（ground-truth 83 两份文件）。不评审代码补丁（阶段 A 的 8 个缺口补完后单独评审）。
评审通过 → 阶段 A 补代码 → 阶段 B ECS 治理 → 阶段 C 部署。

## 三、北极星硬约束（评审红线）

- **§三.3 git 真值不可绕过** → 自进化日志 + lineage 全进 git，append-only 不可篡改
- **§三.5 可制动** → kill switch 双层 + 用户唯一裁判（宪法 §八）
- **§五.1 从问题本质出发** → 自进化的对象是 harness 不是 weights（元原则 M1）
- **§五.4 零认知负担** → canonical 单一真相（元原则 M3），不让 Pi 维护多套副本
- **§五.5 执行不偏离** → 宪法是 Pi 的上岗证，没有边界约束的自改进 = 漂移

## 四、第一性原理检验问题（请评审方回答）

1. **本质问题**：这套宪法是否真的解决了"让 Pi 自进化但不失控"？还是只是堆了一堆规则？有没有更简单的路径？
2. **元原则完备性**：M1-M5 这 5 条元原则是否覆盖了自进化的核心风险？有没有遗漏的致命模式？（如 Pi 通过合法手段拿到非法能力的路径）
3. **边界充分性**：可改区/只读区物理隔离 + 可写白名单机制，能否挡住所有 reward hacking / objective hacking 的路径？白名单可能被间接绕过（改技能里的 Bash 调用），设计时是否想到了？
4. **自治档位合理性**：L1→L2→L3 的升级条件和周期是否合理？L1 一周、L2 两周、L3 前置条件——会不会太保守拖慢成长，还是太激进？
5. **与 Aetheris 蓝图对齐**（C 专问）：这套宪法与 `Aetheris-Building-Blueprint-FINAL-v1.1.md` 的定位冲突吗？是否复用了现有资产（EvolutionEngine / Shield / QuotaTracker / ScheduleService / FeishuNotificationService）而非重造？

## 五、已知风险（评审方应知悉）

1. **调研库局限性**：宪法借鉴的 12 模式里，Aider/SWE-agent/Voyager/Darwin Gödel Machine/AutoGPT/BabyAGI/Reflexion 不是从 Codex 调研库一手研究，是通用知识。Codex 库对经典自进化项目零一手结论。
2. **ECS SSH 未完全验证**：之前实测 `ssh root@aetherisonline.xyz` 不通（没带 -i pem），spec 固化命令带 `-i ~/.ssh/aetheris-ecs.pem` 后本次可达性测试已通过。
3. **3 个阻塞项待用户输入**：真实额度上限 / 飞书群 chat_id / quota 占位值。
4. **两同名 MemoryGovernanceService 技术债**：补代码前必须先合并，否则会接错。
5. **Cognitive Surrender 风险**：自进化真正风险不只是 reward hacking，更是人类监督者逐步丧失判断力。宪法把每日报告的人类阅读写进强制项，但执行依赖纪律。
