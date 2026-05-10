# Concurrent Work Protocol

If an agent detects file changes that are not part of the current task, it must stop before editing, staging, committing, or pushing.

The agent may only perform read-only checks:

- current branch and HEAD
- remote HEAD
- `git status --short`
- intended files for the current task
- unexpected changed or untracked files

Before continuing, ask the human to classify the changes:

- current task
- another active task
- safe to ignore
- unknown

Do not reset, clean, overwrite, stage, commit, or push unexpected changes.

If concurrent work must continue, isolate by branch, worktree, or explicit file ownership. Protected entry files should have one owner at a time.

## Serial And Parallel Modes

Use serial mode when one owner executes and other tools only observe or review.

Use parallel mode only when each owner has a separate task record, branch or non-overlapping file scope, and clear integration owner.

Active locks belong in project `.agents/tasks/` records and may be summarized in `.agents/coordination/`.
