# Proposed Permission Baseline

> ⚠️ **历史文档（2026-05-10）**：本文档是 Claude Code 时代的权限基线提案。
> CC 已于 2026-07-25 完全退役，本提案不再活跃使用。
> Phase D（2026-07-26）后，文中 `~/.agent-collaboration/backups/` 路径已降级为只读历史快照，
> **不再作备份写入目标**。本文档仅作历史记录，禁止按此执行。
> 现行权限基线见 `.zcode/AGENTS.md`。

This is a proposed target baseline. Do not apply automatically.

## Goal

Keep autonomous coding fast for safe local work while forcing approval for sensitive actions.

## Auto-Allow Categories

- File reads inside the active workspace.
- File edits inside the active workspace and approved global rules directories.
- Directory creation inside approved workspaces.
- Local build and test commands.
- Local typecheck and lint commands.
- Git inspection commands such as status, diff, log, branch list, and remote info.
- Read-only Feishu and article extraction tools when already authenticated.

## Ask-First Categories

- `git push`, `git rebase`, `git reset`, force operations, stash operations.
- SSH, SCP, rsync, remote server commands.
- Deploy, restart, production runtime, cloud resource changes.
- `.env`, tokens, credentials, API keys, CI/CD, auth, billing.
- Database schema changes, migrations, data deletes.
- Global dependency installs or system package managers.
- Destructive deletion commands.
- Broad shell escape commands such as unrestricted PowerShell or shell.
- Network download or execution commands that are not pinned and reviewed.

## Claude Code Target

Keep:

- Local build/test/typecheck commands.
- Safe Git inspection.
- Tool-specific read-only commands.
- Project-local script execution.

Remove or require approval:

- Any stored secret-bearing command.
- Broad `curl *`, `powershell *`, unrestricted shell, `git push *`, install commands, SSH/SCP, deletion, task killing, and user-home broad reads.

## Trae IDE Target

Keep:

- Safe file operations in approved paths.
- Local project commands.
- Safe Git inspection.

Tighten:

- Replace broad `git` with read-only Git commands where possible.
- Remove always-on `Remove-Item`, `Move-Item`, broad `powershell`, and broad `.claude` / `.trae-cn` write access after setup.

## Trae SOLO PC Target

Add:

- Same human style and collaboration rules.
- Same ask-first categories.
- Same handoff summary.

Do not add broad permissions unless a concrete workflow requires them.

## Rollback

Before changing settings, copy each original file to:

`C:\Users\Admin\.agent-collaboration\backups\YYYYMMDD-HHMMSS\`

