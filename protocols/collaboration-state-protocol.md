# Collaboration State Protocol

Agents must be able to report the current collaboration state without relying on the human to relay context between tools.

## State Sources

Read in this order:

1. Global standard repository and commit.
2. Project `AGENTS.md`.
3. Project current source-of-truth document.
4. Project `.agents/project-agents.md` if present.
5. Project `.agents/coordination/` if present.
6. Active task record under `.agents/tasks/` if present.
7. Git branch, HEAD, remote HEAD, and dirty state.

## Required State Output

Before work, report:

- Global standard:
- Project:
- Source of truth:
- Tool role:
- Branch / HEAD:
- Remote HEAD:
- Active task:
- Intended files:
- Active lock:
- Unexpected changes:
- Risk:
- Next safe action:

## Stop Conditions

Stop before editing, staging, committing, or pushing if:

- global standard is unreadable
- project entry is unreadable
- current source-of-truth is missing
- local changes are not attributable to the current task
- another active task owns the intended files
- the task asks for reset, force push, deletion, secret access, deployment, or permission changes without explicit approval

## Human Relay Reduction

Agents should use GitHub files, task records, commits, and PRs as the shared context layer. Human chat may initiate or approve work, but should not be the only carrier of current state.

For `/ALL`, load shared state for all tools before acting.

For `/one`, select one owner and make other tools read-only unless the task is later split into parallel records.
