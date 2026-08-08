---
version: 1.0
status: active
type: process-spec
created: 2026-07-26
owner: Mira + Trae
title: O1 全域一致性治理 — 评审流程规范
scope: 定义 O1 治理工程的强制交叉评审流程，覆盖计划审查 + 每个交付审查
related:
  - specs/o1-governance-plan.md
  - specs/agent-collaboration-git-sync-plan.md
  - standards/north-star-v1.2.md
  - standards/global-roadmap-v1.1.md
supersedes: []
---

# O1 全域一致性治理 — 评审流程规范

## 一、评审原则（对齐北极星 + 路线图）

### 1.1 第一性原理审查（北极星 §五）

每个评审方必须从问题本质出发：
- 这个交付解决了什么根本问题？
- 是否最直接路径？
- 从零设计会怎么做？
- 是否在叠加修补而非系统演进？

**反对**："惯例如此"、"之前就这么做"、"先这样以后再优化"。

### 1.2 北极星/路线图映射（每个交付必须附）

每个交付物必须附**目标映射表**：

| 交付内容 | 对应北极星条款 | 对应路线图 KR | 第一性原理检验 |
|---|---|---|---|
| ... | §三.X / §五.X | O1/O2/O3/O4 哪条 KR | 是否从本质出发 |

评审方按映射核对，**不偏离既定目标**（北极星 §五.5）。

### 1.3 不可委托清单敬畏（路线图）

评审方发现交付触及以下时**必须标红停止**：
- 客户承诺拍板
- T3 高权限动作（密钥/部署/计费/删除）
- 战略制定
- 最终满意度判断

这些只能用户裁决，评审方/执行方不得代决定。

## 二、评审方组合（三方交叉）

> ⚠️ **档位真值源（v2-1 round2，2026-07-25）**：本表格**仅为人读视图**，档位/调度 pattern 的**唯一机器源是 `governance/specs/reviewer-tiers.yaml`**。
> 若本表与 YAML 冲突，**以 YAML 为准**。改档位必须先改 YAML（hook 强制 lint，见下）。
> 本表不复述档位数值（防双写漂移），只列评审方 + 视角 + 调度方式概述。

| 评审方 | 平台 | 视角 | 调度方式概述（精确档位见 YAML） |
|---|---|---|---|
| **评审方 A** | Mira (Claude Opus Pro) | 架构级深度审查、语义一致性、第一性原理 | `mira -p --model <YAML.A.tier>` |
| **评审方 B** | Mira (GPT Sol) | 快速结构化审查、逻辑漏洞、覆盖度、规则冲突 | `mira -p --model <YAML.B.tier>` |
| **评审方 C** | Qoder (Cantus) | 编队主架构师视角、与 Aetheris 蓝图对齐、与现有架构契合 | `ssh ecs 'qoder-bridge.py --tier <YAML.C.tier>'` |
| **最终裁决** | 用户（林于炜）| 战略层、满意度、不可委托清单 | 飞书/直接对话 |

> 查精确档位 → `cat governance/specs/reviewer-tiers.yaml`
> 改档位 → 改 YAML，hook 自动跑 lint 校验三处一致（spec §二不再复述数值，无需手动同步）

### 2.1 调度前校验（防协作链路跳链，2026-07-25 round3 加 / SO-11 机制化）

**教训来源**：`review-process-lessons.md` §8.6——meta-review-gate round1 误把 opus4.8p 换成 opus4.6，未验证就跳链，round1 A 票作废。

**调度评审方前必须执行**（每次调度，不可省）：
1. **档位/路径与真值层一致**：查 `governance/specs/reviewer-tiers.yaml`（机器源，v2-1 起取代本节表格作 hook 真值层）+ `mira-integration-status.md` 平台清单，确认要调的档位名（如 opus4.8p）在真值层有记载。
2. **实测可达性**：真值层档位名用一条最小命令实测（A/B：`mira -p "OK" --model <档位> --output-format json` 看 `is_error: false`；C：`ssh root@aetherisonline.xyz 'cd /opt/pi-orchestrator/extensions/feishu-bridge && source /opt/pi-orchestrator/.env && python3 qoder-bridge.py --tier cantus "OK"'` 看 done 状态，详见下方 C 调用固化）。**禁止凭 CLI `--help` 列表判断可达性**（mira --help 列表滞后，实测优先于文档）。
3. **环境与真值层冲突时上报**：若实测发现档位不可用，**停下问用户**"真值层过期还是别名变了"，禁止未验证就换档自行"对齐现实"。
4. **材料内联**：评审材料必须**内联**随任务下发（写进 prompt 文本），不依赖评审方主动 fetch 外部 URL（mira 沙箱看不到 Windows 本地文件，是 SO-1 评审材料投递无确认回执问题的根因）。
5. **调度元数据内联注入（round2 M1/M2）**：调评审前必须 export 两个环境变量（一次性，不污染后续 shell），让 session-gate hook 识别当前项目和 round：
   ```bash
   CURRENT_REVIEW_PROJECT=<项目名> CURRENT_REVIEW_ROUND=<N> mira -p "评审方 A round<N> ..." --model opus4.8p [-r <sid>]
   ```
   - `CURRENT_REVIEW_PROJECT`：项目名（与 `archive/review-sessions-index.yaml` 的 `project` 字段精确匹配）
   - `CURRENT_REVIEW_ROUND`：当前轮号（如 round2 则设 `2`）
   - 缺任一 → session-gate hook deny（fail-closed，防兜底扫描导致的静默上下文污染）

#### C (cantus) 完整调度命令（2026-07-25 round2 固化，防调用方式断链）

C 的调度方式曾因未固化导致协作链路断裂（SO-11-v2-2 round1 调 C 时花时间排查）。本节固化真实路径：

```bash
ssh -i ~/.ssh/aetheris-ecs.pem root@aetherisonline.xyz \
  'set -a && source /opt/pi-orchestrator/.env && set +a && \
   cd /opt/pi-orchestrator/extensions/feishu-bridge && \
   python3 qoder-bridge.py --tier cantus "<task>"'
```

**关键事实**：
- ECS 主机：`aetherisonline.xyz`，用户 `root`，密钥 `~/.ssh/aetheris-ecs.pem`
- qoder-bridge.py 真实路径：`/opt/pi-orchestrator/extensions/feishu-bridge/qoder-bridge.py`（**不是** `/opt/pi/feishu-bridge/`——后者不存在）
- `QODER_PAT` 在 `/opt/pi-orchestrator/.env`，**永远不进 repo/commit/日志**（红线，AGENTS.md 强制）
- 调度前必须 `source /opt/pi-orchestrator/.env`（否则 qoder-bridge 报 "QODER_PAT 未设置"）
- 返回格式：stdout 含 `📤 发送到 Qoder [qoder-cantus/cmodel]` / `⏱ 耗时: Xs` / `🆔 会话 sess_xxx` / `💬 回复: <内容>`
- chain-gate 的 `dispatchers.qoder_cantus.invocation_pattern` 已对齐（匹配 `qoder-bridge(?:\.py)?\s+--tier\s+cantus\b`）
- C 无 session 续接机制（每次 new session），不记 session_id（见 §二.2.2 第 5 条）

**SO-11 机制化（2026-07-25，本节约束不再纯靠自觉 / v2-1: YAML 单源）**：
- ZCode 应用层 PreToolUse hook（`~/.zcode/hooks/chain-gate-precommit.py`）在 `mira -p` + 评审关键字 / `qoder-bridge --tier cantus` 调度评审时，自动校验 `--model` / `--tier` 与 `reviewer-tiers.yaml` 一致
- 不一致 → **Hard deny** + 提示真值层期望档位
- 评审方识别靠 prompt 里的"评审方 A/B/C"显式标注（dispatch_keyword，不能用档位名隐式识别，防循环）
- 真值层 YAML 解析失败 → fail-closed deny
- 旁路健康检查：YAML 的 A/B 档位必须在 `mira-integration-status.md` 平台清单内（防 YAML 与平台能力漂移）
- 紧急场景（真值层过期）写 `~/.zcode/hooks/.chain-gate-override.json`（30 分钟窗口），但需先问用户
- 威胁模型：防忘记（用默认档 / 凭 --help 换档），不防恶意（改 prompt 措辞绕关键字识别）—— 与 review-gate 同边界
- **改档位流程**：改 `reviewer-tiers.yaml` + 本节表格 + `mira-integration-status.md` 三处同步，跑 `scripts/check-reviewer-tiers-drift.py` 校验

### 2.2 会话归类与续接（2026-07-25 round1 加 / round2 M1-M5 修复）

> ⚠️ **范围声明（round2 M4，C round1 指出过度承诺）**：本准则的**执法点仅 ZCode 应用层 hook**（`~/.zcode/hooks/session-gate-precommit.py`）。Kimi / Trae / Pi 不加载 .zcode hooks，本准则对它们是"应遵循"而非"被强制"。架构真值 §4.4 已锁定 Mira 调度终局由 Pi 接管——届时 ZCode hook 对 Pi 调度路径**零覆盖**，执法逻辑须同步移植到 Pi Extension（登记为迁移债务）。

**用户需求原话**："将本项目所有的评审的 Mira 调用全部归类为一个项目，后续在同一个会话中调用 Mira CLI 让会话有上下文，这个要求加入调度准则被所有协作矩阵加载和遵循。"

**实测验证（2026-07-25）**：mira `-r <session_id>` 跨进程续接可用——
- 新进程 `mira -p "代号？" -r <round1_session_id>` 能精确回忆 round1 设的上下文
- 同档续接可用（opus4.8p round1 → opus4.8p round2）
- session 至少几小时内不过期（长时效待观察，独立任务，M5 提供过期降级）

**准则**：
1. **归类**：本项目所有评审的 Mira 调用按评审对象归类（如 meta-review-gate / so11-chain-gate 各一个项目），登记在 `archive/review-sessions-index.yaml`。新评审项目启动时追加 entry。
2. **续接**：同一评审项目内 Mira A/B 调用，roundN 必须用 `-r <roundN-1 的 session_id>` 续接前一轮上下文。session_id 从 `review-sessions-index.yaml` 的 `reviewer_sessions.{A,B}.round<N-1>` 字段读。
3. **记录**：每轮 mira 调用完成后（mira json 输出的 `session_id` 字段），立即回填到 `review-sessions-index.yaml` 对应 `reviewer_sessions.{A,B}.round<N>` 字段。
4. **归档**：评审项目 PASS 后，`review-sessions-index.yaml` 该 entry 的 status 改 `ARCHIVED`，session 不再续接（新项目开新 session）。
5. **C 例外（能力驱动表述，round2 M2 改）**：qoder-bridge（评审方 C）无 `-r` 续接机制（每次 new session）。准则的真实目标是**上下文连续**（北极星终局第 4 条），`-r` 只是手段之一。C 改用"prompt 内嵌上轮结论摘要"作上下文补偿——C 从"豁免"改为"替代实现"。
6. **历史项目**：2026-07-25 机制建立前的评审项目（meta-review-gate/so8/so11/so11-v2-1 等）session_id 未记录，status 标 ARCHIVED，不补录。
7. **过期降级（round2 M5 加，C round1 指出 BLOCKER）**：Mira session 可能过期，过期后 `-r` 必败。此时 index 的 `expired_rounds` 列表登记该轮（如 `expired_rounds: [1]`），hook 放行 fresh 调用，但**评审 prompt 必须内嵌上轮结论摘要**（补偿上下文）。index 记录断链原因。封死"过期 session 硬卡死评审流程"的死路。

**机制化（session-gate hook，round2 M1-M5）**：
- ZCode 应用层 PreToolUse hook（`~/.zcode/hooks/session-gate-precommit.py`）在 mira 评审调度时强制续接。
- **M1（项目识别 fail-closed）**：`CURRENT_REVIEW_PROJECT` 环境变量未设 → **deny**。删兜底扫描（最坏失败是续接错误会话的静默上下文污染，比 deny 更危险）。
- **M2（round 显式参数）**：`CURRENT_REVIEW_ROUND` 环境变量未设 → **deny**。命令文本里的 round 号仅作交叉校验 warn（prompt 可能描述历史 round），不作判据。
- **M3（配置缺失 fail-closed + 威胁模型分层）**：`session_continuity` 节点缺失/损坏/`enabled` 非 bool → **deny**（防配置删除即绕过机制）。但 `enabled: false` 显式禁用 → 放行（保留紧急制动）。命令完全无"评审方"字样 → 非评审调用，放行（真边界）。
- **M5（过期通道）**：roundN-1 在 `expired_rounds` 列表 → 放行 fresh + stderr 提示"prompt 必须内嵌上轮结论"。
- **既有校验保留**：有 roundN-1 sid 且未用 `-r` → deny + 提示正确 id；`-r` id 不匹配 → deny；首轮/归档/无记录 → 放行。

**调度元数据内联注入约定（M1/M2）**：调评审前必须 export 环境变量（一次性，不污染后续 shell）：
```bash
CURRENT_REVIEW_PROJECT=<项目名> CURRENT_REVIEW_ROUND=<N> mira -p "评审方 A round<N> ..." --model opus4.8p [-r <sid>]
```

**迁移债务（round2 M4 登记）**：本机制是过渡态。运行时 session 状态（session_id / round / expired_rounds）终局归 Aetheris 运行时真值层，git 只留评审证据归档。迁移登记见后续 v2-3 任务（独立任务）。

**为何重要**：之前每轮 mira 调用都是无上下文 fresh，导致评审方（尤其 B 结构化挑漏）重复指出已修问题，成本高。续接后 A/B 有项目内记忆，专注增量。

## 三、评审节点（4 个强制节点）

### 节点 1：治理计划本身（启动前）
- **评审对象**：`o1-governance-plan.md` + `agent-collaboration-git-sync-plan.md` + `governance-review-process.md`（本文件）
- **门槛**：三方一致通过才启动执行
- **分歧**：列三方观点 + ZCode 判断，上报用户裁决

### 节点 2：阶段 1 同步结果
- **评审对象**：local → git 同步后的实际状态（git diff + 文件清单）
- **重点**：是否丢失内容、是否误带密钥、是否破坏 git 已有内容（protocols/knowledge 等）
- **门槛**：三方一致通过才进入阶段 2

### 节点 3：阶段 2 文档去留决策表
- **评审对象**：每份冗余/冲突文档的去留决策（合并/删除/重写/保留）
- **重点**：决策是否符合单一真值原则、是否丢失关键信息、是否对齐北极星
- **门槛**：三方一致通过 + **用户逐份确认**（战略制定不可委托）

### 节点 4：阶段 3 重构后文档
- **评审对象**：语义重构后的每份文档（合并版/重写版）
- **重点**：是否丢信息、是否引入新冲突、是否真的消除冗余
- **门槛**：三方一致通过才进入阶段 4

## 四、评审流程（每个节点统一执行）

### 步骤 0：pre-commit 评审前置闸门（强制触发）

**强制触发条件**（任一命中必须先走三方评审，PASS 后才能改 ECS/写 patch 脚本/scp 部署）：

| # | 触发类 | 描述 |
|---|--------|------|
| 1 | dispatch-server.py | 改 `/opt/pi-orchestrator/extensions/dispatch-server.py`（治理契约对外接口） |
| 2 | systemd unit | 改任何 ECS systemd 服务文件 / `.service` unit |
| 3 | 端点路由 | 改 dispatch-server 端点（加/改/删路由） |
| 4 | 漂移核心脚本 | 改 drift-cron.sh / drift-check.sh / conflict-tracker.py（漂移治理核心脚本） |
| 5 | 鉴权逻辑 | 改 dispatch-server 鉴权（AUTH_KEY / IP allowlist / Caddy auth） |
| 6 | drift-check.sh | 改 drift-check.sh（含远端事实探明的场景，详见 lessons §8.4 第 6 项 mira 教训） |

**闸门流程**：
1. 命中任一 → Plan Mode 出方案（必须显式标 `⚠️ pre-commit 三方评审强制触发`）
2. 用户批准 plan
3. 新建 `archive/governance-review-<对象>-<date>/` 评审目录
4. 走步骤 1-5 三方评审，直到三方一致 PASS
5. **PASS 后**才允许写 patch 脚本（`apply-<对象>-<date>.py`）+ scp 到 ECS + 重启服务
6. 在 `governance/specs/pre-commit-review-gate-log.md` 追加一行（对象 / commit SHA / 触发类 / 评审目录 / PASS 轮次 / 状态=PASS）

**当前强制机制（2026-08-08）**：
- Pi 负责触发评审和收敛状态，不执行代码或部署。
- ZCode 负责非终端风险评审，不运行 hook、shell、SSH 或 Git 写操作。
- Mira 负责治理真值评审。
- Trae 负责分支、PR、CI、测试和集成；Qoder/Kimi 按领域参与实现与交叉评审。
- 所有治理 master 变更必须经 PR，并通过 `.github/workflows/governance-validate.yml`。
- ECS、systemd、Caddy、数据库、secrets 和 T3 变更仍需用户明确授权。
- 历史 `.zcode/hooks/review-gate-precommit.py` 和 override 流程只作审计证据，不是当前执行入口。

**反面案例**（写入 `review-process-lessons.md` §8）：2026-07-27 Pi 治理纳入 B/C 层三次跳过此闸门，事后补审，根因是当时无强制触发机制（本步骤 0 + hook 是修复方案）。

**循环闭合声明**（2026-07-25 meta-review-gate round2 加，C 裁定）：
- **本机制自身的变更属强制评审对象**。改 `review-gate-precommit.py` / `pre-commit-review-gate-log.yaml` schema / 本 §四.步骤0 强制清单 / `.zcode/config.json` hook 挂载点 → 命中本步骤 0，必须走三方评审。这把"修评审流程的方案走评审"从循环依赖闭合为自指但良性的结构。
- **覆盖缺口声明**：GitHub CI 只能覆盖进入 PR 的变更。未授权生产直改由用户授权门、ECS 漂移检测和审计记录共同约束。
- **威胁模型边界**：本机制防止误操作和未评审变更，不替代 GitHub/ECS 访问控制。

### 步骤 1：准备评审材料包
Pi 指定 owner；Mira、Trae 或专项 owner 为每个交付准备：
1. **交付物本身**（文档/diff/代码）
2. **目标映射表**（对应北极星/路线图哪条）
3. **项目上下文摘要**（本次治理的目标、范围、约束）
4. **从 `governance/version-manifest.json` 读取当前北极星、路线图和规格版本**
5. **第一性原理检验问题**（要评审方回答的 3-5 个本质问题）

### 步骤 2：并行调用三方评审
- Mira opus4.8p（同步调用，分钟级）
- Mira gpt5.6sol（同步调用，分钟级）
- Qoder cantus（异步调度，可能 10+ 分钟）

### 步骤 3：汇总评审结果
ZCode 汇总三方意见，输出：
- 三方各自的观点 + 证据
- 一致点 / 分歧点
- ZCode 的综合判断
- 是否一致通过

### 步骤 4：分歧处理（一致通过制）
- **三方一致通过** → 进入下一阶段
- **任一方反对** → 不通过，ZCode 列分歧上报用户
- **用户裁决** → 修改后重新评审，直到三方一致

### 步骤 5：归档评审记录
每个节点的评审记录归档到 `archive/governance-review-<node>-<date>/`，含：
- 评审材料包
- 三方评审原文
- 汇总报告
- 用户裁决（如有）

**ECS 改动额外要求**：若本次评审命中 §四.步骤 0 强制清单（改 ECS 脚本/端点/鉴权），PASS 后必须在 `governance/specs/pre-commit-review-gate-log.md` 追加一行（对象 / commit SHA / 触发类 / 评审目录 / PASS 轮次 / 状态=PASS），否则下次部署会被 PreToolUse hook 阻断。

## 五、项目上下文摘要（所有评审方必读）

### 5.1 用户与目标
- 用户：林于炜，飞书 CSM（12+ 并发客户），非程序员懂架构
- 终局（北极星 §一）：用户只定战略和确认关键决策，其余自动运转
- 当前阶段：O1 基座就绪 + O2 执行闭环 并行

### 5.2 本次治理的真实问题
- 本次会话所有改动（路线图 v1.1 含 Trae 收口、Mira 接入、CC 退役清理）**没进 git**
- `~/.agent-collaboration/`（最新）和 git 仓库（滞后到 07-25 之前）是**两套独立存储**
- 规则文档散乱：`unified` vs `workspace-collaboration` 两份协作标准（冗余）；`protocols/` 7 份跟 `governance/` 部分主题重叠；`unified` 仍引用已退役的 Claude Code（语义错误）

### 5.3 北极星硬约束（评审红线）
- §三.3 **git 真值不可绕过** → 终局只有一个真值存储
- §五.1 从问题本质出发 → 不因"惯例如此"保留冗余
- §五.4 零认知负担 → 编队成员读规则时每条规则只有一份权威
- §五.5 终局已定执行不偏离 → 不偏离既定架构

### 5.4 路线图硬约束
- O1 退出条件：退役清理完成 + "你不再担心系统会崩/数据会丢/密钥会泄"
- 不可委托清单：战略制定（文档去留决策）只能用户定

## 六、执行前置

1. ✅ 本流程规范落盘
2. ⏳ 启动节点 1（治理计划评审）：准备评审材料包 → 调用三方评审
3. ⏳ 三方一致通过后，启动阶段 1 执行
