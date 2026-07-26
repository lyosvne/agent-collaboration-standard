# Project Rules Checklist

Use this when opening or initializing a project.

## Required

- [ ] Project has a single agent entry file: `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.trae/rules`, or README.
- [ ] Repository URL and default branch are explicit.
- [ ] Current source of truth is explicit.
- [ ] Tech stack and run commands are explicit.
- [ ] Test, build, lint, or typecheck commands are discoverable.
- [ ] Runtime data and generated files are separated from Git truth.
- [ ] Secrets and `.env` handling are documented.
- [ ] Deployment authority is documented.
- [ ] Completion definition is documented.

## Strongly Recommended

- [ ] Handoff template is linked.
- [ ] Code ownership or module boundaries are documented.
- [ ] Known stale docs are marked.
- [ ] Architecture decisions have a durable location.
- [ ] Screenshots or preview workflow are documented for frontend projects.

## Do Not Start Major Work If

- Source of truth is unclear.
- Branch or dirty worktree state is unsafe.
- Verification command is unknown.
- Task requires secrets, database, deployment, or Git history changes without approval.

