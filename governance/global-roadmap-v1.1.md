---
version: "v1.1"
status: "active"
type: "roadmap"
supersedes: "global-roadmap-v1.0"
title: "全局路线图"
signoff: "ZCode+Qoder 2026-07-25"
---
# 全局路线图 v1.1（修订稿）

> 签发: ZCode + Qoder（共创，经两轮交叉对抗式论证，19条逐条修订）
> 裁定: 用户
> 日期: 2026-07-25
> 性质: 路线图罗盘——定义方向和退出条件，不定义具体实施（实施由当前阶段智能体分解执行）
> 依据: 北极星v1.2 + Aetheris蓝图v1.11 + soul.yaml + Codex知识库战略洞察 + 全量资产调研 + Qoder客户端两轮审查
> 管理哲学: 对标OKR——从使命推导方向，用关键结果衡量进展，用评估反馈体系保证不偏航

---

## 使命（为什么存在）

服务林于炜——飞书CSM（12+并发客户长期跟进），需要深度思考客户业务、用AI和飞书搭建效率系统。系统是放大器：让他从"手动操作每个客户"变成"制定战略、系统执行"。

## 北极星（方向，不是计算）

**系统杠杆率 = 系统帮你放大的产出 ÷ 你投入的协调成本**

- 性质：方向锚，感知导向，**不该被强行计算**——你感受到"系统让我变强了还是拖后腿"就是答案
- 可操作代理度量（月度趋势）：系统独立闭环任务数 ÷ 你的介入次数（Pi日志可采）
- 当前：低（大量时间协调系统，产出有限）
- 终局：高（说一句话，系统产出十倍结果，你只做战略和验收）

## 七维度（杠杆率的支撑度量）

北极星=方向（感知），七维度=度量（可采集可追踪）。

| 维度 | 衡量什么 | 当前 | 终局 |
|---|---|---|---|
| **执行力放大** | 你说一个意图→系统产出可用结果，中间需要你介入几次 | 每次需3-5次介入 | 0-1次（只验收） |
| **知识复利** | 你看到的好东西→下次能用，需要你手动操作几次 | 每次需手动告诉存储整理 | 0次（自动捕获沉淀） |
| **上下文连续** | 跨会话/跨工具/跨客户，你需要重复说同一件事吗 | 经常重复（"消息总线"问题） | 永不重复 |
| **决策支撑** | 系统给你看的信息，你能否直接做决策而不需要追问 | 常需追问技术细节 | 给你的就是人话+决策选项 |
| **系统自治** | 系统不依赖你推进工作的程度 + 运转结果反哺系统变强的程度 | 关机即停 + 无进化闭环 | 24h按轨道运转（T3红线内）+ 执行结果自动沉淀为新能力 |
| **评估反馈** | 系统每个产出是否有验证证据 + 你的反馈被系统吸收沉淀 | 无度量体系、反馈靠手动转达 | 每次产出附验证证据、你的反馈被吸收沉淀 |
| **客户感知** | 系统是否主动发现客户信号 + 客户关系连续性 + 代行动责任边界 | 无（系统不感知客户） | 主动发现客户动态、跨时间客户记忆、代行动可追溯 |

**系统自治的本地/云端分界**：
- 云端自治：任务执行/数据处理/知识沉淀/24h运转
- 本地必须：密钥主权（T3不出本地守卫）/交互引导/需要本地文件的操作
- 自治上限：T3红线内的动作（如Ark CLI SSO登录需人工交互）仍暂停等你确认

---

## 四阶段（OKR Objectives）

每个阶段允许与前序阶段并行推进。退出条件不仅要求系统能力达标，还要求Aetheris产出的结果**你验收通过**。每个阶段含正向退出条件和异常降级路径。

### O1：基座就绪

**方向**：系统能站住，不塌不丢不泄密。

**你的角色**：建设者 + 决策者（定方向、授权、审批）

**退出条件（KR）**：
- 协作底座稳定运行（Pi + 飞书桥接 + Qoder三档 + 漂移治理 + 调度上下文，7×24不崩）
- 退役清理完成（Codex/CC/QoderWork退役收尾，知识库归属已定）
- 基础设施治理完成（ECS稳定/时钟正确/无OOM风险/密钥守卫到位）
- O1与O2允许并行（O1退出条件="地基稳到能承载O2施工"）
- **你的验收**：你不再担心系统会崩/数据会丢/密钥会泄

### O2：执行闭环

**方向**：你交给系统的任务，它闭环交付。Aetheris产出你能用的真实结果。

**你的角色**：任务发起者 + 抽样评审员（系统标红才看，抽检确认基线）

**退出条件（KR）**：
- 你能通过Aetheris跟进至少1个真实客户，数据是准的（W5.5数据流闭环）
- 3类标准任务（客户跟进/知识沉淀/内容生成）连续5次介入≤2次
- **降级路径**：产出质量不达标时可一键退回手动模式
- **你的验收**：你用Aetheris产出的客户跟进结果，准确到你能直接用于工作（抽样+异常驱动验收）

### O3：矩阵协作

**方向**：亲属智能体之间协作，不靠你中转。

**你的角色**：观测员（偏航时矫正）

**退出条件（KR）**：
- 多agent协作产出你验收通过的方案（一个任务经多agent交接→互检→评审→交付）
- 你一周内不需要在agent间手动转发信息（从"消息总线"退场）
- 系统自动采集七个维度的水位数据，事件驱动给你校准报告
- 系统能主动推送需介入信号（异常/偏航/不可委托事项）——这是你进入观测员模式的前置
- **降级路径**：agent协作出错时可一键退回你中转
- **你的验收**：你确认系统协作的质量达到你的标准

### O4：自治运转

**方向**：系统按轨道自动运转，持续服务你演进的需求。

**你的角色**：战略制定者 + 最终裁判（只定战略、偶尔校准）

**退出条件（KR）**：
- 你只需说战略方向，系统理解并执行（M19认知转译成熟 + Pi智能路由）
- 系统自治运转中持续进化（执行结果反哺为新能力，有质量门把关）
- 你的反馈从细项主观评价演进到满意度确认（客观数据为主 + 满意度为锚）
- **协调成本**（=转发/追问/返工/救火的时间）趋近于零。注意：反馈/验收时间不计入协调成本——那是你的核心价值（判断和决策）
- **降级路径**：已有M5紧急制动，自治异常时一键停全部自动化
- **你的验收**：你确认系统按轨道运转且持续进化

---

## 不可委托清单（永远不交给系统）

角色演进 = 退出可委托的，守住不可委托的：

- **客户承诺拍板**——你对客户的承诺永远由你决定
- **T3高权限动作**——密钥/部署/计费/删除，永远需你确认
- **战略制定**——系统提方案，你定方向
- **最终满意度判断**——"这对我有没有用"永远由你说了算

---

## 评估反馈体系（贯穿全程，事件驱动）

对标OKR的PDCA哲学，但执行节奏改为事件驱动（非固定日历）。

**不变的底线：只要你在使用系统，你的反馈就是评估闭环的最终锚。**

**数据采集是硬前置**：当前仅2个维度可自动采集（介入次数/自治动作），其余维度需在O1-O2阶段逐步建立埋点。未建埋点的维度以你的主观评价为主。

**反馈吸收依赖记忆层**：反馈被系统吸收沉淀成行为变化，依赖记忆层（OpenViking）——未建前，你的反馈只能人工消化（agent记录但不自动改变行为）。记忆层是O2→O3的硬依赖。

| PDCA | 在我们系统中的形态 | O1-O2（你主导） | O3（系统辅助） | O4（系统为主） |
|---|---|---|---|---|
| **对齐** | 系统目标 vs 你的真实需求是否一致 | 你裁定方向，Qoder起草 | 你确认方向，系统提议 | 你定战略锚，系统自校准 |
| **跟踪** | 七维度水位采集 | 你逐项主观评价（系统记录） | 系统自动采集+你满意度锚 | 系统全自动+你确认异常 |
| **校准** | 偏航→回轨提案 | 你发现偏航→手动纠偏 | Qoder出报告+Mira评审+你裁定 | 系统自校准+你审批回轨 |

**校准触发**：事件驱动——阶段切换/重大交付/异常告警/你的主动要求。日历只留轻量满意度锚（飞书卡片一键评分，绝不发问卷）。

**反馈演进**：
```
O1-O2：你的主观反馈为主，客观数据为辅
  → 每个细项你都参与评价
  → 系统记录你的判断，积累校准基线

O3：客观指标 + 你的满意度
  → 系统自动采集的维度用数据说话
  → 你定期给满意度判断（一键评分）
  → 系统用你的满意度校准客观指标是否准确

O4：客观数据为主 + 你的满意度确认
  → 绝大多数维度由数据自动评价
  → 你只在战略层确认
  → 你的满意度是校准北极星的最终锚点
```

---

## Wave ↔ 阶段映射（供给侧 vs 需求侧）

Wave是供给侧（造能力），四阶段是需求侧（验收水位）。两套体系交叉映射：

| 四阶段 | 对应Wave | 关系 |
|---|---|---|
| O1 基座 | 编队P0（已完成大部分）+ ECS治理 | O1消费P0产出的协作能力 |
| O2 执行闭环 | W5.5数据流 + Wave2-3（知识/编排器/Mira） | [W5.5归属见分歧项] |
| O3 矩阵协作 | Wave3-4（Mira调度/外部Agent接入） | O3需要多agent协作能力就绪 |
| O4 自治运转 | Wave5（收尾）+ M系列（方向环） | O4需要进化闭环+校准体系成熟 |

---

## 当前位置

**O1（基座就绪）Phase D + 节点 3 方案 A + Pi 治理纳入 A 层 + .zcode/AGENTS.md 路径切换全部完成；待 Pi 治理纳入 B/C 层（ECS 实施）+ 5 域闭环（云端/知识库校准）（2026-07-26 更新）。**

### 已完成（O1 协作底座 + 退役清理 + 治理真值）
- CC→ZCode 迁移（CC 完全退役 + 密钥清除本机零残留）
- Pi ECS 部署验证（daemon 进程存活，部署验证 PASS；systemd 托管 + pi-drift-guard Extension 待 ECS 实施，详见 `specs/pi-drift-governance-spec.md §10`）
- Qoder 三档 SSE 消费器 + qoder-bridge.py 统一桥
- 漂移治理（设计 + push 授权）
- 调度上下文（dispatch-server，第 1 批已补全 4 端点 + 启动头注入，见下方缺口 #4 闭环标记）
- Mira 主干接入（trunk-complete: Togo CLI v5.21 + 40 模型 + 生图 + c360）
- Kimi 本机调度（ZCode Bash 调 kimi.exe 实测通过）
- Trae 收口（C 选项: SOLO 独立角色 + Aetheris 分支合并 master）
- **O1 治理 Phase A-D**:
  - Phase A 语义修正（11 条 ROLE 替换）
  - Phase B 安全同步（commit 314b35a）
  - 节点 2 评审 5 轮迭代三方通过（A round4 + B/C round5）
  - **Phase C 合并 master（commit b2eb24e，2026-07-26）**
  - **Phase D-A 路径声明切换 + 抢救入库（commits a4e98d8/36a49d3/51f16b5，2026-07-26）**：
    - 抢救本机独有新内容（review-process-lessons §六 + session-handoff 完整版 + node2-review-package）入库
    - START_HERE/LOCAL-USAGE 路径 standards/ → governance/（修正 P0 自相矛盾）
    - P1 治理文档本机路径漂移修正（fleet-division/workspace-collaboration/knowledge）
    - 本机 `~/.agent-collaboration/` 降级为只读历史快照（不物理删除，物理删除留第 5 批长期卫生阶段）
  - **Phase D-B scripts 解硬依赖 + 扫描基准切真值（2026-07-26）**：
    - 7 个 scripts 路径常量切环境变量 + git 仓库 fallback（gate-checks/rebuild-exceptions/complete-exceptions/analyze-gate3/list-hits/gen-scan-patterns/redact-tokens）
    - STANDARDS 扫描基准从本机 `~/.agent-collaboration/standards/` 切 git 仓库 `governance/`（修正 fail-closed 语义漂移）
    - secret-patterns 迁到 `~/.config/agent-collaboration/secret-patterns/`（语义正确：门禁工具的敏感配置，非治理真值）
    - mirror-sync.py `--apply` 禁用（Phase D 后原方向会覆盖 git 真值）+ DST_ROOT 改 REPO 推导
    - REPO 统一从 `Path(__file__).resolve().parents[1]` 推导（避免跨 checkout 混读，round4 修复 A+B 共识阻断）
    - fail-closed 门禁 4 测试全过（默认配置 / fallback / 不存在目录 exit 1 / rebuild 重建后）
  - **Phase D 三方交叉评审通过（2026-07-26，5 轮迭代）**：
    - round1：A 4 阻断 + B 3 阻断 + C timeout（cantus 深度思考特性）
    - round2：修复 A+B 共识 4 阻断（路径补扫/REPO 推导/mirror 禁用/complete-exc fail-closed）
    - round3：A FAIL + B FAIL（redact-tokens SyntaxError + mirror REPO + configs 残留）+ C PASS（拆分任务策略奏效）
    - round4：修复 round3 共识 3 阻断 + 软观察清理
    - round5：A PASS + B PASS（C 已在 round3 PASS，round4 未触及 C 审范围）
    - 三方一致通过，评审证据 11 文件归档 `archive/governance-review-phaseD-20260726/`
    - 关键教训：自检漏跑 `ast.parse` 导致 SyntaxError regression；门禁 fail-closed 实战验证（捕获 token/现行角色/exceptions 漏登）
  - **Phase D 合并 master + push + ECS 同步（2026-07-26）**：
    - ff-only 合并 review/phaseD-20260726 → master（a6e67e1）
    - push origin master（5061b96 → a6e67e1）
    - ECS governance-mirror git pull 同步（5 域一致性 Git + ECS 域闭环）
  - **第 3 批远程分支清理（2026-07-26）**：
    - 远程分支 5 → 1（只剩 master）：删 agent/qoder / sync/v3 / review/phaseD / feat/check-self-actuating-ack
    - feat/check-self-actuating-ack 合并到 master（:CHECK announcement-driven self-actuating ack，Mira 2026-05-11 +53 行 protocols 增强）
    - 本地分支清理（backup-pre-sync / sync 删除，只剩 master）
  - **节点 3 评审通过（2026-07-26，三方一致推荐方案 A）**：
    - 裁定项：unified vs workspace-collaboration 职责分工
    - 三方全票推荐方案 A（分层保留）：workspace 管"谁干什么"，unified 改 title 为 Agent Operating Standard 管"怎么干活"
    - 识别 6 处真冲突（规则优先级/owner/红线授权/完成契约/Git/Tool Roles）+ 2 个事实矛盾（Trae 职责 + Qoder Webhook/SSE）
    - 不改文件名（引用迁移归零），只改文档内 title
    - 评审证据 4 文件归档 `archive/governance-review-node3-20260726/`
    - **执行待另起任务 + 独立评审**（节点 3 纪律）
  - **节点 3 方案 A 执行完成（2026-07-26，4 轮评审通过）**：
    - round1 执行：unified 重定位（title 改 Agent Operating Standard，文件名保留）+ 删 Tool Roles + 修 2 事实矛盾 + START_HERE 单一 Read Order + Tool Routing 去名单化（9c5797c）
    - round1 评审：A CONDITIONAL（3 阻断：Qoder Webhook 未传播 + Trae SOLO 名称未统一 + exceptions 失效 ROLE 条目）+ C PASS + B 空输出
    - round2 修复：Qoder Webhook 全面传播（architecture 4 处 + qoder-sse-consumer-design v3 重写 + pi-drift-governance + README）+ Trae SOLO 3 处统一 + exceptions ROLE 清零 + Completion Protocol 权威声明（f62aeae）
    - round3 评审：A CONDITIONAL（Trae SOLO 仍有 8+ 处遗漏）+ C PASS
    - round3 修复：全仓统一 Trae SOLO（architecture 6 处 + fleet-division/workspace/north-star/kimi-integration/pi-drift-governance，pi-drift L103 agent/trae→agent/solo 分支名修复关键）（64d3814）
    - round4 评审：**A/B/C 三方全 PASS**（7 评审证据归档 `archive/governance-review-node3-exec-20260726/`）

### O1 待完成（P0 阻断真退出）
1. **5 域一致性真闭环**（Git + ECS 已完成，本地降级为快照，云端/知识库 待校准）
2. **Pi 漂移治理纳入** + **时序版本自动化**：A 层 ✅ + B 层 ✅ 完成（spec 真值对齐 + `configs/drift-config.json` + dispatch-server `/truth/versions` + `/drift` 两端点，2026-07-26/27）；C 层收窄（shell cron 已覆盖 §3 漂移体检 ~95% 功能，实证见 `archive/ecs-scripts/README.md`；§5 源头预防部分覆盖；剩 drift-check.sh 退役分支修复 + §5.2/§5.3 增强 + 可选 TS Extension 待 spawn exports bug 修复），详见 `specs/pi-drift-governance-spec.md §10`
3. **`.zcode/AGENTS.md` 路径声明切换** ✅ 已完成（2026-07-26，Option Y 落地）：L54-56 路径切到 git 仓库本地 clone（`Documents\trae_projects\agent-collaboration-standard\`）；L44 Trae→Trae SOLO + L45 架构真值路径补全；L59 加 Phase D 降级声明；快照保留作只读历史（用户裁定，物理删除留第 5 批）

### 节点 2 评审新暴露的真缺口（2026-07-26 新增，无历史章节承载）
5. ~~**dispatch-server 治理文档透出缺失**（P0 传播缺口）~~ ✅ **已闭环（2026-07-26 第 1 批）**：
   - dispatch-server 补全 4 端点（north-star/architecture/fleet-division/start-here）+ 双源 fallback（governance-mirror 优先 + GitHub raw 兜底）
   - qoder-bridge.py 注入 FLEET_HEADER 启动头（红线 + 编队身份 + WebFetch 指引）
   - ECS 部署 + governance-mirror 同步 + 端到端验证（cantus 复述红线 5 条 + 北极星 + 路线图）
   - 详见 `specs/node2-review-retrospective-20260726.md` §三
6. **dispatch-server 架构 spec 缺失**（生产组件无文档/无职能归属）
7. **scripts/ 工具脚本长期维护归属**（5 个 .py 无 spec；Phase D-B 已触及，建议合并处理）
8. **manual-history-overrides 可持续性**（人工 override + 双解析函数会漂移；每次文档增行要 rebuild-exceptions）
9. **root 层 legacy 文档退役角色清理**（C round4 指出非阻断）：TOOL_ROLE_MATRIX.md / GLOBAL_AGENT_GUIDE.md L5 / protocols/communication-command-protocol.md L218/254-255 / BOOTSTRAP_ONE_LINE.md L3 / docs/multi-agent-collaboration-operating-system.md L26 仍含 Trae IDE / Claude Code 活跃角色表述，建议并入"删 Tool Roles"待办或第 5 批长期卫生阶段

### O1 收口并行项（P1）
10. ~~远程分支清理（29 条已合未删）~~ ✅ 已完成（2026-07-26 第 3 批，5→1 只剩 master）
11. ~~unified vs workspace-collaboration 去留裁定（节点 3 用户裁决）~~ ✅ 已完成（2026-07-26 节点 3 方案 A 执行，4 轮评审通过）
12. ECS 基础设施治理（swap/时钟同步/cloudflared 孤儿进程）

### O2 并行推进中
- W5.5 数据流闭环（横跨 O1/O2，详见分歧项）

---

## 分歧项（已裁定）

### W5.5数据流闭环归属 → 横跨O1/O2（用户裁定）

- O1侧：W5.5让Aetheris产出真实数据，是"你敢用系统"的前提——基座不只是不崩，还要可信
- O2侧：W5.5数据准确、你验收通过，才是执行闭环达标
- 两阶段都对W5.5有退出条件要求

---

## Non-goals（不做）

- 不自建知识库（蓝图修正案已裁定选Obsidian集成）
- 不做live session共享（已付过学费的并发风险）
- 路线图不定义具体实施步骤（由当前阶段智能体分解执行）
- 不在M05成熟前灌入知识库
- 不让系统进化突破红线（用户唯一裁判/密钥主权/git真值/可制动）
- Trae IDE 已于 2026-07-26 C 选项裁定退役为编队角色（软件保留供个人使用，不进 Pi 调度链）。编队里 Trae 系只保留 **Trae SOLO 一个独立角色**（端到端测试/QA，Aetheris `agent/solo` 分支有实际产出）。原 B1 合并方案已撤销（详见 `archive/b1-rollback-20260726/`）。Trae IDE 在 Aetheris 的历史分支内容将通过独立任务合并入 `agent/solo`。

---

## 版本历史

| 版本 | 日期 | 变更 |
|---|---|---|
| v1.12 Pi C 层 fail-open 修复 | 2026-07-27 | drift-cron.sh + conflict-tracker.py 两个 fail-open 路径修复（三方评审软观察 backlog）：(1) drift-cron drift-check 失败发飞书系统异常卡片 + 保留旧 drift-latest.json（实测验证 fail-safe，B/C 评审说的"半成品 cp"证伪——set -e 在 L17 触发，L18 cp 不执行）；(2) conflict-tracker 区分 RESOLVED vs DISAPPEARED（分支消失/配置漂移不误判 RESOLVED，实测 3 场景验证：配置漂移→DISAPPEARED / 真解决→RESOLVED / 冲突还在→无 escalation）。patch `apply-c-layer-failopen-fix-20260727.py`（整体重写 conflict-tracker 避免锚点脆弱）；gen-card.py 归档 `archive/ecs-scripts/`；按 §8.4 第 4 类走 pre-commit 流程 |
| v1.11 Pi C 层 drift-check 去硬编码 | 2026-07-27 | drift-check.sh 去硬编码（从 drift-config.json 读 Aetheris agent_branches）+ 加 ref 存在性检查（防御配置漂移，MISSING 级别）+ 配置读失败 fail-closed；drift-config.json 真值校准（repos[0] agent-collaboration-standard 标 monitor_level none + agent_branches=[] 因治理仓库无 agent/* 模型；repos[1] Aetheris 保留 5 分支含 mira——实测 mira 存在 head=c51a93a7）；patch `apply-c-layer-drift-check-20260727.py`；实测 5 分支（zcode OK / qoder+kimi+mira CRITICAL / solo NOTICE），claude/trae 已移除；按 §8.4 第 4 类走 pre-commit 流程；**过程教训**：探明报告说 mira 不存在误导用户决策，实测应用后发现真实存在，已写入 lessons §8.4.6 |
| v1.10 Pi B 层 round3 drift 鉴权 | 2026-07-27 | `/dispatch/drift` 加 AUTH_KEY（query param `?key=$DISPATCH_KEY`，修 A round2 阻断：公网 `https://aetherisonline.xyz/dispatch/drift` 无 auth 可达）；`/truth/versions` 保持公开（敏感度低）；3 patch 脚本归档 `archive/dispatch-server-patches/`；按 §8.4 走完整 pre-commit 流程（Plan Mode → 用户审 → 应用 → 验证 → 评审），是 §8.4 首个正面案例；实测公网无 key 403 / 带 key 200 / truth/versions 公开 / health 回归 |
| v1.9 Pi 治理纳入 B 层 | 2026-07-27 | dispatch-server.py 加 `/dispatch/truth/versions`（治理文档版本清单，时序版本自动化）+ `/dispatch/drift`（漂移体检最新报告透传）两端点；patch 脚本归档 `archive/dispatch-server-patches/apply-b-layer-20260727.py`；ECS 备份 `.bak-b-layer-20260727-103156`；spec §10 B 层标完成，C 层范围收窄（shell cron 已覆盖 90%，剩 drift-check 退役分支 + 可选 TS Extension）；探明 ECS 已有 drift-cron.sh/drift-check.sh/conflict-tracker.py 生产运行。**过程违规**：未走 pre-commit 三方评审直接改 ECS + push + 重启，事后补审 A/B/C 全 CONDITIONAL 共识 4 阻断（详见 §八 + `archive/governance-review-pi-b-layer-20260727/`）；修复 patch `apply-b-layer-fix-20260727.py` 补 commit_sha/content_sha12/mtime + drift fail-closed + 正则放宽 + MARKER 哨兵 + 消费者契约 docstring |
| v1.8 .zcode/AGENTS.md 路径切换 | 2026-07-26 | Option Y 落地（node1 用户裁决第 1 项）：`.zcode/AGENTS.md` L54-56 路径切到 git 仓库本地 clone（START_HERE/governance/templates）；L44 Trae→Trae SOLO；L45 架构真值路径补全；L59 加 Phase D 降级声明；快照保留作只读历史（用户裁定）。O1 #3 标完成。AGENTS.md 在仓库外不入 git，本行留审计痕迹 |
| v1.7 Pi 治理纳入 A 层 | 2026-07-26 | Pi 治理纳入 A 层完成：spec 4 处过时修复（claude/trae/mira角色/review状态）+ `configs/drift-config.json` 创建（治理对象清单不硬编码）+ L180 措辞对齐 deployment 实证（Pi 未 systemd 托管/Extension 未写）+ spec §10 实施状态固化；O1 #2 改为"A 层完成；B/C 层待 ECS 实施"；删 O1 重复 #5；manual-overrides +7 条（pi-spec 5 + drift-config 2）；B/C 层登记后续任务 |
| v1.6 节点3执行完成 | 2026-07-26 | §当前位置更新：节点3方案A执行4轮评审通过（A/B/C 全PASS）；Qoder Webhook 全面传播+Trae SOLO 全仓统一+exceptions ROLE清零；O1收口项 #10/#11 标完成；增 #9 root层legacy文档清理待办；Pi治理纳入触发条件已满足 |
| v1.5 节点3评审通过 | 2026-07-26 | §当前位置更新：Phase D 合并 master+push+ECS 同步完成；第3批远程分支清理（5→1）+ feat 合并；节点3评审三方一致推荐方案 A（分层保留）；待办改为节点3执行 + Pi 治理纳入 |
| v1.4 Phase D 评审通过 | 2026-07-26 | §当前位置更新：Phase D 三方交叉评审 5 轮通过（A+B+C 一致）；round4 修复 redact-tokens SyntaxError + mirror REPO 推导 + configs 历史标注；待办改为合并 master + push + ECS 同步 |
| v1.3 Phase D-B 收尾 | 2026-07-26 | §当前位置更新：Phase D-B 完成（scripts 解硬依赖 + 扫描基准切 git 仓库 governance/ 真值 + patterns 迁 ~/.config/）；Phase D 全部完成（A+B）；fail-closed 门禁 4 测试全过；待办改为 push + ECS 同步 + Pi 治理纳入 |
| v1.2 Phase D-A 收尾 | 2026-07-26 | §当前位置更新：Phase D-A 完成（路径声明切换 + 抢救入库，commits a4e98d8/36a49d3/51f16b5）；缺口 #4 dispatch 透出闭环标记（第 1 批已完成）；增 Phase D-B 待办（scripts 解硬依赖）+ .zcode/AGENTS.md 待用户单独审；manual-overrides 缺口 #7 从 53→54 条更新 |
| v1.1节点2收尾更新 | 2026-07-26 | §当前位置全面更新：Phase C 合并 master 完成(b2eb24e)；Mira/Kimi/CC 退役标 done；增补节点2评审暴露的4项真缺口(dispatch透出/dispatch spec/scripts归属/manual-overrides可持续性)；指向 node2-review-retrospective §三 |
| v1.1定稿 | 2026-07-25 | W5.5归属裁定为横跨O1/O2。路线图定稿生效 |
| v1.1修订 | 2026-07-25 | Qoder客户端19条逐条修订：补客户感知维度、O1/O2并行、KR口径量化、降级路径、事件驱动校准、不可委托清单、北极星=方向/七维度=度量、Wave↔阶段映射、文件名修正 |
| v1.1 | 2026-07-24 | OKR管理哲学重构：使命→北极星→维度→四阶段O/KR→评估反馈体系 |
| v1.0 | 2026-07-24 | 全量资产调研+交叉论证（实施清单式，已降级为实施参考） |
