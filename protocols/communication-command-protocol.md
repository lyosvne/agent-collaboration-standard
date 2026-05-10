# Communication Command Protocol

## Purpose

Reduce cross-tool copy/paste by making GitHub-readable files the shared communication layer.

## Core Commands

Use these as human-facing commands in any supported tool:

- `::ALL`: load the global standard, project entry, project agents, current source of truth, active task records, work ledger, branch, HEAD, remote HEAD, and dirty state; then report collaboration state before acting.
- `::ONE`: load the same sources, but select one primary owner for the task and state why other tools should stay read-only.
- `::CHECK`: run a read-only self-check for conflicts between the tool's local rules, skills, memory, project rules, and the GitHub global standard.

These commands are plain text tokens, not slash commands. This avoids collisions with tool-native slash-command or skill systems.

Legacy aliases `/ALL` and `/one` may be accepted for compatibility, but new instructions should use `::ALL` and `::ONE`.

## Input Precision

`::ONE` may be used with either precise or fuzzy human input.

Precise input example:

```text
::ONE owner=Claude task=Implement Phase 1 truthful resource grounding; scope=backend resource status answer path; no frontend changes.
```

Fuzzy input example:

```text
::ONE 看下资源状态回答这块下一步谁做最合适
```

If input is fuzzy, the receiving tool must normalize it before execution:

- Restate the inferred goal.
- Recommend one owner.
- Explain why this owner is the safest next executor.
- State non-goals and intended files if implementation is likely.
- Ask before editing when scope, owner, or risk is unclear.

Fuzzy `::ONE` can select an owner or produce a task pack. It must not silently become broad implementation.

## Self-Check Mode

Use `::CHECK` when the human wants a tool to verify its own environment before real work.

The tool must read GitHub truth first, then compare it with local or memory-layer rules it can access.

Check at least:

- global standard commit and required protocols
- project `AGENTS.md` and coordination files
- local system/user/project rules
- available skills or command templates
- remembered collaboration behavior
- Git branch, remote HEAD, and dirty state when a repository is available

Report:

- Source of truth read:
- Local rules checked:
- Skills/templates checked:
- Conflicts found:
- Stale or missing items:
- Action needed:
- Recommended next command:
- Recommended next owner:
- Owner reason:

`::CHECK` is read-only. It must not edit local rules automatically.

## Required Sources

Read in this order:

1. Global standard repository and commit.
2. Project `AGENTS.md`.
3. Project `.agents/project-agents.md`.
4. Project current source-of-truth document.
5. Project `.agents/coordination/` if present.
6. Project `.agents/tasks/` active task records if present.
7. Git branch, HEAD, remote HEAD, and dirty state.

## Coordination Directory

Projects may add:

- `.agents/coordination/README.md`: project-specific coordination rules and file locations.
- `.agents/coordination/work-ledger.jsonl`: append-only task events.
- `.agents/tasks/*.md`: task records with owner, mode, scope, lock, verification, and handoff.

Do not use chat history as the only state carrier.

## Work Modes

### Serial

Use serial mode when one tool should execute and all others should observe.

Rules:

- One owner.
- One branch or explicit commit target.
- One active task record.
- Other tools may read and review, but must not edit, stage, commit, or push the same task.

### Parallel

Use parallel mode only when scopes are separable.

Rules:

- Each owner has a task record.
- Each owner has a branch or explicitly non-overlapping file scope.
- Protected files have one owner at a time.
- Integration happens through PR, patch, or a designated integrator.

## Lock Fields

Every active task record should include:

- Mode: serial / parallel
- Owner:
- Tool:
- Branch:
- Base commit:
- Intended files:
- Forbidden files:
- Lock scope:
- Started at:
- Expected finish or checkpoint:

If a received task conflicts with an active lock, stop and report the conflict.

## Append-Only Rule

Use append-only events for coordination records. Do not rewrite another tool's event.

Valid event types:

- `start`
- `claim`
- `update`
- `blocked`
- `handoff`
- `review`
- `finish`
- `archive`

Corrections should be new events that supersede earlier events, not edits that erase them.

## Final Archival

When work is accepted:

1. Commit or PR becomes the code truth.
2. Task record receives a finish event.
3. Durable decisions move into project source-of-truth docs only if they remain valid after implementation.
4. Temporary coordination details stay in the coordination/task record layer.

## Next Instruction Rule

Every agent response that completes a meaningful step must end with:

- Recommended next command: a copyable `::ALL`, `::ONE ...`, or `::CHECK ...` instruction.
- Recommended next owner: Trae IDE / Claude Code / Trae SOLO PC / Trae SOLO Sandbox / Mira / human.
- Owner reason: why that owner is the best next step.

If no further work is recommended, the next command should be:

```text
::ALL status check only; no active task.
```

## Mira Memory Instruction

When onboarding Mira, ask it to remember:

```text
Remember this collaboration mode: the global source is https://github.com/lyosvne/agent-collaboration-standard. For any project, read the global standard first, then the project's AGENTS.md, .agents/project-agents.md, current source-of-truth, .agents/coordination if present, and active .agents/tasks records. Default role: senior architect, text editor, and reviewer. Default mode: read-only unless explicitly assigned a branch or PR task. Use ::ALL to load shared state for all tools, ::ONE to select one owner and keep others read-only, and ::CHECK to compare local rules/skills/memory against GitHub truth. Treat GitHub commit, branch, and PR as hard sync points. Use append-only coordination events; do not rely on chat history as source of truth.
```

If Mira cannot persist memory, paste the same instruction at the start of a new Mira workspace.

## Long-Term Correctness

Minimum change is a validation strategy, not an excuse to stop at a short-term patch.

Agents must distinguish:

- smallest safe next action
- verified functional unit
- durable design target
- remaining convergence work

Do not convert a workaround into permanent truth unless it has been verified and archived intentionally.
