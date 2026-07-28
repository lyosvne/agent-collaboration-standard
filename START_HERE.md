# Start Here For Coding Agents

Read this before any coding-agent work.

## One Rule

Use one shared operating language across all fleet agents (current roster: ZCode / Qoder / Kimi / Mira / Trae SOLO / Pi; see `workspace-collaboration-v2.1.md` §2 for the authoritative roster).

GitHub standard source: `https://github.com/lyosvne/agent-collaboration-standard`.

## Read Order (节点 3 重构为单一分层入口)

> 阅读顺序按"方向 → 治理 → 操作 → 按需专题"分层。每次开工按此顺序加载上下文。

### 所有任务必读（方向 + 治理 + 操作）

1. **北极星（方向）**: `governance/north-star-v1.2.md` — 终局/第一性原则/红线/不可委托清单
2. **协作协议（治理）**: `governance/workspace-collaboration-v2.1.md` — 权威/编队注册/任务路由/双环治理（**编队名单与路由的唯一权威**）
3. **Agent Operating Standard（操作）**: `governance/unified-agent-collaboration-standard.md` — 启动/执行/验证/交接的字段、命令、流程、纪律

### 按需读取（专题 + 路由辅助）

4. **全局路线图（执行罗盘）**: `governance/global-roadmap-v1.1.md` — 七维度/四阶段O/KR/当前位置
5. **编队分工（组织链）**: `governance/fleet-division-v1.1.md` — G/M 双环职能映射（涉及职责边界/owner 争议时）
6. **架构真值**: `governance/agent-matrix-architecture-v1.0.md` — 涉及架构/接入方式时
7. `registry/skill-registry.md` + `registry/skill-governance.md` — Skill 能力与治理
8. `templates/handoff-pack.md` — 需要交接时
9. `configs/tool-entry-map.md` — 工具入口与能力适配
10. `governance/cloud-agent-connection-protocol.md` — 涉及云端 agent 时
11. Project-specific entry files after entering a project.
12. **治理 hook 基础设施（ZCode 专属，但原则编队共享）**: `governance/specs/governance-infrastructure-status.md` — 5 个 ZCode hook（chain/session/review/bootstrap/drift-gate）全景 + 四闸门拦截矩阵 + 漂移面。涉及 hook 行为/评审调度/compact 续接时查。配套原则：`governance/specs/cross-boundary-state-transfer-principle.md`（跨边界状态传递元原则）。

Truth source: `https://github.com/lyosvne/agent-collaboration-standard` → `governance/` 目录
Local snapshot (read-only, 2026-07-26 Phase D 起降级为历史快照): `C:\Users\Admin\.agent-collaboration\standards\`

## Version Declaration Convention (版本声明约定)

**每个 agent 启动时，必须报告所读目标体系的版本**——这是软约束（O1阶段），硬约束（Pi回声hash）进O3。

报告格式（写入会话首条或工作日志）：
```
[TRUTH-VERSION] agent-collaboration-standard @ <commit-hash-前7位>
  north-star: v1.2
  roadmap: v1.1
  fleet-division: v1.1
```

获取commit hash:
- 本机: `cd C:\Users\Admin\Documents\trae_projects\agent-collaboration-standard && git rev-parse --short HEAD`
- ECS: `cd /opt/pi/governance-mirror/repo && git rev-parse --short HEAD`
- 云端/Qoder Cloud Agent: WebFetch `https://aetherisonline.xyz/dispatch/roadmap` 首部 frontmatter

冲突时按 commit hash 判新旧。如果你读的版本落后于真值源最新版，先 pull 再行动。


## Knowledge Base (Karpathy LLM Wiki)

All agents must consult the shared knowledge base before acting on cross-project questions:

- Path: `C:\Users\Admin\Documents\Codex\knowledge-audit-2026-07\Knowledge`
- Read order: `AGENTS.md` → `README.md` → `INTEGRATION.md` → `index.json`
- Contents: agent registry, OSS project analysis, skill catalog, audit insights, action roadmap
- Lint: `node C:\Users\Admin\Documents\Codex\knowledge-audit-2026-07\Knowledge\scripts\lint.js` to verify knowledge base health
- Ingest: Send article URLs to any agent with instruction "save to Knowledge base"

## Shared Commands

- `:ALL`: load global, project, task, coordination, and Git state before acting.
- `:ONE`: load the same state, select one owner, and keep other tools read-only.
- `:CHECK`: compare local rules, skills, memory, and project rules against GitHub truth. Read-only by default; append coordination result when safe.

## Minimum Start Output

- Goal:
- Source of truth:
- Owner:
- Scope:
- Risk:
- Verification:
- Next action:

## Minimum Finish Output

- Changed:
- Verified:
- Not verified:
- Risk:
- Commit / PR:
- Handoff:
- Recommended next command:
- Recommended next owner:
- Owner reason:

For changes, include rollback target, rollback method, and rollback verification.

For handoff, minimum required fields are Goal, Source of truth, Verification, and Next action.

## Tool Routing（节点 3 去名单化）

> 编队角色名单与任务路由的**唯一权威**是 `workspace-collaboration-v2.1.md` §2-§3。本节不复制名单（避免编队变化时多源漂移）。

- **GitHub**: only hard code sync point.
- **Cloud agents**: isolated workers through issue, branch, PR, or handoff pack.
- 当前编队成员、职责、路由：见 workspace §2-§3 + `fleet-division-v1.1.md`

## Local Machine Notes

- For GitHub network failures, do not write fixed `github.com` hosts entries first. Use default DNS if it passes `Resolve-DnsName`, `Test-NetConnection github.com -Port 443`, `curl -I https://github.com`, and `git ls-remote`.
- On this machine, ZCode is the primary tool (桌面应用, GLM-5.2). (历史) Claude Code launcher 已随退役归档.

## `:ONE` Rule

`:ONE` can be precise or fuzzy. If fuzzy, first normalize it into goal, owner, scope, risk, and next action. Do not edit until the safe owner and scope are clear.
