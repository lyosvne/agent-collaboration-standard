---
version: 1.0
status: active
type: process-spec
created: 2026-07-26
owner: ZCode
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

| 评审方 | 模型 | 视角 | 调度方式 |
|---|---|---|---|
| **评审方 A** | Mira opus4.8p（Claude Opus 4.8 Pro）| 架构级深度审查、语义一致性、第一性原理 | `mira -p` + opus4.8p 档 |
| **评审方 B** | Mira gpt5.6sol（GPT 5.6 Sol）| 快速结构化审查、逻辑漏洞、覆盖度、规则冲突 | `mira -p` + gpt5.6sol 档 |
| **评审方 C** | Qoder cantus（Cantus 顶层档）| 编队主架构师视角、与 Aetheris 蓝图对齐、与现有架构契合 | Qoder Cloud Agent 调度（ECS `qoder-bridge.py --tier cantus`） |
| **最终裁决** | 用户（林于炜）| 战略层、满意度、不可委托清单 | 飞书/直接对话 |

### 2.1 调度前校验（防协作链路跳链，2026-07-25 round3 加）

**教训来源**：`review-process-lessons.md` §8.6——meta-review-gate round1 误把 opus4.8p 换成 opus4.6，未验证就跳链，round1 A 票作废。

**调度评审方前必须执行**（每次调度，不可省）：
1. **档位/路径与真值层一致**：查本节表格 + `mira-integration-status.md` 档位表，确认要调的档位名（如 opus4.8p）在真值层有记载。
2. **实测可达性**：真值层档位名用一条最小命令实测（A/B：`mira -p "OK" --model <档位> --output-format json` 看 `is_error: false`；C：`ssh ecs 'qoder-bridge.py --tier cantus "OK"'` 看 done 状态）。**禁止凭 CLI `--help` 列表判断可达性**（mira --help 列表滞后，实测优先于文档）。
3. **环境与真值层冲突时上报**：若实测发现档位不可用，**停下问用户**"真值层过期还是别名变了"，禁止未验证就换档自行"对齐现实"。
4. **材料内联**：评审材料必须**内联**随任务下发（写进 prompt 文本），不依赖评审方主动 fetch 外部 URL（mira 沙箱看不到 Windows 本地文件，是 SO-1 评审材料投递无确认回执问题的根因）。

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

**强制机制**：
- ZCode 在 Plan Mode 出方案时，若命中以上任一，必须在 plan 里显式标"⚠️ pre-commit 三方评审强制触发"，否则用户应拒绝批准
- ZCode 应用层 PreToolUse hook（`~/.zcode/hooks/review-gate-precommit.py`）会在 `scp/ssh` 到 ECS 且匹配 `apply-*.py` 或 `/opt/pi-orchestrator` 写路径时，**Hard deny**——查闸门日志表无对应 PASS 条目即阻断
- 紧急 hotfix 可写 `.review-gate-override.json`（30 分钟窗口）绕过，但闸门表会留"override 跳闸"记录（不推荐）

**反面案例**（写入 `review-process-lessons.md` §8）：2026-07-27 Pi 治理纳入 B/C 层三次跳过此闸门，事后补审，根因是当时无强制触发机制（本步骤 0 + hook 是修复方案）。

**循环闭合声明**（2026-07-25 meta-review-gate round2 加，C 裁定）：
- **本机制自身的变更属强制评审对象**。改 `review-gate-precommit.py` / `pre-commit-review-gate-log.yaml` schema / 本 §四.步骤0 强制清单 / `.zcode/config.json` hook 挂载点 → 命中本步骤 0，必须走三方评审。这把"修评审流程的方案走评审"从循环依赖闭合为自指但良性的结构。
- **覆盖缺口声明**：本闸门**只覆盖 ZCode 路径**（PreToolUse 拦 ZCode 的 Bash 调用）。Kimi / Trae SOLO 等其他 agent 直接碰 ECS 不受本闸门控制。可接受——过去 3 次跳审全是 ZCode，先修出血点；其他 agent 的治理靠 ECS 侧 drift-check 兜底（漂移发现）+ 编队分工纪律。
- **威胁模型边界**：hook 是"防忘记"不是"防恶意"。agent 主动改写命令文本（rsync/sftp/管道/IP 拆分）可绕过——这是设计边界不是 bug。防恶意需 ECS 服务端闸门（部署入口校验 PASS token），是 v2 演进方向（SO-3）。

### 步骤 1：准备评审材料包
ZCode 为每个交付准备：
1. **交付物本身**（文档/diff/代码）
2. **目标映射表**（对应北极星/路线图哪条）
3. **项目上下文摘要**（本次治理的目标、范围、约束）
4. **北极星 v1.2 + 路线图 v1.1 关键条款**（让评审方对齐）
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
