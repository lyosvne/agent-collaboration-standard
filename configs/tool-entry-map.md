# Tool Entry Map

This file maps where each coding agent should read global rules from.

## Shared Entry

All tools should start from the checked-out repository `START_HERE.md`, or fetch it from:

`https://github.com/lyosvne/agent-collaboration-standard`

> Phase D（2026-07-26）：真值源迁到 git 仓库。本机 `~/.agent-collaboration\` 降级为只读历史快照，不再作活跃入口。

## Pi

Primary entries:

- `START_HERE.md`
- `governance/north-star-v1.2.md`
- `specs/pi-cognitive-plane-and-self-evolution-v1.0.md`
- `governance/version-manifest.json`

Required behavior:

- Central coordination, routing and result convergence.
- Read governance through the ECS governance mirror.
- Do not execute code, Git writes, SSH, deployment or T3 operations.

## ZCode

Primary entries:

- `START_HERE.md`
- Project activity rules and ZCode effective context

Required behavior:

- Non-terminal knowledge assimilation, review, analysis, feedback and fallback.
- Do not execute shell, Git, code implementation, SSH or deployment.

## Unified Trae

Primary entries:

- `START_HERE.md`
- Project `AGENTS.md` and `COLLABORATION.md`
- `governance/workspace-collaboration-v2.1.md`

Required behavior:

- Implementation, integration, Git/PR/CI, product testing and browser validation.
- Inherits historical Trae and Solo responsibilities.
- Historical Solo branches and profiles are evidence only.

## GitHub

Primary entry:

- Branches, commits, PRs, issues, and releases.

Required behavior:

- GitHub is the hard code sync layer.
- Chat summaries are not enough.

## Cloud Agents

Primary entry:

- A handoff pack, issue, branch, or PR.

Required behavior:

- Do not rely on local chat memory.
- Return a PR, patch, or structured report.
- Use `templates/cloud-agent-task-pack.md` before execution.
