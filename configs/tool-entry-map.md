# Tool Entry Map

This file maps where each coding agent should read global rules from.

## Shared Entry

All tools should start from:

`C:\Users\Admin\Documents\trae_projects\agent-collaboration-standard\START_HERE.md`

> Phase D（2026-07-26）：真值源迁到 git 仓库。本机 `~/.agent-collaboration\` 降级为只读历史快照，不再作活跃入口。

## ZCode (接替 Claude Code)

Primary entry:

`C:\Users\Admin\.zcode\AGENTS.md`

Required behavior:

- Read `START_HERE.md`.
- Use global collaboration skills from `C:\Users\Admin\.agents\skills` (共享,工具无关).
- Load project `AGENTS.md`, `CLAUDE.md`(历史保留), or README after entering a repository.
- (历史) Claude Code 入口 `.claude\CLAUDE.md` 已随退役归档,不再使用。

## Trae SOLO（编队独立角色：端到端测试/QA）

> 2026-07-26 C 选项裁定：SOLO 是编队里 Trae 系的**唯一独立角色**，承担端到端测试/QA 职能。
> 实际工作产出在 `~/Aetheris-clones/solo/` 的 `agent/solo` 分支（W2/W3/W4 测试基线、dispatcher red/green、wave4 owner plan）。
> 之前的 B1 合并方案（把 SOLO 合并进 Trae）已撤销，详见 `archive/b1-rollback-20260726/`。

Primary entries:

- `C:\Users\Admin\Documents\trae_projects\agent-collaboration-standard\configs\trae-solo-operating-profile.md`
- `C:\Users\Admin\Documents\trae_projects\agent-collaboration-standard\configs\trae-solo-pc-alignment.md`
- `C:\Users\Admin\AppData\Roaming\TRAE SOLO CN\User\SOLO_AGENT_RULES.md`
- Imported Claude rules when `AI.rules.importClaudeMd` is enabled.

Required behavior:

- Treat SOLO PC as a full autonomous coding agent.
- Read `START_HERE.md`.
- End every task with a handoff-ready summary.

## Trae IDE（已退役为编队角色）

> 2026-07-26 C 选项裁定：Trae IDE **不再作为编队独立角色**（退到个人工具）。
> 软件保留（用户个人使用），但不进 Pi 调度链。
> Trae IDE 在 Aetheris 的历史产出（`agent/trae` 分支）将通过独立的 git 合并任务并入 `agent/solo`（见 todo）。

历史入口（仅供个人使用参考，不再纳入编队协作）:

- `C:\Users\Admin\.trae-cn\GLOBAL_AGENT_RULES.md`

## GitHub

Primary entry:

- Branches, commits, PRs, issues, and releases.

Required behavior:

- GitHub is the hard code sync layer.
- Chat summaries are not enough.

## Cloud Agents

Primary entry:

- A handoff pack, issue, branch, or PR.

Required behavior:

- Do not rely on local chat memory.
- Return a PR, patch, or structured report.
- Use `C:\Users\Admin\Documents\trae_projects\agent-collaboration-standard\templates\cloud-agent-task-pack.md` before execution.
