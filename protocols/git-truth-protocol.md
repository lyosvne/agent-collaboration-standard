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
