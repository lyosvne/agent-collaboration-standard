---
version: 1.0
status: planning
type: governance-plan
created: 2026-07-26
owner: ZCode
title: O1 完整治理规划 — git 仓库 / 本地代码 / 知识文档 / 规则文件
scope: O1 退役清理 KR 的完整治理规划，覆盖之前遗漏的代码与文档治理维度
related:
  - standards/global-roadmap-v1.1.md（O1 退出条件）
  - standards/unified-agent-collaboration-standard.md（协作规则待治理）
  - standards/workspace-collaboration-v2.1.md（协作规则待治理）
supersedes: []
---

# O1 完整治理规划

## 一、为什么需要这份规划

之前推进 O1 时只做了**工具退役**（CC/Codex/QoderWork），遗漏了**代码与文档治理**。实测盘点发现四类严重散乱：

1. **git 仓库**：109 条远程分支（29 条已合未删）、Aetheris 有 8 个散落 clone
2. **本地代码**：`.codex/.tmp/` 残留克隆、`.claude/projects/` 历史会话、各工具配置目录散乱
3. **知识文档**：Codex 知识库迁移后 `Documents/Codex/` 残留、各处散落知识片段
4. **规则文件**：协作规则散落 5+ 份文档、互相重叠、未随 CC 退役更新

**O1 真退出条件**："你不再担心系统会崩/数据会丢/密钥会泄"——当前散乱状态下，担心是对的。

## 二、现状盘点（2026-07-26 实测）

### 2.1 git 仓库现状

**远程分支（109 条）**：
| 类别 | 数量 | 状态 |
|---|---|---|
| agent/* | 10 | 含废弃的 `agent/claude`（CC 退役）、`agent/trae-wave5-integration`、`agent/trae-wave5-m23a`、`agent/mira-w4-m25`（历史 wave 分支）|
| feat/wo-* | 32 | **29 条已合 master**（应清理），3 条未合（wo-0082/wo-0084/wo-0099）|
| deploy/* | 1 | wo-0040-ecs-smoke（未合 master）|
| integration/* | 1 | 历史 |

**本机 Aetheris 相关 clone（8 个）**：
| 路径 | 推测用途 | 权威性 |
|---|---|---|
| `~/Aetheris-link/` | 主 clone？ | 待核实 |
| `~/Aetheris-clones/claude/` | CC 工作目录 | ⛔ CC 退役，可清理 |
| `~/Aetheris-clones/kimi/` | Kimi 工作目录 | 保留 |
| `~/Aetheris-clones/qoder/` | Qoder 工作目录（脏 3 文件）| 保留 |
| `~/Aetheris-clones/solo/` | SOLO 工作目录 | 保留（刚合并）|
| `~/Aetheris-clones/trae/` | Trae 工作目录（脏 5 文件）| Trae IDE 退役为编队角色，clone 待定 |
| `~/Aetheris-clones/trae-w4-master-integration/` | 历史 wave 集成 | 可清理 |
| `~/Documents/trae_projects/Aetheris/` | 历史遗留 | 待核实 |
| `~/Documents/trae_projects/Aetheris-link/` | 历史遗留 | 待核实 |

### 2.2 本地代码现状

**退役工具残留**：
- `~/.codex/.tmp/plugins-clone-*`（Codex 插件克隆临时文件，2 个）
- `~/.codex/memories/`（Codex 记忆，独立 git 仓库）
- `~/.claude/projects/`（CC 历史会话，114M）
- `~/.claude/skills/anygen-suite/`（CC 独立 git 仓库）
- `~/.qoderwork/`（QoderWork 已退役但目录还在）

**多工具配置目录**（30+）：
- 主力：`.zcode/` `.mira/` `.kimi-code/` `.togo/` `.trae-cn/` `.codex/` `.claude/` `.cc-switch/`
- 历史/实验：`.aetheris/` `.anygen/` `.agentbuddy/` `.coco/` `.coze/` `.hermes/` `.icube-remote-ssh/` `.kimi-webbridge/` `.kimi-work/` `.mmx/` `.model-config-backups/` `.aily-cli/` `.arkcli/` `.lark-cli/`

**散落项目目录**：
- `~/Documents/trae_projects/Aetheris/`、`Aetheris-link/`、`aetheris-design-archive/`
- `~/Documents/Codex/`、`Feishu/`、`kimi/`、`Qoder/`
- `~/projects/_tools/`、`miaoda-app_*/`

### 2.3 知识文档现状

**Codex 知识库迁移**：
- ✅ 已迁移到 `agent-collaboration-standard/knowledge/`（wiki/raw/analysis/pipeline/scripts）
- ❌ `~/Documents/Codex/knowledge-audit-2026-07/` 残留（迁移源头，148M）
- ❌ `~/Documents/Codex/2026-07-08/` 残留

**散落的知识片段**：
- `~/Documents/Feishu/`（飞书导出的会议/评审材料，多个）
- 各 clone 内的 `docs/` 目录（Aetheris 项目的知识沉淀）
- `agent-collaboration-standard/docs/`、`governance/`、`protocols/`

### 2.4 规则文件现状

**协作规则类文档（5+ 份，可能重叠）**：
| 文档 | 内容 | 问题 |
|---|---|---|
| `unified-agent-collaboration-standard.md` | Trae IDE/SOLO PC/Claude Code/GitHub 通用规则 | ❌ 仍引用 Claude Code（已退役）|
| `workspace-collaboration-v2.1.md` | 工作空间协作 | 跟前者重叠？|
| `agent-matrix-architecture-v1.0.md` | 编队架构 | 已部分更新 |
| `fleet-division-v1.1.md` | 职能分工 | 已部分更新 |
| `cloud-agent-connection-protocol.md` | 云端连接协议 | 待审 |

**入口文档**：
- `START_HERE.md`（全局入口）
- `README.md`（目录说明）

**配置类**：
- `configs/` 下 6 份（含退役工具的 baseline）

**审计类**：
- `audits/periodic-health-check.md`（已部分更新）
- `audits/security-permission-audit-2026-05-10.md`（历史快照）

## 三、治理规划（4 维度 + 优先级）

### 维度 A：git 仓库治理

#### A1. 远程分支清理（高优，低风险）
**动作**：
- 删除 29 条已合 master 的 feat/wo-* 分支（保留 reflog，可恢复）
- 删除 4 条历史 wave agent 分支（`agent/claude`/`agent/trae-wave5-*`/`agent/mira-w4-m25`）
- 保留 3 条未合 master 的 feat 分支（wo-0082/wo-0084/wo-0099，需用户确认是否还需要）

**风险**：低（已合分支删除后 master 仍含全部历史；GitHub 支持 restore）

**红线**：`git push origin --delete` 是不可逆动作（虽然 GitHub 可 restore），需用户逐批授权。

#### A2. 本机 clone 清理（高优，中风险）
**动作**：
- 核实 8 个 Aetheris clone 的权威性（哪个是主？哪些废弃？）
- 清理明确的废弃 clone（CC/历史 wave）
- 对齐脏 clone（qoder/trae 的脏文件先处理）

**红线**：删除 clone 是不可逆（本地），需逐个用户确认。

### 维度 B：本地代码治理

#### B1. 退役工具残留清理（中优，低风险）
**动作**：
- 清理 `~/.codex/.tmp/plugins-clone-*`
- 评估 `~/.codex/memories/`（独立 git 仓库，是否归档到知识库）
- 评估 `~/.claude/projects/`（114M，已备份到 `.zcode/migrated-from-claude/`，可清理）
- 清理 `~/.qoderwork/`（已退役）

**红线**：删除大目录前先归档。

#### B2. 多工具配置目录审计（低优）
**动作**：
- 审计 30+ 配置目录，区分"在用"/"历史"/"实验"
- 历史/实验目录归档或清理
- 出一份"本机工具配置目录清单"（哪个工具用哪个目录）

#### B3. 散落项目目录治理（低优）
**动作**：
- 核实 `~/Documents/trae_projects/Aetheris*` 3 个目录的状态
- 整理 `~/Documents/{Codex,Feishu,kimi,Qoder}/` 的归属

### 维度 C：知识文档治理

#### C1. Codex 知识库迁移收尾（中优，低风险）
**动作**：
- 确认 `agent-collaboration-standard/knowledge/` 是权威知识库
- 清理 `~/Documents/Codex/` 残留（迁移源头，已备份到 git 仓库）
- 知识库的 INTEGRATION.md 更新权限模型

#### C2. 散落知识片段归集（低优）
**动作**：
- `~/Documents/Feishu/` 飞书导出材料归档
- 各 clone 内 `docs/` 跟主知识库的关系明确

### 维度 D：规则文件治理

#### D1. 协作规则统一（高优，中风险）
**动作**：
- 审计 5+ 份协作规则文档的重叠/冲突
- 选定"唯一权威规则"（推测应该是 `unified-agent-collaboration-standard.md`）
- 其他文档要么合并进去、要么降级为附录、要么归档
- **更新 CC 退役相关引用**（unified-agent-collaboration-standard.md 仍引用 Claude Code）

#### D2. 配置类文件清理（低优）
**动作**：
- `configs/` 下 6 份文件审计（含退役工具的 baseline）
- 退役工具的 baseline 归档

#### D3. branch currency 自动化（中优，高价值）
**动作**：
- `ecs-runtime-truth.md §0a` 的 branch currency 规则已有（Wave5 踩坑后写的）
- 但没强制执行——加 pre-merge hook 自动检查
- 避免 agent/xxx 合 master 前漏核 branch currency

## 四、执行原则

### 4.1 不动手前先出方案
每个维度动作前，先出具体清单给用户审，**不批量删**。

### 4.2 归档优先于删除
所有"删除"动作都先归档到 `~/.agent-collaboration/archive/<topic>-<date>/`，保留可恢复性。

### 4.3 红线动作必须授权
- `git push origin --delete`（删远程分支）
- 删除大目录（>100M）
- 修改协作规则权威文档
- 都需用户明确授权

### 4.4 治理与主线并行
代码治理不是 Wave5.5 的前置（Wave5.5 是 importer bug + 数据），但**是 O1 退出条件的前置**。建议：
- 优先做 A1（远程分支清理）+ D1（协作规则统一）—— 这两个最影响编队协作
- B/C 维度可以并行或后续

## 五、推进顺序建议

| 阶段 | 内容 | 价值 | 风险 |
|---|---|---|---|
| **第 1 批** | A1 远程分支清理 + D1 协作规则统一 | 直接影响编队协作质量 | 中（需授权）|
| **第 2 批** | A2 clone 清理 + D3 branch currency hook | 本地环境整洁 + 防再次踩坑 | 中 |
| **第 3 批** | B1 退役工具残留 + C1 Codex 收尾 | 释放空间 + 知识归一 | 低 |
| **第 4 批** | B2/B3/C2 配置审计 + 散落归集 | 长期卫生 | 低 |

## 六、不在本规划范围

- Wave5.5 数据流闭环（独立主线，不依赖本治理）
- Mira 深度挖掘 Backlog
- ECS 基础设施治理（已部分完成）

## 七、当前状态

**planning** — 规划已出，等待用户裁决推进顺序与授权范围。
