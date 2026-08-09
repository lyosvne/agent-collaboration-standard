# 固定 GitHub Release 治理同步设计

日期：2026-08-09
状态：已批准并实施
范围：Governance 发布与 Aetheris ECS 手动同步通道

## 背景与决策

Runner 直接向 ECS 传输 bundle 的通道不稳定；ECS 直接对 Git 仓执行 fetch
又扩大了 Git 协议、配置与对象导入实现面。采用已批准的“GitHub Release API
+ 增量 bundle”方案：治理仓负责发布不可覆盖的 commit-bound Release。ECS
从固定匿名 API 端点下载增量 bundle，在本地临时 bare 仓中以固定 mirror
objects 作为 alternates 重建完整 bundle，再复用已经审计的旧 helper。

## 目标

- `master` push 与手动指定 target 都发布相对固定 baseline 的增量 bundle。
- baseline 固定为 `bef402ae2c2518961c6abe0d90a1838346e9afb9`。
- tag 固定为 `governance-sync-v2-<40hex commit>`。
- target 必须是 commit、可达 canonical `master`，且 baseline 必须是 target 祖先。
- Release 与既有 tag 不可覆盖、更新或删除。
- ECS 不持有 token、PAT、deploy key、netrc 或 credential helper。
- ECS 只信任 Release metadata 的 tag、target、asset name/id/size。
- manifest 与 bundle 的 commit、size、SHA-256 必须精确一致。
- 增量 bundle 只允许从本地 file 路径读取；禁止 Git 网络协议。
- public helper 在不可输入覆盖的临时 bare 仓中重建完整 target 历史。
- 只有重建后的完整 bundle 原子发布到固定 incoming 路径，再用旧 helper 固定 argv。
- 无论成功或失败都清理本次发布的 incoming bundle。
- forced-command gate 继续只接受 `sync-public <commit> dry-run|apply`。

## 非目标

- 不修改旧 bundle helper。
- 不修改 sudoers、tmpfiles、authorized-key forced command。
- 不修改治理正文、manifest 逻辑版本或 Pi memory 语义。
- 不增加可输入 URL、仓库、branch、asset URL、路径或凭据。

## Publisher workflow

`.github/workflows/governance-release.yml` 在以下事件运行：

1. push 到 `master`，target 为 push commit；
2. `workflow_dispatch`，target 为精确 40 位小写 commit。

Workflow 使用固定 SHA 的 `actions/checkout`，checkout canonical `master`，
`fetch-depth: 0` 且不持久化凭据。它验证 target 是 commit，并执行：

```text
git merge-base --is-ancestor <target> refs/remotes/origin/master
```

随后验证 baseline 是 target 祖先，将本地 `refs/heads/master` 精确指向 target。
当 target 等于 baseline 时排除 `target^`；否则排除 baseline。由此创建增量
`governance.bundle` 并执行 `git bundle verify`。

Manifest 文件名固定为 `governance-sync-manifest.json`，是 sorted-key、
compact-separator、末尾单换行的 canonical JSON：

```json
{
  "bundle": {
    "name": "governance.bundle",
    "sha256": "<64 lowercase hex>",
    "size": 123
  },
  "base_commit": "bef402ae2c2518961c6abe0d90a1838346e9afb9",
  "bundle_kind": "incremental",
  "commit": "<40 lowercase hex>",
  "schema_version": 2
}
```

Workflow 权限为 `contents: write`。创建前 GET 固定 tag endpoint，只有明确
`404` 才允许 POST；已存在、网络错误或其他状态均失败。创建 Release 时
`tag_name`、`target_commitish` 和 name 均绑定 target。只上传 manifest 和
bundle 两个 asset。流程只允许一次将验证完成的 draft 发布为非 draft 的
PATCH；禁止修改 tag、target、asset、名称，禁止 DELETE、clobber、复用或覆盖。
发布后必须回读 `immutable=true` 并重新验证锁定后的 tag ref 精确指向 target。

## Public helper 固定资源

安装路径：

```text
/usr/local/sbin/aetheris-governance-sync-public
```

固定值：

| 资源 | 值 |
|---|---|
| Release API base | `https://api.github.com/repos/lyosvne/agent-collaboration-standard` |
| Release tag prefix | `governance-sync-v2-` |
| Baseline | `bef402ae2c2518961c6abe0d90a1838346e9afb9` |
| Manifest asset | `governance-sync-manifest.json` |
| Bundle asset | `governance.bundle` |
| Incoming bundle | `/var/lib/aetheris-governance-sync/incoming/governance.bundle` |
| Existing helper | `/usr/local/sbin/aetheris-governance-sync` |

CLI 保持：

```text
aetheris-governance-sync-public --commit <40hex> --dry-run
aetheris-governance-sync-public --commit <40hex> --apply
```

参数不允许缩写、额外值或大写 commit；helper 使用 isolated Python，拒绝
effective root，并只输出稳定 JSON。

## 下载与信任边界

Release metadata 只能来自：

```text
https://api.github.com/repos/lyosvne/agent-collaboration-standard/releases/tags/governance-sync-v2-<commit>
```

Metadata 中仅提取：

- `tag_name`，必须等于构造的 tag；
- `target_commitish`，必须精确等于请求 commit；
- `assets[].name/id/size`。

忽略并绝不跟随 metadata 中的 `url`、`browser_download_url`、HTML URL 或
其他字段。Asset 下载 URL 由 helper 使用已验证的正整数 ID 自行构造：

```text
https://api.github.com/repos/lyosvne/agent-collaboration-standard/releases/assets/<id>
```

Manifest 与 bundle 必须各恰好出现一次。JSON 拒绝 duplicate key。Manifest
只接受 schema 2、固定 `base_commit`、`bundle_kind=incremental`、请求 commit
及精确 bundle name/size/SHA；额外、缺失、错误类型或值均失败。

`curl` 使用绝对路径、`--disable`、空 config、sanitized allowlist 环境、
禁用 proxy、HTTPS-only 原协议和重定向、TLS 1.2 下限、连接/总超时、重定向
上限和下载大小上限。Metadata、manifest、bundle 上限分别为 1 MiB、16 KiB、
64 MiB。主机不提供 token。stderr 和响应正文不向调用方透传。

下载后同时验证：

1. metadata bundle size 等于 manifest size；
2. 实际文件是普通文件；
3. 实际 size 等于 manifest size；
4. 实际 SHA-256 等于 manifest SHA-256；
5. manifest commit 等于请求 commit。

## 本地完整 bundle 重建

Public helper 在固定 incoming 目录下创建 owner-only 临时目录和 bare 仓；名称
由 helper 生成，不接受路径或环境覆盖。它只把固定
`/opt/pi/governance-mirror/repo/.git/objects` 写入 alternates，并验证该目录由
effective UID/GID 所有且不可被 group/world 写入。Git 使用 allowlist 环境，
清除 ambient `GIT_*` 配置，`protocol.allow=never` 且只开放 `file`。

helper 在带 alternates 的 bare 仓中 verify 增量 bundle，要求唯一
`refs/heads/master` 精确指向请求 target，只从下载的本地 bundle fetch 该 ref，
再验证 commit 与对象连通性。随后创建包含 target 完整历史的本地 full bundle，
并在不带 alternates 的空 bare 仓中 verify。旧 helper 接收的是 full bundle
及重新计算的 full SHA-256，而不是 manifest 中的增量 SHA。

## 原子发布与 relay

Public helper 验证 effective-ID-owned exact-mode `0700` incoming 目录和已有
固定 bundle（若存在）。它以 `O_EXCL|O_NOFOLLOW` 创建固定 staging inode，
复制、`fchown`、`fchmod 0600`、fsync，重新验证 name-to-inode identity，再
原子 rename 为 `governance.bundle` 并 fsync 目录。

随后只允许以下 argv：

```text
/usr/local/sbin/aetheris-governance-sync \
  --bundle /var/lib/aetheris-governance-sync/incoming/governance.bundle \
  --commit <commit> \
  --sha256 <rebuilt full bundle sha256> \
  [--dry-run]
```

stdin 关闭、`shell=False`、环境固定。Public helper 对旧 helper 的 success 和
error JSON 执行 exact schema 检查后原样 relay；traceback、额外 JSON、额外
字段、错误 commit/hash、非法 receipt 或 backup ref 均不转发。

`finally` 按发布时记录的 device/inode 验证固定 bundle 后 unlink 并 fsync；
下载文件、临时 bare、alternates 和 full bundle 同时清理。
如果名字已被替换，绝不删除替换 inode，而报告 cleanup state unknown。

## Gate 与部署

Gate 继续保留：

```text
sync-public <40hex> dry-run
sync-public <40hex> apply
```

它仍持 root-owned gate lock，且不自行打开 incoming；public helper 负责安全
发布和清理。Gate 以固定 argv 启动 public helper，并验证其 relay 的旧 bundle
helper schema。Legacy upload/chunk/dry-run/apply/cleanup 全部保留。

部署只替换 publisher workflow、public helper 和 gate；旧 bundle helper、
sudoers、tmpfiles 与治理正文不变。安装后验证任意命令拒绝、两种 public
命令、legacy smoke、incoming 最终为空、mirror/receipt/backup 事务语义和
公开 endpoint。

## 测试与完成标准

- Publisher 静态测试覆盖 trigger、contents write、pinned checkout、baseline
  ancestry、baseline no-op 排除规则、增量 bundle、schema 2 和不可覆盖 Release。
- Helper 测试覆盖 metadata URL 注入、duplicate asset/key、类型混淆、大小/
  hash/commit 错配、curl timeout/oversize、symlink/inode replacement。
- Fault/cleanup 测试覆盖 staging 清理、成功/失败 finally、替换 inode保护。
- 重建测试覆盖 109 KiB 级增量、missing prerequisite、恶意 target、完整历史、
  full bundle SHA，以及 ambient Git/temp 输入不能覆盖 alternates 或临时仓。
- Relay 测试覆盖固定 argv、full SHA、关闭 stdin、exact JSON 与错误内容收敛。
- Contract/deploy 测试确认固定端点、固定资源、无凭据和旧工件不变。
- 全套 unittest、governance truth scanner 和 `git diff --check` 通过。
