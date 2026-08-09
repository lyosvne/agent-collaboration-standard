# 固定公共源治理同步实施计划

日期：2026-08-09
设计依据：`docs/superpowers/specs/2026-08-09-public-source-governance-sync-design.md`

## 完成标准

- GitHub Runner 只向 ECS 发送目标 commit 和固定动作，不传输 bundle 或其他治理数据。
- ECS 只从固定公共仓的 `refs/heads/master` 主动 fetch，不持有 GitHub 凭据。
- Helper 独立验证 canonical master、目标对象、fast-forward、mirror 状态和权限。
- Dry-run、apply、backup、CAS、reset、receipt 与回滚语义通过测试和安全审查。
- 手动 no-op、最小 FF、重复 no-op 均通过，endpoint、mirror、receipt 与 Pi 投影一致。

## 阶段一：治理仓实现

### 基线

1. 从最新 `origin/master` 创建独立实现分支。
2. 将已批准设计与本实施计划带入实现分支。
3. 确认最新 master 包含现有 bundle helper、forced gate、tmpfiles、sudoers 与事务化分块修复。
4. 不修改治理正文、manifest 逻辑版本或 Pi memory 语义。

### Public helper

新增：

```text
runtime/governance-sync/aetheris-governance-sync-public
```

CLI：

```text
aetheris-governance-sync-public --commit <40hex> --dry-run
aetheris-governance-sync-public --commit <40hex> --apply
```

要求：

- 两个模式互斥且必须提供一个。
- 拒绝 root、额外参数、缩写参数、非小写完整 commit。
- 固定远端 `https://github.com/lyosvne/agent-collaboration-standard.git`。
- 固定 canonical ref `refs/heads/master`。
- 固定 mirror、lock、receipts、backup 和 operation ref namespace。
- Git 使用绝对 executable、空 HOME、禁用系统配置、prompt、hooks 和自动维护，设置超时。
- 不读取 mirror `.git/config` remote URL作为网络目标。

执行顺序：

1. 获取 helper lock。
2. 验证 mirror、`.git`、config、HEAD、master、worktree 和权限。
3. 清理 operation namespace 中的 stale refs。
4. 将固定远端 master fetch 到内部 operation ref。
5. 验证目标是 commit且可达本次 remote master。
6. 验证当前 mirror master是目标祖先。
7. Dry-run 删除 operation ref并返回。
8. Apply no-op删除 operation ref，不创建 backup或receipt。
9. Apply FF创建 immutable backup ref，CAS更新master，reset并验证。
10. 删除 operation ref，原子发布 receipt并fsync。
11. 失败时沿用 bundle helper 的可验证回滚和 `receipt_state_uncertain` 规则。

Public receipt使用独立 schema，至少包含：

```text
source_mode = public-fixed-remote
remote_url_id = governance-public-origin-v1
remote_master
target_commit
before_commit
after_commit
backup_ref
operation_id
started_at
finished_at
```

不得记录 URL、凭据、环境变量、Git stderr、治理正文或临时 ref。

### Gate

修改：

```text
runtime/governance-sync/aetheris-governance-sync-ssh
```

新增 canonical 命令：

```text
sync-public <40hex> dry-run
sync-public <40hex> apply
```

要求：

- 旧五类 bundle 命令原样保留。
- Public 命令只持 root-owned gate lock，不验证 incoming。
- Gate 以固定 argv、`shell=False`、关闭 stdin调用 public helper。
- Gate 严格验证 helper JSON schema，错误只输出稳定 error code。
- URL、branch、路径、额外参数和 shell metacharacters全部拒绝。

### 契约与测试

新增：

```text
runtime/governance-sync/tests/test_governance_sync_public.py
```

修改：

```text
runtime/governance-sync/tests/test_ssh_gate.py
runtime/governance-sync/tests/test_contract.py
runtime/governance-sync/contract.md
runtime/governance-sync/ssh-gate-contract.md
runtime/governance-sync/ssh-gate-deployment.md
```

必须覆盖：

- 当前 commit dry-run/no-op。
- canonical master新 commit FF。
- 未合并侧枝、回退、分叉和非 commit拒绝。
- Dry-run与apply之间remote变化时重新fetch。
- Dirty、detached、权限错误和锁冲突。
- Stale operation ref清理与清理失败。
- CAS、reset、operation ref删除、receipt和rollback fault injection。
- `receipt_state_uncertain`不错误回滚。
- Public helper不读取token、netrc或credential helper。
- Gate public命令不打开incoming但与legacy命令共享锁。
- Legacy bundle helper行为和测试保持不变。

验证：

```text
python3 -m unittest discover -s runtime/governance-sync/tests -p 'test_*.py'
python3 scripts/check-governance-truth.py
python3 -m unittest scripts/check_governance_truth_test.py
git diff --check
```

完成独立安全审查后提交 Governance PR。记录 merge commit和两个新二进制 SHA256。

## 阶段二：ECS 事务部署

### 部署前证据

记录：

- 当前 gate、bundle helper和public helper存在性、SHA256、owner/group/mode。
- sudoers、authorized key、gate lock和helper lock状态。
- mirror HEAD、master、symbolic HEAD和clean状态。
- backup refs与receipts数量。
- endpoint文档commit集合。
- Pi confirmed governance fact数量与reflection数量。

不得输出密钥或 secret内容。

### 双锁与备份

按顺序获取：

1. Gate lock。
2. Helper lock。

持锁后创建root-only恢复目录并备份：

- 当前 gate。
- 当前 bundle helper。
- sudoers、tmpfiles和authorized key元数据。
- 已存在的public helper。

记录每个备份的hash、owner和mode。Mirror不做副本，依赖当前commit和immutable backup ref恢复。

### 安装

1. 上传治理仓合并产物到root-only临时路径。
2. 校验产物SHA256。
3. Python语法检查。
4. 安装public helper为`root:root 0755`。
5. 原子替换gate为`root:root 0755`。
6. 不修改sudoers、tmpfiles或authorized key。
7. 验证deploy用户不能直接执行helper，仍只能sudo无参数gate。
8. 验证任意SSH命令和malformed public命令被拒绝。
9. 验证`pi-governance-sync`无需凭据即可访问固定公共仓。

### ECS 直接 no-op

以当前mirror commit通过forced gate执行：

```text
sync-public <current> dry-run
sync-public <current> apply
```

要求：

- Dry-run `would_change=false`。
- Apply返回`no-op`。
- Master、HEAD和worktree不变。
- Backup、receipt数量不变。
- Operation namespace为空。
- Legacy gate smoke仍通过。

失败时在Aetheris workflow PR合并前恢复旧gate/public helper。

## 阶段三：Aetheris workflow切换

从最新Aetheris `origin/master` 创建独立分支。

修改：

```text
.github/workflows/governance-sync.yml
```

保留：

- 唯一`workflow_dispatch`。
- `target_commit`。
- `environment: production`。
- concurrency。
- pinned governance checkout和GitHub侧canonical检查。
- pinned SSH host key与专用identity。
- endpoint验证。

删除：

- bundle create与SHA256。
- upload、upload-chunk、dd、openssl。
- ControlMaster、ControlPersist、ControlPath。
- remote cleanup与staging marker。

只调用：

```text
sync-public <target_commit> dry-run
sync-public <target_commit> apply
```

严格解析public dry-run、applied和no-op JSON。

新增：

```text
scripts/governance-sync-workflow.test.mjs
```

静态契约要求：

- 只有手动触发。
- Governance repo和master固定。
- 只出现两种sync-public命令。
- 禁止bundle、upload、cleanup、ControlMaster、URL输入和branch输入。
- endpoint必须验证全部documents为目标commit。

在`validate.yml`的governance job执行该测试。原CI和独立安全审查通过后提交Aetheris PR。

## 阶段四：生产验收

### 完整 workflow no-op

输入当前mirror commit：

- Workflow绿色。
- Dry-run false，apply no-op。
- Runner日志无bundle、hash、offset或治理数据。
- Endpoint全部documents等于目标。
- Backup、receipt不增加。
- Operation refs为空。
- Mirror attached、clean。

### 最小 FF

在governance仓创建独立的最小文档变更PR：

- 不修改manifest逻辑版本。
- 不修改Pi memory语义。
- 不改运行代码。
- 正常CI与review合并。

以该merge commit手动触发：

- Dry-run `would_change=true`。
- Apply返回`applied`。
- Backup ref指向旧commit。
- 恰好新增一个public receipt。
- Mirror、HEAD、worktree和endpoint等于目标。
- Operation refs为空。
- Pi重启后confirmed fact唯一、reflection为零。

### 重复 no-op

再次触发同一commit：

- Dry-run false。
- Apply no-op。
- 不新增backup或receipt。
- Endpoint与Pi投影不变。

## 回滚

### Workflow

- Revert Aetheris workflow PR。
- 保持仅手动触发。
- 不并行运行public与bundle同步。

### ECS二进制

- 禁止新的dispatch。
- 获取gate lock和helper lock。
- 校验当前hash与部署记录匹配。
- 原子恢复gate和public helper备份。
- 复验sudo、forced command、任意命令拒绝和legacy smoke。

### Mirror

- 优先依赖helper自动CAS回滚。
- 自动回滚失败时保持锁与服务隔离，使用immutable backup ref和expected-old CAS人工恢复。
- `receipt_state_uncertain`时不得自动回滚或重试apply。
- 已成功FF后的业务回滚优先在公共governance master提交正常revert，再通过public通道FF收敛。

## 停止条件

出现以下任一情况立即停止：

- 需要PAT、token、deploy key或新增sudo授权。
- Public命令依赖incoming。
- URL或branch可被输入覆盖。
- Canonical或FF ancestry方向不明确。
- Dry-run/no-op产生backup、receipt或operation ref。
- `rollback_failed`或`receipt_state_uncertain`未处理。
- Endpoint commit集合不唯一。
- Pi出现多个confirmed fact或非零reflection。
