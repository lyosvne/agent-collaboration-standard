# Global Agent Guide

## Purpose

Provide a common operating language for Pi, unified Trae, ZCode, Qoder, Kimi, Mira, GitHub, and future cloud agents.

## Layering

- Global collaboration standard: cross-project rules and protocols.
- Project entry: project-specific `AGENTS.md`, source-of-truth documents, tool participants, and exceptions.
- Task record: concrete owner, branch, base commit, intended files, verification, and handoff.
- Coordination layer: Pi routing, append-only task events, serial/parallel locks and explicit handoff state.
- GitHub commit / PR: hard synchronization point.
- Runtime artifacts: logs, screenshots, databases, generated vaults, and local state are not code truth unless explicitly promoted.

## Start Contract

Before substantive work, state:

- Goal:
- Source of truth:
- Owner:
- Scope:
- Risk:
- Verification:
- Next action:

If joining an existing project, first report the collaboration state defined in `protocols/collaboration-state-protocol.md`.

## Legacy Commands

`:ALL`, `:ONE` and `:CHECK` are historical compatibility commands, not the default task entry. New work starts with natural language grounded in current truth.

Use `protocols/communication-command-protocol.md` only when interpreting or maintaining legacy coordination records.

## Finish Contract

Before claiming completion, state:

- Changed:
- Verified:
- Not verified:
- Risk:
- Commit / PR:
- Handoff:
- Recommended next command:
- Recommended next owner:
- Owner reason:

For code, configuration, runtime, data, or rule changes, include:

- Rollback target:
- Rollback method:
- Rollback verification:

Use `templates/finish-state.md.template` when a project does not provide its own finish template.

Every finish must give the human a copyable next instruction. The instruction should be usable in any tool without adding hidden chat context.

## Rule Update Policy

Do not upgrade global rules for one-off project friction. Promote a rule globally only when the issue is cross-tool, cross-project, repeatable, and can be expressed simply with a low daily burden.

## Local Network And Launcher Notes

- For GitHub network failures, do not write fixed `github.com` entries to `hosts` first.
- First inspect `hosts`, DNS resolution, TCP 443, HTTPS, and `git ls-remote`.
- Prefer default DNS when it works. Fixed GitHub IPs can become unreachable or reset connections.
- Edit `hosts` only after explicit human approval, with a backup and rollback path.
- Current local execution uses Mac independent clones. Claude Code and independent Solo launchers are retired.

## Project Rule Boundary

Project files should not copy this standard wholesale. They should point to this repository, declare project participants, list project-specific source-of-truth documents, and define project exceptions.

## Long-Term Correctness

Minimum change is a validation strategy, not the final design target. Prefer the smallest safe next action, but keep durable convergence work visible until it is verified or intentionally rejected.
