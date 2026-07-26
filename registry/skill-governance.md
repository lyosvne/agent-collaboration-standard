# Skill Governance

## Purpose

Keep the global skill system small, complete, and non-overlapping.

## Skill Types

- Gate skills: enforce behavior before or after work.
- Tool skills: operate a specific external tool.
- Domain skills: support a specific domain such as frontend design.
- Project skills: belong to one repository only.

## Global Skill Admission Rules

A new global skill is allowed only when:

- It is reusable across projects.
- It has a clear trigger.
- It does not overlap an existing core skill.
- It defines input, output, red lines, and verification.
- It can be maintained by Trae, SOLO, or another active tool.

## Merge Rules

Merge skills when:

- They trigger in the same moment.
- They produce the same output.
- They differ only by wording or tool name.
- They are upstream variants of the same behavior.
- Usage logs show repeated co-triggering without separate decisions.

## Retire Rules

Retire or demote skills when:

- They are project-specific.
- They are no longer used.
- They duplicate a gate skill.
- They encourage broad, unsafe, or vague behavior.

## Current Core Set

- `collaboration-bootstrap`
- `cross-agent-handoff`
- `git-truth-guardian`
- `verification-gate`
- `debugging-gate`
- `plan-gate`
- `review-gate`
- `security-boundary-gate`

## Usage Tracking

For meaningful work, record:

- Skills used:
- Skills skipped:
- Reason:
- Missing skill:
- Merge candidate:

Keep tracking lightweight. Do not create a separate reporting system unless repeated failures justify it.

## Sandbox Skills

Sandbox agents may use a workspace path such as `/workspace/.agents/skills/`, but this is not guaranteed to auto-load.

If a sandbox must use a skill:

- Reference it in `AGENTS.md` or the task pack.
- Include the skill file in the repository or task context.
- Do not assume the agent will scan new skills automatically.

## Review Cadence

- Monthly.
- After major tool upgrade.
- After installing a new plugin pack.
- After a security incident or accidental cross-agent conflict.
