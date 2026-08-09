# 固定公共源治理同步设计

日期：2026-08-09
状态：已批准，待实施计划
范围：Aetheris ECS governance mirror 的手动同步通道

## 背景

现有 Aetheris workflow 在 GitHub-hosted runner 构造完整 governance bundle，再通过受限 SSH gate 上传到 ECS。安全边界已经收紧，但 runner 到中国 ECS 的数据通道在累计约 3 MiB 后停止推进。多次试跑均停留在 upload，未进入 dry-run 或 apply。

本设计取消 workflow 到 ECS 的 bundle 数据传输。Workflow 只发送一个经过校验的 40 位 commit；ECS 以固定公共 GitHub 仓库为唯一网络源，主动拉取并在本地完成 canonical master、fast-forward、事务更新和回执验证。

## 目标

- GitHub Workflow 仅发送精确 commit，不发送 bundle、URL、路径或命令文本。
- ECS 只从固定公共仓 `https://github.com/lyosvne/agent-collaboration-standard.git` 拉取。
- 目标 commit 必须可达远端 `refs/heads/master`。
- Mirror 只允许 fast-forward，不允许回退、分叉或 detached HEAD。
- 保留 backup ref、CAS、worktree reset、receipt 和失败回滚语义。
- 第一阶段仅保留手动 `workflow_dispatch`，不启用定时或 push 自动触发。

## 非目标

- 不修改治理正文、manifest 逻辑版本或 Pi memory 语义。
- 不为 ECS 配置 GitHub token、PAT、deploy key 或普通服务凭据。
- 不允许 workflow 指定 remote URL、branch、ref namespace、mirror 路径或任意 shell 命令。
- 不在本阶段移除 bundle helper；它作为回滚通道保留，但新 workflow 不调用。
- 不在本阶段增加 systemd timer 或跨仓 `repository_dispatch`。

## 方案选择

采用固定远端 fetch helper。

备选方案未采用：

- 独立 bare cache：隔离更强，但增加第二套仓库、锁、清理和恢复状态。
- systemd transient unit：能脱离 workflow 进程，但扩大 systemd 授权和审计面。
- ECS timer：自动化程度高，但在手动 no-op 和最小 FF 尚未验收前不应启用。

## 组件

### GitHub Workflow

保留 Aetheris 仓的 `governance-sync.yml`，删除 bundle 构造、上传、分块、ControlMaster 和 staging cleanup。

输入：

```text
target_commit = 40 位小写十六进制 commit
```

Workflow 仍 checkout governance `master`，在 GitHub 侧先确认目标对象存在且可达 `master`。该检查用于尽早失败，但不替代 ECS 的独立验证。

### SSH forced-command gate

Gate 新增且只新增：

```text
sync-public <40hex> dry-run
sync-public <40hex> apply
```

Gate 不接受 URL、branch、路径、remote 名、环境变量覆盖或额外参数。它以固定 argv 调用 public-source helper，不经过 shell。

现有任意 SSH 命令拒绝、固定有效 UID/GID、JSON 输出收敛、root-owned gate、sudoers 和 authorized_keys 限制保持不变。

### Public-source helper

安装路径：

```text
/usr/local/sbin/aetheris-governance-sync-public
```

编译固定资源：

| 资源 | 固定值 |
|---|---|
| Public remote | `https://github.com/lyosvne/agent-collaboration-standard.git` |
| Canonical branch | `refs/heads/master` |
| Mirror | `/opt/pi/governance-mirror/repo` |
| Lock | `/run/lock/aetheris-governance-sync.lock` |
| Receipts | `/var/lib/aetheris-governance-sync/receipts` |
| Backup namespace | `refs/aetheris-governance-sync/backups/` |

Helper 以 `pi-governance-sync` 运行并拒绝 root。Git 使用固定绝对路径、空 HOME、禁用系统配置、禁用 prompt、禁用 hooks，并设置超时。

## 数据流

1. 操作者手动触发 Aetheris workflow，输入目标 commit。
2. Workflow checkout governance `master`，验证目标存在且可达。
3. Workflow 通过 pinned SSH 调用 `sync-public <commit> dry-run`。
4. Gate 严格解析并以固定 argv 启动 public-source helper。
5. Helper 获取固定远端 `master` 到临时 ref，不覆盖 mirror `master`。
6. Helper 验证目标 commit 可达临时远端 master。
7. Helper 验证当前 mirror `master` 是目标祖先。
8. Dry-run 返回结构化 JSON，不修改 mirror、backup 或 receipt。
9. Workflow 校验 dry-run JSON 后调用 `sync-public <commit> apply`。
10. Helper 重新执行所有网络、对象、权限和 ancestry 检查，不复用 dry-run 结论。
11. Helper 创建 backup ref，以 compare-and-swap 更新 `master`，reset worktree并写 receipt。
12. Workflow 验证公开 truth endpoint 中所有文档 commit 等于目标。

## Git 获取策略

Helper 不信任 mirror 中已有的 `origin` 配置。每次调用均对固定 URL 执行显式 fetch：

```text
refs/heads/master -> 临时 operation ref
```

临时 ref 使用 helper 固定 namespace 和 operation ID，不由输入控制。验证结束后删除临时 ref；若进程异常退出，后续调用在持锁状态下清理过期 operation ref。

必须验证：

- fetch 得到的对象是 commit；
- 输入目标可达本次获取的 canonical master；
- 当前 mirror master 可达目标；
- mirror HEAD 附着于 `master` 且 worktree clean；
- mirror、`.git`、config、lock、receipt 路径和权限仍符合现有 contract。

## 事务语义

### Dry-run

返回精确字段：

```json
{
  "status": "dry-run",
  "before_commit": "<40hex>",
  "commit": "<40hex>",
  "remote_master": "<40hex>",
  "would_change": true
}
```

目标等于当前 mirror 时 `would_change=false`。Dry-run 不创建 backup ref 或 receipt。

### Apply

Apply 不信任 dry-run 缓存，重新 fetch 并重新验证。目标等于当前 mirror 时返回 no-op，不创建 backup 或 receipt。

Fast-forward apply：

1. 创建 immutable backup ref 指向旧 master。
2. 使用 `update-ref` compare-and-swap 更新 master。
3. hard reset worktree 到新 master。
4. 验证 attached、clean 和 exact target。
5. 原子写 receipt 并 fsync。

Receipt 增加：

```text
source_mode = public-fixed-remote
remote_url_id = governance-public-origin-v1
remote_master = <40hex>
target_commit = <40hex>
```

Receipt 不记录凭据、环境变量、完整远端响应或治理正文。

## 失败与回滚

- 网络失败、超时、TLS 校验失败：fail closed，不修改 mirror。
- 目标不属于远端 master：`target_not_canonical`。
- 当前 mirror 不能 fast-forward 到目标：`non_fast_forward`。
- Mirror dirty、detached 或权限异常：沿用现有稳定错误码。
- CAS 后 reset 或 receipt 失败：沿用现有 rollback 语义恢复旧 master。
- 回滚不能验证：`rollback_failed`。
- Receipt 发布状态不确定：沿用 `receipt_state_uncertain`，不执行可能制造矛盾的回滚。

所有错误仅输出稳定 JSON error code，不透传 Git stderr、URL 查询信息或 traceback。

## 权限与网络

- Deploy 用户仍无 mirror、incoming、receipt、lock 写权限。
- Deploy 用户不能直接运行 helper。
- Sudoers 仍只允许无参数 gate。
- Public helper 只允许固定 GitHub HTTPS URL。
- 不读取 `.git/config` remote URL 作为网络目标。
- 不使用 SSH Git remote、credential helper、netrc、GitHub token 或 PAT。
- ECS 出站网络策略应仅允许 DNS、TLS 和固定 GitHub 公共端点；若当前主机无法做域名级 egress allowlist，则至少通过 helper 固定 URL和 TLS 校验限制应用层目标。

## 测试

### 单元与契约

- 严格接受两种 gate 命令，拒绝 URL、branch、路径、额外参数和 shell metacharacters。
- 固定 remote、branch、mirror、lock、receipt 和 backup namespace 不可由环境覆盖。
- Git subprocess 使用固定 argv、环境、超时和 `shell=False`。
- JSON schema、错误码、receipt 字段和隐私扫描通过。

### Git 集成

- 当前 commit：dry-run no-op，apply no-op。
- 新 canonical master commit：dry-run would-change，apply fast-forward。
- 未合并侧枝：拒绝。
- 回退 commit：拒绝。
- 分叉 commit：拒绝。
- 远端 master 在 dry-run 与 apply 之间变化：apply 重新验证，不能复用旧判断。
- Mirror dirty、detached、权限错误、锁冲突：全部 fail closed。
- CAS、reset、receipt 和 rollback fault injection 保持通过。

### 生产验收

1. 部署 helper 和 gate contract 后验证任意 SSH 命令仍被拒绝。
2. 手动运行当前 mirror commit，要求完整 no-op workflow 绿色。
3. 创建最小 governance 文档变更并经 PR/CI 合并。
4. 手动运行新 commit，要求 backup、FF、receipt 和 endpoint 全部通过。
5. 再次运行同一 commit，要求 no-op 且不新增 receipt。
6. 确认 Pi 重启后治理 confirmed fact 仍保持唯一、reflection 为零。

## 发布与回滚

发布顺序：

1. Governance PR：public helper、gate 命令、contract、测试。
2. CI 全绿并完成独立安全审查。
3. ECS 备份现有 helper、gate 和 sudoers。
4. 安装 public helper 与新 gate，执行 no-op smoke test。
5. Aetheris PR：workflow 切换到 commit-only 调用。
6. 手动 no-op 验收。
7. 最小 FF 验收。

回滚：

- Aetheris workflow 回滚到上一个 commit，保持仅手动触发。
- ECS 恢复 gate/helper 备份。
- Mirror 使用 immutable backup ref 恢复。
- Bundle helper 与现有 bundle gate 在本阶段保留，不作为默认 workflow 通道。

## 完成标准

- GitHub Runner 不再向 ECS 传输治理仓数据。
- ECS 不持有 GitHub 凭据。
- 手动 no-op 和最小 FF workflow 均通过。
- 所有失败场景在 mirror 变更前 fail closed，或按既有事务语义完成可验证回滚。
- 公开 endpoint、mirror commit、receipt 和 Pi confirmed 投影一致。
