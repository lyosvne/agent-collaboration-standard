# 架构规格：Pi Dispatch Context Server

> 签发: ZCode（出规格）| Review: 待对等互检 | 裁定: 用户 | 日期: 2026-07-28
> 状态: 草案（架构真值反推，待 ECS 实测补完字段后转 active）
> 依据: `archive/dispatch-server-patches/*.py`（5 个 patch 头部说明）+ `archive/ecs-scripts/README.md`（systemd unit + crontab 实证）+ `pi-drift-governance-spec.md §10`（B 层实施状态）
> 缺口来源: `global-roadmap-v1.1.md` L246「dispatch-server 架构 spec 缺失（生产组件无文档/无职能归属）」
> 变更前置: 改本文件 → 走 `governance-review-process.md §四` pre-commit 三方评审（spec 属真值层）

---

## 1. 为什么存在（职能归属）

**问题**：编队是多 agent / 多机 / 跨会话的（ZCode 本机 + Qoder/Kimi/Mira 云端 + Pi ECS）。每个 agent 启动时都需要同一份"编队上下文"（北极星 / 架构 / 分工 / 启动头 + 治理文档时序版本 + 漂移体检结果）。若各自从 GitHub fetch，有三个缺口：
- GitHub 网络不稳定（本机实测 `AGENTS.md`「本机运行经验」记录的 DNS 污染路径）
- 没有"时序版本"概念——文档改了但消费方不知道改了什么、何时改的
- 漂移体检结果是 ECS cron 产物，本机 agent 无法直接读

**dispatch-server 的职能**：**编队共享上下文的单一 HTTP 投递点**。把治理真值 + 时序版本 + 漂移结果统一从 ECS 暴露，让任何 agent（含 qoder-bridge.py 启动的云端 agent）用一次 HTTP 调用拿到完整启动上下文。

**红线归属**：dispatch-server 是**生产组件**（systemd 托管 + 公网经 Caddy 暴露），属 O1 基座。改它 = 改真值投递链 = 触发 `governance-review-process.md §8.4` 第 4 类 pre-commit 强制评审。

---

## 2. 部署拓扑（实证来源 ecs-scripts/README.md）

```
┌─────────────────────────────────────────────────────────────┐
│  ECS (aetherisonline.xyz)                                    │
│                                                              │
│  systemd: pi-dispatch-server.service                         │
│    ExecStart=/usr/bin/python3                                │
│      /opt/pi-orchestrator/extensions/dispatch-server.py      │
│    EnvironmentFile=/opt/pi-orchestrator/.env                 │
│    Environment=DISPATCH_DIR=/opt/pi/dispatch                 │
│    Environment=DISPATCH_PORT=8765                            │
│    Restart=always RestartSec=5                               │
│                                                              │
│  dispatch-server.py (Python stdlib http.server)              │
│    LISTEN 127.0.0.1:8765  ← 仅 bind localhost，不暴露公网    │
│         │                                                    │
│         │ Caddy 反代 /dispatch/* → 127.0.0.1:8765            │
│         ▼                                                    │
│  公网: https://aetherisonline.xyz/dispatch/*                 │
│       （Caddy 配置控制公网可达性 + 部分端点 AUTH_KEY）       │
└─────────────────────────────────────────────────────────────┘
```

**网络绑定（安全闭环，评审 B/C 共识）**：dispatch-server 仅 bind `127.0.0.1`，公网访问全部经 Caddy 反代，Caddy 层做路由 + AUTH_KEY 鉴权。这闭环了"公网无 auth 可达治理数据"的安全疑虑。

**配套 ECS 脚本**（cron 触发，写文件供 dispatch-server 读取）：

| 脚本 | cron | 产出文件 | dispatch 端点消费 |
|------|------|----------|-------------------|
| `drift-cron.sh` | `*/30 * * * *` | `logs/drift-latest.json` | `/dispatch/drift` |
| `governance-sync.sh` | `0 * * * *` | git pull governance-mirror | `/dispatch/{north-star,architecture,fleet-division,start-here}` |
| `model-tracker.sh` | `0 10 * * *` | Qoder Cloud 模型清单 | （未透出，本地用）|

---

## 3. 端点契约（实证来源 5 个 patch 头部说明 + roadmap L241-245）

### 3.1 治理文档透出端点（公开，第 1 批，2026-07-26）

| 端点 | 方法 | 鉴权 | 返回 | 数据源 |
|------|------|------|------|--------|
| `/dispatch/north-star` | GET | 公开 | 北极星 v1.2 正文 | governance-mirror 优先 + GitHub raw 兜底 |
| `/dispatch/architecture` | GET | 公开 | 架构真值 v1.0 正文 | 同上双源 fallback |
| `/dispatch/fleet-division` | GET | 公开 | 编队分工 v1.1 正文 | 同上 |
| `/dispatch/start-here` | GET | 公开 | START_HERE.md 正文 | 同上 |

**双源 fallback 语义**：governance-mirror（ECS 本地 git clone）优先；失败则 fallback 到 GitHub raw。这保证 GitHub 网络异常时云端 agent 仍能拿到上下文（本机运行经验印证此必要性）。

### 3.2 时序版本端点（公开，B 层，2026-07-27）

| 端点 | 方法 | 鉴权 | 返回 |
|------|------|------|------|
| `/dispatch/truth/versions` | GET | 公开（敏感度低）| 治理文档版本清单 |

**返回字段**（round2 修复后契约，patch apply-b-layer-fix-20260727.py）：
```json
{
  "<doc-key>": {
    "commit_sha": "<git commit hash>",
    "content_sha12": "<文件内容 sha256 前 12 位>",
    "mtime": "<ISO8601>",
    "versioned": true
  }
}
```

**用途**：消费方（本机 ZCode / 云端 agent）比对本地版本与 ECS 版本，检测"文档已变但本地没拉"的漂移。`content_sha12` 区分"commit 没动但文件被改"（如 ECS 本地误编辑）。

### 3.3 漂移体检端点（AUTH_KEY 鉴权，B 层 round3，2026-07-27）

| 端点 | 方法 | 鉴权 | 返回 |
|------|------|------|------|
| `/dispatch/drift` | GET | **AUTH_KEY**（query param `?key=$DISPATCH_KEY`，缺失/错误 → 403）| `logs/drift-latest.json` 内容 |

**fail-closed 语义**（round2 修复）：`drift-latest.json` 缺失 / malformed → 返回 502（不返回空 200，防消费方误判"无漂移"）。

**鉴权原因**（A round2 阻断）：公网 `https://aetherisonline.xyz/dispatch/drift` 经 Caddy 反代无 auth 可达，会暴露编队内部分支漂移细节（分支名/ahead-behind 数）。加 `?key=` 后公网无 key → 403。

### 3.4 历史追加端点（AUTH_KEY 鉴权，先于 B 层存在）

| 端点 | 方法 | 鉴权 | 用途 |
|------|------|------|------|
| `/dispatch/append-history` | POST | AUTH_KEY | agent 上报执行历史（manual-history-overrides 的对称面）|

> ⚠️ **待补完**：本端点先于 B 层存在（apply-b-layer-auth patch 复用它的 auth 模式），但完整契约（字段/消费者/与 manual-overrides 的关系）本 spec 未覆盖——**待 ECS 实测或读到 dispatch-server.py 源码后补 §3.4 字段表**。

---

## 4. 鉴权模型

```
公开（无 key）:
  /dispatch/north-star
  /dispatch/architecture
  /dispatch/fleet-division
  /dispatch/start-here
  /dispatch/truth/versions     ← 敏感度低（版本号非正文）

AUTH_KEY（?key=$DISPATCH_KEY，403 失败）:
  /dispatch/drift              ← 含分支漂移细节
  /dispatch/append-history     ← 写入面，必须鉴权
```

**AUTH_KEY 来源**：`/opt/pi-orchestrator/.env` 的 `DISPATCH_KEY`（systemd EnvironmentFile 注入）。**红线**：DISPATCH_KEY 明文不进任何 git 文件 / 日志 / commit（AGENTS.md 红线）。

**鉴权判定位置**：dispatch-server.py handler 内（query param 校验），非 Caddy 层。Caddy 只做反代 + 路由，不做鉴权——**这是设计边界，若未来要在 Caddy 层加鉴权需重走评审**。

---

## 5. 消费者契约（谁调什么）

| 消费者 | 调用端点 | 注入位置 |
|--------|----------|----------|
| `qoder-bridge.py` | `/dispatch/{north-star,architecture,fleet-division,start-here}` | 启动头注入（FLEET_HEADER：红线 + 编队身份 + WebFetch 指引）|
| `qoder-bridge.py`（cantus 档） | 同上 | C 评审实测：cantus 能复述红线 5 条 + 北极星 + 路线图 |
| ZCode 本机（漂移治理 hook） | `/dispatch/truth/versions` | chain-gate / tiers-drift-gate 比对本地版本 |
| ZCode 本机（漂移诊断） | `/dispatch/drift` | 手动诊断时 curl（需 DISPATCH_KEY）|

**未消费方**：Kimi / Trae SOLO / Mira 目前不经 dispatch-server（各自调度链），是覆盖缺口。

---

## 6. 变更前置（红线）

改 dispatch-server.py / Caddy 配置 / systemd unit / 端点路由 / 鉴权逻辑 → **必须走 `governance-review-process.md §四` pre-commit 三方评审**（§8.4 第 4 类）。

**已发生的违规教训**（roadmap v1.9 版本历史）：2026-07-27 B 层首批改动未走评审直接改 ECS + push + 重启，事后补审 A/B/C 全 CONDITIONAL 共识 4 阻断。**这是反面案例，不许复现**。

**patch 规范**（已建立的实践）：
- 每个 ECS 改动写一个 `apply-*.py` patch 脚本，归档 `archive/dispatch-server-patches/`
- patch 必须幂等（哨兵字符串检测，已应用则跳过）
- patch 必须先备份（`.bak-<patch-name>-<timestamp>`）
- patch 头部 docstring 写明：改什么 / 前置依赖 / 幂等标记 / 对应评审阻断

---

## 7. 待补完（本 spec 的已知缺口）

本 spec 是**从 patch + ecs-scripts/README + roadmap 反推**的架构真值，非源码直读。以下字段待读到 dispatch-server.py 源码或 ECS 实测后补完：

1. **§3.4 `/dispatch/append-history` 完整字段表**（请求体 schema / 消费者 / 与 manual-history-overrides 关系）
2. **§3.1-3.3 的精确 Content-Type / 缓存头 / 错误响应 body schema**
3. **Caddy 配置真值**（反代规则 / 是否有 rate limit / TLS）
4. **DISPATCH_DIR 目录结构**（治理文档 mirror 的实际路径布局）
5. **健康检查端点**（如有 `/health` 或 `/dispatch/health`，本 spec 未覆盖）

补完方式：下次 ECS 操作时 `cat /opt/pi-orchestrator/extensions/dispatch-server.py` + `cat /etc/caddy/Caddyfile`（或对应路径），回填本 spec。

---

## 8. 与其他 spec 的关系

| 关联 spec | 关系 |
|-----------|------|
| `pi-drift-governance-spec.md` | drift 端点的上游（drift-cron.sh 产出 → dispatch-server 透出）|
| `governance-review-process.md §8.4` | 本组件变更的前置评审触发条款 |
| `qoder-sse-consumer-design.md` | qoder-bridge.py 消费 dispatch 端点的下游契约 |
| `node2-review-retrospective-20260726.md §三` | 第 1 批 4 端点的评审实证来源 |

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1（草案）| 2026-07-28 | ZCode 反推起草（patch + ecs-scripts/README + roadmap）；闭合 roadmap 缺口 #6「dispatch-server 架构 spec 缺失」。待 ECS 实测补完 §7 五项后转 active |
