# SO-11-v2-2 评审 Round1 三方汇总

> 评审对象：Mira 会话归类 + session 续接（commit 317d213）
> 评审日期：2026-07-25
> 评审性质：§四.步骤0 强制触发（循环闭合：改 hook + spec + YAML）
> 评审方：A (opus4.8p) / B (gpt5.6sol) / C (cantus)

## 一、三方 verdict 一致

| 评审方 | verdict | 必修项数 | 视角 |
|---|---|---|---|
| A (opus4.8p) | **CONDITIONAL** | 3 | 架构级深度、第一性原理 |
| B (gpt5.6sol) | **CONDITIONAL** | 9（含 3 BLOCKER） | 结构化、覆盖度、规则冲突 |
| C (cantus) | **CONDITIONAL** | 5 | 编队主架构师、Aetheris 蓝图对齐 |

**三方一致结论：机制骨架方向正确，但有实质缺陷必须修后才能 PASS。不能 round1 直接合入。**

## 二、三方共识必修项（收敛后的 5 项，A/B/C 都同意）

### M1【项目识别 fail-closed】（A-M1 / B-必修3 / C-必修1 三方共识）

**问题**：`find_current_project` 兜底扫 archive 最近改动目录，是架构级反模式。最坏失败模式是**静默上下文污染**——扫到别的项目 → 查到错的 session_id → 强制 `-r` 到错误会话 → 上下文污染（比 deny 更糟，deny 可见，污染不可见）。

**修复**：
- `CURRENT_REVIEW_PROJECT` 未 export → **直接 deny** + 提示 `export CURRENT_REVIEW_PROJECT=<project_key>`
- **删除兜底扫描**（C 强调：其最坏结果是续接错误会话，比误拦更危险）
- 单测补：未 export 环境变量 → deny

### M2【round 标识显式参数】（A-M2 / B-必修1 BLOCKER / C-必修2 三方共识）

**问题**：`identify_current_round` 用 regex `re.search(r'\bround[_\s]*(\d+)\b')` 抓命令文本，`re.search` 返回**首个**匹配。真实评审 prompt 常含"round1 已修 → 本轮 round2"，会误抓 round1 → 查 round0 → 放行（绕过校验）。这是控制平面（调度元数据）与数据平面（prompt 内容）未分离。

**修复**：
- 引入环境变量 `CURRENT_REVIEW_ROUND=roundN`（或 `=N`），hook 优先读它
- 环境变量缺失 → **deny** + 提示先 export（不回退到 regex）
- regex 仅作**交叉校验**（环境变量与命令文本不一致时告警）
- 单测补：prompt 含双 round 字样 + 环境变量正确 → 查对 session_id

### M3【威胁模型分层 + 配置缺失 fail-closed】（A-M3 / B-必修7 / C-必修5 三方共识，C 修正版）

**问题**：当前"识别不出评审方 → 放行"、"无 round 标识 → 放行"、"session_continuity 节点缺失 → 放行"全是静默失败。§8.4 教训是"漏执行"，此机制在最容易漏的场景反而不拦。

**修复**（C 修正版，区分故障态与制动态）：
- 命令含 `mira -p` + 任一"评审方"字样 → 进入严格模式，`CURRENT_REVIEW_PROJECT`/`CURRENT_REVIEW_ROUND`/`dispatch_keyword` 三者缺任一 → **deny**
- 命令完全无"评审方"字样 → 视为非评审调用，放行（这才是真边界）
- `session_continuity` 节点**缺失/损坏** → **deny**（A-M3 方向）
- `session_continuity.enabled: false` **显式禁用** → 放行（保留紧急制动能力）
- lint 校验 `session_continuity` 必填字段（enabled/strategy/resume_arg/record_index），缺失 → lint exit 1

### M4【spec §二.2.2 范围表述修正】（C 新增 C1，A/B 未提但与 A-M3 边界声明同向）

**问题**：spec §二.2.2 说"被所有协作矩阵加载和遵循"，但实际执法点**只在 ZCode 的 .zcode hook**——Kimi/Trae/Pi 不加载 .zcode hooks。这是过度承诺。更深的问题：架构真值 §4.4 已锁定 Mira 终局由 Pi 调度，届时 ZCode hook 对 Pi 调度路径**零覆盖**，机制自动失效。

**修复**（改文字，零代码成本）：
- spec §二.2.2 准则首句改："调度 Mira 评审的调度方遵循；当前执法点仅 ZCode hook；Mira 调度权移交 Pi（架构真值 §4.4）时执法逻辑须同步移植"
- 登记为过渡态 + 迁移债务（运行时 session 状态最终归 Aetheris）

### M5【session 过期降级通道】（C 新增 C2，A/B 未提但属 BLOCKER 级——机制会卡死自己服务的流程）

**问题**：Mira session 会过期，过期后 `-r` 必失败。但 hook 仍强制 `-r`，唯一出口 `ARCHIVED` 语义不符（项目没 PASS）。这是一条**会硬卡死评审流程的死路**——机制自身卡死自己服务的对象。

**修复**：
- index 支持 `EXPIRED` 状态（或等价显式 override），过期后放行 fresh
- 过期续接时要求 prompt 内嵌上轮结论（补偿上下文，对齐北极星终局第 4 条"跨会话连续"）
- index 记录断链原因（哪轮为何 fresh）

## 三、A/B/C 分歧与互补

| 维度 | A | B | C |
|---|---|---|---|
| 项目识别 | M1 fail-closed | 必修3 同 | 必修1 同 + 强调静默污染比 deny 更糟 |
| round 抓取 | M2 显式参数 | 必修1 BLOCKER | 必修2 同 |
| 威胁模型 | M3 分层 | 必修7 节点 fail-closed | 必修5 修正版（区分故障/制动） |
| spec 范围 | 未提 | 未提 | **新增 C1**（过度承诺 + 迁移债务） |
| session 过期 | 建议项 B2 提及 `--fresh` | 未提 | **新增 C2 BLOCKER**（死路） |
| 配置健壮性 | 未提 | 必修5/7（节点缺失 fail-closed） | 必修5 同（修正版） |
| hook 共存 | 未提 | D6 CONFLICT-2 顺序 | 建议项 4（顺序是隐式契约） |
| 跨平台 | 未提 | D4 Linux CI | 未提 |

**ZCode 综合判断**：
- M1/M2/M3 是三方共识，**必修**
- M4/M5 是 C 独有但切中要害（M5 是 BLOCKER 级——会卡死流程），**必修**
- B 的 D4（Linux CI）/ D6（hook 顺序文档化）降为建议项（hook 只在 Windows ZCode 跑，Linux CI 非阻塞；hook 顺序已隐式正确，文档化是优化）
- B 的必修 9（AGENT_COLLABERATION typo）经查证**只在测试注释里**（生产代码用 AGENT_COLLABORATION_REPO 正确），**降为测试代码清理项**，不阻塞
- B 的必修 4（drift-gate schema 白名单）经查证**不成立**——drift-gate 不做 schema 白名单，只跑 lint 校验三处一致，session_continuity 加字段后 lint 已 exit 0

## 四、事实查证（ZCode 主动核对 B 的 factual 问题）

| B 的问题 | 查证结果 | 结论 |
|---|---|---|
| drift-gate schema 白名单是否含 session_continuity | drift-gate 不做 schema 白名单，只跑 lint | **不成立**（B 多虑） |
| AGENT_COLLABERATION typo 在哪 | 只在 test-session-gate.py:96 注释，hook 生产代码用 AGENT_COLLABORATION_REPO | **测试 bug，非 BLOCKER** |
| chain-gate 与 session-gate 执行顺序 | config.json PreToolUse 数组顺序：review-gate → chain-gate → session-gate | **已明确**（ZCode 文档约定数组顺序即执行顺序） |
| lint 是否校验 session_continuity 字段 | lint 只校验 reviewers/dispatchers/平台清单，**不校验 session_continuity** | **真问题**（M3 包含：lint 要补 session_continuity 必填校验） |

## 五、round1 结论

**三方一致 CONDITIONAL，不可 round1 合入。**

必修 5 项（M1-M5）必须修完才能走 round2 复核。修复涉及：
- session-gate-precommit.py（M1/M2/M3 代码层）
- reviewer-tiers.yaml（M3：session_continuity 加 lint 校验声明）
- scripts/check-reviewer-tiers-drift.py（M3：lint 补 session_continuity 必填字段校验）
- governance-review-process.md §二.2.2（M4/M5：范围表述 + 过期通道）
- archive/review-sessions-index.yaml（M5：支持 EXPIRED 状态）
- test-session-gate.py（补 M1/M2/M3 单测）

## 六、待用户裁决

修复后走 round2（用 mira -r 续接 round1 session，eat own dogfood 测试续接机制）。请用户确认：
1. 是否同意按 M1-M5 修复方案推进 round2？
2. M5（session 过期通道）是否本轮做，还是登记为 v2-3 独立任务？（C 标 BLOCKER，但实现成本中等）
3. M4 的迁移债务（运行时 session 状态迁 Aetheris）登记到哪个文档？（建议 docs/ground-truth 或 backlog）

## 七、原文索引

- review-A-round1.txt（opus4.8p，session_id 235302197011，74s）
- review-B-round1.txt（gpt5.6sol，session_id 222347143699，74s）
- review-C-round1.txt（cantus，sess_00kkzn1yvhlvkadsp5l1，128s）
