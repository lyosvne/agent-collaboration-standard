# Handoff Pack: Claude Code → Zcode 替换任务

> 依据 v2.0.1 协作协议（`C:\Users\Admin\.agent-collaboration\standards\workspace-collaboration-v2.0.md`）
> 签发: Qoder（执行落地） | 日期: 2026-07-22 | 任务所有者: Zcode（独占）

---

## Goal

Zcode 完整接管 Claude Code 的职能（深度实现/调试/审查/终端编排），Claude Code 验证通过后正式退役。

## Source of truth

- GitHub `https://github.com/lyosvne/Aetheris-link.git` origin/master（硬真值锚点，当前 HEAD: 6d29c2f1）
- 协作协议: `C:\Users\Admin\.agent-collaboration\standards\workspace-collaboration-v2.0.md`（必读，先读再动手）
- 全局协作入口: `C:\Users\Admin\.agent-collaboration\START_HERE.md`

## Scope（允许操作的范围）

- `C:\Users\Admin\Aetheris-clones\claude`（唯一与 origin/master 同步的干净副本，接管或参考后重新 clone）
- `C:\Users\Admin\.claude\skills`（技能清单，评估迁移哪些到 Zcode）
- `C:\Users\Admin\Aetheris-worktrees\claude`（Claude 的 worktree，确认后接管或归档）
- Zcode 自己的配置目录 `C:\Users\Admin\.zcode`

## Out of scope（禁止触碰）

- 其他智能体的 clone: `Aetheris-clones\{kimi, qoder, solo, trae, trae-w4-master-integration}`（内有未抢救的 dirty 文件，Phase 0 处理中）
- `agent/mira`、`agent/kimi` 分支（活跃保留，分别属于 Mira 和 Kimi）
- 受保护文件: 各项目 `AGENTS.md`、`COLLABORATION.md`、`.agents/project-agents.md`（变更需 Mira/用户审批）
- 主仓库 `C:\Users\Admin\Aetheris-link`（落后 200 commits，由 Qoder 在 Phase 0 处理）
- 一切删除操作（清理统一在 Phase 5 由用户确认后执行）

## Red lines（继承协议 §5）

- 不 push / rebase / reset --hard / clean / force
- 不碰 secrets、.env、tokens、CI/CD
- 不部署、不 SSH ECS、不动生产数据
- 不删除任何文件、分支、Git 历史

## 前置条件

- [ ] Claude Code 进程（PID 176728）已冻结或退出，不再接新任务
- [ ] Zcode 已通读协作协议 v2.0.1

## Verification（验收标准，全过才算替换完成）

1. Zcode 能在 `clones/claude`（或新 clone）上正确执行 `git status` / `git log`，确认与 origin/master 同步
2. 完成一个冒烟任务（如：修复一个小 bug 或补一个测试）并通过构建/测试
3. 按完成契约（协议 §6）汇报：Changed / Verified / Not verified / Risk / Handoff
4. Qoder 点检确认无越界写入（其他 clone 与受保护文件的 mtime 无变化）

## Next action

1. 读协议 → 2. 确认 Claude 冻结 → 3. 盘点 `.claude\skills` → 4. 接管/重建 clone → 5. 冒烟任务 → 6. 按契约汇报

## 完成后交接

- Recommended next owner: Qoder（更新协议 v2.1 移除 Claude Code 注册，宣告退役生效）
- Owner reason: 协议文档同步是 Qoder 的执行落地职责
