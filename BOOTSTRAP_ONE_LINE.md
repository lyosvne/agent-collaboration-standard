# Bootstrap One-Liner

Use this when asking Mira, Claude Code, Trae SOLO, or another coding agent to join a project.

```text
Read https://github.com/lyosvne/agent-collaboration-standard first, then read this project's AGENTS.md, .agents/project-agents.md, and current source-of-truth; report the collaboration state, your role, the current HEAD, active risks, and the next safe action before making any change.
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
- Unexpected changes:
- Blockers:
- Risk:
- Next safe action:

## Rule

If the agent cannot read the global standard or project entry, it must stop and ask for the missing link or file.
