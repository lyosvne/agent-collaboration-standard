# Permission Tightening Change List

> ⚠️ **历史文档（2026-05-10）**：本文档记录 Claude Code 权限收紧的执行过程。
> CC 已于 2026-07-25 完全退役，本配置不再活跃使用。
> Phase D（2026-07-26）后，文中 `~/.agent-collaboration/` 路径已降级为只读历史快照，
> **不再作备份/写入目标**。本文档仅作历史记录，禁止按此执行。
> 现行权限基线见 `.zcode/AGENTS.md` + 项目级 AGENTS.md。

Do not execute without explicit user approval.

## Backup First

Create a timestamped backup directory:

`C:\Users\Admin\.agent-collaboration\backups\<timestamp>\`

Back up:

- `C:\Users\Admin\.claude\settings.local.json`
- `C:\Users\Admin\AppData\Roaming\Trae CN\User\settings.json`
- `C:\Users\Admin\AppData\Roaming\TRAE SOLO CN\User\settings.json`

## Claude Code

Target file:

`C:\Users\Admin\.claude\settings.local.json`

Proposed changes:

- Remove secret-bearing command entries.
- Remove or approval-gate broad shell entries:
  - unrestricted PowerShell.
  - unrestricted curl.
  - unrestricted git push.
  - unrestricted package install.
  - SSH/SCP remote operations.
  - destructive delete/process-kill commands.
  - broad user-home reads.
- Keep safe local development entries:
  - build/test/typecheck commands.
  - read-only Git inspection.
  - approved read-only tool commands.

Execution status:

- Safe baseline created at `C:\Users\Admin\.agent-collaboration\configs\claude-settings.local.safe-baseline.json`.
- Direct write to `settings.local.json` was blocked by local safety wrapper.
- Manual replacement or tool-level allowlist update is still required.

## Trae IDE

Target file:

`C:\Users\Admin\AppData\Roaming\Trae CN\User\settings.json`

Proposed changes:

- Narrow `AI.toolcall.v2.command.allowList`.
- Remove always-on destructive or broad commands:
  - `Remove-Item`
  - broad `powershell`
  - broad `Move-Item`
  - broad `git`
- Keep setup-safe commands:
  - `Test-Path`
  - `New-Item`
  - `Get-Content`
  - `Set-Content`
  - `Add-Content`
  - `Out-File`
  - `Measure-Object`
  - `lark-cli`
  - local build/test commands as needed.
- Narrow `AI.toolcall.v2.fileOp.allowPaths` after setup:
  - keep `.agent-collaboration`
  - keep global skill folders
  - avoid broad write access to entire `.claude` and `.trae-cn` unless actively maintaining rules.

Execution status:

- Applied.

## Trae SOLO PC

Target file:

`C:\Users\Admin\AppData\Roaming\TRAE SOLO CN\User\settings.json`

Proposed changes:

- Keep `AI.rules.importClaudeMd`.
- Do not add broad command allowlists yet.
- Add only if SOLO PC requires explicit permission configuration later.

Execution status:

- No change needed.

## Post-Change Verification

- Parse all JSON files.
- Read global entry files.
- Confirm key skills exist.
- Confirm no project repository files changed.
- Confirm no secret values are printed.
