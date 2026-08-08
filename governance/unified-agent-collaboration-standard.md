# Agent Operating Standard

> 节点 3 方案 A 重定位（2026-07-26，三方评审一致推荐）：本文档从 "Unified Agent Collaboration Standard" 重定位为 "Agent Operating Standard"。
> 文件名保留（不改名，引用迁移归零）；只改文档内 title + 内容分层。
> **职责分工**：本文档管"怎么干活"（操作标准：字段/命令/流程/红线/Skill）。"谁干什么"（权威/编队/路由/双环治理）见 `workspace-collaboration-v2.1.md`。

## Positioning

This is the shared operating standard for all fleet agents (current and future). It is not tied to any project.

- 项目无关的跨工具操作接口（启动/执行/验证/交接的字段、命令、流程、纪律）
- **不定义编队成员、角色、任务路由**——以 `workspace-collaboration-v2.1.md` §2-§3 为唯一权威
- **不定义方向/终局/不可突破边界**——以 `north-star-v1.2.md` 为唯一校准基准
- **不定义工具入口/能力适配**——以 `configs/tool-entry-map.md` 为准

GitHub standard source: `https://github.com/lyosvne/agent-collaboration-standard`.

## Human Style

- Use Chinese by default unless the user asks otherwise.
- Lead with conclusions.
- Be concise. Do not repeat analysis unless it changes the decision.
- Give judgment, not only execution.
- Prefer simple, stable, reversible solutions.
- Do not silently fill ambiguous requirements.
- Do not praise ideas by default. Point out risks directly.

## Rule Layers

> **权威声明（节点 3）**：文档间权威冲突（如本标准 vs workspace vs north-star vs 项目规则）按 `workspace-collaboration-v2.1.md` §1 真值层级裁决。本节只裁决**同一文档层内**的规则冲突。

1. Human style and red lines: shared by all tools.
2. Collaboration protocol: shared by all coding agents.
3. Tool-level rules: adapted to each tool's environment.
4. Project-level rules: loaded only after entering a project.
5. Task-level instructions: apply only to the current task.

Higher layers win when rules conflict.

When rules conflict inside the same layer, resolve in this order:

1. More specific rule wins.
2. Rule closer to the current source of truth wins.
3. Safer and more reversible rule wins.
4. If still unclear, stop and ask the human.

## Shared Language

Every agent should use the same fields:

- Goal: what problem this task solves.
- Scope: files, modules, systems, or documents touched.
- Non-goals: what is intentionally not included.
- Source of truth: branch, commit, PR, issue, or document used as authority.
- Blocker: missing information or risk that prevents safe progress.
- Verification: commands, tests, screenshots, logs, or human paths used as proof.
- Risk: likely regressions, safety issues, and rollback path.
- Handoff: what the next agent must know.
- Done: verified state, commit/PR state, and remaining gaps.

## Shared Start Protocol

Before substantive work:

1. Identify the task type: research, planning, implementation, debugging, review, deployment, documentation, or configuration.
2. Identify the current source of truth.
3. Check repository state if the task touches code.
4. Read tool and project entry rules relevant to the task.
5. Choose the agent owner: per `workspace-collaboration-v2.1.md` §3 task routing（本标准不定义编队成员）。
6. State the smallest safe next action.

Minimum start output:

- Goal:
- Source of truth:
- Owner:
- Scope:
- Risk:
- Verification:
- Next action:

## Shared Completion Protocol

> **权威声明（节点 3 round2）**：完成契约的权威最小字段以 `workspace-collaboration-v2.1.md` §5 为准（治理层）。本节提供操作步骤 + 扩展字段（Recommended next command / Rollback 细项等），不复制 §5 的最低门槛。

Before claiming completion:

1. Re-read the user's request.
2. List what changed.
3. Run fresh verification or state exactly why it was not run.
4. Check whether unrelated changes exist.
5. Produce a handoff summary.
6. Sync through GitHub commit or PR when the task requires code synchronization.

No verification evidence means no completion claim.

Minimum finish output:

- Changed:
- Verified:
- Not verified:
- Risk:
- Commit / PR:
- Handoff:
- Recommended next command:
- Recommended next owner:
- Owner reason:

For code, configuration, data, deployment, or rule changes, include rollback:

- Rollback target:
- Rollback method:
- Rollback verification:

Any agent may keep internal methodology checklists (e.g. Superpowers, TDD), but cross-agent output must use the shared start and finish fields.

## Shared Commands

- `:ALL`: load global standard, project entry, project agents, coordination records, active task records, source of truth, and Git state.
- `:ONE`: load the same state, choose one primary owner, and keep other tools read-only unless parallel records are created.
- `:CHECK`: compare local rules, skills, memory, and project rules against GitHub truth. Read-only by default; append coordination result when safe.

Use append-only task events for shared coordination. Corrections supersede older events instead of erasing them.

Minimum change is a validation strategy, not a permanent endpoint. Keep long-term correctness and remaining convergence work visible.

`:ONE` may be fuzzy. If fuzzy, normalize it into inferred goal, recommended owner, owner reason, non-goals, risk, and next action before editing. Do not silently turn fuzzy `:ONE` into broad implementation.

Every meaningful finish must include a copyable next command and a recommended next owner so the human can continue in any tool.

## Role Resolution（节点 3 重写）

本标准**不维护编队成员名单**（避免编队一变就跟着腐坏，节点 3 三方共识）：

- **当前编队成员、职责、任务路由**：见 `workspace-collaboration-v2.1.md` §2-§3（唯一权威）
- **职能映射 + 双环治理**：见 `fleet-division-v1.1.md`
- **工具入口与能力适配**：见 `configs/tool-entry-map.md`

## Execution Constraints (agent-neutral)

以下约束适用于所有 agent，与具体编队角色无关：

### GitHub

- Only hard code synchronization surface.
- Branches, commits, PRs, issues, and releases are the durable handoff layer.

### Cloud Coding Agents

- Isolated execution workers.
- Must receive a handoff pack and return a branch, PR, patch, or written report.
- Must not inherit chat context as authority.
- Must not depend on local Windows paths. Use project `AGENTS.md`, task packs, branches, PRs, or a shared standard repository.
- Must not touch production secrets, production data, SSH, deployment, or long-running services unless explicitly authorized.

## Safety Red Lines

> **权威声明（节点 3）**：红线权威版本为 `workspace-collaboration-v2.1.md` §4（T1/T2/T3 密钥分级、分支纪律、Pi 无 Git 写权限）。本节是操作视角的执行清单，与 §4 不一致时以 §4 为准。

Ask before:

- Editing secrets, `.env`, tokens, or credentials.
- Changing database schema or running migrations.
- Deploying to production or changing cloud runtime state.
- Running `git push`, `git rebase`, `git reset --hard`, or force operations.
- Installing global dependencies or changing system configuration.
- Deleting files, directories, branches, worktrees, or Git history.
- SSH, SCP, remote server operations, or production data access.

## Git Rules

> **权威声明（节点 3）**：分支所有权、push 权限、master 集成等治理规则以 `workspace-collaboration-v2.1.md` §4/§6 为准。Pi 只读检测和协调，不执行 Git 写操作。

- GitHub branch, commit, and PR are the only hard sync points.
- Never use `git add .`.
- Stage only files touched by the current task.
- Do not mix unrelated dirty work into a commit.
- If unexpected changes appear, stop and ask.
- Commit per independently verified functional unit when code synchronization is required.

## Local GitHub Network Rules (local Windows machine only)

> 本节是本机排障经验，非跨项目通用规则。云端 agent 不适用。整节迁移到本机运行手册留后续卫生批次。

- Do not hard-code `github.com` in `C:\Windows\System32\drivers\etc\hosts` by default.
- If GitHub fails, first inspect `hosts`, DNS, TCP 443, HTTPS, and `git ls-remote`.
- Prefer default DNS when it works. On this machine, removing fixed `github.com` hosts entries restored GitHub via `20.205.243.166`.
- Only edit `hosts` after explicit human approval, with a backup and rollback path.
- If a temporary GitHub IP is needed, test the candidate IP before writing it. Do not assume `140.82.121.4` or `140.82.112.4` is stable.

## Skill Rules

> **权威声明（节点 3）**：Skill 生命周期治理（准入/合并/退役/沙箱）以 `registry/skill-governance.md` 为唯一权威。本节只规定执行要求。

- Skills are behavior protocols, not prose notes.
- Prefer a small complete skill set over many overlapping skills.
- New skills must explain trigger, input, output, red lines, and verification.
- Reuse upstream skills where suitable. Adapt and compress; do not blindly copy.
- Project-specific skills must not enter the global skill set unless reusable across projects.
- Sandbox agents do not automatically discover local skills unless their runtime explicitly supports it. Reference required skills from `AGENTS.md` or task packs.
