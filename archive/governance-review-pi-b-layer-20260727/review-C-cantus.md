# 评审方 C（cantus via Qoder）— Pi 治理纳入 B 层事后补审

> 评审日期: 2026-07-27
> 评审对象: commit bac6e95

## 评审结论：CONDITIONAL

可通过，但须记录 1 项过程纪律条件 + 2 项消费者契约补丁（非回滚级）。无技术性阻断（端点能跑、幂等可靠、安全边界在内网模型下成立）。

## 阻断项

**无技术性阻断。** 改动可保留上线。

## 逐条判断

### 1. 端点设计 — CONDITIONAL（契约缺口，非阻断）

消费者能用 `version` 字符串比对，逻辑闭环。但：
- 缺 commit hash / content hash。`source: mirror` 只告诉消费者"镜像有这份文件"，但镜像落后于 github 时，消费者会误判"已对齐"
- `github_raw_base` 在响应里给了，但没给当前 mirror 的 commit SHA 或拉取时间戳。`time` 字段是请求处理时间，不是 mirror 同步时间

消费者侧推荐用法：不能仅凭 `/truth/versions` 判定"我绝对对齐了"，只能判定"版本号对齐"。要绝对对齐需结合本机 `git log -1` 的 SHA 与 mirror 同步点 SHA——后者端点没给。

### 2. 版本解析正则 — PASS（边界实测，但有一个语义陷阱）

Node REPL 验证：
- `v1.0`/`v1.2`/`v1.11`/`v2.0` → 全部 MATCH ✅
- `START_HERE.md` → no match → `version=null` ✅
- `v1.md`（缺 minor）→ no match
- `v1.2.3.md`（semver 三段）→ no match ⚠️
- `v1.20.md` → MATCH，version="1.20" ⚠️

两个真实风险（软观察级）：
- **版本号字符串比较陷阱**：`"1.10" < "1.2"`（字典序）会误判。spec 应明示"version 用 split+int 比较而非字符串比较"
- **semver 三段不匹配**：建议正则放宽为 `-v(\d+\.\d+(?:\.\d+)?)\.md$`
- START_HERE.md `version=null` 的消费者处理：spec/docstring 应明确"null = 非时序版本文件，跳过版本校验"

### 3. drift 透传 — CONDITIONAL（fail-open 隐患，经典教训级）

这正是 review-process-lessons.md §6.4 反复强调的 fail-open 模式，本端点踩中了：
- 文件不存在 → `read_file(DRIFT_LATEST, "{}")` 返回 `"{}"` → `_send_text("{}", 200)` → 消费者收到 HTTP 200 + 空 JSON
- 消费者无法区分三种状态：(a) drift 系统正常、当前无任何漂移；(b) drift-cron 挂了；(c) 文件路径配错
- drift-latest.json 真实结构顶层有 `timestamp`，所以正常无漂移时也应是 `{"timestamp": "...", "branches": [...]}` 而非 `{}`。`{}` 几乎一定意味着异常

修法（建议）：
- 方案 A（fail-closed）：文件不存在时返回 HTTP 503 + `{"error": "drift-latest.json missing"}`
- 方案 B（保留 200 但加 health）：响应 header 加 `X-Drift-Report-Age-Seconds`

### 4. 幂等性 — PASS

`MARKER = "DRIFT_LATEST = os.environ.get"` 选得好：新增常量行，应用前必然不存在，应用后必然存在。四处替换每处都做了 `src.count(anchor) != 1` 断言，fail-closed。`compile(src, ..., "exec")` 语法检查在 write 前。备份命名 `.bak-b-layer-{ts}` 秒级唯一。

### 5. 404 字符串 — PASS（轻微渲染观察）

24 空格缩进是手工对齐"可用:"后的列，若将来再加端点，对齐会乱。建议改为无缩进的换行列表。

### 6. 安全 — PASS（在内网模型下，附升级路径警示）

drift-latest.json 含 `branches[].branch`（分支名）、`ahead/behind`（开发活跃度侧信道）、`conflicts`（冲突文件路径）。这些是操作元数据，无密钥、无 PII、无源码内容。分支名/版本号本身已是公开仓库信息。

关键前置条件（未在材料包实证）：材料包没给 dispatch-server 的 bind 地址（是否 `0.0.0.0`）和 Caddyfile 的 dispatch 路由是否加 auth。

- 若 dispatch-server 仅 `127.0.0.1` + Caddy 反代且 Caddy 加 auth → PASS
- 若 dispatch-server 直接 `0.0.0.0:port` 公网无 auth → CONDITIONAL

本次改动未引入新的暴露风险等级（同池）。材料包应补一句"dispatch-server bind + Caddy auth 状态"以闭合安全论证。

### 7. C 层收窄 — CONDITIONAL（90% 无实证，收窄本身合理但数字需校正）

§3 要求的功能矩阵逐项核对 shell cron 覆盖度：
| §3 要求 | shell cron 覆盖 |
|---|---|
| fetch（不改工作区）| ✅ drift-cron.sh |
| ahead/behind/dirty 计数 | ✅ drift-check.sh |
| branch_vs_master | ✅ |
| 分级 OK/NOTICE/WARN/CRITICAL | ✅ |
| 飞书卡片 | ✅ pi-feishu |
| drift-latest.json 落盘 | ✅ |

**cron 确实覆盖了 §3 漂移体检的全部功能**。所以"90%"其实是保守说法——对 §3 而言是 ~100%。

但 cron 没覆盖的：(a) systemd 托管；(b) pi-drift-guard 作为 Pi Extension 的 `registerTool` 集成；(c) drift-check.sh 退役分支修复。

"90%"是个未量化口号。真实分解：对 §3 ≈100%，对整个 C 层（含 systemd/Extension 集成）≈60-70%。

应改为分项说明（"§3 体检 100% 由 cron 覆盖；C 层剩余 = drift-check 退役分支修复 + systemd 托管 + 可选 TS Extension"），删除无实证的"90%"硬数字。

### 8. 过程纪律 — CONDITIONAL（接受补审，但必须记录违规）

违规事实明确：pre-commit 三方评审未走。

本次改动低风险（2 个 GET 只读端点 + 幂等 patch + 备份 + 回滚方案齐备 + 实证证据完整），不涉及密钥/写操作/master 分支。按 review-process-lessons.md §四.建议2 分类，本次违规属"流程违规"而非"技术阻断"，**不触发回滚**。

补审质量高：diff 真实、锚点断言 fail-closed、备份+回滚方案具体、ECS 实证有时间戳。

但：lessons.md §七明说"本文件作为活文档，后续每次评审后追加新教训"。本次违规必须在 review-process-lessons.md 追加一节，记录：(a) 违规情形；(b) 为何可接受；(c) 防复发措施。

## 软观察（按优先级）

1. **【必须，作为 CONDITIONAL 放行条件】** 在 review-process-lessons.md 追加一节记录本次事后补审违规
2. **【必须，作为 CONDITIONAL 放行条件】** 在 spec §10 或 `/dispatch/drift` docstring 写明消费者契约：`{}` = 数据缺失而非零漂移
3. **【建议】** `/dispatch/truth/versions` 响应补 `mirror_commit_sha` 或 `mirror_last_sync`
4. **【建议】** spec §10 / roadmap 把"shell cron 覆盖 90%"改为分项覆盖度说明，删除无实证"90%"硬数字
5. **【建议】** 版本正则放宽为 `-v(\d+\.\d+(?:\.\d+)?)\.md$`
6. **【建议】** 材料包补 dispatch-server bind 地址 + Caddy auth 状态
7. **【建议】** 404 帮助串改无缩进换行列表
8. **【建议】** dispatch-server.py 不在 git 仓库的现状登记为独立任务

**评审风格说明**：保持我（cantus）一贯的"实现细节 vs 真阻断"分类——本次无真阻断，CONDITIONAL 的两条放行条件都是文档/契约级，不要求代码回滚或重走流程。
