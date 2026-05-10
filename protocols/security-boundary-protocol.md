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
