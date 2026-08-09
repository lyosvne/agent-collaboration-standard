# 固定 GitHub Release 治理同步实施计划

日期：2026-08-09
设计依据：`docs/superpowers/specs/2026-08-09-public-source-governance-sync-design.md`

## 完成标准

- push `master` 与 manual target 都产生相对固定 baseline 的 commit-bound
  增量 bundle 和 schema 2 canonical manifest。
- tag 为 `governance-sync-v2-<commit>`；baseline 固定为
  `bef402ae2c2518961c6abe0d90a1838346e9afb9`，且必须是目标祖先。
- ECS 匿名访问固定 `api.github.com` release/tag 与 asset-ID endpoint。
- Public helper 校验 metadata、schema 2、size、增量 SHA-256 后，以固定 mirror
  objects alternates 离线重建 full bundle，再原子发布固定 incoming bundle。
- Public helper 使用固定 argv 调用旧 bundle helper并在 finally 清理。
- `sync-public` gate、legacy bundle 通道、sudoers、tmpfiles 和治理正文不变。
- publisher、攻击、故障、cleanup、relay、contract/deploy 测试全部通过。

## 阶段一：Publisher workflow

新增 `.github/workflows/governance-release.yml`：

1. 配置 `push.branches = [master]` 和带 required `target_commit` 的
   `workflow_dispatch`。
2. 设置最小 `contents: write`。
3. 使用完整 40-hex SHA pin `actions/checkout`，checkout master、全历史、
   `persist-credentials: false`。
4. push 选择 `github.sha`，manual 选择输入；验证精确小写 commit。
5. 验证 target 是 commit、可达 origin/master，且固定 baseline 是 target 祖先。
6. 将本地 master ref 指向 target；target 等于 baseline 时排除 `target^`，
   否则排除 baseline；创建增量 `governance.bundle` 并 verify。
7. 生成 sorted/compact schema 2 manifest，包含固定 `base_commit`、
   `bundle_kind=incremental`、commit 与增量 bundle name/size/SHA-256。
8. GET release-by-tag；只有 404 才创建。
9. 创建 target-bound `governance-sync-v2-<commit>` draft Release。
10. 只上传并验证 `governance-sync-manifest.json` 与 `governance.bundle`。
11. 只允许一次 draft→published PATCH；发布后验证 `immutable=true` 和锁定后的
    tag ref。禁止修改 tag/target/assets/name，禁止 DELETE、clobber、复用或覆盖。

新增 publisher 静态测试，逐项锁定 trigger、权限、pin、target ancestry、
bundle、manifest、tag、404 create-only 和 asset allowlist。

## 阶段二：Public helper

重写 `runtime/governance-sync/aetheris-governance-sync-public`，保持 CLI：

```text
--commit <40hex> --dry-run
--commit <40hex> --apply
```

### 下载

1. 构造固定 release tag endpoint，不接受 URL 输入。
2. 以 `/usr/bin/curl`、sanitized environment、无 token、无 proxy、
   HTTPS-only、TLS/redirect/connect/total timeout 和 size limits 下载 metadata。
3. JSON duplicate-key rejection。
4. 只提取并验证 `tag_name`、`target_commitish` 和 asset name/id/size。
5. 忽略 metadata URL，自行用 asset ID 构造固定 API URL。
6. 先下载 manifest，验证 schema 2、固定 baseline、incremental kind 与 commit。
7. 校验 manifest size 等于 metadata size。
8. 下载增量 bundle，并校验 metadata size、actual size 和 SHA-256 三者一致。

### Full bundle 重建

1. 在固定 incoming 下创建 helper-owned 临时目录与 bare 仓，不接受路径输入。
2. 验证固定 mirror `.git/objects` owner/group/mode，并写入 bare alternates。
3. 清除 ambient Git 配置和对象目录变量，禁止所有协议，仅开放本地 `file`。
4. verify 增量 bundle，要求 `refs/heads/master` 精确指向请求 target。
5. 只从本地 bundle fetch exact master，检查 commit 与对象连通性。
6. 创建 full bundle，在无 alternates 的空 bare 中 verify，并计算 full SHA-256。

### Incoming 发布

1. 验证 incoming 为 effective UID/GID owned exact `0700` non-symlink 目录。
2. 验证已有固定 bundle（若存在）是同 IDs、`0600` 普通文件。
3. 以 fixed staging name、`O_EXCL|O_NOFOLLOW` 创建 owner-only inode。
4. 复制下载 bundle，fsync，验证 name/inode/owner/group/mode。
5. 原子 rename 到 fixed `governance.bundle`，fsync directory。
6. 记录 published device/inode。

### Existing helper relay

固定调用：

```text
/usr/local/sbin/aetheris-governance-sync
--bundle /var/lib/aetheris-governance-sync/incoming/governance.bundle
--commit <commit>
--sha256 <rebuilt-full-sha256>
[--dry-run]
```

关闭 stdin、`shell=False`、固定环境。只 relay exact dry-run/no-op/applied/error
schema；所有其他 stdout/stderr 收敛为稳定 public helper error。

### Finally cleanup

成功、helper failure、JSON failure 和中断路径都进入 finally。只有固定 bundle
仍对应 published device/inode 时才 unlink 并 fsync；替换 inode 不删除并报告
不确定状态。TemporaryDirectory 自动清理 metadata、manifest、增量 bundle、
临时 bare、alternates 与 full bundle。

## 阶段三：Gate、contract 与 deployment

保留 `sync-public <commit> dry-run|apply` parser、global gate lock 和 fixed argv。
将 public response validator 更新为旧 bundle helper 的 relay schema：

- dry-run 包含 exact commit、SHA-256、before commit、would_change；
- no-op 包含 commit/before/`backup_ref=null`；
- applied 包含 commit、合法 receipt、合法 immutable backup ref；
- error 仅为稳定 code。

更新：

- `runtime/governance-sync/contract.md`
- `runtime/governance-sync/ssh-gate-contract.md`
- `runtime/governance-sync/ssh-gate-deployment.md`
- `runtime/governance-sync/tests/test_contract.py`
- `runtime/governance-sync/tests/test_ssh_gate.py`

契约必须声明固定 API base/tag/assets、metadata 最小信任、self-constructed asset
URL、curl 边界、manifest exact schema、incoming 原子发布/finally cleanup 和
existing helper relay。

部署只安装 public helper 和 changed gate；publisher workflow 随治理仓部署。
明确不改旧 bundle helper、sudoers、tmpfiles、authorized key 与治理正文。

## 阶段四：测试

### Publisher

- 仅 push master/manual target。
- contents write。
- checkout 固定 commit SHA。
- target commit、master reachability 与 baseline ancestry。
- baseline no-op 的 `target^` 排除分支和增量 master bundle verify。
- schema 2 canonical exact manifest。
- tag/target 绑定、404-only create。
- 无 overwrite/delete/clobber。

### Helper 攻击面

- metadata URL/browser URL/file URL 注入被忽略。
- wrong tag/target、missing/duplicate assets。
- bool-as-int、负 ID、oversize。
- duplicate JSON key、extra manifest key。
- wrong commit/name/size/hash。
- curl 非固定 URL、timeout、oversize、ambient token/proxy/config。
- 109 KiB 级增量、missing prerequisite、恶意 target/ref。
- ambient Git/object/config/temp 输入不能覆盖固定 alternates 或临时仓。
- incoming symlink、unsafe mode、staging collision、inode replacement。
- helper traceback、multiple JSON、extra fields、非法 receipt/ref。

### 故障、cleanup 与 relay

- staging copy/publish/fsync fault 清理。
- helper success/failure 后 fixed bundle 均清理。
- replaced bundle inode 不被 unlink。
- fixed helper argv、closed stdin、no shell。
- full bundle 包含 target 完整历史，且 helper 接收重建后的 full SHA。
- dry-run/no-op/applied/error exact relay。
- Gate public 与 legacy command 共享 lock，public gate 本身不打开 incoming。

## 验证命令

```text
python3 -m unittest discover -s runtime/governance-sync/tests -p 'test_*.py'
python3 scripts/check-governance-truth.py
python3 -m unittest scripts/check_governance_truth_test.py
python3 -m py_compile \
  runtime/governance-sync/aetheris-governance-sync-public \
  runtime/governance-sync/aetheris-governance-sync-ssh
git diff --check
```

最终审查：

- `git status --short` 只包含预期文件。
- `git diff` 不含旧 bundle helper、sudoers、tmpfiles 或治理正文变化。
- 不提交、不推送。

## 生产验收

1. 对当前 mirror commit 运行 public dry-run 与 apply no-op。
2. 要求 incoming 最终无 `governance.bundle` 或 `.public-release`。
3. 要求 backup/receipt 数量不变，endpoint commit 不变。
4. 发布最小 canonical master commit 后运行 dry-run/apply。
5. 要求旧 helper 创建 immutable backup、CAS FF、receipt 和 endpoint 收敛。
6. 重复同 commit，要求 no-op 且不新增 backup/receipt。
7. 任意 cleanup state unknown、rollback failed 或 receipt state uncertain 都停止
   自动重试并人工检查。
