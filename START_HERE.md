# Start Here For Coding Agents

Read this before any coding-agent work.

## One Rule

Use one shared operating language across all fleet agents (current roster: Pi / unified Trae / ZCode / Qoder / Kimi / Mira; see `workspace-collaboration-v2.1.md` §2 for the authoritative roster).

GitHub standard source: `https://github.com/lyosvne/agent-collaboration-standard`.

## Read Order (节点 3 重构为单一分层入口)

> 阅读顺序按"方向 → 治理 → 操作 → 按需专题"分层。每次开工按此顺序加载上下文。

### 所有任务必读（方向 + 治理 + 操作）

1. **北极星（方向）**: `governance/north-star-v1.2.md` — 终局/第一性原则/红线/不可委托清单
2. **Pi 自进化规格（质量门）**: `specs/pi-cognitive-plane-and-self-evolution-v1.0.md`
3. **协作协议（治理）**: `governance/workspace-collaboration-v2.1.md` — 权威/编队注册/任务路由/双环治理（**编队名单与路由的唯一权威**）
4. **Agent Operating Standard（操作）**: `governance/unified-agent-collaboration-standard.md` — 启动/执行/验证/交接的字段、命令、流程、纪律

### 按需读取（专题 + 路由辅助）

5. **全局路线图（执行罗盘）**: `governance/global-roadmap-v1.1.md` — 七维度/四阶段O/KR/当前位置
6. **编队分工（组织链）**: `governance/fleet-division-v1.1.md` — G/M 双环职能映射（涉及职责边界/owner 争议时）
7. **架构真值**: `governance/agent-matrix-architecture-v1.0.md` — 涉及架构/接入方式时
8. `registry/skill-registry.md` + `registry/skill-governance.md` — Skill 能力与治理
9. `templates/handoff-pack.md` — 需要交接时
10. `configs/tool-entry-map.md` — 工具入口与能力适配
11. `governance/cloud-agent-connection-protocol.md` — 涉及云端 agent 时
12. Project-specific entry files after entering a project.
13. **治理 hook 基础设施（历史源自 ZCode，当前规则编队共享）**: `governance/specs/governance-infrastructure-status.md`。实现与集成由 Trae 承接，ZCode 只做非终端评审和分析。

Truth source: `https://github.com/lyosvne/agent-collaboration-standard` → `governance/` 目录
Local snapshot (read-only, 2026-07-26 Phase D 起降级为历史快照): `C:\Users\Admin\.agent-collaboration\standards\`

## Version Declaration Convention (版本声明约定)

**每个 agent 启动时，必须报告所读目标体系的版本**——这是软约束（O1阶段），硬约束（Pi回声hash）进O3。

报告格式（写入会话首条或工作日志）：
```
[TRUTH-VERSION] agent-collaboration-standard @ <commit-hash-前7位>
  north-star: <读取 frontmatter 或 version-manifest>
  roadmap: <读取 frontmatter 或 version-manifest>
  fleet-division: <读取 frontmatter 或 version-manifest>
```

获取commit hash:
- 本机/临时治理工作区: 在仓库根目录运行 `git rev-parse --short HEAD`
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
- ZCode 是非终端桌面 App，负责评审、分析、反哺和兜底；实现、Git、测试和集成由统一 Trae 承接。

## `:ONE` Rule

`:ONE` can be precise or fuzzy. If fuzzy, first normalize it into goal, owner, scope, risk, and next action. Do not edit until the safe owner and scope are clear.
