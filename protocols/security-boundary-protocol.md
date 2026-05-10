# Security Boundary Protocol

Ask before:

- editing `.env`, secrets, tokens, credentials, auth, billing, or CI/CD
- changing database schema or running migrations
- deploying, restarting production, or modifying cloud runtime
- running SSH/SCP or production data access
- installing global dependencies or changing system configuration
- deleting files, directories, branches, worktrees, or Git history
- changing repository permissions or branch protection

Never print or persist secrets in logs, commits, or summaries.

## Hosts And System Network Changes

- Treat `hosts` edits as system configuration changes.
- Do not add fixed `github.com` IP entries as the first fix for GitHub failures.
- Before any `hosts` edit, state the exact entry, why it is needed, what can break, and how to roll back.
- Back up `hosts` before editing, then verify DNS, TCP 443, HTTPS, and `git ls-remote`.
