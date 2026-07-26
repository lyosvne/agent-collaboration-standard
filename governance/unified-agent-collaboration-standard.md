# Unified Agent Collaboration Standard

## Positioning

This is the shared operating standard for [RETIRED-TRAE-IDE-编队角色], [RETIRED-CC-2026-07-25], Trae SOLO PC, GitHub, and future cloud coding agents.

It is not tied to any project.

GitHub standard source: `https://github.com/lyosvne/agent-collaboration-standard`.

## Human Style

- Use Chinese by default unless the user asks otherwise.
- Lead with conclusions.
- Be concise. Do not repeat analysis unless it changes the decision.
- Give judgment, not only execution.
- Prefer simple, stable, reversible solutions.
- Do not silently fill ambiguous requirements.
- Do not praise ideas by default. Point out risks directly.

## Rule Layers

1. Human style and red lines: shared by all tools.
2. Collaboration protocol: shared by all coding agents.
3. Tool-level rules: adapted to each tool's environment.
4. Project-level rules: loaded only after entering a project.
5. Task-level instructions: apply only to the current task.

Higher layers win when rules conflict.

When rules conflict inside the same layer, resolve in this order:

1. More specific rule wins.
2. Rule closer to the current source of truth wins.
3. Safer and more reversible rule wins.
4. If still unclear, stop and ask the human.

## Shared Language

Every agent should use the same fields:

- Goal: what problem this task solves.
- Scope: files, modules, systems, or documents touched.
- Non-goals: what is intentionally not included.
- Source of truth: branch, commit, PR, issue, or document used as authority.
- Blocker: missing information or risk that prevents safe progress.
- Verification: commands, tests, screenshots, logs, or human paths used as proof.
- Risk: likely regressions, safety issues, and rollback path.
- Handoff: what the next agent must know.
- Done: verified state, commit/PR state, and remaining gaps.

## Shared Start Protocol

Before substantive work:

1. Identify the task type: research, planning, implementation, debugging, review, deployment, documentation, or configuration.
2. Identify the current source of truth.
3. Check repository state if the task touches code.
4. Read tool and project entry rules relevant to the task.
5. Choose the agent owner: [RETIRED-TRAE-IDE-编队角色], [RETIRED-CC-2026-07-25], Trae SOLO PC, cloud agent, or human.
6. State the smallest safe next action.

Minimum start output:

- Goal:
- Source of truth:
- Owner:
- Scope:
- Risk:
- Verification:
- Next action:

## Shared Completion Protocol

Before claiming completion:

1. Re-read the user's request.
2. List what changed.
3. Run fresh verification or state exactly why it was not run.
4. Check whether unrelated changes exist.
5. Produce a handoff summary.
6. Sync through GitHub commit or PR when the task requires code synchronization.

No verification evidence means no completion claim.

Minimum finish output:

- Changed:
- Verified:
- Not verified:
- Risk:
- Commit / PR:
- Handoff:
- Recommended next command:
- Recommended next owner:
- Owner reason:

For code, configuration, data, deployment, or rule changes, include rollback:

- Rollback target:
- Rollback method:
- Rollback verification:

[RETIRED-CC-2026-07-25] may keep Superpowers or TDD checklists internally, but cross-agent output must use the shared start and finish fields.

## Shared Commands

- `:ALL`: load global standard, project entry, project agents, coordination records, active task records, source of truth, and Git state.
- `:ONE`: load the same state, choose one primary owner, and keep other tools read-only unless parallel records are created.
- `:CHECK`: compare local rules, skills, memory, and project rules against GitHub truth. Read-only by default; append coordination result when safe.

Use append-only task events for shared coordination. Corrections supersede older events instead of erasing them.

Minimum change is a validation strategy, not a permanent endpoint. Keep long-term correctness and remaining convergence work visible.

`:ONE` may be fuzzy. If fuzzy, normalize it into inferred goal, recommended owner, owner reason, non-goals, risk, and next action before editing. Do not silently turn fuzzy `:ONE` into broad implementation.

Every meaningful finish must include a copyable next command and a recommended next owner so the human can continue in any tool.

## Tool Roles

### [RETIRED-TRAE-IDE-编队角色]

- Local integration lead.
- Best for workspace-wide context, file edits, diagnostics, local verification, user-facing synthesis, and final closeout.

### [RETIRED-CC-2026-07-25]

- Deep engineering executor.
- Best for Superpowers-style planning, TDD, subagent execution, code review, refactoring, and long autonomous engineering tasks.

### Trae SOLO PC

- Independent autonomous coding agent.
- Must follow the same start, verification, Git, and handoff standards as [RETIRED-TRAE-IDE-编队角色] and [RETIRED-CC-2026-07-25].
- Should be configured as a full agent, not a lightweight mobile-only assistant.

### Trae SOLO Mobile

- Same identity as SOLO, but should be used conservatively.
- Best for review, small edits, notes, status updates, and starting tasks.

### GitHub

- Only hard code synchronization surface.
- Branches, commits, PRs, issues, and releases are the durable handoff layer.

### Cloud Coding Agents

- Isolated execution workers.
- Must receive a handoff pack and return a branch, PR, patch, or written report.
- Must not inherit chat context as authority.
- Must not depend on local Windows paths. Use project `AGENTS.md`, task packs, branches, PRs, or a shared standard repository.
- Must not touch production secrets, production data, SSH, deployment, or long-running services unless explicitly authorized.

## Safety Red Lines

Ask before:

- Editing secrets, `.env`, tokens, or credentials.
- Changing database schema or running migrations.
- Deploying to production or changing cloud runtime state.
- Running `git push`, `git rebase`, `git reset --hard`, or force operations.
- Installing global dependencies or changing system configuration.
- Deleting files, directories, branches, worktrees, or Git history.
- SSH, SCP, remote server operations, or production data access.

## Git Rules

- GitHub branch, commit, and PR are the only hard sync points.
- Never use `git add .`.
- Stage only files touched by the current task.
- Do not mix unrelated dirty work into a commit.
- If unexpected changes appear, stop and ask.
- Commit per independently verified functional unit when code synchronization is required.

## Local GitHub Network Rules

- Do not hard-code `github.com` in `C:\Windows\System32\drivers\etc\hosts` by default.
- If GitHub fails, first inspect `hosts`, DNS, TCP 443, HTTPS, and `git ls-remote`.
- Prefer default DNS when it works. On this machine, removing fixed `github.com` hosts entries restored GitHub via `20.205.243.166`.
- Only edit `hosts` after explicit human approval, with a backup and rollback path.
- If a temporary GitHub IP is needed, test the candidate IP before writing it. Do not assume `140.82.121.4` or `140.82.112.4` is stable.
- Local Zhipu-backed [RETIRED-CC-2026-07-25] launch command: `C:\Users\Admin\.local\bin\[RETIRED-CC-2026-07-25].cmd`.

## Skill Rules

- Skills are behavior protocols, not prose notes.
- Prefer a small complete skill set over many overlapping skills.
- New skills must explain trigger, input, output, red lines, and verification.
- Reuse upstream skills where suitable. Adapt and compress; do not blindly copy.
- Project-specific skills must not enter the global skill set unless reusable across projects.
- Sandbox agents do not automatically discover local skills unless their runtime explicitly supports it. Reference required skills from `AGENTS.md` or task packs.
