# Tool Role Matrix

## Pi

- Role: ECS central coordinator, intent routing, result convergence, cognitive and memory loop.
- Local clone: none.
- Must not: code, Git writes, SSH, deployment, T3 operations, secrets, or audit mutation.

## Unified Trae

- Role: implementation, integration, Git/PR/CI, product testing, browser validation.
- Default access: project-scoped write through an isolated branch and visible diff.
- Inherits: historical Trae and Solo responsibilities.
- Must not: push `master`, rewrite history, or perform production/T3 operations without user authorization.

## ZCode

- Role: non-terminal knowledge assimilation, review, root-cause analysis, feedback, fallback.
- Default access: read and structured review output.
- Must not: shell, Git execution, code implementation, SSH, deployment, or production changes.

## Qoder

- Role: design assets, frontend design, architecture planning, assigned implementation.
- Default access: read-only until a scoped branch or design task is assigned.
- Must not: push `master`, rewrite history, or perform production operations without authorization.

## Kimi

- Role: terminal implementation, file/data processing, Feishu collaboration.
- Default access: task-scoped terminal and branch work.
- Must not: push `master`, expose credentials, or perform production/T3 operations without authorization.

## Mira

- Role: cloud PM, architecture, governance and public memory.
- Default access: read-only fresh checkout.
- Write access: explicit governance branch or PR task.
- Must not: push `master`, edit secrets, or touch runtime state.

## Retired roles

- Claude Code: retired; coordination history → Pi, review knowledge → ZCode, execution → Trae.
- Independent Solo: retired; product-test knowledge and duties → unified Trae.

## Future Cloud Agents

- Role: task-specific reviewer or implementation worker.
- Default access: read-only until a task package grants scoped authority.
- Must read: `START_HERE.md`, current version manifest, project activity rules and current source-of-truth.
