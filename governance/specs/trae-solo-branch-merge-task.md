---
version: 3.0
status: completed
type: task-spec
created: 2026-07-26
updated: 2026-07-26
owner: ZCode
title: Aetheris 分支合并任务 — Trae IDE 退役后的分支归并
scope: 把 Trae IDE 在 Aetheris 的 `agent/trae` 分支内容合并到 `agent/solo`，作为 Trae IDE 退役为编队角色后的分支清理
related:
  - standards/fleet-division-v1.1.md（G3 SOLO 承接测试职能）
  - configs/tool-entry-map.md（Trae IDE 退役标记）
supersedes: []
---

# Aetheris 分支合并任务（已完成）

## ✅ 执行结果（2026-07-26）

### 最终状态
- **本地 HEAD**：`049278a1`（远程同步）
- **远程 origin/agent/solo**：`049278a1`（已 push）
- **solo vs master**：落后 **0 条**，独有 **74 条**
- **工作区**：干净
- **Wave 进展**：完全同步到 **W5.5**（含 Wave5.5 数据流闭环、F3 决策、CC→ZCode 迁移）

### 执行过程
1. ✅ 创建本地备份分支 `solo-backup-pre-merge-20260726`（指向合并前 `cef58611`）
2. ✅ stash 脏改动作为 safety net（`pre-merge-safety-net-20260726`）
3. ✅ 分类脏改动（SAME 10 + DIFF 2 + SOLO-ONLY 48），删除冗余 12 个 `.trae/skills/` 副本
4. ✅ commit SOLO 独有 skill 资产（49 文件 / 10857 行）
5. ✅ merge origin/master（336 commits），解决 3 个冲突：
   - `work-ledger.jsonl`：两边事件按时间戳合并+去重（solo 12 + master 27 = 39 条）
   - `graph-service.ts`：取 master（W2-2a 幂等去重修复）
   - `GoalExecutionOrchestrator.ts`：取 master（async 修复，SOLO W2 工作已并入 master）
6. ✅ 补 f3-decision 死链文件（从 agent/mira cherry-pick）
7. ✅ push 到 origin/agent/solo（339 commits）

### 关键观察
- master 里**已经有 SOLO 的 Wave5 产出**（M23-A tab 历史导航 hotfix 等），是通过 claude/trae 分支合并的
- agent/solo 之前**落后于 SOLO 实际工作进展**（虽是 SOLO 的分支，但 Wave5 工作没经过它）
- 合并后 SOLO 分支回到主线，后续工作可直接从 agent/solo 走

## 历史背景（保留）

2026-07-26 C 选项裁定：编队里 Trae 系只保留 **Trae SOLO** 一个独立角色（端到端测试/QA），**Trae IDE 退役为编队角色**（软件保留个人用）。

退役后，Trae IDE 在 Aetheris 的 `agent/trae` 分支历史产出归并到 `agent/solo`，让 SOLO 成为 Trae 系的唯一活跃分支。

## 后续待办（不在本任务范围）

- `agent/trae` 分支的归档/删除决策（目前保留作历史，未做处理）
- 本机 Trae IDE 软件卸载（用户明确保留个人使用，不做）
- Trae IDE 的 `~/.trae-cn/` 配置清理（个人使用保留，不做）

## 一、任务背景

2026-07-26 C 选项裁定：编队里 Trae 系只保留 **Trae SOLO** 一个独立角色（端到端测试/QA），**Trae IDE 退役为编队角色**（软件保留个人用）。

退役后，Trae IDE 在 Aetheris 的 `agent/trae` 分支历史产出需要归并到 `agent/solo`，让 SOLO 成为 Trae 系的唯一活跃分支。

## 二、调研结果（2026-07-26 实测）

### 2.1 solo 工作区脏改动来源（已查清，2026-07-26 完整对比）

**来源**：SOLO 之前在本地下载/启用的 skill 集合，未 commit。

**完整分类（实测对比 master）**：

| 类别 | 数量 | 处理 |
|---|---|---|
| **SAME**（跟 master 内容完全相同）| 10 | 删除工作区副本（master 接管，零损失） |
| **DIFF**（跟 master md5 不同）| 2 | **实际是行尾差异**（solo=CRLF, master=LF），内容一致。删除工作区副本让 master 接管 |
| **SOLO-ONLY**（master 没有）| 48 | **commit 保留**（SOLO 独有资产） |

**SOLO-ONLY 48 个文件分布**：
- `.agents/skills/` 下 15 个 skill 目录（brainstorming / design-taste-frontend / dispatching-parallel-agents / executing-plans / finishing-a-development-branch / receiving-code-review / requesting-code-review / subagent-driven-development / systematic-debugging / test-driven-development / using-git-worktrees / using-superpowers / verification-before-completion / writing-plans / writing-skills）
- `.trae/skills/design-taste-frontend/SKILL.md`

**SAME + DIFF 的 12 个文件**（删除工作区副本）：
- 全部在 `.trae/skills/` 下，跟 master 路径重叠（brainstorming/scripts/、dispatching-parallel-agents、executing-plans、finishing-a-development-branch、receiving-code-review 等）

**结论**：脏改动里**真正需要保留的只有 48 个 SOLO 独有文件 + skills-lock.json**，其余 12 个是 master 已有的冗余副本。

### 2.2 trae 分支里 SOLO 产出来源（已查清）

**关键发现**：SOLO 的 Wave5 产出**不在 agent/solo 分支上**，而是通过其他分支合并到 master 的。

实测 commit `60ca2fba`（SOLO 生产 smoke PASS）的分布：
- ✅ 在：master / agent/claude / agent/trae / agent/zcode
- ❌ **不在**：agent/solo

**含义**：SOLO 的 Wave5 工作（M23-A tab 历史导航 hotfix）是通过 claude 或 trae 分支合并到 master 的，没经过 agent/solo 分支。说明 **agent/solo 分支已经落后于实际 SOLO 工作的进展**。

### 2.3 分支差距全景（实测）

| 比较 | commit 数 | 说明 |
|---|---|---|
| solo 落后 master | **336 条** | SOLO 错过了 Wave5 全部 + W5.5 + CC→ZCode 迁移 |
| solo 落后 agent/trae | **351 条** | trae 比 solo 多了 Wave5 + 后续 |
| **solo 领先 agent/trae** | **71 条** | solo 独有：W2/W3/W4 测试基线（dispatcher red/green、test baseline、wave4 owner plan） |

**solo 独有的 71 条 commit** 全部是 SOLO 的测试工作：
- W4: dispatcher runtime red/green、solo w4 s1 test baseline
- W3: solo task10 boundary、test and health gaps research
- W2: knowledge extraction / orchestrator registration / matter task bridge / vault view 等 2a-2e 测试系列
- W1: solo wave1 acceptance / review

**这 71 条 commit 是 SOLO 的核心资产，必须保留**。

### 2.4 master 里 SOLO 的产出（实测）

master 里有 SOLO 的 Wave5 产出（通过其他分支合并的）：
- `60ca2fba` SOLO 生产 smoke PASS — M23-A tab 历史导航 hotfix 闭环
- `03e7ea87` M23-A tab 历史导航 hotfix 部署记录
- `7a57158a` SOLO P0 真实集成护栏
- `cb227f74` SOLO P0 better-sqlite3 落列契约
- `62c25c11` Wave5 协作全流程 handoff pack（含 SOLO 测试 owner 分配）

**含义**：SOLO 的 Wave5 产出已经在 master 里了，agent/solo 只是没同步下来。

## 三、合并方案（3 选 1，请你裁决）

### 方案 A：solo 从 master 重新同步（推荐）⭐

**动作**：
```bash
cd ~/Aetheris-clones/solo
# 1. 先 commit 脏改动（保留 skill 资产）
git add skills-lock.json .agents/skills/ .trae/skills/
git commit -m "chore(skills): commit pending skill assets before master sync"

# 2. 从 master rebase 或 merge 到 agent/solo
git fetch origin
git merge origin/master   # 或 git rebase origin/master

# 3. 解决冲突（主要是 solo 的 71 条测试 commit 跟 master 的 Wave5 可能有交叉）
# 4. push
git push origin agent/solo
```

**优点**：
- SOLO 拿到所有 Wave5 + W5.5 + CC 迁移内容
- SOLO 的 71 条测试 commit 保留
- 之后 agent/solo 就是 Trae 系唯一活跃分支
- agent/trae 可以归档/删除

**风险**：
- solo 的 71 条 commit 跟 master 可能冲突（尤其测试文件）
- master 里已经有 SOLO 的 Wave5 产出，可能跟 solo 的某些 commit 重复
- 需要 336 条 commit 的合并/变基，冲突解决工作量大

### 方案 B：solo 废弃，从 master 新建 agent/solo-v2

**动作**：
```bash
# 1. 把 solo 的 71 条独有 commit 导出为 patch
cd ~/Aetheris-clones/solo
git format-patch origin/agent/trae..HEAD -o /tmp/solo-unique-patches/

# 2. 从 master 新建分支
git checkout -b agent/solo-v2 origin/master

# 3. 按需 cherry-pick solo 的关键测试 commit
git cherry-pick <commit-hash>...

# 4. push 新分支，归档旧 agent/solo
```

**优点**：
- 干净起步，不带历史包袱
- 只挑有用的 commit
- 新分支跟 master 完全同步

**风险**：
- 71 条 commit 挑选工作量大
- 可能漏挑
- 需要重命名分支（agent/solo → agent/solo-archived，agent/solo-v2 → agent/solo）

### 方案 C：保持现状，agent/solo 不动，agent/trae 也不动

**动作**：什么都不做，只在文档层标记 agent/trae 为"已退役历史分支"

**优点**：零风险

**风险**：
- agent/solo 继续落后 master（336 条）
- 编队里 Trae 系还是有"两个分支"（虽然其中一个标记退役）
- SOLO 后续工作如果还从 agent/solo 走，会越来越偏离主线

## 四、我的推荐：方案 A

**理由**：
1. **符合 C 选项目标**：让 SOLO 成为 Trae 系唯一活跃分支
2. **保留 SOLO 全部历史**：71 条测试 commit 是 SOLO 的核心资产
3. **同步到主线**：SOLO 后续工作基于最新 master，不会再漂移
4. **agent/trae 可归档**：合并完后清理

**但方案 A 有真实风险**：336 条 commit 合并 + 可能的冲突解决，不是 5 分钟能搞定。需要你授权后我分步执行，每步报告。

## 五、执行前置条件（方案 A）

1. ⚠️ 用户授权 git merge + 解决冲突 + push（红线动作）
2. ⚠️ 接受可能需要 1-2 小时的冲突解决
3. ⚠️ 接受 push 后不可逆（虽然有 reflog 兜底）
4. ✅ 脏工作区的 skill 资产会先 commit 保留

## 六、不在本任务范围

- 本机 Trae IDE 软件卸载（用户明确保留个人使用）
- Trae IDE 的 `~/.trae-cn/` 配置清理（个人使用保留）
- 编队文档层调整（已在 2026-07-26 C 选项落地中完成）

## 七、当前状态

**investigation-complete-awaiting-decision** — 调研完成，3 个方案已列出，等待用户选择 A/B/C。
