# 维护规格：root 层 legacy 文档退役角色清理清单

> 签发: ZCode（出规格）| Review: 待对等互检 | 裁定: 用户 | 日期: 2026-07-28
> 状态: active（清理清单 spec，执行待排期——属 roadmap「第 5 批长期卫生阶段」低优先级）
> 依据: `global-roadmap-v1.1.md` L249（round4 C 指出非阻断）+ 5 个 legacy 文件实证扫描（2026-07-28）
> 缺口来源: `global-roadmap-v1.1.md` L249「root 层 legacy 文档退役角色清理」
> 变更前置: **实际执行清理时**（改文件内容）→ 走 `governance-review-process.md §四` pre-commit 三方评审（改仓库入口文档真值）

---

## 1. 为什么是 spec 而非立即执行

**roadmap L249 原话**：「建议并入'删 Tool Roles'待办**或第 5 批长期卫生阶段**」——这是被刻意推迟的低优先级项。

**本 spec 的职能**：把清理任务**精确化成可执行清单**（哪些文件 / 哪些行 / 改成什么），让未来执行时有据可依，不漏不改错。**不立即改文件内容**——因为：
1. 改 root 层入口文档（README Entry Points）触发 §四.步骤0 评审，成本高于当前收益
2. 这些引用是"历史快照"性质，不阻断任何活跃机制（gate-checks 门禁只扫 governance/，不扫 root legacy）
3. 优先级低于 SO-13 hook 加固 + 5 域一致性

**何时启动清理**：第 5 批长期卫生阶段，或 root 层文档被重新激活引用时（如新 agent 入职读 README）。

---

## 2. 清理范围（5 文件实证扫描，2026-07-28）

### 2.1 `TOOL_ROLE_MATRIX.md`（确凿活跃角色表述，**必清**）

整个文件是编队角色定义表。退役角色仍列在活跃角色区：

| 行 | 现状 | 处理 |
|----|------|------|
| L3-8 | `## Trae IDE` 段：Role: project owner... | 改为 `## Trae IDE（已退役，2026-07-26）` + 角色职责迁移到 ZCode（主控）/ Trae SOLO |
| L10-14 | `## Claude Code` 段：Role: focused implementation... | 改为 `## Claude Code（已退役，CC→ZCode 迁移完成）` + 职责迁移说明，或整段移入 archive |

**判定依据**：纯角色定义表，无"通用举例"语义空间。Trae IDE / Claude Code 在此被当现行编队成员描述权限（Default access / Must read），是确凿的活跃角色表述。

### 2.2 `GLOBAL_AGENT_GUIDE.md`（混合，**精确清理**）

| 行 | 现状 | 性质 | 处理 |
|----|------|------|------|
| L5 | "Provide a common operating language for Trae IDE, Claude Code, Trae SOLO, Mira..." | 活跃角色表述（列举编队成员）| 改为 "ZCode, Trae SOLO, Mira, Qoder, Kimi, Pi" |
| L74 | "the Zhipu-backed Claude Code launcher is `C:\Users\Admin\.local\bin\claude-zhipu.cmd`" | 历史路径（CC 退役后已归档）| 标注"（已退役，launcher 随 CC 归档）"或删除 |

**判定依据**：L5 是编队成员枚举（活跃表述），L74 是历史路径残留。两者性质不同，分开处理。

### 2.3 `protocols/communication-command-protocol.md`（混合，**精确清理**）

| 行 | 现状 | 性质 | 处理 |
|----|------|------|------|
| L218 | "Recommended next owner: Trae IDE / Claude Code / Trae SOLO PC / Trae SOLO Sandbox / Mira" | 活跃角色表述（任务 owner 候选）| 改为 "ZCode / Trae SOLO / Mira / Qoder / Kimi" |
| L254 | "This section defines how any agent (Mira, Trae IDE, Claude Code, Trae SOLO...)" | 活跃角色表述（协议适用对象）| 同上替换 |

**判定依据**：协议文档定义"谁遵守此协议"，列举退役角色 = 协议适用范围错误。

### 2.4 `BOOTSTRAP_ONE_LINE.md`（活跃表述，**必清**）

| 行 | 现状 | 处理 |
|----|------|------|
| L3 | "Use this when asking Mira, Claude Code, Trae SOLO, or another coding agent..." | 改为 "asking Mira, ZCode, Trae SOLO..." |

**判定依据**：bootstrap 指令的适用对象，列 Claude Code = 误导新 agent 用退役工具。

### 2.5 `docs/multi-agent-collaboration-operating-system.md`（**通用文档，谨慎处理**）

**性质特殊**：L3 明确声明"本文是**通用协作体系说明**。GitHub、Trae IDE、Claude Code... 等软件和平台名称**不脱敏**"。这是**通用方法论文档举例**，不是编队角色定义。

| 行 | 现状 | 性质 | 处理 |
|----|------|------|------|
| L3 | "GitHub、Trae IDE、Claude Code、Trae SOLO、Mira... 不脱敏" | 通用举例声明 | **保留**（文档自声明不脱敏）|
| L7 | "把 Trae IDE、Claude Code、Trae SOLO、Mira 等多个 AI 开发工具..." | 通用举例 | **保留** |
| L26-27 | 角色表：Trae IDE=主控 / Claude Code=专项代码 | **混合**：通用示例但用了编队角色名 | 加注"（示例角色，编队实际分工见 governance/fleet-division-v1.1.md）" |
| L43, L70 等 | 架构图/流程里列举工具名 | 通用举例 | **保留** |

**判定依据**：此文档是"多 agent 协作通用方法论"，工具名作为示例。强行清理会破坏通用性。**只清理 L26-27 角色表**（加注指向编队真值），其余保留。

---

## 3. 清理原则（执行时遵守）

1. **区分两类引用**（核心）：
   - **活跃角色表述**（把退役工具当现行编队成员描述职责/权限/适用范围）→ **必清**
   - **通用举例/历史叙述**（作为方法论示例或历史背景提及）→ **保留或加注**
2. **替换而非删除**：退役角色段不直接删，改为"（已退役，YYYY-MM-DD）+ 职责迁移到 X"，保留审计痕迹
3. **指向真值**：清理后的角色定义指向 `governance/fleet-division-v1.1.md`（编队分工真值），不在此重复维护
4. **README 同步**：若 TOOL_ROLE_MATRIX 整体退役，README Entry Points #10 同步移除
5. **门禁验证**：清理后跑 gate-checks.py 确认门禁 3（现行角色引用）仍 PASS（gate 不扫 root legacy，但清理后应确保不引入新现行角色引用）

---

## 4. 执行前置（实际清理时）

| 改动 | 前置 |
|------|------|
| 改任一 legacy 文件内容 | 走 `governance-review-process.md §四` pre-commit 三方评审（改仓库入口文档真值）|
| 删除文件（如 TOOL_ROLE_MATRIX 整体退役）| **红线：必须先问用户** + 评审 + README 同步 |
| 改 README Entry Points | 走评审（仓库入口）|

**不立即执行的理由**（重申）：roadmap 明确归入"第 5 批长期卫生阶段"，当前优先级低于 hook 加固 + 5 域一致性。本 spec 锁定清单，待时机成熟批量执行。

---

## 5. 与其他 spec 的关系

| 关联 spec | 关系 |
|-----------|------|
| `fleet-division-v1.1.md`（governance/）| 清理后角色定义指向的编队分工真值 |
| `governance-review-process.md §8.4` | 执行清理的前置评审触发条款 |
| `review-process-lessons.md` | 退役清理的历史教训（CC 退役流程）|

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-07-28 | ZCode 起草：5 文件实证扫描 + 逐文件逐行清理清单 + 两类引用区分原则（活跃表述 vs 通用举例）+ 执行前置。闭合 roadmap 缺口 #9（清单 spec，执行留第 5 批）|
