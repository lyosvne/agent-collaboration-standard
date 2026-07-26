# Unified Skill Registry

This registry keeps the global skill set small and non-overlapping.

## Core Skills To Install

| Skill | Purpose | Source To Reuse | Status |
|---|---|---|---|
| `collaboration-bootstrap` | Shared start protocol for any coding task | Superpowers `using-superpowers`, user global rules | Created in Trae + Claude |
| `cross-agent-handoff` | Generate and read handoff packs | Superpowers plan/finish flow, local handoff needs | Created in Trae + Claude |
| `git-truth-guardian` | Protect GitHub source of truth and dirty worktrees | Claude commit discipline, user rules | Created in Trae + Claude |
| `verification-gate` | Evidence before completion claims | Superpowers `verification-before-completion` | Created in Trae + Claude |
| `debugging-gate` | Root-cause-first debugging | Superpowers `systematic-debugging`, TRAE-debugger | Created in Trae + Claude |
| `plan-gate` | Lightweight planning and execution discipline | Superpowers `writing-plans`, `executing-plans` | Created in Trae + Claude |
| `review-gate` | Second-view code review | Claude `code-review`, TRAE-code-review | Created in Trae + Claude |
| `security-boundary-gate` | Secrets, DB, deploy, permissions red lines | Global rules, security guidance | Created in Trae + Claude |

## Existing Skills To Keep

| Skill | Keep Because | Boundary |
|---|---|---|
| `feishu-cli-operator` | Stable read-only Feishu operations | Tool skill, not development mainline |
| `wechat-article-reader` | Stable WeChat article extraction | Article-read-only |
| `frontend-visual-review` | Structured frontend review | Use only for visual/product surfaces |
| `frontend-design` | Design-led frontend creation | Use only when visual direction matters |
| `typescript-lsp` | TypeScript diagnostics | Claude-side or equivalent checks |
| `prd` | Product requirement drafting | Use when user asks for PRD |
| `tavily-research` | Deep cited research | Use only for research requiring external sources |

## Existing Skills To Merge

| Existing | Merge Into |
|---|---|
| `requesting-code-review`, `receiving-code-review`, `TRAE-code-review` | `review-gate` |
| `writing-plans`, `executing-plans`, `finishing-a-development-branch` | `plan-gate` |
| `verification-before-completion` | `verification-gate` |
| `systematic-debugging`, `TRAE-debugger` | `debugging-gate` |
| Multiple visual style skills | One design/review capability group |

## Existing Skills To Avoid As Always-On

| Skill | Reason |
|---|---|
| `full-output-enforcement` | Only needed for exhaustive full output tasks |
| Greenfield `web-dev` | Too broad for existing codebases |
| Project-specific Aetheris skills | Stay inside Aetheris context only |

## Rule

Do not add a new global skill unless it is reusable across projects and does not overlap an existing core skill.
