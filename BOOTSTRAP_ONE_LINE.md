# Bootstrap One-Liner

Use this when asking Pi, unified Trae, ZCode, Qoder, Kimi, Mira, or another approved agent to join a project. Claude Code and independent Solo are retired.

```text
Read https://github.com/lyosvne/agent-collaboration-standard first, then read this project's AGENTS.md, .agents/project-agents.md, current source-of-truth, .agents/coordination if present, active .agents/tasks records, and Git state; report collaboration state, role, HEAD, active risks, locks, and next safe action before changing anything.
```

## Required Response

The agent must answer with:

- Global standard:
- Global standard commit:
- Project:
- Project entry:
- Current source of truth:
- Tool:
- Role:
- Environment:
- Branch:
- Local HEAD:
- Remote HEAD:
- Active task:
- Intended files:
- Active lock:
- Unexpected changes:
- Blockers:
- Risk:
- Next safe action:

## Rule

If the agent cannot read the global standard or project entry, it must stop and ask for the missing link or file.

## Initial Acknowledgement

First-time bootstrap into a project counts as the agent's initial
acknowledgement of all currently merged protocols at the global
standard's HEAD. Subsequent rule changes follow the Rule Update
Lifecycle in `protocols/communication-command-protocol.md` and require
an explicit `rule-ack` event when the proposer marks the upgrade as
"full ack required".
