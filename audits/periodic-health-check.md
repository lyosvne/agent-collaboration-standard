# Periodic Agent Health Check

Run this monthly, after tool upgrades, or after adding a new coding agent.

## Rule Entry

- [ ] `START_HERE.md` still exists and is readable.
- [ ] Trae SOLO PC global entry points to `START_HERE.md`.
- [ ] Trae IDE entry `~/.trae-cn/GLOBAL_AGENT_RULES.md` still readable (个人使用，已退役为编队角色).
- [ ] No stale `trae-operating-profile.md` references remain (B1 错误合并已回滚).
- [ ] Project templates still point to the global entry.
- [ ] No project-specific rule leaked into global standards.

## Skills

- [ ] Core skill registry has no duplicates.
- [ ] Trae has all core skills.
- [ ] Claude has all core skills if Claude is being maintained.
- [ ] Tool-only skills are not confused with development gates.
- [ ] Stale skills are marked for merge or removal.

## Permissions

- [ ] No raw API key, token, or secret appears in rule or permission files.
- [ ] High-impact actions require approval.
- [ ] Broad command allowlists are still justified.
- [ ] Remote operations are not auto-allowed.
- [ ] Git push/rebase/reset are not auto-allowed unless deliberately approved.

## Project Sync

- [ ] GitHub is still the hard code sync point.
- [ ] Handoff template is being used for cross-agent work.
- [ ] Completion summaries include verification gaps.
- [ ] Dirty worktree conflicts are not ignored.

## Learning Loop

- [ ] New external articles are classified before becoming rules.
- [ ] Only reusable behavior becomes a global skill.
- [ ] Project-specific lessons stay in project memory or docs.
- [ ] Old recommendations are retired when superseded.

