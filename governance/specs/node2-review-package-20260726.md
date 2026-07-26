---
version: 1.0
status: ready-for-review
type: review-package
created: 2026-07-26
owner: ZCode
title: 节点 2 评审材料包 — sync 分支 v3.4 同步
scope: 供三方评审（A/B/C）针对 commit 314b35a 核对 v3.4 §五的 10 条门禁
related:
  - specs/agent-collaboration-git-sync-plan.md (v3.4 执行依据)
  - specs/review-process-lessons.md (评审提示词优化)
  - archive/retired-terms-exceptions-20260726.md (v2 重建, HISTORY 逐条)
  - .review-evidence/node2-checks-20260726-152040.md (本地证据, 已 .gitignore)
---

# 节点 2 评审材料包

## 〇、评审对象

| 项 | 值 |
|---|---|
| 仓库 | https://github.com/lyosvne/agent-collaboration-standard |
| 分支 | `sync/agent-collaboration-import-20260726-v3`（远程已 push）|
| **commit SHA** | **`314b35aea674341b8987be17f68b94544c29c69a`** |
| 基线（同步前）| `4250353` (tag `pre-agent-collaboration-sync-20260726-v3` + branch `backup-pre-sync-v3-20260726`) |
| 同步方案 | v3.4（节点 1 三方一致通过）|
| 执行者 | ZCode (GLM-5.2) |
| 执行时间 | 2026-07-26 |

## 一、10 条门禁实测值（v3.4 §五）

| # | 门禁 | 预期 | 实测 | 通过 |
|---|---|---|---|---|
| 1 | cc-retirement 进入工作树/暂存区/tracked | 0 个 | **0 个** | ✅ |
| 2 | secret 扫描命中（未豁免）| 0 个 | **0 个**（patterns: `[REDACTED-FRAGMENT]`，扫暂存区 blob，排除 scripts/）| ✅ |
| 3 | 现行规范中退役角色引用 | 0 个 | **0 个**（116 条命中全部为 HISTORY，集合比对验证）| ✅ |
| 4 | 历史引用命中已批准例外清单 | 100% | **100%**（116/116，与门禁 3 同一集合比对）| ✅ |
| 5 | 每个源-目标映射的新增/修改/删除/排除数量 | 有清单 + 经审核 | **dry-run 输出四清单**（见下表），用户过目后 apply | ✅ |
| 6 | dry-run 与实际暂存区文件差异 | 0 个 | **0 个**（dry-run 53+5+1，apply 后 git status 一致）| ✅ |
| 7 | 未声明策略/未声明目标路径 | 0 个 | **0 个**（v3.4 §二 13 行映射表，每行显式策略）| ✅ |
| 8 | 三位评审者针对同一 commit SHA 评审 | 3/3 | ⏳ **待评审**（本材料包发出后）| ⏳ |
| 9 | 用户批准的也是同一 commit SHA | 是 | ⏳ **待用户批准**（门禁 8 通过后）| ⏳ |
| 10 | 所有门禁输出保存为可复核证据 | 是 | ✅ `.review-evidence/node2-checks-20260726-152040.md`（本地，已 .gitignore）| ✅ |

## 二、门禁 5 详细：dry-run 同步清单

按 v3.4 §二策略表，每个映射的实测：

| 映射 | 策略 | 新增 | 修改 | 删除 | 跳过 | 排除 |
|---|---|---|---|---|---|---|
| standards→governance | mirror | 11 | 5 | 1 (LOCAL-USAGE.md, 内容一致) | - | - |
| audits | mirror | 2 | 0 | 0 | - | - |
| configs | mirror | 6 | 0 | 0 | - | - |
| registry | mirror | 3 | 0 | 0 | - | - |
| project-starter | mirror | 3 | 0 | 0 | - | - |
| archive | selective-mirror | 27 | 0 | 0 | - | cc-retirement + backups + secret-patterns |
| templates | add-only | 0 | 0 | 0 | 17 | - |
| docs | add-only | 0 | 0 | 0 | 1 | - |
| README→LOCAL-USAGE | add-only(file) | 0 | 0 | 0 | 1 | - |
| START_HERE→根 | add-only(file) | 0 | 0 | 0 | 1 | - |
| **合计** | - | **52** | **5** | **1** | **20** | - |

注：apply 时 LOCAL-USAGE.md 被 mirror 删除后由 add-only(file) 写回（内容与源一致，diff 验证 exit 0），最终结果无信息损失。

## 三、本 session 现场补强（相对 v3.4 方案的偏离声明）

评审方请注意以下"现场补强"，这些是 v3.4 方案未明确但本 session 发现必须处理的：

### 3.1 rsync 缺失 → Python 脚本替代
- **问题**：Git Bash 没装 rsync，v3.4 §二 的 rsync 命令无法执行
- **处理**：写 `scripts/mirror-sync.py`，对齐 rsync `-a --delete --exclude` 语义（递归复制 + 删除目标独有 + glob 排除）
- **评审点**：Python 脚本的 mirror 语义是否真的对齐 rsync？排除模式匹配是否正确？

### 3.2 Token 脱敏（v3.0 评审 A 的 hard blocker 复现）
- **问题**：评审归档 + specs 里发现 **43 处真实 token 片段**（`[REDACTED-FRAGMENT]` ×4 类前缀），正是 v3.0 评审 A 标记的"方案文档不含 token"硬约束违反
- **处理**：源端 + 工作树双向脱敏为 `[ANTHROPIC-REDACTED]`/`[ANYGEN-REDACTED]`/`[ZCODE-REDACTED]`
- **评审点**：脱敏是否彻底？是否破坏文档语义？脱敏占位符是否合适？

### 3.3 Phase A HISTORY 逐条登记（修正虚标）
- **问题**：上个 session 的 exceptions 文件 HISTORY 部分用概括描述（"130 条"），实际无法支持门禁 4 集合比对
- **处理**：重建 exceptions 文件，HISTORY 改为 116 条逐条登记（file:line|tool + 自动分类）
- **评审点**：116 条分类是否合理？是否有遗漏的现行角色引用？

### 3.4 secret-patterns 外置（避免自扫描陷阱）
- **问题**：脚本若硬编码 patterns 字面量，会扫到自己（v3.0 评审 A 警告）
- **处理**：patterns 放 `~/.agent-collaboration/archive/secret-patterns/`（不入 git），脚本从外部读
- **评审点**：外部文件机制是否可靠？scripts/ 排除是否合理？

### 3.5 门禁 3/4 合并为集合比对
- **问题**：v3.4 §A.5 门禁 3 用 grep 关键词过滤，无法识别"Codex知识库"等合法引用
- **处理**：门禁 3/4 改用集合比对（所有命中 ⊆ exceptions 全集）
- **评审点**：集合比对是否等价于 v3.4 原意？是否弱化了"现行角色=0"的判定？

## 四、已知待治理项（不在本次评审范围）

按 v3.4 commit 降级声明，以下项留待节点 3 用户裁决：
1. unified vs workspace-collaboration 文档去留
2. ~/.agent-collaboration/ 废弃 + 路径引用替换（Phase D）
3. Pi 漂移治理纳入（任务已登记，触发条件 Phase D 完成）

## 五、本地证据文件

评审方可向 ZCode 索取以下本地证据（不入 git，避免泄露内部细节）：
- `.review-evidence/node2-checks-20260726-152040.md`（4 门禁实测 + 暂存区统计）
- `scripts/mirror-sync.py` / `scripts/gate-checks.py` / `scripts/redact-tokens.py`（同步工具脚本，已入 git 可直接看）

## 六、评审提示词模板（基于 review-process-lessons.md 建议 1）

```
你是评审方X（模型）。按第一性原理审查 commit 314b35a 的 v3.4 同步执行。

## 必须检查的 5 类问题（review-process-lessons 教训）
1. **真值一致性**：是否真建立单一真值，还是把两套合成更大的两套
2. **fail-open 检查**：每个门禁/扫描是否 fail-closed（失败时阻断）
3. **代码副作用**：tr/sed/awk/string.replace 等是否破坏数据语义
4. **grep 方言**：所有 grep -E 模式转义是否正确（ERE 不需 \|）
5. **不可委托敬畏**：战略决策是否留给用户

## 重点核对（本 session 偏离点）
- §3.1 Python mirror 是否对齐 rsync --delete --exclude？
- §3.2 43 处 token 脱敏是否彻底？占位符是否破坏语义？
- §3.3 HISTORY 116 条分类是否合理？有无现行角色遗漏？
- §3.4 secret-patterns 外置 + scripts/ 排除是否引入新 fail-open？
- §3.5 门禁 3/4 集合比对是否弱化了"现行角色=0"判定？

## 输出格式（必须）
- 5 类问题逐条核对（✅通过/❌阻断/⚠️观察）
- 阻断点（最多 5 个，每个含具体修法）
- 改进建议（最多 3 个）
- 结论：通过 / 有条件通过（列条件）/ 不通过（列阻断）
```

## 七、当前状态

**ready-for-review** — 材料包就绪，待 A/B/C 三方评审（门禁 8）+ 用户批准（门禁 9）。
