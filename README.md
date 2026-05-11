# Agent Collaboration Standard

Global collaboration standard for coding agents across repositories and tools.

This repository is above any single project. Project repositories should reference a released version of this standard, then define their own project-specific participants, source of truth, risk boundaries, and task records.

## Entry Points

1. `GLOBAL_AGENT_GUIDE.md`
2. `BOOTSTRAP_ONE_LINE.md`
3. `protocols/collaboration-state-protocol.md`
4. `protocols/communication-command-protocol.md`
5. `protocols/git-truth-protocol.md`
6. `protocols/concurrent-work-protocol.md`
7. `protocols/verification-protocol.md`
8. `protocols/handoff-protocol.md`
9. `protocols/security-boundary-protocol.md`
10. `TOOL_ROLE_MATRIX.md`

## Operating System Overview

- `docs/multi-agent-collaboration-operating-system.md`

## Core Rule

Global rules should be stable and infrequently changed. Project rules should stay thin and point to this standard instead of copying it wholesale.

## Rule Updates

Changes to this repository follow the Rule Update Lifecycle defined in
`protocols/communication-command-protocol.md` (Initiate → Sync → Acknowledge → Confirm).
Agents acknowledge updates by appending a `rule-ack` event to the project
work-ledger, declaring **where** they internalized the rule (global,
skill, or personal-store class). Project-scoped internalization is not
permitted for global rules.

## Shared Commands

- `:ALL`: load global, project, task, coordination, and Git state; report task board and recommended next action.
- `:ONE`: continue one owned task or choose one primary owner and keep other tools read-only.
- `:CHECK`: self-check for conflicts between local rules, skills, memory, project rules, and GitHub truth.

Use single-colon commands as the canonical shortcuts because many tools reserve `/` for native commands or skills. Legacy `::ALL`, `::ONE`, `::CHECK`, `/ALL`, and `/one` may still be understood as aliases.

`:ONE` may start from fuzzy input, but the receiving tool must normalize it into goal, owner, scope, risk, and next action before editing.

Every meaningful finish must include a copyable next command and recommended next owner.

## One-Line Start

```text
Read https://github.com/lyosvne/agent-collaboration-standard first, then read this project's AGENTS.md, .agents/project-agents.md, current source-of-truth, .agents/coordination if present, active .agents/tasks records, and Git state; report collaboration state, role, HEAD, active risks, locks, and next safe action before changing anything.
```
