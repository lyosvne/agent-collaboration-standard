# Multi-Agent Development Collaboration

This directory is the local, tool-level collaboration home for AI coding agents.
It is not project-specific.

## Purpose

- Keep human style, collaboration language, and completion standards consistent across tools.
- Let Pi, unified Trae, ZCode, Qoder, Kimi, Mira, GitHub, and future cloud agents hand work to each other safely.
- Keep project rules inside each project and tool rules here.

## Read Order

1. `START_HERE.md`
2. `governance/unified-agent-collaboration-standard.md`
3. `registry/skill-registry.md`
4. `templates/handoff-pack.md`
5. `configs/tool-entry-map.md`
6. `specs/pi-cognitive-plane-and-self-evolution-v1.0.md`

> 2026-08-08：原 Trae 与 Solo 已合并为统一 Trae。`configs/trae-solo-*` 只保留历史证据，不再作为活动入口。

## Useful Operating Files

- `governance/cloud-agent-connection-protocol.md`
- `templates/cloud-agent-task-pack.md`
- `templates/agent-entry-checklist.md`
- `templates/skill-usage-log.md`
- `project-starter/AGENTS.md.template`
- `project-starter/PROJECT_RULES_CHECKLIST.md`
- `audits/periodic-health-check.md`
- `registry/skill-governance.md`
- `registry/learning-ingestion-pipeline.md`

## Phase D 存储降级声明（2026-07-26）

本机 `C:\Users\Admin\.agent-collaboration\` 自 2026-07-26 Phase D 起降级为**只读历史快照**，不再作活跃真值存储。

| 资源 | Phase D 前 | Phase D 后 |
|---|---|---|
| 治理文档真值 | `~/.agent-collaboration/standards/` | git 仓库 `governance/`（本机快照仅作历史参考） |
| secret 扫描 patterns | `~/.agent-collaboration/archive/secret-patterns/` | `~/.config/agent-collaboration/secret-patterns/`（含 token 不入 git，环境变量 `SECRET_PATTERNS_DIR` 可覆盖） |
| exceptions/overrides | `~/.agent-collaboration/archive/` | git 仓库 `archive/`（已纳入 git 真值） |
| scripts 扫描基准 | 扫本机 `standards/`（滞后） | 扫 git 仓库 `governance/`（真值，环境变量 `STANDARDS_SCAN_DIR` 可覆盖） |

**物理删除**：本机 `~/.agent-collaboration/` 暂不物理删除（过渡期保留双源），物理删除留第 5 批长期卫生阶段，需用户单独授权。`~/.agent-collaboration/archive/secret-patterns/` 旧位置已冻结（B.2 起 scripts 只读新位置）。

## Hard Truth

- GitHub commit, branch, and PR are the only hard code sync points.
- Chat history is not a source of truth.
- Runtime state is not a source of truth.
- A task is not complete without verification evidence and a handoff summary.
