# Tool Role Matrix

## Trae IDE

- Role: project owner, architecture controller, final integrator.
- Default access: local write with human-visible changes.
- Must read: global standard, project `AGENTS.md`, `.agents/project-agents.md`, current source-of-truth.
- Must not: silently mix concurrent task changes, reset, force push, or rewrite history.

## Claude Code

- Role: focused implementation, review, refactor, debugging.
- Default access: task-scoped write when assigned.
- Must read: global standard, project `AGENTS.md`, `.agents/project-agents.md`, current source-of-truth.

## Trae SOLO PC

- Role: autonomous implementation agent.
- Default access: task-package driven.
- Must read: global standard, project `AGENTS.md`, `.agents/project-agents.md`, current source-of-truth.
- Must use branch or explicitly approved scope for writes.

## Trae SOLO Sandbox

- Role: cloud/sandbox review or small isolated patch.
- Default access: read-only unless explicitly assigned a branch/PR task.
- Must read: global standard, project `AGENTS.md`, `.agents/project-agents.md`, current source-of-truth.
- Must not rely on local Windows paths.

## Mira

- Role: senior architect, text-editing specialist, and review-oriented collaboration agent.
- Default access: read-only.
- Write access: only through explicit branch or PR task.
- Must read: global standard, project `AGENTS.md`, `.agents/project-agents.md`, current source-of-truth.
- Best use: architecture review, document restructuring, rules/text quality review, consistency audit, and design critique.
- Must not: push to `master`, reset, force push, edit secrets, or touch runtime state.

## Future Cloud Agents

- Role: task-specific reviewer or implementation worker.
- Default access: read-only until a task package grants scoped write authority.
- Must read: global standard, project `AGENTS.md`, `.agents/project-agents.md`, current source-of-truth.
