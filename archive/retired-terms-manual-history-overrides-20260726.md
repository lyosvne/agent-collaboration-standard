# 退役工具引用 - 人工确认 HISTORY 覆盖清单（round4）

> 用途: rebuild-exceptions.py 最严收窄后, 部分合法 HISTORY 引用（知识资产/迁移/兼容性/方案代码）
>       不含明确历史关键词, 会被 classify raise。本文件是 ZCode 逐条人工判定为 HISTORY 的覆盖清单。
> 加载: rebuild-exceptions.py 读本文件, 命中此清单的跳过 classify, 直接归 HISTORY。
> 维护: 新增退役工具引用若被 raise 且确属 HISTORY, 加到此清单（附判定理由）。
>
> 判定原则（round4 ZCode 逐条确认）:
>   - 现行角色引用（把退役工具当当前编队成员描述能力）→ 不入此清单, 走 Phase A 替换
>   - 历史资产/迁移任务/兼容性描述/方案代码示例 → 入此清单（合法 HISTORY）

## 覆盖清单

格式: `文件 | 行 | 工具 | 判定理由`

| 文件 | 行 | 工具 | 判定理由 |
|---|---|---|---|
| fleet-division-v1.1.md | 165 | Codex | Codex 知识库资产路径（历史资产, 非编队角色）|
| global-roadmap-v1.1.md | 15 | Codex | 路线图依据引用 Codex 知识库战略洞察（历史资产）|
| specs/agent-collaboration-git-sync-plan.md | 75 | Trae IDE | 方案文档讨论"替换工具角色引用"的示例 |
| specs/agent-collaboration-git-sync-plan.md | 150 | Trae IDE | 方案文档 ROLE 标记说明（含[RETIRED-示例, 是方案讨论）|
| specs/agent-collaboration-git-sync-plan.md | 158 | Trae IDE | 方案文档 ROLE 标注示例表 |
| specs/agent-collaboration-git-sync-plan.md | 179 | Claude Code | 方案 bash case 示例（placeholder 映射）|
| specs/agent-collaboration-git-sync-plan.md | 180 | claude-zhipu | 方案 bash case 示例（placeholder 映射）|
| specs/agent-collaboration-git-sync-plan.md | 181 | Codex | 方案 bash case 示例（placeholder 映射）|
| specs/agent-collaboration-git-sync-plan.md | 182 | QoderWork | 方案 bash case 示例（placeholder 映射）|
| specs/agent-collaboration-git-sync-plan.md | 183 | Trae IDE | 方案 bash case 示例（placeholder 映射）|
| specs/agent-collaboration-git-sync-plan.md | 163 | Claude Code | 方案修订记录（历史变更叙述）|
| specs/agent-collaboration-git-sync-plan.md | 195 | claude-zhipu | 方案修订记录（历史变更叙述）|
| specs/agent-collaboration-git-sync-plan.md | 199 | Claude Code | 方案 bash 脚本示例（REMAINING_ROLE grep）|
| specs/agent-collaboration-git-sync-plan.md | 199 | claude-zhipu | 方案 bash 脚本示例 |
| specs/agent-collaboration-git-sync-plan.md | 199 | Codex | 方案 bash 脚本示例 |
| specs/agent-collaboration-git-sync-plan.md | 199 | QoderWork | 方案 bash 脚本示例 |
| specs/agent-collaboration-git-sync-plan.md | 199 | Trae IDE | 方案 bash 脚本示例 |
| specs/agent-collaboration-git-sync-plan.md | 211 | Claude Code | 方案 bash 脚本示例 |
| specs/agent-collaboration-git-sync-plan.md | 211 | claude-zhipu | 方案 bash 脚本示例 |
| specs/agent-collaboration-git-sync-plan.md | 211 | Codex | 方案 bash 脚本示例 |
| specs/agent-collaboration-git-sync-plan.md | 211 | QoderWork | 方案 bash 脚本示例 |
| specs/agent-collaboration-git-sync-plan.md | 211 | Trae IDE | 方案 bash 脚本示例 |
| specs/agent-collaboration-git-sync-plan.md | 217 | Claude Code | 方案 awk 脚本示例 |
| specs/agent-collaboration-git-sync-plan.md | 218 | claude-zhipu | 方案 awk 脚本示例 |
| specs/agent-collaboration-git-sync-plan.md | 219 | Codex | 方案 awk 脚本示例 |
| specs/agent-collaboration-git-sync-plan.md | 220 | QoderWork | 方案 awk 脚本示例 |
| specs/agent-collaboration-git-sync-plan.md | 221 | Trae IDE | 方案 awk 脚本示例 |
| specs/full-survey-method.md | 7 | Codex | Codex 知识库盘点（历史资产）|
| specs/full-survey-method.md | 8 | Codex | Codex 知识库路径（历史资产）|
| specs/full-survey-method.md | 52 | Codex | Codex 知识库盘点索引（历史资产）|
| specs/full-survey-method.md | 56 | Codex | Codex 知识库深读（历史资产）|
| specs/mira-integration-status.md | 354 | Claude Code | Mira 兼容 Claude Code 插件（工具兼容性, 非编队角色）|
| specs/mira-vs-larkcli-capabilities.md | 165 | Codex | c360 团队官方适配列表（工具兼容性）|
| specs/mira-vs-larkcli-capabilities.md | 255 | Codex | c360 官方支持列表（工具兼容性）|
| specs/node2-review-package-20260726.md | 90 | Codex | 评审包讨论 Codex 知识库引用（元文档）|
| specs/o1-governance-plan.md | 24 | Codex | Codex 知识库迁移后残留（迁移任务）|
| specs/o1-governance-plan.md | 57 | Codex | Codex 插件克隆临时文件路径（迁移清理）|
| specs/o1-governance-plan.md | 58 | Codex | Codex memories 路径（迁移清理）|
| specs/o1-governance-plan.md | 69 | Codex | Documents/Codex 路径（迁移清理）|
| specs/o1-governance-plan.md | 74 | Codex | Codex 知识库迁移任务（迁移）|
| specs/o1-governance-plan.md | 76 | Codex | Codex knowledge-audit 残留（迁移清理）|
| specs/o1-governance-plan.md | 77 | Codex | Codex 2026-07-08 残留（迁移清理）|
| specs/o1-governance-plan.md | 148 | Codex | Documents 归属整理（迁移清理）|
| specs/o1-governance-plan.md | 152 | Codex | Codex 知识库迁移收尾任务（迁移）|
| specs/o1-governance-plan.md | 155 | Codex | 清理 Codex 残留（迁移清理）|
| specs/review-process-lessons.md | 60 | Claude Code | 评审经验引用 tr bug（历史叙述）|
| specs/survey-zcode.md | 4 | Codex | 调研范围含 Codex 知识库（历史资产）|
| specs/survey-zcode.md | 100 | Codex | Codex 知识库章节（历史资产）|
| specs/trae-solo-branch-merge-task.md | 53 | Trae IDE | Trae IDE 软件卸载（工具状态, 个人使用保留）|
| specs/trae-solo-branch-merge-task.md | 54 | Trae IDE | Trae IDE 配置清理（工具状态）|
| specs/trae-solo-branch-merge-task.md | 210 | Trae IDE | 同 L53（工具状态）|
| specs/trae-solo-branch-merge-task.md | 211 | Trae IDE | 同 L54（工具状态）|
| workspace-collaboration-v2.1.md | 41 | Codex | 知识库路径引用（历史资产）|
| specs/node2-review-retrospective-20260726.md | 44 | Codex | 门禁绕过句构造示例（"in case Codex fails" 含 case）, 讨论启发式不可能零 fail-open 的反例, 非编队角色描述 |
| specs/pi-drift-governance-spec.md | 16 | Claude Code | §2 真值层对照声明（"Claude Code / Trae IDE 已退役"）, 历史叙述 |
| specs/pi-drift-governance-spec.md | 16 | Trae IDE | 同 L16, 真值层对照声明（历史叙述）|
| specs/pi-drift-governance-spec.md | 30 | Claude Code | §2 已退役分支记录（"Claude Code 2026-07-25 退役, 分支冻结"）, 历史叙述 |
| specs/pi-drift-governance-spec.md | 31 | Trae IDE | §2 已退役分支记录（"Trae IDE 2026-07-26 退役为编队角色"）, 历史叙述 |
| specs/pi-drift-governance-spec.md | 108 | Trae IDE | §7 实施形态注记（"原 agent/trae 已随 Trae IDE 退役"）, 历史叙述 |

## 审核人

ZCode（round4 逐条人工判定, 2026-07-26; Phase D-A 追加 1 条, 2026-07-26; Pi 治理纳入 A 层追加 5 条, 2026-07-26）

## 复核要求

节点 2 round4 评审方应抽查此清单（如随机 5 条）, 确认判定合理。
若发现误判（现行角色引用混入）, 标阻断要求 ZCode 重新判定。
