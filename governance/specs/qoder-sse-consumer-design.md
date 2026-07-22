# 设计规格：Pi 侧 Qoder Session SSE 消费器

> 签发: Qoder | 状态: 草案（待用户裁定分工后生效实施）| 日期: 2026-07-23
> 依据: docs.qoder.com 官方 API 契约（已逐项核查）+ 架构真值 v1.0（webhook 表述已纠错）
> Review: ZCode（对等互检）| 裁定: 用户

---

## 1. 背景与目标

架构 v1.0 原设计「Qoder --webhook--> Pi」不成立（官方 API 无 Webhook 出站能力，已实证）。
本规格定义替代方案：**Pi 作为调用方，主动调度 Qoder Cloud Agents 并订阅其 Session SSE 流**，
将结果写入 ECS 共享文件，供 ZCode/编队消费。

```
Pi(ECS daemon) --REST--> Qoder Cloud (创建 Session / 发消息)
Pi(ECS daemon) <--SSE---- Qoder Cloud (stream-events, 长连接)
Pi --写--> ECS 共享文件 / Aetheris(真值层) / 飞书通知
```

## 2. 官方 API 契约（已核查，非假设）

| 操作 | 端点 | 说明 |
|------|------|------|
| 验证连通 | `GET /api/v1/cloud/agents` | PAT 校验 + 列 Agents |
| 建环境 | `POST /api/v1/cloud/environments` | 新账号无预置环境，必须先建；body: `{"name","config":{"type":"cloud","networking":{"type":"unrestricted"}}}` |
| 建 Agent | `POST /api/v1/cloud/agents` | body: name/model(如 "ultimate")/system/tools(`agent_toolset_20260401` + enabled_tools) |
| 建 Session | `POST /api/v1/cloud/sessions` | body: `{"agent": <agent_id>, "environment_id": <env_id>}` → 返回 `sess_*`，status=idle |
| 发消息 | Session send（user.message） | 触发任务执行 |
| **订阅事件** | `GET /api/v1/cloud/sessions/{id}/events/stream` | SSE；`Accept: text/event-stream`；可选 `event_deltas[]=agent.message/agent.thinking` |
| 轮询降级 | `GET .../events`（list-events） | SSE 断连时的降级路径 |

认证：所有请求 `Authorization: Bearer $QODER_PAT`。

## 3. SSE 事件模型（官方格式）

- **缓冲事件**（入历史，带 `id:` 游标）：`user.message` / `agent.message` / `session.status_idle`（含 `stop_reason`）等
- **增量帧**（不入历史）：`event_start` → N × `event_delta`（共享同一 event ID）→ 最终缓冲 `agent.message`
- 心跳：服务器周期发 `: heartbeat` 注释行
- **终态判定**：收到 `session.status_idle` 且 `stop_reason.type == "end_turn"` 即任务回合完成

## 4. 消费器设计（Pi Extension: `pi-qoder-dispatch`）

### 4.1 组件

```
pi-qoder-dispatch (TypeScript, Pi Extension)
├── QoderClient        REST 封装（PAT 注入、分页、错误包络解析）
├── SessionRunner      任务生命周期：ensureEnv → ensureAgent → createSession → send → consume
├── SseConsumer        SSE 长连接 + Last-Event-ID 重连 + 降级轮询
├── ResultSink         结果落盘（共享文件）+ 回写 Aetheris + 飞书通知（经 pi-feishu 桥）
└── registerTool: qoder_dispatch / qoder_status / qoder_cancel
```

### 4.2 SSE 重连策略（按官方语义）

1. 记录最近缓冲事件的 SSE `id:` 作为游标
2. 断连 → 指数退避重连（1s/2s/4s…上限 30s），带 `Last-Event-ID`
3. 重连语义（官方）：
   - 游标在 `event_start` 之前 → 重放保留的 start + 历史 delta
   - 游标 == 进行中事件 ID → 跳过历史 delta，只收后续
   - 生成已完成 → 收到最终缓冲 `agent.message`（不重放 delta）
4. 连续 N 次（默认 5）重连失败 → 降级 list-events 轮询（间隔 10s），恢复后切回 SSE
5. 400（游标指向已归档事件）→ 丢弃游标全量拉取 list-events 重建状态

### 4.3 结果落盘约定

```
ECS: /opt/pi/outbox/qoder/<session_id>/
├── task.json        # 任务元数据（发起者、目标、时间、agent/env id）
├── transcript.md    # agent.message 聚合（人类可读）
├── events.jsonl     # 原始缓冲事件（审计）
└── result.json      # 终态：stop_reason / 摘要 / 产物引用
```

关键状态变迁（session 创建/完成/失败）回写 Aetheris（真值层）；完成/失败经 pi-feishu 发飞书卡片。

### 4.4 密钥管理（对齐 T1/T2/T3 分级）

- `QODER_PAT` 属 **T2 常规操作凭证**：一次性配置进 ECS 上 Pi 的环境（systemd EnvironmentFile 或 agent vault），带 TTL 轮换提醒
- 绝不写入 git / 共享文件 / 日志；QoderClient 日志脱敏 `Bearer ***`
- PAT 失效（401 authentication_error）→ 飞书告警用户轮换，任务挂起不重试

### 4.5 错误处理（官方错误包络）

| HTTP | type | 处置 |
|------|------|------|
| 400 | invalid_request_error | 修正参数；游标失效走 4.2-5 |
| 401 | authentication_error | 挂起 + 飞书告警（PAT 轮换） |
| 404 | not_found_error | Session 不存在 → 标记任务失败，回写 Aetheris |
| 5xx/网络 | — | 指数退避；超限降级轮询 |

## 5. 验收标准

1. E2E：Pi 发起一个 Qoder Session（如"列出仓库文件树"）→ SSE 全程消费 → `result.json` 落盘 → 飞书收到完成卡片
2. 断连注入：消费中 kill 连接 → 自动重连且 transcript 无缺失/无重复
3. 降级注入：模拟 SSE 持续失败 → 切轮询 → 任务仍完成
4. 密钥审计：日志/落盘文件中 grep 不到 PAT 明文
5. ZCode 对等互检：mtime + git diff 确认无越界写入

## 6. 依赖与前置

- 前置：用户裁定分工（本规格实施权）；ECS 上 Pi daemon 就绪（ZCode 的部署验证任务）
- 依赖：`QODER_PAT`（用户在 Qoder 控制台创建后按 T2 注入）；账号首次需 `POST /environments`
- 不依赖：Webhook（不存在）、Qoder 侧任何改造
