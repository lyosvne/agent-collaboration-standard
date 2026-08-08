# 架构规格：Pi Dispatch Context Server

> 历史起草: ZCode | 当前 owner: Mira（治理）+ Trae（集成验证）| 裁定: 用户 | 更新: 2026-08-08
> 状态: 草案（架构真值反推，待 ECS 实测补完字段后转 active）
> 依据: `archive/dispatch-server-patches/*.py`（5 个 patch 头部说明）+ `archive/ecs-scripts/README.md`（systemd unit + crontab 实证）+ `pi-drift-governance-spec.md §10`（B 层实施状态）
> 缺口来源: `global-roadmap-v1.1.md` L246「dispatch-server 架构 spec 缺失（生产组件无文档/无职能归属）」
> 变更前置: 改本文件 → 走 `governance-review-process.md §四` pre-commit 三方评审（spec 属真值层）
> 源码恢复: 2026-08-08 将生产 `dispatch-server.py` 按 SHA-256 原样回收到
> `runtime/dispatch-server/dispatch-server.py`；systemd 脱敏模板、endpoint
> contract 和兼容测试位于同目录。后续功能修改必须
> 基于该 canonical source，不再以历史 patch 或生产单份文件为基线。

---

## 1. 为什么存在（职能归属）

**问题**：编队是多 agent / 多机 / 跨会话的（Pi ECS + Trae/Qoder/Kimi Mac 环境 + ZCode 非终端 App + Mira 云端）。每个 agent 启动时都需要同一份"编队上下文"（北极星 / 架构 / 分工 / 启动头 + 治理文档时序版本 + 漂移体检结果）。若各自从 GitHub fetch，有三个缺口：
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
│    EnvironmentFile=/opt/pi-orchestrator/config/dispatch.env  │
│    Restart=always RestartSec=5                               │
│                                                              │
│  dispatch-server.py (Python stdlib http.server)              │
│    LISTEN 127.0.0.1:8765  ← 仅 bind localhost，不暴露公网    │
│         │                                                    │
│         │ Caddy 反代 /dispatch/* → 127.0.0.1:8765            │
│         ▼                                                    │
│  公网: https://aetherisonline.xyz/dispatch/*                 │
│       （Caddy 负责 TLS/反代；handler 负责端点鉴权）           │
└─────────────────────────────────────────────────────────────┘
```

**网络绑定**：dispatch-server 仅 bind `127.0.0.1`，公网访问经 Caddy
反代。handler 使用 header key 对运行数据和写入端点做 fail-closed 鉴权。
Caddy 配置未在本次回收，不能据此断言其是否另有鉴权、限流或日志策略。
环境变量由专用 `EnvironmentFile` 注入，unit 本身不内联值。

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
| `/dispatch/roadmap` | GET | 公开 | 全局路线图正文 | 当前兼容实现；manifest-aware 修复见后续 PR |

**双源 fallback 语义**：governance-mirror（ECS 本地 git clone）优先；失败则 fallback 到 GitHub raw。这保证 GitHub 网络异常时云端 agent 仍能拿到上下文（本机运行经验印证此必要性）。

### 3.2 时序版本端点（公开，B 层，2026-07-27）

| 端点 | 方法 | 鉴权 | 返回 |
|------|------|------|------|
| `/dispatch/truth/versions` | GET | 公开（敏感度低）| 治理文档版本清单 |

**返回字段**（round2 修复后契约，patch apply-b-layer-fix-20260727.py）：
```json
{
  "time": "<ISO8601>",
  "github_raw_base": "<public source base>",
  "manifest_status": "ok|commit-missing|missing|unavailable|malformed|invalid",
  "degraded": false,
  "documents": {
    "<doc-key>": {
      "filename": "<stable filename>",
      "version": "<filename-derived compatibility version>",
      "logical_version": "<manifest logical version>",
      "filename_version": "<stable filename version>",
      "version_source": "manifest|filename|unversioned",
      "versioned": true,
      "degraded": false,
      "degraded_reasons": [],
      "missing": false,
      "commit_sha": "<mirror HEAD>",
      "content_sha12": "<sha256 prefix>",
      "mtime": "<last Git commit time for this file at mirror HEAD>",
      "source": "mirror|github|missing"
    }
  }
}
```

**用途**：消费方（本机 ZCode / 云端 agent）比对本地版本与 ECS 版本，检测"文档已变但本地没拉"的漂移。`logical_version`、正文指纹和文件最后提交时间均从一次捕获的 mirror HEAD Git 对象读取；旧 `version` 和 `filename_version` 保留稳定文件名兼容语义。manifest、Git 对象或 fallback 正文源异常时端点显式返回 `degraded`，不把文件名版本伪装为逻辑版本。工作树即使存在未提交修改也不会混入同一响应。

### 3.3 漂移体检端点（AUTH_KEY 鉴权，B 层 round3，2026-07-27）

| 端点 | 方法 | 鉴权 | 返回 |
|------|------|------|------|
| `/dispatch/drift` | GET | `X-Dispatch-Key` 或 Bearer；缺失/错误 → 403，key 未配置 → 503 | `logs/drift-latest.json` 内容 |

**fail-closed 语义**（round2 修复）：`drift-latest.json` 缺失 / malformed → 返回 502（不返回空 200，防消费方误判"无漂移"）。

**鉴权原因**：漂移报告包含内部分支状态。query string key 会进入 access log
和浏览器历史，因此 canonical contract 只允许 header key。

### 3.4 历史追加端点（AUTH_KEY 鉴权，先于 B 层存在）

| 端点 | 方法 | 鉴权 | 用途 |
|------|------|------|------|
| `/dispatch/history/<agent>` | POST | header key | agent 上报执行历史 |

请求体必须是 JSON object。支持 `caller`、`task`、`status`、`session_id`、
`duration` 和 `result`；未知 agent 返回 404，空体或非法 JSON 返回 400。

---

## 4. 鉴权模型

```
公开治理正文:
  /dispatch/north-star
  /dispatch/architecture
  /dispatch/fleet-division
  /dispatch/start-here
  /dispatch/roadmap
  /dispatch/truth/versions

Header key（X-Dispatch-Key 或 Authorization: Bearer）:
  /dispatch/all
  /dispatch/context
  /dispatch/fleet
  /dispatch/survey
  /dispatch/history/<agent>
  /dispatch/models
  /dispatch/health
  /dispatch/drift
  POST /dispatch/history/<agent>
```

**AUTH_KEY 来源**：`/opt/pi-orchestrator/config/dispatch.env` 的
`DISPATCH_KEY`（systemd EnvironmentFile 注入）。**红线**：DISPATCH_KEY
明文不进任何 git 文件、日志或 commit。

**应用鉴权判定位置**：dispatch-server.py handler。`DISPATCH_KEY` 缺失时受保护
端点返回 503；query string key 被拒绝。Caddy 是否有附加控制待独立取证。

---

## 5. 消费者契约（谁调什么）

| 消费者 | 调用端点 | 注入位置 |
|--------|----------|----------|
| `qoder-bridge.py` | `/dispatch/{north-star,architecture,fleet-division,start-here}` | 启动头注入（FLEET_HEADER：红线 + 编队身份 + WebFetch 指引）|
| `qoder-bridge.py`（cantus 档） | 同上 | C 评审实测：cantus 能复述红线 5 条 + 北极星 + 路线图 |
| Pi ECS / governance mirror | `/dispatch/truth/versions` | 当前发布 mirror commit、内容 hash、manifest 逻辑版本、文件名兼容版本和 degraded 状态 |
| Trae（授权诊断） | `/dispatch/drift` | 集成或部署验证时调用（需授权，不输出 key）|

**待扩展消费方**：Trae、Kimi、ZCode、Mira 应按各自能力读取公开治理端点；需要鉴权的运行诊断只能由获授权的执行角色调用。ZCode 只消费结果，不运行 curl。

---

## 6. 变更前置（红线）

改 dispatch-server.py / Caddy 配置 / systemd unit / 端点路由 / 鉴权逻辑 → **必须走 `governance-review-process.md §四` pre-commit 三方评审**（§8.4 第 4 类）。

**已发生的违规教训**（roadmap v1.9 版本历史）：2026-07-27 B 层首批改动未走评审直接改 ECS + push + 重启，事后补审 A/B/C 全 CONDITIONAL 共识 4 阻断。**这是反面案例，不许复现**。

**部署规范**：后续改动基于 `runtime/dispatch-server/dispatch-server.py`，
通过 PR/CI 和后续 G3 受限部署 helper 发布。G3 尚未合并前，本目录不提供
生产 apply/rollback 工具；历史 patch 仅保留作证据，不再作为源码基线。

---

## 7. 待补完（本 spec 的已知缺口）

源码与 systemd unit 已完成生产取证。仍需单独确认：

1. Caddy 精确路由、access-log 脱敏和 rate limit；
2. production environment 的变量存在性，但不得读取或记录变量值；

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
| v0.3（manifest）| 2026-08-08 | `/truth/versions` 从 mirror HEAD manifest 读取逻辑版本，保留文件名兼容字段并显式报告 degraded |
| v0.2（恢复）| 2026-08-08 | 回收 canonical source；修正真实端点结构、header 鉴权、systemd/Caddy 边界和运行数据分级 |
| v0.1（草案）| 2026-07-28 | ZCode 反推起草（patch + ecs-scripts/README + roadmap）；闭合 roadmap 缺口 #6「dispatch-server 架构 spec 缺失」。待 ECS 实测补完 §7 五项后转 active |
