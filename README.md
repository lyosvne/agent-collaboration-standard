# Agent Collaboration Standard

Global collaboration standard for coding agents across repositories and tools.

This repository is above any single project. Project repositories should reference a released version of this standard, then define their own project-specific participants, source of truth, risk boundaries, and task records.

## Entry Points

1. `GLOBAL_AGENT_GUIDE.md`
2. `BOOTSTRAP_ONE_LINE.md`
3. `protocols/collaboration-state-protocol.md`
4. `protocols/git-truth-protocol.md`
5. `protocols/concurrent-work-protocol.md`
6. `protocols/verification-protocol.md`
7. `protocols/handoff-protocol.md`
8. `protocols/security-boundary-protocol.md`
9. `TOOL_ROLE_MATRIX.md`

## Core Rule

Global rules should be stable and infrequently changed. Project rules should stay thin and point to this standard instead of copying it wholesale.

## One-Line Start

```text
Read https://github.com/lyosvne/agent-collaboration-standard first, then read this project's AGENTS.md and current source-of-truth; report the collaboration state, your role, the current HEAD, active risks, and the next safe action before making any change.
```
