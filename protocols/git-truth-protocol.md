# Git Truth Protocol

- GitHub branch, commit, and PR are the hard synchronization points.
- Project-local files and chat history are not code truth.
- Start with recent commits, branch, remote HEAD, and dirty state.
- Do not use `git add .`.
- Stage only task-owned files.
- Do not push, reset, rebase, force push, delete history, or rewrite history without explicit approval.
- Prefer feature branches for concurrent work.
- Only one writer should update `master` at a time.

## GitHub Connectivity Checks

- If GitHub cannot be reached, diagnose before changing configuration.
- Check, in order: `hosts`, DNS resolution, TCP 443, HTTPS, then `git ls-remote`.
- Do not assume a hard-coded GitHub IP is stable. Test any candidate IP before using it.
- Prefer default DNS when it passes connectivity and `git ls-remote` checks.

---

## State Directory as Truth (§9)

> **Bootstrap note**: This section is a one-time global rule introduced
> on 2026-05-11. It is **not** part of the Rule Update Lifecycle
> methodology defined in `communication-command-protocol.md`. All agents
> acknowledge this section once via the bootstrap rule-ack of that PR.
> Future rule upgrades will not require re-acknowledging §9.

When a project uses a state-directory model (e.g. `inbox/ → running/ →
judging/ → done/ → failed/` for work orders, or any other file-based
state machine) the directory location of a record **is** its state.
This makes state observable from `git log` alone.

Mandatory rules:

1. A state transition (`git mv` of the record file) and the code/data
   change that justifies the transition must be in **the same commit**.
   Splitting them across commits creates a window where the filesystem
   says "still in state X" while master already contains "result of
   state Y", and any reviewer reading either side gets a wrong picture.
2. The board / index file (e.g. `DISPATCH-BOARD.md`,
   `.agents/coordination/work-ledger.jsonl`) must be updated in the
   same commit as the `git mv`. The directory and the index never
   disagree on master.
3. Editors that move records without moving the file (e.g. flipping a
   status field but leaving the file in `running/`) violate this rule.
   Move the file.

Violation handling: a reviewer who sees state-directory drift on master
must reject the change and require a follow-up commit that re-aligns
filesystem, index, and content. This is a hard fail, not a style note.

---

## Push-Before-Review (§10)

> **Bootstrap note**: One-time global rule introduced on 2026-05-11
> alongside §9 and §11. Not part of the Rule Update Lifecycle
> methodology. Acknowledged via the bootstrap rule-ack.

A work item is reviewable only when **both** are true:

1. Its branch (or commit, if pushed directly to `master`) exists on
   `origin` with the SHA the worker claims.
2. The work record (task file, WO file, PR description) names that SHA
   explicitly so a reviewer can verify without asking.

Local-only branches, or claims of "pushed" without a verifiable
`origin` SHA, are not reviewable. The reviewer must reject with
"branch not on origin" without inspecting any other criterion.

This complements but does not duplicate `verification-protocol.md`'s
"evidence before completion" rule: §10 is specifically about the
artifact's reachability; verification-protocol covers the evidence of
correctness once the artifact is reachable.

---

## Branch Currency for Review (§11)

> **Bootstrap note**: One-time global rule introduced on 2026-05-11
> alongside §9 and §10. Not part of the Rule Update Lifecycle
> methodology. Acknowledged via the bootstrap rule-ack.

A feature branch presented for review must be **current** with its
integration target (typically `master`) at review time. "Current"
means:

```
git rev-list --left-right --count origin/<target>...origin/<branch>
# Left side (commits target is ahead of branch) MUST be 0.
```

If the branch is behind, merging it would silently revert work landed
on `master` after the branch's fork point. This is "phantom
regression" and is indistinguishable from sabotage at merge time.

Worker obligations:

1. Before declaring a branch ready for review, run
   `git fetch origin && git rebase origin/<target>` (or merge if the
   project explicitly forbids history rewrite — but rebase is the
   default).
2. Re-run the project's verification commands after rebase. A clean
   pre-rebase build is not transitive.
3. Push with `git push --force-with-lease`. Plain `--force` is
   forbidden; force-with-lease protects against racing pushers.

Force-push permission scope: §11 grants a narrow, conditional
permission to force-push **only on a feature branch you own, only
after a rebase that brings it current with the integration target,
and only with `--force-with-lease`**. This is the only carve-out from
the "no force push without explicit approval" rule above. Any other
force-push still requires explicit approval.

Reviewer obligations:

1. Run the rev-list check above before any other review step. A
   non-zero left side is an immediate FAIL — do not inspect code, do
   not run tests, do not negotiate. Bounce back to the worker.
2. After PASS on rev-list, also run `git diff --stat
   origin/<target>..origin/<branch>` and confirm the diff contains
   only files in the WO's declared scope. Phantom regressions
   sometimes survive a stale rebase if conflicts were resolved
   incorrectly.

This complements `concurrent-work-protocol.md`'s "if changes are not
part of the current task, stop" rule: §11 makes that rule verifiable
at review time using only `git`.
