# O1 全域一致性治理 — 计划评审材料包

## 评审要求
请按第一性原理审查本材料包里的 3 份方案 + 1 份评审流程规范。
每个评审方必须回答 5 个本质问题（见末尾）。
分歧会列给用户裁决，不要求你替用户决定。

## 项目上下文摘要

### 用户与目标
- 用户：林于炜，飞书CSM（12+并发客户），非程序员懂架构
- 终局（北极星§一）：用户只定战略和确认关键决策，其余自动运转
- 当前阶段：O1基座就绪 + O2执行闭环 并行

### 本次治理的真实问题
1. 本次会话所有改动没进git（路线图v1.1含Trae收口/Mira接入/CC退役清理）
2. ~/.agent-collaboration/（最新）和git仓库（滞后到07-25之前）是两套独立存储
3. 规则文档散乱：unified vs workspace-collaboration两份协作标准；protocols/跟governance/部分主题重叠；unified仍引用已退役的Claude Code

### 北极星硬约束（评审红线）
- §三.3 git真值不可绕过 → 终局只有一个真值存储
- §五.1 从问题本质出发 → 不因惯例保留冗余
- §五.4 零认知负担 → 每条规则只有一份权威
- §五.5 终局已定执行不偏离

### 路线图硬约束
- O1退出条件：退役清理完成 + 用户不再担心崩/丢/泄
- 不可委托清单：战略制定（文档去留决策）只能用户定

---

## 文档 1: O1 治理规划（4维度）

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

---

## 文档 2: agent-collaboration → git 同步方案

---
version: 1.0
status: plan-awaiting-approval
type: sync-plan
created: 2026-07-26
owner: ZCode
title: ~/.agent-collaboration → git 仓库 同步方案
scope: 把 ~/.agent-collaboration/ 的最新内容完整同步到 agent-collaboration-standard git 仓库，建立单一真值机制
related:
  - specs/o1-governance-plan.md
supersedes: []
---

# ~/.agent-collaboration → git 仓库 同步方案（待审批）

## 一、问题严重性（实测诊断）

### 1.1 根本问题：两套独立存储，git 滞后

| 位置 | 性质 | 状态 |
|---|---|---|
| `~/.agent-collaboration/` | 普通目录（非 git）| **最新**（本次会话所有改动都在这）|
| `agent-collaboration-standard` git 仓库 | git 仓库（master 4250353）| **滞后**（07-25 之前停止同步）|
| GitHub origin | 远程 | 跟本地 git 仓库一致（滞后）|

**git 仓库不是真值源**——`~/.agent-collaboration/` 才是事实真值。这违背了"git 为真值源"的目标。

### 1.2 完整差异盘点（2026-07-26 实测）

#### A. standards/（对应 git governance/）—— 部分同步

| 类别 | 数量 | 详情 |
|---|---|---|
| ✅ SAME（已同步）| 7 | README, cloud-agent-connection-protocol, north-star-v1.2, unified-agent-collaboration-standard, workspace-collaboration-v2.1, specs/full-survey-method, specs/pi-drift-governance, specs/qoder-sse-consumer-design, specs/survey-zcode |
| ⚠️ DIFF（同步过但本次改了）| 4 | agent-matrix-architecture-v1.0, fleet-division-v1.1, **global-roadmap-v1.1**, specs/pi-feishu-bridge-design |
| ❌ NEW（git 仓库完全没有）| 6 | specs/kimi-integration-status, specs/mira-deep-dive-backlog, specs/mira-integration-status, specs/mira-vs-larkcli-capabilities, specs/o1-governance-plan, specs/trae-solo-branch-merge-task |
| 反向（git 有 local 无）| 0 | 无 |

#### B. 其他顶层目录（git 仓库完全缺失）—— 严重

| 目录 | local 文件数 | git 仓库 | 说明 |
|---|---|---|---|
| `archive/` | 3 子目录 | ❌ 完全没有 | 本次会话归档（CC退役/Trae收口/B1回滚）|
| `audits/` | 2 | ❌ 完全没有 | 健康检查 + 安全审计 |
| `backups/` | 1 | ❌ 完全没有 | 历史备份 |
| `configs/` | 6 | ❌ 完全没有 | tool-entry-map + SOLO profile + 权限 baseline |
| `docs/` | 1 | ✅ 1（可能不同）| |
| `project-starter/` | 3 | ❌ 完全没有 | |
| `registry/` | 3 | ❌ 完全没有 | skill-registry + skill-governance |
| `templates/` | 17 | 6 | local 多 11 个（qoder-cross-review/zcode-* 等本次新增）|

**git log 验证**：archive/audits/configs/registry 这 4 个目录**从未进过 git**。说明历史上同步机制就只覆盖了 standards/ 一部分，从来没全量同步过。

### 1.3 本次会话改动丢失风险

本次会话所有改动（约 30 个文件）都在 `~/.agent-collaboration/`，**没一个进 git**。包括：
- 路线图 v1.1（C 选项 Trae IDE 退役）
- Mira 系列 spec（4 份）
- CC 退役清理记录
- Trae 收口 + B1 回滚记录
- Aetheris 分支合并任务
- O1 治理规划

如果 `~/.agent-collaboration/` 目录出问题（误删/磁盘故障），**这些改动全部丢失**。

## 二、同步方案

### 2.1 同步策略：全量覆盖（local → git）

**原则**：以 `~/.agent-collaboration/` 为准（它有最新内容），全量覆盖 git 仓库对应位置。

**为什么不用反向（git → local）**：git 是旧的，反向会丢失本次会话所有改动。

### 2.2 目录映射关系（Phase 1 核查后修订）

**Phase 1 核查发现**：git 仓库不是空壳，它有完整的 protocols/、根级元文档、knowledge/。原"全量覆盖"方案会破坏这些。修订为**精确同步**：

| local 路径 | git 仓库路径 | 处理 | 说明 |
|---|---|---|---|
| `standards/` | `governance/` | **覆盖** | 已确认是镜像关系 |
| `archive/` | `archive/`（新建）| **rsync 排除 cc-retirement** | 含密钥归档，绝对排除 |
| `audits/` | `audits/`（新建）| 全量复制 | |
| `configs/` | `configs/`（新建）| 全量复制 | |
| `registry/` | `registry/`（新建）| 全量复制 | |
| `project-starter/` | `project-starter/`（新建）| 全量复制 | |
| `templates/` | `templates/` | **补齐**（只加 local 多的，不覆盖 git 已有）| 避免覆盖 git 已有的 6 个 |
| `docs/` | `docs/` | **合并**（local 的 pi-feishu-commands.md 加进去）| git 的 multi-agent-operating-system.md 保留 |
| `README.md` | `governance/README.md` 或 `LOCAL-USAGE.md` | **不覆盖 git 根 README** | 两份是不同层级文档 |
| `START_HERE.md` | 根 `START_HERE.md`（新建）| 全量复制 | |
| `backups/` | ⚠️ **不进 git** | - | 含可能的敏感数据 |
| - | `protocols/` 根级元文档 `knowledge/` `schemas/` | **不动** | 保留 git 已有的 |

**关键修订**：
1. **README 不覆盖**——local README 是"工具协作目录说明"，git 根 README 是"仓库元文档"，两份是不同层级
2. **templates 不覆盖**——只补齐 local 多的 11 个，保留 git 已有的 6 个
3. **docs 合并**——两份都保留
4. **protocols/ 根级文件 knowledge/ 不动**——这些是 git 仓库的核心内容，local 没有，绝不能覆盖

### 2.3 不进 git 的内容（红线）

| 内容 | 原因 |
|---|---|
| `backups/` | 含可能的敏感数据 + 体积大 |
| `.gitignore`（local 自己加的）| 临时保护 archive 不被误推，git 仓库自己的 .gitignore 应单独管理 |
| `archive/cc-retirement-20260726/`（含密钥归档）| ⚠️ 含已删除的明文 token，**绝对不进 git** |
| `archive/b1-rollback-20260726/`（错误的 B1 profile）| 历史错误，可进 git 但要在 commit message 说明 |

**关键红线**：`archive/cc-retirement-20260726/` 里有今天刚删的 3 个密钥文件（settings.json.retired-backup / .env.anygen / settings.local.json），**绝对不能进 git**。同步时必须排除。

## 三、执行步骤（分 5 步，每步可回滚）

### Step 1: 备份 git 仓库当前状态（safety net）
```bash
cd ~/Documents/trae_projects/agent-collaboration-standard
git tag pre-agent-collaboration-sync-20260726
git branch backup-pre-sync-20260726
```
**作用**：万一同步出错，能 `git reset --hard pre-agent-collaboration-sync-20260726` 回滚。

### Step 2: 全量复制 local → git（排除红线）
```bash
# 复制 standards/ → governance/
cp -r ~/.agent-collaboration/standards/* governance/

# 新建并复制缺失的目录
for d in archive audits configs registry project-starter; do
    mkdir -p $d
    cp -r ~/.agent-collaboration/$d/* $d/ 2>/dev/null
done

# 补齐 templates/
cp ~/.agent-collaboration/templates/*.md templates/

# 根目录文件
cp ~/.agent-collaboration/START_HERE.md .
```

**排除**：
- `archive/cc-retirement-20260726/`（含密钥，**不复制**）
- `backups/`（不复制）

### Step 3: 创建 .gitignore 保护敏感归档
```bash
# 在 git 仓库根创建 .gitignore
cat > .gitignore <<EOF
# 含已删除密钥的归档，绝对不进 git
archive/cc-retirement-20260726/
# 本地备份
backups/
EOF
```

### Step 4: 检查 + commit
```bash
git status  # 人工审查变更清单
git add .
git commit -m "sync: 全量同步 ~/.agent-collaboration → git（建立单一真值）

本次同步内容：
- standards/ 4 个 DIFF 文件（global-roadmap-v1.1 含 Trae IDE 退役 / fleet-division / agent-matrix / pi-feishu-bridge）
- standards/specs/ 6 个 NEW（Mira 系列 4 份 + trae-solo-branch + o1-governance-plan）
- 新增顶层目录：archive/audits/configs/registry/project-starter（历史从未进 git）
- templates/ 补齐 11 个（qoder/zcode 系列）
- 根目录新增 START_HERE.md

排除（红线）：
- archive/cc-retirement-20260726/（含已删除密钥）
- backups/（本地备份）

建立单一真值机制：今后所有规则改动直接在 git 仓库做，~/.agent-collaboration/ 作为符号链接或废弃。"
```

### Step 5: push 到 GitHub
```bash
git push origin master
```

## 四、风险与回滚

### 4.1 风险

| 风险 | 等级 | 缓解 |
|---|---|---|
| 密钥误进 git | ⚠️⚠️⚠️ 高 | .gitignore + Step 4 人工审查 + commit 前再次确认 |
| 覆盖 git 仓库现有内容丢失 | ⚠️ 中 | Step 1 已 tag + branch 备份 |
| push 后 GitHub 历史改变 | ⚠️ 低 | 正常 commit（不 force push），GitHub 可 revert |
| 大量文件 commit 导致 PR 难审 | ⚠️ 低 | 直接 push master（本仓库是个人维护，不走 PR）|

### 4.2 回滚方案

| 场景 | 回滚命令 |
|---|---|
| commit 后发现问题（未 push）| `git reset --hard pre-agent-collaboration-sync-20260726` |
| push 后发现问题 | `git revert <commit-hash>` + push |
| 密钥误进 git | 立即 `git reset --hard` + 清理 + 重新 commit + **force push 覆盖远程**（密钥场景特例）+ **轮换被泄露的 token** |

## 五、同步后的长期机制（关键）

### 5.1 单一真值原则

**今后所有规则改动直接在 git 仓库做**，`~/.agent-collaboration/` 不再作为改动入口。

### 5.2 ~/.agent-collaboration/ 的处理（待你裁决）

3 个选项：

**选项 X**：把 `~/.agent-collaboration/` 变成 git 仓库的符号链接
```bash
mv ~/.agent-collaboration ~/.agent-collaboration.old
ln -s ~/Documents/trae_projects/agent-collaboration-standard ~/.agent-collaboration
```
- 优势：路径不变（所有引用 `~/.agent-collaboration/` 的文档仍然有效），但实际指向 git 仓库
- 劣势：Windows 软链可能有权限问题

**选项 Y**：废弃 `~/.agent-collaboration/`，所有引用改指向 git 仓库路径
- 优势：彻底清晰
- 劣势：要改大量文档里的路径引用（`~/.agent-collaboration/` → `~/Documents/trae_projects/agent-collaboration-standard/`）

**选项 Z**：保留 `~/.agent-collaboration/` 作为"运行时缓存"，定期从 git 同步
- 优势：兼容现有引用
- 劣势：又是两套存储，治标不治本

### 5.3 自动化真值校验（对应你的"时序版本"目标）

同步完成后，建立 `/truth/versions` 端点（dispatch-server）：
- 返回所有关键文档的 version / updated / commit-hash
- 各域能自动校验自己是否对齐
- 这是后续全域一致性治理的基础设施

## 六、执行前置条件

1. ⚠️ 用户审阅本方案（特别是红线排除清单）
2. ⚠️ 用户明确授权 commit + push（红线动作）
3. ⚠️ 用户裁决 ~/.agent-collaboration/ 的长期处理方式（选项 X/Y/Z）

## 七、当前状态

**plan-awaiting-approval** — 方案已出，等待用户审批。

---

## 文档 3: 评审流程规范

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
| **评审方 C** | Qoder cantus（Cantus 顶层档）| 编队主架构师视角、与 Aetheris 蓝图对齐、与现有架构契合 | Qoder Cloud Agent 调度 |
| **最终裁决** | 用户（林于炜）| 战略层、满意度、不可委托清单 | 飞书/直接对话 |

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

---

## 文档 4: 目标映射表（本评审节点）

| 交付内容 | 对应北极星条款 | 对应路线图 KR | 第一性原理检验 |
|---|---|---|---|
| 4维度治理规划 | §五.1本质/§五.4零认知负担 | O1退役清理+O1基础设施治理 | 是否从'单一真值'本质出发而非机械清理 |
| local→git同步方案 | §三.3 git真值不可绕过 | O1退役清理 | 是否建立单一存储而非维持两套 |
| 三方评审流程 | §五.5终局已定执行不偏离 | O1+评估反馈体系 | 是否对齐'反馈被吸收沉淀'目标 |

---

## 评审方必答的 5 个本质问题

1. **真值一致性**：方案是否真的建立了'单一真值存储'，还是只是把两套存储合并成更大的两套？终局应该是几个真值位置？
2. **冗余消除**：方案是否真的消除了文档冗余（unified vs workspace等），还是只是把冲突暂时搁置？
3. **语义错误修正**：方案是否真的修正了语义错误（退役工具引用），还是只是同步了文件没改内容？
4. **时序版本机制**：方案是否建立了自动化真值校验机制，还是仍依赖人工纪律？
5. **不可委托敬畏**：方案是否把战略决策（文档去留）正确地留给用户，而不是评审方/执行方代决定？

## 输出要求
每个评审方必须给出：
- 5 个本质问题的回答（每个 2-3 句）
- 方案的架构级风险（最多 5 个）
- 改进建议（最多 3 个）
- 是否通过（通过/有条件通过/不通过）+ 理由
