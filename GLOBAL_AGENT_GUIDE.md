# Global Agent Guide

## Purpose

Provide a common operating language for Trae IDE, Claude Code, Trae SOLO, Mira, GitHub, and future cloud coding agents.

## Layering

- Global collaboration standard: cross-project rules and protocols.
- Project entry: project-specific `AGENTS.md`, source-of-truth documents, tool participants, and exceptions.
- Task record: concrete owner, branch, base commit, intended files, verification, and handoff.
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

## Finish Contract

Before claiming completion, state:

- Changed:
- Verified:
- Not verified:
- Risk:
- Commit / PR:
- Handoff:

For code, configuration, runtime, data, or rule changes, include:

- Rollback target:
- Rollback method:
- Rollback verification:

Use `templates/finish-state.md.template` when a project does not provide its own finish template.

## Rule Update Policy

Do not upgrade global rules for one-off project friction. Promote a rule globally only when the issue is cross-tool, cross-project, repeatable, and can be expressed simply with a low daily burden.

## Project Rule Boundary

Project files should not copy this standard wholesale. They should point to this repository, declare project participants, list project-specific source-of-truth documents, and define project exceptions.
