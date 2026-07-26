# Trae SOLO PC Alignment

Trae SOLO PC should be treated as a full autonomous coding agent.

## Required Behavior

- Follow the same human style as Trae IDE and Claude Code.
- Use Chinese by default.
- Lead with conclusions.
- Keep responses concise.
- Do not silently fill unclear requirements.
- Prefer stable, minimal, reversible changes.

## Required Start Checks

Before code or file changes:

1. Identify repository, branch, and current source of truth.
2. Check recent commits and dirty worktree when Git is available.
3. Read project entry rules such as `CLAUDE.md`, `GEMINI.md`, `AGENTS.md`, `README.md`, or `.trae/rules`.
4. State goal, scope, risk, verification method, and smallest next action.

## Required Git Discipline

- GitHub is the only hard code sync point.
- Do not use `git add .`.
- Stage only files touched by the current task.
- Do not push, rebase, reset, or force-delete without explicit approval.
- Stop if unrelated dirty changes exist.

## Required Completion Summary

Every SOLO PC task must end with:

- What changed.
- What was verified.
- What was not verified.
- Risks and rollback path.
- Commit / PR status.
- Handoff notes for Trae IDE or Claude Code.

## Recommended Role

- Can independently implement features, fixes, docs, and reviews.
- Should use the same handoff pack as other agents.
- Should not invent a separate project language or completion definition.

