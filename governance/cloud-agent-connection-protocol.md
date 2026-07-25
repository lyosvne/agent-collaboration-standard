# Cloud Agent Connection Protocol

## Positioning

Cloud coding agents are isolated execution workers.

They can research, implement, test, or review, but they cannot define source of truth by themselves.

Sandbox agents are cloud agents unless they can access the user's local machine directly.

They must not depend on local Windows paths such as `C:\Users\Admin\...`.

## Allowed Entry Paths

- GitHub issue.
- GitHub branch.
- Pull request.
- Patch file.
- Cross-agent handoff pack.
- Project root `AGENTS.md`.
- Shared standard repository, if one exists.

## Required Task Pack

Every cloud agent task must include:

- Repository URL.
- Branch or base commit.
- Goal.
- Non-goals.
- Files or modules in scope.
- Files or modules out of scope.
- Project entry rules.
- Verification commands.
- Safety red lines.
- Expected output: PR, patch, or report.
- Forbidden commands and operations.

## Execution Rules

- Work in a branch or isolated patch.
- Do not change secrets, deployment, database schema, or CI/CD without explicit approval.
- Do not use chat history as source of truth.
- Do not make broad cleanup changes.
- Keep commits focused by functional unit.
- Return verification evidence.
- Do not run `rm -rf`, `git push --force`, `git reset --hard`, `git rebase`, deployment, SSH, SCP, or secret-reading commands unless explicitly authorized.
- Do not touch production data, production credentials, ECS, or persistent services by default.
- If the sandbox has no technical permission barrier, say so in the handoff.

## Return Contract

- Branch / PR / patch:
- Changed:
- Verified:
- Not verified:
- Risk:
- Rollback:
- Open questions:
- Suggested next owner:

## Small Edit Limit

A sandbox small edit means:

- Single file or a small set of text/config changes.
- Diff is usually under 100 lines.
- No database, deployment, secrets, remote server, dependency, or Git high-risk operation.
- Human can quickly review it.
- Rollback is obvious.

## Rejection Conditions

Reject or pause cloud-agent work when:

- Base commit is missing.
- Source of truth is ambiguous.
- Task asks for deployment or secret handling without approval.
- Task scope is too broad.
- Verification cannot be defined.
- Project rules conflict with global red lines.
