# Start Here For Coding Agents

Read this before any coding-agent work.

## One Rule

Use one shared operating language across ZCode, Trae IDE, Trae SOLO PC, Qoder, Kimi, Mira, GitHub, and cloud agents.

GitHub standard source: `https://github.com/lyosvne/agent-collaboration-standard`.

## Read Order

1. `governance/unified-agent-collaboration-standard.md`
2. `registry/skill-registry.md`
3. `templates/handoff-pack.md`
4. `configs/tool-entry-map.md`
5. `governance/cloud-agent-connection-protocol.md` when work involves cloud agents.
6. Project-specific entry files after entering a project.

## Target System (目标体系) — Read Before Acting on Goals

The target system has a single git truth source. Read in gradient order:

1. **北极星 (校准基准)**: `governance/north-star-v1.2.md` — 终局/第一性原则/红线/不可委托清单
2. **全局路线图 (执行罗盘)**: `governance/global-roadmap-v1.1.md` — 七维度/四阶段O/KR/评估反馈体系
3. **编队分工 (组织链)**: `governance/fleet-division-v1.1.md` — G/M双环治理模型
4. **架构真值**: `governance/agent-matrix-architecture-v1.0.md`
5. **协作协议**: `governance/workspace-collaboration-v2.1.md`

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

## Tool Routing

- Trae IDE: local integration lead and final closeout.
- ZCode: terminal orchestrator (接替 Claude Code), deep implementation, TDD, subagents, code review.
- Qoder: cloud execution node (REST API + SSE,可被调度).
- Kimi: cloud CLI worker (Pi subprocess 调度).
- Mira: cloud specialized (生图 + 评审).
- Trae SOLO PC: full autonomous executor.
- GitHub: only hard code sync point.
- Cloud agents: isolated workers through issue, branch, PR, or handoff pack.

## Local Machine Notes

- For GitHub network failures, do not write fixed `github.com` hosts entries first. Use default DNS if it passes `Resolve-DnsName`, `Test-NetConnection github.com -Port 443`, `curl -I https://github.com`, and `git ls-remote`.
- On this machine, ZCode is the primary tool (桌面应用, GLM-5.2). (历史) Claude Code launcher 已随退役归档.

## `:ONE` Rule

`:ONE` can be precise or fuzzy. If fuzzy, first normalize it into goal, owner, scope, risk, and next action. Do not edit until the safe owner and scope are clear.
