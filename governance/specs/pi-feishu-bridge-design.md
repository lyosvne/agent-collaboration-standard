# 设计规格：飞书 pi-feishu 桥接（移动端统一入口）

> 签发: Qoder | 状态: 草案（待用户裁定分工后生效实施）| 日期: 2026-07-23
> 依据: 架构真值 v1.0 §三/§4.5/§七 + 本机 lark-* skills 实证能力
> Review: ZCode（对等互检）| 裁定: 用户

---

## 1. 目标

实现架构 v1.0 裁定的移动端统一入口：**飞书移动端 → Pi(ECS) → 编队**。
用户在飞书下命令/收通知/点审批，不依赖任何 PC 开机。

```
用户(飞书移动端)
  │ ①指令消息 / ③审批点击
  ▼
飞书开放平台 ←──② Interactive Card（通知/审批卡片）── Pi Extension: pi-feishu
  │ 事件长连接(WebSocket)                                    ▲
  ▼                                                          │
pi-feishu 桥接层（跑在 ECS 上的 Pi daemon 内）────────────────┘
  │ 解析意图 → Pi orchestrator 路由
  ▼
Qoder(SSE 消费器) / Kimi(subprocess) / Mira(类Kimi)
```

## 2. 能力基座（本机已实证持有）

| 能力 | 来源 | 用途 |
|------|------|------|
| 收发消息/群管理 | lark-im skill | 指令接收、结果通知 |
| 交互卡片 card-2.0-schema | lark-im | 排版决策通知、任务状态卡 |
| 卡片按钮回调 `card.action.trigger` | lark-im 卡片回调 | **快速审批按钮**（批准/拒绝） |
| 原生审批流 | lark-approval skill | 重量级审批（如计费、破坏性操作） |
| 实时事件流 NDJSON | lark-event skill（`lark-cli event consume`） | 长连接监听消息/卡片回调，为 subprocess 设计 |
| 通讯录解析 | lark-contact | 指令发起人身份校验 |

结论：**飞书侧能力零缺口**，工作量集中在 Pi Extension 桥接层。

## 3. 桥接层设计（Pi Extension: `pi-feishu`）

### 3.1 组件

```
pi-feishu (TypeScript, Pi Extension)
├── EventListener     子进程托管 lark-cli event consume（NDJSON 流）
│                     监听: im.message.receive_v1 / card.action.trigger
├── CommandRouter     指令解析：@Pi <自然语言> → Pi orchestrator 任务路由
├── CardFactory       卡片模板：任务状态卡 / 审批卡 / 漂移报告卡 / 告警卡
├── ApprovalGate      审批门：T3 动作 → 发审批卡 → 等 card.action.trigger 回调
│                     超时（默认 30min）自动拒绝，回执结果
└── IdentityGuard     只接受用户（林于炜）open_id 的指令与审批点击，其余拒绝并告警
```

### 3.2 四类卡片（对齐 v1.0 §七 交互层设计）

| 卡片 | 触发 | 内容 | 按钮 |
|------|------|------|------|
| 任务状态卡 | 任务创建/完成/失败 | 任务名、执行 agent、耗时、结果摘要、Aetheris 详情链接 | 查看详情 |
| **审批卡** | T3 动作（计费/部署/删除/push master 类） | 动作描述、风险等级、发起 agent、影响范围 | **批准 / 拒绝** |
| 漂移报告卡 | 漂移治理 cron（15-30min） | 各 clone/分支漂移摘要，仅异常时发 | 查看全量报告 |
| 告警卡 | 严重漂移(>10 commits)/PAT失效/daemon异常 | 告警级别、根因、建议动作 | 确认已读 |

### 3.3 审批闭环（核心链路）

```
Pi 内任意组件请求 T3 动作
  → ApprovalGate.request({action, risk, agent, scope})
  → CardFactory 生成审批卡 → lark-im 发给用户
  → 用户移动端点击【批准/拒绝】
  → card.action.trigger 回调 → EventListener 捕获
  → IdentityGuard 校验 open_id → ApprovalGate resolve
  → 批准: 放行动作 + 审计记录写 Aetheris
  → 拒绝/超时: 动作取消 + 回执通知
```

这实现了密钥分级设计中的「移动端 = 审批遥控器」：T1/T2 无感，T3 仅一次点击。

### 3.4 指令入口（移动端下命令）

- 用户飞书私聊/指定群 @Pi 发自然语言 → CommandRouter 送 Pi orchestrator（GLM-5.2 大脑）解析
- Pi 决定路由：Qoder 任务 → pi-qoder-dispatch；Kimi/Mira → subprocess
- 立即回一张「已受理」状态卡（含任务 ID），完成后推结果卡

## 4. 凭证与安全

- 飞书 app credentials：**T1 身份凭证**，一次性配置进 ECS（lark-cli auth），长期有效自动刷新
- IdentityGuard 白名单：仅用户 open_id 可下指令/审批；他人消息记录但不执行
- 审批卡防重放：每张审批卡带一次性 token，回调核销后失效
- 全部审批决策写 Aetheris 审计轨迹（真值层）

## 5. 与其他组件的接口约定

| 对端 | 接口 | 方向 |
|------|------|------|
| pi-qoder-dispatch | `ResultSink → CardFactory`（任务完成卡）| 入 |
| 漂移治理 cron | `DriftReport → CardFactory`（报告/告警卡）| 入 |
| Pi orchestrator | `CommandRouter → 任务路由`；`ApprovalGate ← T3 请求` | 双向 |
| Aetheris | 审计写入（审批决策/指令记录）| 出 |

## 6. 验收标准

1. 移动端指令 E2E：飞书发「让 Qoder 列出仓库文件树」→ 收到受理卡 → 收到完成卡（附结果）
2. 审批 E2E：Pi 发起模拟 T3 动作 → 移动端收审批卡 → 点批准 → 动作放行且审计落 Aetheris；点拒绝 → 动作取消
3. 超时路径：审批卡 30min 不点 → 自动拒绝 + 通知
4. 身份防护：用非白名单账号点审批按钮 → 拒绝 + 告警
5. 断线恢复：重启 Pi daemon → EventListener 自动重建长连接，不丢卡片回调

## 7. 依赖与前置

- 前置：用户裁定分工；Pi daemon ECS 部署验证通过（ZCode 任务）
- 依赖：飞书 app 凭证（lark-cli 已有本机登录态，ECS 侧需一次性配置）
- 关联：Trae SOLO Mobile 仅作 Trae 专项补充，不经本桥接（v1.0 已裁定）
