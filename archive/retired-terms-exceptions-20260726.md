# 退役工具引用例外清单（节点 1 Phase A 输出，v2 重建）

> 生成: 2026-07-26（初版）/ 2026-07-26（v2 重建，HISTORY 逐条登记）
> 依据: grep 扫描 standards/ 全部退役词命中 + 自动分类
> 用途: 节点 2 评审时核对门禁 4（历史引用 100% 命中此清单）

## 重建说明

- 初版（2026-07-26）: ROLE 11 条逐条 + HISTORY 用概括描述（130 条声称）
- v2 重建（本次）: HISTORY 改为逐条登记（按 file:line|tool 集合比对）
- 原因: 初版 HISTORY 概括描述无法支持门禁 4 集合比对，本次 Phase B 现场补全

## ROLE（已替换为 [RETIRED-...] 占位符）

| 文件 | 行 | 工具 | 内容预览 | 理由 |
|---|---|---|---|---|
| 文件 | 行 | 工具 | 内容预览 | 理由 |
| standards/unified-agent-collaboration-standard.md | 60 | Claude Code | "Choose the agent owner: Trae IDE, Claude Code..." | CC 作为编队可选 owner（已退役）|
| standards/unified-agent-collaboration-standard.md | 60 | Trae IDE | 同上 | Trae IDE 作为编队可选 owner（退役为编队角色）|
| standards/unified-agent-collaboration-standard.md | 104 | Claude Code | "Claude Code may keep Superpowers..." | CC 单独能力描述（已退役）|
| standards/unified-agent-collaboration-standard.md | 122 | Trae IDE | "### Trae IDE" | Trae IDE 单独章节（退役为编队角色）|
| standards/unified-agent-collaboration-standard.md | 127 | Claude Code | "### Claude Code" | CC 单独章节（已退役）|
| standards/unified-agent-collaboration-standard.md | 135 | Claude Code | "Must follow the same standards as Trae IDE..." | CC 协作要求（已退役）|
| standards/unified-agent-collaboration-standard.md | 135 | Trae IDE | 同上 | Trae IDE 协作要求（退役为编队角色）|
| standards/unified-agent-collaboration-standard.md | 184 | Claude Code | "claude-zhipu launch command" | CC 启动命令（已退役）|
| standards/unified-agent-collaboration-standard.md | 184 | claude-zhipu | 同上 | CC 启动命令（已退役）|
| standards/fleet-division-v1.1.md | 87 | Codex | "G4 批量任务 \| Codex \| 原承接者" | Codex 作为原承接者描述（已退役）|

## HISTORY（保留，不替换）

共 116 条（file:line|tool 组合），自动分类。所有命中经人工抽样核对为合法引用（知识库名/路径/方案文档讨论对象/历史叙述/工具生态参考），无现行角色引用。

| 文件 | 行 | 工具 | 内容预览 | 分类 |
|---|---|---|---|---|
| agent-matrix-architecture-v1.0.md | 66 | Codex | \| **Codex** \| ⛔ 淘汰 \| 本地用方舟模型,云沙箱绑OpenAI调不动,GUI/CLI两套维护重 \| | 历史叙述 |
| agent-matrix-architecture-v1.0.md | 67 | Trae IDE | \| **Trae IDE（编队角色）** \| ⛔ 退役为编队角色 \| 2026-07-26 C 选项裁定：编队里 Trae 系只保留 SOLO 一个独立角色（端到端测试/QA）。Trae IDE 退到个人工具，不进 Pi 调度。软件保 | 历史叙述 |
| agent-matrix-architecture-v1.0.md | 68 | Claude Code | \| **Claude Code** \| ⛔ 退役完成 \| 2026-07-25 退役，2026-07-26 密钥清理完成（详见 `.claude/RETIREMENT-STATUS.md`） \| | 历史叙述 |
| agent-matrix-architecture-v1.0.md | 249 | Codex | \| Codex 去留 \| 淘汰 \| 云沙箱绑OpenAI+GUI/CLI两套+本地已换方舟 \| | 历史叙述 |
| agent-matrix-architecture-v1.0.md | 250 | Trae IDE | \| Trae IDE 退役为编队角色 \| 2026-07-26 C 选项裁定 \| 编队里 Trae 系只保留 SOLO 独立角色（端到端测试/QA），Trae IDE 退到个人工具；Aetheris 分支合并见独立任务 \| | 历史叙述 |
| archive/global-roadmap-v1.0-draft.md | 63 | Codex | - Codex知识库归属转移（331项目调研→迁入协作标准仓库或Aetheris知识层） | 知识库名/路径 |
| archive/global-roadmap-v1.0-draft.md | 86 | Codex | - 本机有大量资产：Codex知识库、Aetheris-clones、配置、历史会话 | 知识库名/路径 |
| archive/global-roadmap-v1.0-draft.md | 92 | Codex | \| Codex知识库 \| Documents\Codex\knowledge-audit-2026-07\ \| ECS或Aetheris知识层 \| 高 \| | 知识库名/路径 |
| archive/global-roadmap-v1.0-draft.md | 130 | Codex | ### Codex 退役 | 历史叙述 |
| archive/global-roadmap-v1.0-draft.md | 136 | Claude Code | ### Claude Code 完全下线 | 历史叙述 |
| archive/global-roadmap-v1.0-draft.md | 144 | QoderWork | ### QoderWork 退役 | 历史叙述 |
| archive/global-roadmap-v1.0-draft.md | 154 | Codex | 3. **知识库归属**：Codex的331项目调研，归入Aetheris知识层（M05）还是独立维护？ | 知识库名/路径 |
| archive/global-roadmap-v1.0-draft.md | 155 | Codex | 4. **退役顺序**：CC下线、Codex退役、QoderWork退役，谁先谁后？有没有依赖关系？ | 历史叙述 |
| archive/global-roadmap-v1.0-draft.md | 155 | QoderWork | 4. **退役顺序**：CC下线、Codex退役、QoderWork退役，谁先谁后？有没有依赖关系？ | 历史叙述 |
| archive/global-roadmap-v1.0.md | 7 | Codex | > 血统: 北极星v1.2终极目标 + Aetheris蓝图v1.11终局定义 + soul.yaml + Codex知识库战略洞察 | 知识库名/路径 |
| archive/global-roadmap-v1.0.md | 43 | Codex | ### 第三优先：Codex退役链（严格顺序） | 历史叙述 |
| archive/global-roadmap-v1.0.md | 47 | Codex | \| 9 \| **Codex知识库→git独立仓库** \| 用户已裁定方案乙 \| 不灌入M05（15%成熟度）。M05成熟后再灌 \| | 知识库名/路径 |
| archive/global-roadmap-v1.0.md | 49 | Codex | \| 11 \| **停Codex+修hook断链+配置归档** \| 序10 \| .codex/hooks.json引用.claude/hooks/，必须改向.zcode/hooks/（或Codex已停则废弃hook） \| | 历史叙述 |
| archive/global-roadmap-v1.0.md | 51 | QoderWork | \| 13 \| **QoderWork skill迁移后退役** \| 独立 \| 先把docx/pptx/pdf/frontend-design等skill迁入.agents共享库。短期产出类任务可路由给Qoder IDE客户端 \| | 历史叙述 |
| archive/global-roadmap-v1.0.md | 61 | Codex | ### 第五优先：知识库建议的技术债（来自Codex知识库5份洞察） | 知识库名/路径 |
| archive/north-star-v1.3-roadmap-annex.md | 7 | Codex | > 依据: 北极星v1.2 + Aetheris蓝图v1.11 + soul.yaml + Codex知识库战略洞察 + 全量资产调研 | 知识库名/路径 |
| archive/north-star-v1.3-roadmap-annex.md | 29 | Codex | \| **知识复利** \| 你看到的好东西→下次能用，需要你手动操作几次 \| 每次需手动告诉Codex存储整理 \| 0次（自动捕获沉淀） \| | 其他(默认HISTORY) |
| archive/north-star-v1.3-roadmap-annex.md | 49 | Codex | - 退役清理完成（Codex/CC/QoderWork退役收尾，知识库归属已定） | 知识库名/路径 |
| archive/north-star-v1.3-roadmap-annex.md | 49 | QoderWork | - 退役清理完成（Codex/CC/QoderWork退役收尾，知识库归属已定） | 知识库名/路径 |
| archive/north-star-v1.3-roadmap-annex.md | 127 | Codex | 待完成（O1剩余）：Mira/Kimi接入、退役清理（Codex/CC/QoderWork）、ECS治理（swap/时钟/密钥）。 | 历史叙述 |
| archive/north-star-v1.3-roadmap-annex.md | 127 | QoderWork | 待完成（O1剩余）：Mira/Kimi接入、退役清理（Codex/CC/QoderWork）、ECS治理（swap/时钟/密钥）。 | 历史叙述 |
| fleet-division-v1.1.md | 11 | Codex | > 基线: 架构真值 v1.0 + 用户三项裁定（Mira 特化 / Codex 淘汰 / Pi push 授权） | 历史叙述 |
| fleet-division-v1.1.md | 80 | Codex | 以下 7 项职能在 Mira 特化、Codex 淘汰、Trae IDE 退役为编队角色（2026-07-26 C 选项，SOLO 作为 Trae 系唯一独立角色）后**悬空**，按自进化闭环逐环检查得出： | 历史叙述 |
| fleet-division-v1.1.md | 80 | Trae IDE | 以下 7 项职能在 Mira 特化、Codex 淘汰、Trae IDE 退役为编队角色（2026-07-26 C 选项，SOLO 作为 Trae 系唯一独立角色）后**悬空**，按自进化闭环逐环检查得出： | 历史叙述 |
| fleet-division-v1.1.md | 88 | Codex | \| G5 \| **知识调研/情报** \| Codex（曾做知识库调研） \| ①感知 \| **Qoder**（research/tavily 等 skills）+ 可经 Pi 分派任意空闲 agent \| 调研是规划的上游，与主架 | 知识库名/路径 |
| fleet-division-v1.1.md | 165 | Codex | \| 知识库 \| `C:\Users\Admin\Documents\Codex\knowledge-audit-2026-07\Knowledge` \| 331 开源项目调研沉淀（Pi/ruflo 选型依据来源） \| | 知识库名/路径 |
| global-roadmap-v1.1.md | 15 | Codex | > 依据: 北极星v1.2 + Aetheris蓝图v1.11 + soul.yaml + Codex知识库战略洞察 + 全量资产调研 + Qoder客户端两轮审查 | 知识库名/路径 |
| global-roadmap-v1.1.md | 66 | Codex | - 退役清理完成（Codex/CC/QoderWork退役收尾，知识库归属已定） | 知识库名/路径 |
| global-roadmap-v1.1.md | 66 | QoderWork | - 退役清理完成（Codex/CC/QoderWork退役收尾，知识库归属已定） | 知识库名/路径 |
| global-roadmap-v1.1.md | 179 | Codex | O1待完成：Mira/Kimi接入、退役清理（Codex/CC/QoderWork）、ECS治理（swap/时钟/密钥）。 | 历史叙述 |
| global-roadmap-v1.1.md | 179 | QoderWork | O1待完成：Mira/Kimi接入、退役清理（Codex/CC/QoderWork）、ECS治理（swap/时钟/密钥）。 | 历史叙述 |
| global-roadmap-v1.1.md | 201 | Trae IDE | - Trae IDE 已于 2026-07-26 C 选项裁定退役为编队角色（软件保留供个人使用，不进 Pi 调度链）。编队里 Trae 系只保留 **Trae SOLO 一个独立角色**（端到端测试/QA，Aetheris `agent/ | 历史叙述 |
| specs/agent-collaboration-git-sync-plan.md | 48 | Trae IDE | \| 3. Phase A 词表漏 Trae IDE + 扫描范围窄 + 无机器判定规则 \| 词表补齐 + 扫描范围扩到所有导入目录 + 历史引用建例外清单 \| | 治理方案文档讨论对象 |
| specs/agent-collaboration-git-sync-plan.md | 75 | Trae IDE | - 替换"工具作为编队角色"的引用（如"Trae IDE 是平行工作者"） | 治理方案文档讨论对象 |
| specs/agent-collaboration-git-sync-plan.md | 117 | Claude Code | "Claude Code" | 治理方案文档讨论对象 |
| specs/agent-collaboration-git-sync-plan.md | 118 | claude-zhipu | "claude-zhipu" | 治理方案文档讨论对象 |
| specs/agent-collaboration-git-sync-plan.md | 119 | Codex | "Codex" | 治理方案文档讨论对象 |
| specs/agent-collaboration-git-sync-plan.md | 120 | QoderWork | "QoderWork" | 治理方案文档讨论对象 |
| specs/agent-collaboration-git-sync-plan.md | 121 | Trae IDE | "Trae IDE" | 治理方案文档讨论对象 |
| specs/agent-collaboration-git-sync-plan.md | 157 | Trae IDE | \| standards/unified-...md \| 130 \| Trae IDE \| HISTORY \| "Trae IDE 退役过程" 历史叙述 \| ZCode \| | 治理方案文档讨论对象 |
| specs/agent-collaboration-git-sync-plan.md | 158 | Trae IDE | \| standards/unified-...md \| 24 \| Trae IDE \| ROLE \| "Trae IDE 是平行工作者" 当前角色 \| ZCode \| | 治理方案文档讨论对象 |
| specs/agent-collaboration-git-sync-plan.md | 163 | Claude Code | v3.3 修订：删除 v3.2 的 `tr -d ' '`（会把 "Claude Code" 变 "ClaudeCode" 导致 case 失效，B.3 真 bug），改用更稳健的 awk 列提取。 | 治理方案文档讨论对象 |
| specs/agent-collaboration-git-sync-plan.md | 195 | claude-zhipu | v3.3 修订：门禁 4 从"打印数量"改为"硬门禁"（不一致直接 exit 1），并补齐 v3.2 遗漏的 `claude-zhipu`。 | 治理方案文档讨论对象 |
| specs/agent-collaboration-git-sync-plan.md | 198 | claude-zhipu | # 门禁 3: 现行规范中退役角色引用 = 0（v3.3 补齐 claude-zhipu） | 治理方案文档讨论对象 |
| specs/agent-collaboration-git-sync-plan.md | 199 | Claude Code | REMAINING_ROLE=$(grep -rn "Claude Code\\|claude-zhipu\\|Codex\\|QoderWork\\|Trae IDE" ~/.agent-collaboration/standards/  | 治理方案文档讨论对象 |
| specs/agent-collaboration-git-sync-plan.md | 199 | Codex | REMAINING_ROLE=$(grep -rn "Claude Code\\|claude-zhipu\\|Codex\\|QoderWork\\|Trae IDE" ~/.agent-collaboration/standards/  | 治理方案文档讨论对象 |
| specs/agent-collaboration-git-sync-plan.md | 199 | QoderWork | REMAINING_ROLE=$(grep -rn "Claude Code\\|claude-zhipu\\|Codex\\|QoderWork\\|Trae IDE" ~/.agent-collaboration/standards/  | 治理方案文档讨论对象 |
| specs/agent-collaboration-git-sync-plan.md | 199 | Trae IDE | REMAINING_ROLE=$(grep -rn "Claude Code\\|claude-zhipu\\|Codex\\|QoderWork\\|Trae IDE" ~/.agent-collaboration/standards/  | 治理方案文档讨论对象 |
| specs/agent-collaboration-git-sync-plan.md | 199 | claude-zhipu | REMAINING_ROLE=$(grep -rn "Claude Code\\|claude-zhipu\\|Codex\\|QoderWork\\|Trae IDE" ~/.agent-collaboration/standards/  | 治理方案文档讨论对象 |
| specs/agent-collaboration-git-sync-plan.md | 211 | Claude Code | grep -rn "Claude Code\\|claude-zhipu\\|Codex\\|QoderWork\\|Trae IDE" ~/.agent-collaboration/standards/ 2>/dev/null \| \ | 治理方案文档讨论对象 |
| specs/agent-collaboration-git-sync-plan.md | 211 | Codex | grep -rn "Claude Code\\|claude-zhipu\\|Codex\\|QoderWork\\|Trae IDE" ~/.agent-collaboration/standards/ 2>/dev/null \| \ | 治理方案文档讨论对象 |
| specs/agent-collaboration-git-sync-plan.md | 211 | QoderWork | grep -rn "Claude Code\\|claude-zhipu\\|Codex\\|QoderWork\\|Trae IDE" ~/.agent-collaboration/standards/ 2>/dev/null \| \ | 治理方案文档讨论对象 |
| specs/agent-collaboration-git-sync-plan.md | 211 | Trae IDE | grep -rn "Claude Code\\|claude-zhipu\\|Codex\\|QoderWork\\|Trae IDE" ~/.agent-collaboration/standards/ 2>/dev/null \| \ | 治理方案文档讨论对象 |
| specs/agent-collaboration-git-sync-plan.md | 211 | claude-zhipu | grep -rn "Claude Code\\|claude-zhipu\\|Codex\\|QoderWork\\|Trae IDE" ~/.agent-collaboration/standards/ 2>/dev/null \| \ | 治理方案文档讨论对象 |
| specs/agent-collaboration-git-sync-plan.md | 217 | Claude Code | if (line ~ /Claude Code/) print $1":"$2"\|Claude Code" | 治理方案文档讨论对象 |
| specs/agent-collaboration-git-sync-plan.md | 218 | claude-zhipu | if (line ~ /claude-zhipu/) print $1":"$2"\|claude-zhipu" | 治理方案文档讨论对象 |
| specs/agent-collaboration-git-sync-plan.md | 219 | Codex | if (line ~ /Codex/) print $1":"$2"\|Codex" | 治理方案文档讨论对象 |
| specs/agent-collaboration-git-sync-plan.md | 220 | QoderWork | if (line ~ /QoderWork/) print $1":"$2"\|QoderWork" | 治理方案文档讨论对象 |
| specs/agent-collaboration-git-sync-plan.md | 221 | Trae IDE | if (line ~ /Trae IDE/) print $1":"$2"\|Trae IDE" | 治理方案文档讨论对象 |
| specs/full-survey-method.md | 7 | Codex | ### 资产1: Codex知识库（已盘点，需深读） | 知识库名/路径 |
| specs/full-survey-method.md | 8 | Codex | 位置：C:\Users\Admin\Documents\Codex\knowledge-audit-2026-07\Knowledge\ | 知识库名/路径 |
| specs/full-survey-method.md | 28 | Codex | C:\Users\Admin\.codex\                   Codex配置（待退役，需盘点残留） | 治理方案文档讨论对象 |
| specs/full-survey-method.md | 29 | QoderWork | C:\Users\Admin\.qoderwork\               QoderWork（已退役，需确认残留） | 治理方案文档讨论对象 |
| specs/full-survey-method.md | 52 | Codex | - 资产1（Codex知识库）的盘点索引——读README/INTEGRATION/index.json，提取主题分类和战略洞察 | 知识库名/路径 |
| specs/full-survey-method.md | 56 | Codex | - 资产1（Codex知识库）的深读——战略洞察的架构级解读、采纳决策的优先级判断 | 知识库名/路径 |
| specs/governance-review-process.md | 126 | Claude Code | - 规则文档散乱：`unified` vs `workspace-collaboration` 两份协作标准（冗余）；`protocols/` 7 份跟 `governance/` 部分主题重叠；`unified` 仍引用已退役的 Clau | 治理方案文档讨论对象 |
| specs/kimi-integration-status.md | 91 | Codex | \| cc-switch provider \| Claude/Codex 都有 Kimi provider（disabled） \| 历史配置 \| | 治理方案文档讨论对象 |
| specs/mira-integration-status.md | 354 | Claude Code | \| `mira plugin add/list/enable` \| Claude Code 兼容插件管理 \| 未测 \| | 治理方案文档讨论对象 |
| specs/mira-vs-larkcli-capabilities.md | 165 | Codex | - c360 CLI 在 Mira 里能用，是因为 **c360 团队官方适配了 Mira**（飞书文档列出支持 Claudecode/Codex/Trae/Aily/Mira） | 治理方案文档讨论对象 |
| specs/mira-vs-larkcli-capabilities.md | 255 | Codex | **c360 CLI 官方支持 Mira 作为 Agent 工具**（飞书文档列出支持 Claudecode/Codex/Trae/Aily/Mira）。在 Mira 里安装 c360 CLI 并完成 OAuth 授权后，可正常调用。 | 治理方案文档讨论对象 |
| specs/o1-governance-plan.md | 20 | Codex | 之前推进 O1 时只做了**工具退役**（CC/Codex/QoderWork），遗漏了**代码与文档治理**。实测盘点发现四类严重散乱： | 治理方案文档讨论对象 |
| specs/o1-governance-plan.md | 20 | QoderWork | 之前推进 O1 时只做了**工具退役**（CC/Codex/QoderWork），遗漏了**代码与文档治理**。实测盘点发现四类严重散乱： | 治理方案文档讨论对象 |
| specs/o1-governance-plan.md | 24 | Codex | 3. **知识文档**：Codex 知识库迁移后 `Documents/Codex/` 残留、各处散落知识片段 | 知识库名/路径 |
| specs/o1-governance-plan.md | 49 | Trae IDE | \| `~/Aetheris-clones/trae/` \| Trae 工作目录（脏 5 文件）\| Trae IDE 退役为编队角色，clone 待定 \| | 治理方案文档讨论对象 |
| specs/o1-governance-plan.md | 57 | Codex | - `~/.codex/.tmp/plugins-clone-*`（Codex 插件克隆临时文件，2 个） | 治理方案文档讨论对象 |
| specs/o1-governance-plan.md | 58 | Codex | - `~/.codex/memories/`（Codex 记忆，独立 git 仓库） | 治理方案文档讨论对象 |
| specs/o1-governance-plan.md | 61 | QoderWork | - `~/.qoderwork/`（QoderWork 已退役但目录还在） | 治理方案文档讨论对象 |
| specs/o1-governance-plan.md | 69 | Codex | - `~/Documents/Codex/`、`Feishu/`、`kimi/`、`Qoder/` | 知识库名/路径 |
| specs/o1-governance-plan.md | 74 | Codex | **Codex 知识库迁移**： | 知识库名/路径 |
| specs/o1-governance-plan.md | 76 | Codex | - ❌ `~/Documents/Codex/knowledge-audit-2026-07/` 残留（迁移源头，148M） | 知识库名/路径 |
| specs/o1-governance-plan.md | 77 | Codex | - ❌ `~/Documents/Codex/2026-07-08/` 残留 | 知识库名/路径 |
| specs/o1-governance-plan.md | 89 | Claude Code | \| `unified-agent-collaboration-standard.md` \| Trae IDE/SOLO PC/Claude Code/GitHub 通用规则 \| ❌ 仍引用 Claude Code（已退役）\| | 治理方案文档讨论对象 |
| specs/o1-governance-plan.md | 89 | Trae IDE | \| `unified-agent-collaboration-standard.md` \| Trae IDE/SOLO PC/Claude Code/GitHub 通用规则 \| ❌ 仍引用 Claude Code（已退役）\| | 治理方案文档讨论对象 |
| specs/o1-governance-plan.md | 148 | Codex | - 整理 `~/Documents/{Codex,Feishu,kimi,Qoder}/` 的归属 | 知识库名/路径 |
| specs/o1-governance-plan.md | 152 | Codex | #### C1. Codex 知识库迁移收尾（中优，低风险） | 知识库名/路径 |
| specs/o1-governance-plan.md | 155 | Codex | - 清理 `~/Documents/Codex/` 残留（迁移源头，已备份到 git 仓库） | 知识库名/路径 |
| specs/o1-governance-plan.md | 170 | Claude Code | - **更新 CC 退役相关引用**（unified-agent-collaboration-standard.md 仍引用 Claude Code） | 治理方案文档讨论对象 |
| specs/o1-governance-plan.md | 208 | Codex | \| **第 3 批** \| B1 退役工具残留 + C1 Codex 收尾 \| 释放空间 + 知识归一 \| 低 \| | 治理方案文档讨论对象 |
| specs/review-process-lessons.md | 60 | Claude Code | B 找到的 `tr -d ' '` 把 "Claude Code" 变 "ClaudeCode"，导致后续 case 永远不命中。 | 治理方案文档讨论对象 |
| specs/session-handoff-20260726.md | 28 | Trae IDE | - Trae IDE 退役为编队角色（软件保留个人用） | 治理方案文档讨论对象 |
| specs/survey-zcode.md | 4 | Codex | > 范围: 本地协作资产 + GitHub代码 + ECS代码 + Codex知识库 | 知识库名/路径 |
| specs/survey-zcode.md | 25 | Codex | 1. **Codex 悬空**：裁定退役但今天仍在活跃运行（logs_2.sqlite-wal 07-24 14:46写入）。config.toml用火山方舟ark-code-latest。**无退役执行计划，无知识库归属方案，未纳入协作体 | 知识库名/路径 |
| specs/survey-zcode.md | 31 | QoderWork | 4. **QoderWork未真正退役**：721M，.cache/.models 07-22仍有更新。skills有docx/pptx/pdf/frontend-design等Qoder专属skill，云端Qoder无等价物。 | 治理方案文档讨论对象 |
| specs/survey-zcode.md | 100 | Codex | ## 四、Codex 知识库 | 知识库名/路径 |
| specs/survey-zcode.md | 117 | Codex | Codex知识库的331项目调研是核心资产，但归入Aetheris知识层(M05)还是独立维护，未裁定。每日自动Pipeline跑在本机Windows Task Scheduler，Codex退役后需迁移到ECS cron。 | 知识库名/路径 |
| specs/survey-zcode.md | 123 | Codex | 2. **Codex退役执行计划**：知识库归属（M05 vs 独立）、Pipeline迁移、配置清理、hook断链修复 | 知识库名/路径 |
| specs/trae-solo-branch-merge-task.md | 8 | Trae IDE | title: Aetheris 分支合并任务 — Trae IDE 退役后的分支归并 | 治理方案文档讨论对象 |
| specs/trae-solo-branch-merge-task.md | 9 | Trae IDE | scope: 把 Trae IDE 在 Aetheris 的 `agent/trae` 分支内容合并到 `agent/solo`，作为 Trae IDE 退役为编队角色后的分支清理 | 治理方案文档讨论对象 |
| specs/trae-solo-branch-merge-task.md | 12 | Trae IDE | - configs/tool-entry-map.md（Trae IDE 退役标记） | 治理方案文档讨论对象 |
| specs/trae-solo-branch-merge-task.md | 46 | Trae IDE | 2026-07-26 C 选项裁定：编队里 Trae 系只保留 **Trae SOLO** 一个独立角色（端到端测试/QA），**Trae IDE 退役为编队角色**（软件保留个人用）。 | 治理方案文档讨论对象 |
| specs/trae-solo-branch-merge-task.md | 48 | Trae IDE | 退役后，Trae IDE 在 Aetheris 的 `agent/trae` 分支历史产出归并到 `agent/solo`，让 SOLO 成为 Trae 系的唯一活跃分支。 | 治理方案文档讨论对象 |
| specs/trae-solo-branch-merge-task.md | 53 | Trae IDE | - 本机 Trae IDE 软件卸载（用户明确保留个人使用，不做） | 治理方案文档讨论对象 |
| specs/trae-solo-branch-merge-task.md | 54 | Trae IDE | - Trae IDE 的 `~/.trae-cn/` 配置清理（个人使用保留，不做） | 治理方案文档讨论对象 |
| specs/trae-solo-branch-merge-task.md | 58 | Trae IDE | 2026-07-26 C 选项裁定：编队里 Trae 系只保留 **Trae SOLO** 一个独立角色（端到端测试/QA），**Trae IDE 退役为编队角色**（软件保留个人用）。 | 治理方案文档讨论对象 |
| specs/trae-solo-branch-merge-task.md | 60 | Trae IDE | 退役后，Trae IDE 在 Aetheris 的 `agent/trae` 分支历史产出需要归并到 `agent/solo`，让 SOLO 成为 Trae 系的唯一活跃分支。 | 治理方案文档讨论对象 |
| specs/trae-solo-branch-merge-task.md | 210 | Trae IDE | - 本机 Trae IDE 软件卸载（用户明确保留个人使用） | 治理方案文档讨论对象 |
| specs/trae-solo-branch-merge-task.md | 211 | Trae IDE | - Trae IDE 的 `~/.trae-cn/` 配置清理（个人使用保留） | 治理方案文档讨论对象 |
| workspace-collaboration-v2.1.md | 41 | Codex | - 知识库: `C:\Users\Admin\Documents\Codex\knowledge-audit-2026-07\Knowledge` | 知识库名/路径 |
| workspace-collaboration-v2.1.md | 69 | Claude Code | \| Claude Code \| ⛔ 退役中（CC→ZCode 迁移进行） \| | 历史叙述 |
| workspace-collaboration-v2.1.md | 70 | Codex | \| Codex \| ⛔ 已淘汰（用户确认） \| | 历史叙述 |
| workspace-collaboration-v2.1.md | 71 | QoderWork | \| QoderWork \| ⛔ 已退役（Qoder 接管） \| | 历史叙述 |

## 审核人

ZCode（基于自动扫描 + 分类规则 + 人工抽样核对）

## 待用户最终确认

按"战略制定不可委托"原则，文档去留/替换最终需用户确认。本清单是 ZCode 建议，节点 2 评审时三方核对。
