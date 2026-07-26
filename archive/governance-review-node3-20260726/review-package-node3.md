---
version: 1.0
status: ready-for-review
type: review-package
created: 2026-07-26
owner: ZCode
title: 节点 3 评审材料包 — unified vs workspace-collaboration 职责裁定
scope: 供三方评审（A/B/C）裁定 unified-agent-collaboration-standard.md 与 workspace-collaboration-v2.1.md 的职责分工/合并/废弃
related:
  - governance/unified-agent-collaboration-standard.md
  - governance/workspace-collaboration-v2.1.md
  - governance/north-star-v1.2.md
  - governance/fleet-division-v1.1.md
---

# 节点 3 评审材料包：unified vs workspace-collaboration 职责裁定

## 一、背景

roadmap §当前位置 P1 收口并行项 #9："unified vs workspace-collaboration 去留裁定（节点 3 用户裁决）"。

用户 2026-07-26 授权启动节点 3 评审。

## 二、两份文档现状

### unified-agent-collaboration-standard.md（193 行）

- **定位**："shared operating standard for ... coding agents"（共享操作标准）
- **历史**：早期文档，引用 [RETIRED-TRAE-IDE-编队角色]/[RETIRED-CC-2026-07-25]（已退役工具，Phase A 部分替换但 Tool Roles 章节仍过时）
- **内容层级**：
  1. Human Style（中文/结论先行/简洁/给判断不谄媚）
  2. Rule Layers（5 层规则优先级）
  3. Shared Language（Goal/Scope/Source of truth/Verification/Risk/Handoff/Done 字段定义）
  4. Shared Start/Completion Protocol（最小启动/完成输出）
  5. Shared Commands（:ALL/:ONE/:CHECK）
  6. **Tool Roles（过时：退役工具）**
  7. Safety Red Lines
  8. Git Rules
  9. Local GitHub Network Rules
  10. Skill Rules
- **特点**：偏**操作层**（agent 怎么干活、用什么字段/命令、什么红线）
- **被引用**：START_HERE Read Order #1、LOCAL-USAGE、knowledge/INTEGRATION、o1-governance-plan（共 9 处）

### workspace-collaboration-v2.1.md（183 行）

- **定位**："Workspace Collective Collaboration Protocol v2.1"（协作协议）
- **历史**：用户 2026-07-23 裁定生效，继承 Aetheris blueprint v1.8 → v2.0.1 → v2.1
- **内容层级**：
  1. 权威框架（用户唯一裁判、智能体对等）
  2. 真值层级与真值位置（6 层冲突裁决 + 5 个真值锚点）
  3. **编队注册（Pi/ZCode/Qoder/Kimi/Trae/Mira + 退役表，当前架构）**
  4. **任务路由（G+M 分工定稿，13 类任务首选）**
  5. 安全边界（Red Lines，T1/T2/T3 密钥分级）
  6. 完成契约（Changed/Verified/Risk/Handoff + Rollback）
  7. 协作同步规则（commit 粒度、漂移治理、Qoder↔Pi Webhook/SSE/轮询）
  8. 实施优先级（P0 底座路线）
  9. 双环治理模型（G1-G7 运转环 + M1-M5 方向环）
  10. 过渡期协调 + 治理文档入 git
- **特点**：偏**治理层**（谁负责什么、任务怎么路由、权威层级、编队架构）
- **被引用**：START_HERE Read Order #5、workspace-collaboration-v2.1.md 自身 frontmatter

## 三、职责差异分析（ZCode 判断）

**核心差异**：
- unified = **怎么干活**（操作标准：字段/命令/红线/流程/Skill）
- workspace = **谁干什么**（治理架构：权威/编队/路由/分工/双环）

**互补不冲突**：
- unified 的 Human Style / Rule Layers / Shared Language / Shared Commands / Git Rules / Skill Rules 是 workspace 没有的操作细节
- workspace 的编队注册 / 任务路由 / 双环治理 / 真值层级是 unified 没有的治理架构

**重叠部分**：
- Safety Red Lines（两者都有，内容基本一致）
- 完成契约（unified 的 Completion Protocol ≈ workspace 的 Finish Contract）

**unified 的问题**：
1. Tool Roles 章节过时（[RETIRED-TRAE-IDE-编队角色]/[RETIRED-CC]）
2. 没有 Pi/ZCode/Qoder/Kimi/Mira 当前编队
3. 没有任务路由
4. Local GitHub Network Rules 含退役 CC 启动命令（[RETIRED-CC].cmd）

## 四、3 个候选方案（供评审方裁定）

### 方案 A：分工保留（unified = 操作层，workspace = 治理层）

**做法**：
- 保留两者，明确分工：
  - unified 改名/重新定位为"Agent Operating Standard"（操作标准，不含编队架构）
  - workspace 保持"Collaboration Protocol"（治理协议，含编队/路由）
- unified 删除/重写 Tool Roles（退役工具移除，编队引用指向 workspace）
- unified 删除 Local GitHub Network Rules 的退役 CC 启动命令
- START_HERE Read Order 明确：unified 教"怎么干活"，workspace 教"谁干什么"
- 两者重叠部分（Red Lines/完成契约）在 unified 标注"详见 workspace §4/§5"

**优点**：职责清晰，各司其职；改动量中等
**缺点**：两份文档仍易混淆（都叫 collaboration），需强声明

### 方案 B：合并为单一标准（workspace 吸收 unified）

**做法**：
- workspace 作为唯一协作标准，吸收 unified 的操作层内容（Human Style/Rule Layers/Shared Language/Shared Commands/Git Rules/Skill Rules）
- unified 废弃（改名为 archive/unified-agent-collaboration-standard-deprecated.md，保留历史）
- 更新 START_HERE Read Order：只保留 workspace 作为 #1（或改名）
- 更新所有引用 unified 的文件（9 处）指向 workspace

**优点**：单一真值，无混淆；与 north-star/fleet-division 三件套对齐（都是"唯一文档"）
**缺点**：合并后 workspace 会很长（~300+ 行）；unified 的 Skill Rules 等内容可能需要在 workspace 新增章节

### 方案 C：unified 废弃，操作层内容分散到各专题文档

**做法**：
- unified 废弃
- Human Style / Rule Layers → 写入 .zcode/AGENTS.md（全局，已部分含）
- Shared Language / Shared Commands → 新建 governance/agent-operating-fields.md
- Skill Rules → registry/skill-governance.md（已存在）
- Git Rules → workspace §6 协作同步规则（已部分含）
- START_HERE Read Order 更新

**优点**：每个主题独立文档，职责最清晰
**缺点**：改动量大（新建文档 + 多处引用更新）；操作层分散不利一次性阅读

## 五、评审重点

1. **职责分析是否成立**：unified（操作层）vs workspace（治理层）的分工判断对吗？有无遗漏的重叠/冲突？
2. **3 方案哪个更优**：考虑 O1 基座就绪阶段、改动成本、长期维护性、与 north-star/fleet-division 三件套的一致性
3. **unified 的 Tool Roles 过时**：无论选哪个方案，unified 的退役工具引用都该处理
4. **START_HERE Read Order**：当前 unified 是 #1，workspace 是 #5——这个顺序合理吗？如果 unified 废弃/改名，Read Order 怎么调
5. **9 处引用**：unified 被 START_HERE/LOCAL-USAGE/INTEGRATION/o1-governance-plan 引用，废弃/改名的引用更新工作量

## 六、红线遵守

- 本评审只是**方案裁定**，不立即执行
- 评审方给方案建议，ZCode 汇总后报用户最终裁决
- 执行阶段（方案确定后）会另起任务，需独立评审

## 七、当前状态

**ready-for-review** — 等待三方评审给方案建议。
