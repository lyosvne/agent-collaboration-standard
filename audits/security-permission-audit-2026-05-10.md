# Security Permission Audit 2026-05-10

## Scope

- Claude Code global settings.
- Trae IDE user settings.
- Trae SOLO PC user settings.
- Global collaboration rule entries.

No project files were intentionally changed during this audit.

## Summary

The current collaboration rules are aligned, but permission hygiene is not yet aligned.

Claude Code has the largest risk surface because `settings.local.json` contains many broad allow rules and historical high-impact commands.

Trae IDE has a smaller but still broad command allowlist.

Trae SOLO PC has minimal visible permission settings.

## Findings

### Critical

- Claude local permissions contain historical API key export commands. Values are not repeated here. Treat them as exposed.
- Claude local permissions include remote server operation patterns such as SSH/SCP and production-like deployment paths.
- Claude local permissions include broad command families such as shell, PowerShell, curl, git push, package install, process kill, and global install patterns.

### High

- Claude local permissions include broad read access to user-level directories.
- Claude local permissions include destructive or high-impact command families such as `rm`, `taskkill`, `git stash`, `git push`, and package manager install commands.
- Trae IDE command allowlist includes broad entries such as `powershell`, `git`, `Remove-Item`, `Set-Content`, `Move-Item`, and `Copy-Item`.
- Trae IDE file operation allow paths include broad access to `.claude` and `.trae-cn`, which is useful for setup but should not stay permanently wide.

### Medium

- Claude global rules still contain some project-leaning language under multi-tool collaboration. The new global entry reduces this risk but does not fully rewrite older text.
- Trae SOLO PC has rule alignment but no verified dedicated skills directory or permission baseline.
- There is no periodic checklist for permission review after tool installation or plugin updates.

## Recommended Immediate Actions

1. Rotate any API keys that appeared in local permission files or command histories.
2. Back up Claude and Trae settings before edits.
3. Replace broad allowlists with a minimal baseline.
4. Move deploy, SSH, SCP, git push, DB migration, global install, and destructive commands behind explicit approval.
5. Keep only read, local build/test, safe Git inspection, and project-local tool commands auto-allowed.

## Proposed Policy

- Auto-allow: read-only inspection, local tests, local builds, diagnostics, and project-local file edits.
- Ask first: push, deploy, remote operations, database migrations, secrets, destructive deletion, system config, global dependencies.
- Never persist: raw API keys, tokens, credentials, or secret-bearing commands.

## Action Taken After Approval

- Trae IDE command allowlist was narrowed.
- Trae IDE file operation paths were narrowed.
- A safe replacement baseline was created for Claude Code at `C:\Users\Admin\.agent-collaboration\configs\claude-settings.local.safe-baseline.json`.
- Claude Code `settings.local.json` was not overwritten by command because the local safety wrapper blocks writes to `.claude`.
- Trae SOLO PC settings were left minimal and unchanged.

## Still Required

- Manually replace `C:\Users\Admin\.claude\settings.local.json` with the safe baseline if you want Claude permissions fully tightened now.
- Rotate any API keys that appeared in local permission command history.
