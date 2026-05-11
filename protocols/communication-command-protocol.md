# Communication Command Protocol

## Purpose

Reduce cross-tool copy/paste by making GitHub-readable files the shared communication layer.

## Core Commands

Use these as human-facing commands in any supported tool:

- `:ALL`: load the global standard, project entry, project agents, current source of truth, active task records, work ledger, branch, HEAD, remote HEAD, and dirty state; then report collaboration state before acting.
- `:ONE`: load the same sources, then continue one owned task or select one primary owner for the next task.
- `:CHECK`: run a read-only self-check for conflicts between the tool's local rules, skills, memory, project rules, and the GitHub global standard.

These commands are plain text tokens, not slash commands. This avoids collisions with tool-native slash-command or skill systems.

Canonical tokens use a single ASCII colon. Full-width aliases `：ALL`, `：ONE`, and `：CHECK` may be normalized to the canonical tokens when a tool receives them from a Chinese input method.

Legacy aliases `::ALL`, `::ONE`, `::CHECK`, `/ALL`, and `/one` may be accepted for compatibility, but new instructions should use `:ALL`, `:ONE`, and `:CHECK`.

A bare `:` is not a valid command.

## Default Behavior

Short commands must work without a long prompt.

### `:ALL`

With no extra arguments, `:ALL` must:

- Read the required sources.
- Build a task board from active task records, the work ledger, locks, assigned owners, branch, HEAD, remote HEAD, and dirty state.
- Report collaboration state.
- Identify open tasks, blocked tasks, and tasks assigned to each tool.
- Recommend the next command, next owner, and owner reason.

`:ALL` must not edit, stage, commit, push, or claim work by default. It is the safe shared-state command.

### `:ONE`

With no extra arguments, `:ONE` must:

- Read the required sources.
- Find unfinished tasks assigned to the current tool or explicitly assigned to this tool in the work ledger.
- If exactly one assigned task exists and the scope is clear, resume or continue that task after restating goal, scope, risk, intended files, and verification.
- If no assigned task exists, recommend the safest next owner and next command instead of inventing work.
- If multiple assigned tasks or unclear scope exist, list options and ask for selection.

`:ONE` must not silently expand scope. It may only execute when owner, scope, lock, and verification path are clear.

### `:CHECK`

With no extra arguments, `:CHECK` must:

- Read GitHub truth first.
- Compare local rules, skills, templates, memory, project rules, active task records, and Git state when available.
- Report conflicts, stale items, missing items, and action needed.
- Append a `review` or `update` event to the project coordination ledger when the tool has safe write access and the project allows coordination writes.

`:CHECK` must not automatically rewrite local rules or repository files. Fixes require a follow-up `:ONE` task.

## Input Precision

`:ONE` may be used with either precise or fuzzy human input.

Precise input example:

```text
:ONE owner=Claude task=Implement Phase 1 truthful resource grounding; scope=backend resource status answer path; no frontend changes.
```

Fuzzy input example:

```text
:ONE 看下资源状态回答这块下一步谁做最合适
```

If input is fuzzy, the receiving tool must normalize it before execution:

- Restate the inferred goal.
- Recommend one owner.
- Explain why this owner is the safest next executor.
- State non-goals and intended files if implementation is likely.
- Ask before editing when scope, owner, or risk is unclear.

Fuzzy `:ONE` can select an owner or produce a task pack. It must not silently become broad implementation.

## Self-Check Mode

Use `:CHECK` when the human wants a tool to verify its own environment before real work.

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

`:CHECK` is read-only by default. Its only allowed write is an append-only coordination event when the project permits it and the tool has safe write access.

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
- `rule-ack` (see "Rule Update Lifecycle" below)

Corrections should be new events that supersede earlier events, not edits that erase them.

## Final Archival

When work is accepted:

1. Commit or PR becomes the code truth.
2. Task record receives a finish event.
3. Durable decisions move into project source-of-truth docs only if they remain valid after implementation.
4. Temporary coordination details stay in the coordination/task record layer.

## Next Instruction Rule

Every agent response that completes a meaningful step must end with:

- Recommended next command: a copyable `:ALL`, `:ONE ...`, or `:CHECK ...` instruction.
- Recommended next owner: Trae IDE / Claude Code / Trae SOLO PC / Trae SOLO Sandbox / Mira / human.
- Owner reason: why that owner is the best next step.

If no further work is recommended, the next command should be:

```text
:ALL status check only; no active task.
```

## Mira Memory Instruction

When onboarding Mira, ask it to remember:

```text
Remember this collaboration mode: the global source is https://github.com/lyosvne/agent-collaboration-standard. For any project, read the global standard first, then the project's AGENTS.md, .agents/project-agents.md, current source-of-truth, .agents/coordination if present, and active .agents/tasks records. Default role: senior architect, text editor, and reviewer. Default mode: read-only unless explicitly assigned a branch or PR task. Use :ALL to load shared state for all tools, :ONE to select or continue one owned task and keep others read-only, and :CHECK to compare local rules/skills/memory against GitHub truth. Treat GitHub commit, branch, and PR as hard sync points. Use append-only coordination events; do not rely on chat history as source of truth.
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

---

## Rule Update Lifecycle

This section defines **how** any agent (Mira, Trae IDE, Claude Code,
Trae SOLO PC, Trae SOLO Sandbox, future participants) proposes,
distributes, acknowledges, and confirms a change to the global standard
or to its own personal/skill-layer rules.

It is the methodology. It is **not** the same thing as any specific
rule that uses it. Rules introduced via this lifecycle (such as the
2026-05-11 bootstrap of `git-truth-protocol.md` §9/§10/§11) are
separate payloads and are acknowledged independently.

### Four Phases

1. **Initiate (发起)**
   The proposer opens a PR against this repository (for global rules)
   or against their own skill / personal-rule store (for self-scoped
   rules). The PR description must state:
   - Scope (global / skill / personal).
   - Whether full-team rule-ack is required, or :CHECK broadcast is
     sufficient.
   - Bootstrap-bundle disclosure (see "Bootstrap Bundles" below) if
     the PR introduces both new rules **and** lifecycle machinery in
     the same change.

2. **Sync (同步)**
   After merge, the proposer broadcasts a one-line :CHECK directive
   in the channel where work is dispatched (chat, work-ledger, or
   project README). The directive names the merged commit SHA so
   every agent fetches a deterministic snapshot.

3. **Acknowledge (回执)**
   Each affected agent runs `:CHECK` against the new global commit,
   internalizes the change at the layer they choose (see
   "Internalization Path Constraints" below), and writes a
   `rule-ack` event to the project's
   `.agents/coordination/work-ledger.jsonl` (or the equivalent
   coordination ledger named in the project's
   `.agents/coordination/README.md`).

   `rule-ack` is an append-only event in the same family as `start`,
   `claim`, `update`, etc. defined in "Append-Only Rule" above.

4. **Confirm (确认)**
   The proposer (or a designated coordinator) reads the ledger,
   verifies every required agent has produced a valid `rule-ack`
   for the upgrade, and posts a confirmation summary. Until
   confirmation, the upgrade is "in flight" and existing work that
   touches the upgraded surface should not assume the new rule is
   universally observed.

   The proposer must also write **their own** `rule-ack` — the
   methodology applies to its initiator. This prevents "I made the
   rule so I'm exempt" double standards.

### Acknowledgement Schema

A `rule-ack` event is a JSON line with at least:

```json
{
  "event": "rule-ack",
  "ts": "2026-05-11T08:00:00+08:00",
  "agent_id": "<stable identifier of the acking agent>",
  "upgrade_id": "<short slug of the upgrade, e.g. state-truth-and-rule-ack>",
  "commit_sha": "<merge commit on the standard repo, full or short>",
  "self_internalization_path": "global | skill:<id> | personal:<store>",
  "notes": "<optional free text>"
}
```

`self_internalization_path` declares **where the agent stored the rule
inside its own system** so a reviewer can later inspect that the rule
is actually loaded, not just acknowledged.

### Internalization Path Constraints

This is **internalization**, not duplication. Once the global standard
has the rule, no agent needs to build a parallel mechanism in any
project to enforce it locally. Internalize once at a global-or-broader
layer; rely on `:CHECK` and the standard repo to keep that layer
honest.

**Allowed values for `self_internalization_path`**:

- `global` — the agent treats the rule as part of the global standard
  it auto-loads on every session start. No additional storage.
- `skill:<id>` — the agent embedded the rule into one of its skills /
  capability packs / persistent system prompts (recommended class:
  collaboration / project-management / coding-agent skill).
- `personal:<store>` — the agent embedded the rule into its personal
  always-on rule store (recommended class: tool-level user rules,
  long-term memory, agent-wide system prompt). Name the **store
  class**, not a specific file path; specific paths are tool-internal
  detail and may change.

**Forbidden**:

- Project-level paths. A global rule is global by definition. Storing
  it inside one project's rule files (`<project>/AGENTS.md`,
  `<project>/.agents/...`, `<project>/CLAUDE.md`-equivalents, etc.)
  would mean every other project re-inherits an outdated copy and
  would re-trigger the same regression that prompted §11
  Branch-Currency. **A `rule-ack` whose
  `self_internalization_path` resolves to a project-scoped store
  must be rejected at confirmation time.**

The phrasing "internalization, not duplication" is normative: agents
are expected to absorb the rule into their always-on layer, not to
spawn project-by-project enforcement copies.

### Bootstrap Bundles

A single PR may bundle two logically separate concerns when the second
concern is the lifecycle machinery itself. The 2026-05-11 PR
introducing `git-truth-protocol.md` §9/§10/§11 **plus** this
"Rule Update Lifecycle" section is the canonical example.

In that case, the initial bootstrap rule-ack covers **both** payloads
at once. After the bootstrap is confirmed:

- The bundled rules are paid up. Future upgrades will not re-request
  acknowledgement of them.
- The lifecycle becomes the standing process. Every later upgrade —
  including upgrades proposed by any agent, not just the original
  proposer — must follow `Initiate → Sync → Acknowledge → Confirm`,
  but only for **its own** payload.

Bootstrap bundles are exceptional. Future PRs should normally carry
one logical concern.

### Re-Acknowledgement Cadence

For substantial global rule changes, the proposer **may** require a
fresh full-team rule-ack (recommended for changes that alter
review-blocking behavior, security boundaries, or directory-as-truth
semantics). For minor edits, broadcasting `:CHECK` and letting agents
self-detect via their next session start is sufficient.

The proposer's choice between "full ack required" vs "broadcast only"
must be stated in the PR description (see Phase 1).

### Relationship to `:CHECK`

`:CHECK` is the read-only diff between an agent's current loaded
rules and the global standard. The Rule Update Lifecycle is the
write-side counterpart: it is how new rules **enter** the global
standard so that subsequent `:CHECK` runs see them. The two are
designed to compose without overlap.
