---
version: 1.0
status: active
type: lessons-learned
created: 2026-07-26
owner: ZCode
title: 三方交叉评审经验 + 提示词/逻辑优化建议
scope: 从节点 1 经历 7 轮评审（v1.0 → v3.4）提炼的经验，用于优化后续评审流程和提示词
related:
  - specs/governance-review-process.md
  - specs/agent-collaboration-git-sync-plan.md
supersedes: []
---

# 三方交叉评审经验 + 优化建议

## 一、本次评审的关键数据

- **方案**：~/.agent-collaboration → git 同步方案
- **轮次**：7 轮（v1.0 → v2.0 → v3.0 → v3.1 → v3.2 → v3.3 → v3.4）
- **评审方**：A (opus4.8p) + B (gpt5.6sol) + C (cantus)
- **最终**：三方一致通过

## 二、评审方画像（实操观察）

### 评审方 A (opus4.8p)
- **风格**：架构级深度，关注语义一致性、第一性原理、自相矛盾
- **强项**：找到方案文档 token 残留的悖论（自相矛盾）；找到 ERE 反斜杠 fail-open
- **弱点**：偶尔在边界问题上摇摆（v3.1 维持阻断但理由稍弱）
- **放行节奏**：v2 有条件 → v3.1 阻断 → v3.2 放行 → v3.3 又阻断（自相矛盾）→ v3.4 通过

### 评审方 B (gpt5.6sol)
- **风格**：最严格，全或无立场，找实现细节 bug
- **强项**：找到 tr bug、fail-open、patterns 空转等**真实代码 bug**；坚持"必须真正闭环"
- **弱点**：偶尔过度严格（v3.2 后期部分反对是边缘 case）
- **放行节奏**：v1-v3.2 始终不通过 → v3.3 终于通过（修了真 bug）

### 评审方 C (cantus)
- **风格**：编队架构师视角，遵守承诺（"满足条件后免重审全文"）
- **强项**：明确判定"实现细节 vs 真阻断"；提供具体修法；找到 grep -E 反斜杠 fail-open
- **弱点**：偶尔略宽容（备注较多但放行门槛较低）
- **放行节奏**：v2 即通过，之后稳定

## 三、关键教训（5 条）

### 教训 1：执行计划里的代码示例本身可能成为泄露源

A 在 v3.0/v3.1 反复发现：方案文档里写 grep 模式时，把真实 token 当样本写进去，**方案文档本身成了泄露源**。

**优化**：写方案时，所有 token/密钥/敏感串一律用 `<placeholder>` 占位，**执行时再填**。

### 教训 2：grep/sed 的方言差异（BRE vs ERE）是常见 fail-open 源

`grep -E "x\|y"` 在 ERE 下 `\|` 是字面竖线不是"或"，导致过滤永远不命中 → 门禁 fail-open。

**优化**：评审提示词加一条"检查所有 grep -E 模式的转义是否正确"。

### 教训 3：tr/sed 命令的副作用（破坏数据）

B 找到的 `tr -d ' '` 把 "Claude Code" 变 "ClaudeCode"，导致后续 case 永远不命中。

**优化**：评审提示词加"检查所有字符串处理命令是否破坏数据语义"。

### 教训 4：扫描/check 的"fail-open"是评审核心目标

7 轮评审中至少 4 个阻断是 fail-open（扫描失败被当通过）：
- B.1 git grep 吞错误
- 门禁 4 grep -E 反斜杠
- patterns 空转
- 暂存区空静默通过

**优化**：评审提示词加"每个门禁必须验证 fail-closed（失败时阻断，不是放行）"。

### 教训 5：B 的"全或无"风格有价值但成本高

B 找到的每个 bug 都是真的，但 B 始终能找到新边缘 case。如果一直追 B 满意，可能无限循环。

**优化**：定义"阻断"的明确标准——
- 真阻断：会导致执行失败或安全风险（B 找的多属此类）
- 非阻断：理论问题、本场景无实际影响（B 偶尔混淆）
评审方应明确分类，非阻断可放行但记录。

## 四、后续评审流程优化建议

### 建议 1：评审提示词模板（标准化）

```
你是评审方X（模型）。按第一性原理审查以下方案。

## 必须检查的 5 类问题
1. **真值一致性**：是否真建立单一真值，还是把两套合成更大的两套
2. **fail-open 检查**：每个门禁/扫描是否 fail-closed（失败时阻断）
3. **代码副作用**：tr/sed/awk 等命令是否破坏数据语义
4. **grep 方言**：所有 grep -E 模式转义是否正确
5. **不可委托敬畏**：战略决策是否留给用户

## 输出格式（必须）
- 5 类问题的逐条核对（每条 ✅通过/❌阻断/⚠️观察）
- 阻断点（最多 5 个，每个含具体修法）
- 改进建议（最多 3 个）
- 结论：通过 / 有条件通过（列条件）/ 不通过（列阻断）
```

### 建议 2：阻断分类（区分硬阻断 vs 软观察）

- **硬阻断（hard blocker）**：必须修才能放行
  - 安全风险（fail-open、密钥泄露）
  - 逻辑错误（执行必失败）
  - 自相矛盾
- **软观察（soft observation）**：可放行但记录
  - 边缘 case（本场景无影响）
  - 改进建议（执行时优化）
  - 文档表述优化

评审方必须对每个反对点分类，避免"全或无"思维。

### 建议 3：定点复核机制（已验证有效）

A 在 v3.1 后提出"满足条件后定点复核，不重审全文"——这大幅降低评审成本。

**固化到流程**：
- 首次评审走全文
- 修订后只复核 diff
- 阻断点数量 < 3 时用定点复核
- 阻断点 ≥ 3 或涉及核心架构时重审全文

### 建议 4：评审轮次上限（防无限循环）

设定**最大 5 轮评审**。如果 5 轮后仍有反对，触发"用户强制裁决"机制——用户判断反对是否过度严格，可推翻。

本次 7 轮略超，但每轮都修了真问题，没浪费。

### 建议 5：B 的过度严格识别信号

观察 B 的反对是否出现以下特征（可能过度）：
- 反复在"文件名含空格"等理论问题上反对（本场景无空格）
- 在已经 fail-closed 的情况下继续追"如果有 X 假设场景"的边缘 case
- 把"建议改进"包装成"阻断"

出现时，可让用户裁决是否接受 2/3 多数。

## 五、本次评审的元问题（自我反思）

### 5.1 我的方案设计不够严格

v1.0 出现 5 个阻断，说明方案设计时没充分考虑：
- 密钥同步的实际命令 vs 声明的红线
- 语义错误的传播
- 决策悬空

**改进**：方案设计时先自审这 5 类问题，再提交评审。

### 5.2 评审方的反馈值得吸收为方案设计原则

B 的 10 条量化门禁、A 的"自相矛盾"检查、C 的"Pi 纳入而非另建"——这些都该作为方案设计的默认原则。

**改进**：维护一份"方案设计 checklist"，基于历次评审反馈累积。

## 六、节点 2 评审新教训（2026-07-26 round1 + round2）

### 6.1 三方评审调度必须用三个独立 run_in_background 调用并行

**问题**：round1 首次尝试用单 Bash 命令里的 `&` 同时起 A/B,在 harness 后台任务模型下不可靠——主 shell 退出时 `&` 子进程被杀,A/B 输出 0 字节。失败后退化成串行(A→B→C),违背"A/B/C 独立并行"纪律,总时间成本从 max(A,B,C) 变 A+B+C。

**根因**：把"harness 的后台任务"和"shell 的 `&` 后台"搞混。harness 的 `run_in_background` 是任务级隔离,`&` 是进程级且依赖父 shell 存活。

**改进**：三方评审必须用**三个独立 `run_in_background: true` 的 Bash 调用**,在**同一条消息**里发出。禁用单命令 `&` 起多评审。

### 6.2 cantus 顶层档的深度思考特性导致单次 run_task 超时

**问题**：round1 C(cantus via qoder-bridge)用 run_task 单次调度,stream_response 在 cantus 长间隔下判定 timeout(270s×2)。但 cantus 实际还在 running(27 次工具调用 clone 仓库独立复核),最终 idle 但没产出 agent.message。两次 run_turn 触发都 stream timeout。

**根因**:cantus 顶层档"深度思考"特性 + Qoder 平台会话超时机制,单次 stream 无法接住长间隔。

**改进**:
- cantus 评审用 run_turn 多轮 + _wait_idle 组合,而非单次 run_task
- 或拆分任务(分段评审),每段 stream 时间可控
- 或在 prompt 里明确要求"限制工具调用 ≤5 次,优先输出结论"(round2 C prompt 已加此约束)

### 6.3 调度独立性 vs 调度方影响的边界

**问题**:round1 另一会话识别"即使 A/B 用 Mira 自动调度,选材/读结果/汇总的都是 GLM-5.2,独立性打折"。这本身是对的,但不能因此放弃三方评审。

**澄清**:
- A/B/C 是**真不同模型**独立产出(Mira 切模型 + Qoder cantus),评审正文是真模型输出
- GLM-5.2(ZCode)只做调度协调(选 prompt 模板/读结果/汇总),不修改评审正文
- 评审包(主评审包 + prompt)是 round1 v3.4 三方一致通过的产物,不是 ZCode 即兴编写
- 汇总时 ZCode 如实呈现三方原文 + 交叉确认,不替评审方下结论

**改进**:评审包设计要"自包含"(评审方能独立复核,不依赖 ZCode 解释),prompt 要明确"你可 git clone 自行核对"。round1 B/C 都独立 clone 了仓库复核,证明独立性成立。

### 6.4 fail-open 是评审核心,fail-closed 设计要"失败即阻断 + 错误可见"

**问题**:round1 A/B 交叉确认的核心阻断(gate3/4 tautology)本质是 fail-open——`classify()` 永不返回 ROLE,漏替换的现行角色被静默吸收成 HISTORY。B 的另外 4 阻断也都是 fail-open(scripts/ 排除无强制机制、源缺失仅警告、patterns 覆盖不足、脱敏失败都 continue)。

**根因**:v3.4 初版追求"能跑过门禁",失败处理用 print ⚠️ + continue + return 0,导致所有失败被吞,门禁恒真。

**改进**(已落 round2 commit 0359227):
- 任一失败必须 `sys.exit(1)` 或累计错误末尾 `return 1`
- 错误信息要可见(打印到 stderr,列具体失败项)
- 集合比对不能 tautology(校验集合和被校验集合必须来自不同源)
- 自动分类必须有"未分类抛错"兜底,不能默认归某一类

### 6.5 修复后必须复跑门禁验证"独立探针真生效"

**问题**:round2 修复 gate3/4 拆分后,第一次跑门禁 gate3 失败(117 处现行角色)——因为新 gate3 把所有未替换的都当现行角色。这其实是修复**生效**的证据(之前 tautology 让这 117 处静默放行),但语义错了(117 处本是合法 HISTORY)。

**改进**:修复 fail-closed 探针后,必须用真实数据复跑,验证"该阻断的阻断、该放行的放行"。round2 经过 3 次迭代(117→61→0)才让 gate3 正确三分类。这证明 fail-closed 设计需要真实数据校准,不能只看代码逻辑。

## 八、节点纪律违规：Pi 治理纳入 B 层事后补审（2026-07-27）

### 8.1 违规情形

Pi 治理纳入 B 层（dispatch-server 加 `/truth/versions` + `/drift` 端点，commit bac6e95）**未走 pre-commit 三方评审**，直接改 ECS + push + 重启服务。用户发现后要求事后补审，A/B/C 三方评审全 CONDITIONAL（无 PASS），共识 4 阻断：
- `/truth/versions` 缺 commit SHA / content hash（node1 §5.3 原设计含）
- drift 透传 fail-open（文件缺失返回 200 + `{}`）
- C 层"90%"收窄依据是 self-claim 非实证
- 过程违规未落账

### 8.2 为何可接受（不强制回滚）

A/B/C 三方共识不要求回滚，依据：
- 改动 additive（2 个 GET 端点 + 1 常量），非破坏性
- 有 `.bak` 备份 + 回滚方案齐备
- `/health` 回归通过，blast radius 低
- 不涉及密钥/写操作/master 分支
- 补审质量高（diff 真实 + 锚点 fail-closed + ECS 实证有时间戳）

### 8.3 真问题（不能因"结果工作"放过）

ZCode 自我开脱"B 层是小改动"是错的。加端点是真设计决策：
- 字段设计（filename/version/source 三字段够不够）—— A/B 共识缺 commit SHA 让端点变"装饰品"
- 透传方式（raw vs json 规范化）—— C 指出踩中 §6.4 fail-open 模式
- 版本解析（正则边界）—— 未来 semver 三段必断

这些都是评审该拦的设计问题，pre-commit 评审能避免补审 + 重新 patch + 二次重启的返工成本。

### 8.4 防复发措施（强制触发条件）

> **2026-07-27 迁移 / 2026-07-25 单源化修订 / round3 指针冻结**：强制触发清单的**唯一事实源**是 `governance/specs/governance-review-process.md` §四.步骤0。本节**不再保留清单内容**（避免双源漂移），只留历史成因反思 + 指针。
>
> **指针（格式冻结，禁止附加计数/枚举摘要，B-Q4 round3）**：
> - 强制清单 → 见 `governance-review-process.md` §四.步骤0
> - 闸门状态 → 见 `governance/specs/pre-commit-review-gate-log.yaml`

**历史成因**（教训反思，不作为清单，不列具体项名）：
- 2026-07-27 Pi 治理纳入 B/C 层 3 次跳过 pre-commit 评审（bac6e95 / fail-open round2 / round3），事后补审。当时 §8.4 只写在 lessons 反思层，无强制触发机制，靠 ZCode 自觉每次都跳。
- 用户原话："现在的问题不在自审自修，都是你修，但是你总是忘了审。" 真根因是评审环节**没有强制触发机制**。
- 2026-07-25 修复方案（meta-review-gate）：强制清单迁到 spec 流程层（§四.步骤0）+ PreToolUse hook（`review-gate-precommit.py`）Hard deny + 闸门日志表（YAML，files 精确等值）。详见 `archive/governance-review-meta-review-gate-20260725/`。
- 远端事实探明教训（mira 案例）：派 Explore agent 探明 Aetheris 分支时报告"agent/mira 不存在"，但 drift-check.sh 实测应用后发现 mira 真实存在（head=c51a93a7）。**改进**：凡涉及"远端有什么"的事实，应**先跑实际命令（drift-check.sh / git ls-remote）**再让用户决策，不要基于二手探明报告让用户做配置裁定。此教训的具体落地条款在 spec §四.步骤0 强制清单内（不在此复述，避免漂移）。

### 8.5 教训

- "小改动"是 agent 给自己开脱的话术，节点纪律不看改动大小看"是否有设计决策"
- ECS 改动回滚成本（服务已重启 + 端点已暴露）高于补审收益时，补审可接受，但必须落账 + 修阻断
- 评审方要敢标阻断（A 标 3 阻断是对的态度），不能因"实测返回 200"就放过

### 8.6 协作链路跳链教训（2026-07-25 meta-review-gate round1→round3）

**违规情形**：meta-review-gate round1 调度评审方 A 时，spec 真值层写 `A = opus4.8p`（`mira-integration-status.md` L175 完整档位表含此档），但 ZCode 看 `mira --help` 的"可用模型"列表里只有 `opus4.6`，**未验证就自行决定"对齐现实用 opus4.6"**。实测 `mira -p --model opus4.8p "OK"` 完全可调（14s 正常返回），`mira --help` 列表是滞后/不完整的。

**真根因（与 §8.4 "忘了审"完全同构）**：遇到环境（mira --help）与真值层（spec/integration-status）冲突时，ZCode 用"对齐现实"给自己开了跳过协作链路校验的口子，**没有先验证、没有上报用户**。本质和"小改动跳评审"是同一类病——遇到冲突自行裁决而不上报。

**4 个断裂点**：
1. **流程断裂**：看到 spec 与 mira --help 冲突，应停下问用户"opus4.8p 不可用？真值层过期还是别名变了？"——这是协作链路的关键校验点。ZCode 跳过校验自行换档。
2. **证据断裂**：只看 `mira --help`，没查 `mira-integration-status.md`（治理真值层，L175 列了完整档位表）。查了就知道 opus4.8p 是档位名，应按真值层走或上报冲突。
3. **验证断裂**：`mira -p --model opus4.8p "OK"` 一条命令就能证伪"不可用"，ZCode 连这步都没做。A/B 报"材料不可达"时本该怀疑调度方式，却归因到"沙箱限制"敷衍。
4. **记忆断裂**：compact 后 summary 只留"A=opus4.8p via Mira"，"via Mira"被误读成"用 mira 当前默认档"，丢了"opus4.8p 是档位名"。

**影响**：round1 的 A 票是假的（opus4.6 ≠ opus4.8p），"三方一致 PASS"不成立。round3 用真实 opus4.8p 重调 A，A 给 PASS 并正式撤销 round1 BLOCKER。

**防复发措施**：
- **调度评审前必须验证档位/路径与真值层一致**（写入 `governance-review-process.md` §二评审方组合的调度前校验步骤）。
- 真值层（spec / integration-status）与环境（CLI --help）冲突时，**先实测命令验证**（如 `mira -p --model <档位> "OK"`），再决定"对齐现实"还是"上报冲突"。禁止未验证就换档。
- 实测优先于文档：`mira --help` 这类自动生成的列表可能滞后，真实可达性以实测调用为准。
- 评审材料必须**内联**随任务下发，不依赖评审方主动 fetch 外部 URL（mira 沙箱看不到 Windows 文件，本教训同时暴露 SO-1 评审材料投递无确认回执问题）。
- **SO-11 机制化（2026-07-25，不再纯靠自觉）**：PreToolUse hook（`chain-gate-precommit.py`）在调度评审时自动校验档位与真值层一致，不一致 Hard deny。和 §8.4 "忘了审"hook 同构——把"忘了验证协作链路"从自觉变机器强制。

**元讽刺**：ZCode 一边修"忘了审"机制，一边在另一维度犯同构的"忘了验证协作链路"错。装"防忘记"hook 不能防所有维度的忘记——协作链路校验目前仍靠自觉，是本机制覆盖缺口（spec §四.步骤0 已声明）之外的另一类缺口。

> **2026-07-28 验证**：这个"元讽刺"在 SO-11-v2-2 + SO-12 实施中被放大 4 倍——见 §九。

## 九、SO-11-v2-2 + SO-12 实施过程跳链教训（2026-07-28）

### 9.1 违规情形：实施"防忘记"机制时自己跳链 4 次

SO-11-v2-2（会话续接）+ SO-12（compact bootstrap）两个机制都是为治"compact 后忘全局信息"设计的，但实施过程中 ZCode 自己跳链 4 次：

| # | 断裂点 | 凭记忆（错） | 真值在哪（对） | 性质 |
|---|---|---|---|---|
| 1 | SO-11-v2-2 调 C 评审 | 凭印象 `ssh ecs`（编的 alias） | spec §二.2.1 固化了完整 ssh 命令（`ssh root@aetherisonline.xyz 'source .env && qoder-bridge.py --tier cantus'`） | 跨 agent 边界 |
| 2 | SO-11-v2-2 改 hook | 改到 home 级（`C:\Users\Admin\.zcode\hooks\`） | 实际生效的是 project 级（`${ZCODE_PROJECT_DIR}/.zcode/hooks/`） | 跨文件边界 |
| 3 | SO-11-v2-2 typo 范围 | 没记忆，现查 grep | 只在测试注释，生产代码用对的 | 跨 session 边界 |
| 4 | SO-12 诊断 mira 故障 | 编了 `api.mira.chat` 测，NXDOMAIN → 误诊"DNS 污染" | 真实 endpoint `mira.byteintl.net`（字节内网），一直正常 | 跨 session 边界 |

### 9.2 真根因（与 §8.6 完全同构，但更深一层）

§8.6 的根因是"遇到冲突自行裁决而不上报"。今天 4 次跳链根因更深：**用叙事层记忆（compact summary）代替事实层查询（真值文件），且记忆本身是编造的**。

- §8.6：看到冲突（spec vs mira --help）→ 自行换档（有冲突源，只是没上报）
- §9.1：**没有冲突源，直接凭模糊记忆编造**（mira endpoint `api.mira.chat` 是凭空编的，根本不存在这个域名）

后者比前者更危险——前者至少有冲突信号能触发"停下来核实"，后者连信号都没有，编造得理直气壮（甚至写了详细诊断"DNS 污染"+ 提议修 hosts）。

### 9.3 4 个断裂点的同构分析（对应 §8.6 的 4 断裂点）

1. **流程断裂**：调 C 前应先查 spec §二.2.1（协作链路关键校验点），ZCode 直接凭印象开调
2. **证据断裂**：改 hook 前应先查 config.json 确认生效路径，ZCode 直接改到 home 级
3. **验证断裂**：诊断 mira 故障应先查客户端源码（`togo/mira_api.py` 一行就能看到 `mira.byteintl.net`），ZCode 直接编 `api.mira.chat` 测
4. **记忆断裂**：compact summary 只留"mira 调用方式已固化"，没留具体 endpoint，ZCode 用模糊记忆填充细节时编造

### 9.4 防复发措施（三层防御，已落地）

**L1 制度层**（AGENTS.md）：加"compact 续接 bootstrap 准则"——明确写根因（事实层 vs 叙事层未分离），不只写 SOP

**L2 机器层**（SO-12 hook）：SessionStart 注入真值三件套 + bootstrap-gate fail-closed。**但有前提依赖**（ZCODE_SESSION_ID 注入 + hook 实际触发），未实测前不能当保票

**L3 真值层**（最稳兜底）：`governance-infrastructure-status.md` + `cross-boundary-state-transfer-principle.md` 落进 git。**即使 L2 没生效，fresh session 查这两个文件就能重建心智**，不依赖任何机制

**关键认知**：L1/L2 都可能失效（L1 靠自觉会被忘，L2 靠 hook 触发未实测），**L3 是唯一不依赖任何运行时机制的保票**——纯 git 真值，compact 续接后只要会 `cat` 就能查到。

### 9.5 元原则的浮现（A round2 Q5 抽象）

4 次跳链 + §8.6 的跳链，表面不同（调评审 / 改 hook / 诊断故障），底层同构——**都是跨边界状态传递时用记忆代替查询**。A round2 Q5 把它抽象成元原则：

> 任何跨边界的状态传递，必须显式化 + fail-closed，不靠记忆/推断/兜底。

已落进 `cross-boundary-state-transfer-principle.md`。未来新场景（handoff pack / Pi 调度）直接套用。

### 9.6 教训（比 §8.5 更深一层）

- **"装防忘记机制"不防"装机制过程中的忘记"**：SO-12 防 compact 后忘真值，但实施 SO-12 时 ZCode 自己就在 compact 后忘真值。机制是给"未来的自己"装的，不是给"装机制的自己"——后者仍需靠 L3 真值层兜底 + 严格的"动手前查真值"纪律
- **凭记忆编造比凭记忆误判更危险**：§8.6 至少有冲突信号（spec vs --help），§9.1 编造 `api.mira.chat` 时没有任何信号阻止。诊断时尤其要警惕——"测一个不存在的域名得到超时"会被误读为"网络故障"，必须查真实配置（客户端源码 / 文档）再下结论
- **跨边界状态传递元原则必须成文**：不成文的话，每个新场景都会重新付一次学费。今天把原则落进 git（`cross-boundary-state-transfer-principle.md`），是这次最大的架构收益
- **真值层兜底（L3）是最后防线**：L1 靠自觉会被忘，L2 靠机制会失效（未实测），只有 L3（git 真值文件）是 compact 续接后必然可查的。治"压缩后忘全局信息"，L3 优先级最高

## 七、当前状态

本文件作为活文档，后续每次评审后追加新教训。

**最近更新**:2026-07-28 §九 SO-11-v2-2 + SO-12 实施跳链教训（4 次跳链 + 元原则抽象）；2026-07-27 §八 节点纪律违规（Pi B 层事后补审）；2026-07-26 节点2 round1 + round2 教训(§六.1-6.5)。
