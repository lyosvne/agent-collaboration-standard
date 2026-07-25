---
version: "v2.1"
status: "active"
type: "collaboration-protocol"
supersedes: "workspace-collaboration-v2.0"
title: "协作协议"
signoff: "用户 2026-07-23"
---
# Workspace Collective Collaboration Protocol

> 继承: Aetheris blueprint v1.8 → v2.0.1 草案 → **v2.1 定稿**
> 生效日期: 2026-07-23 | 状态: **用户（林于炜）已裁定生效**
> 本版依据: 架构真值 v1.0（ZCode）+ 编队分工 v1.1（G1-G7 + M1-M5，用户批准）+ Qoder 回执纠错

---

## 0. 权威框架 (Authority Framework)

- **唯一协调者与最终裁判是用户（林于炜）**。协调者地位由用户授予，任何智能体不得自封。
- **所有智能体地位对等**，无主智能体/下属之分。
- 任务所有权来自用户对具体任务的指派或本协议已裁定的路由。
- 硬同步以 git commit 为准，不依赖任何聊天记录或会话状态。

---

## 1. 真值层级与真值位置

冲突裁决顺序：
1. 用户红线与即时指令
2. 本协议 v2.1
3. 架构真值 v1.0（`.agent-collaboration/standards/agent-matrix-architecture-v1.0.md`）+ 编队分工 v1.1
4. 各项目内部文档
5. 代码与 Git 历史
6. 历史归档记录

真值位置锚点：
- **代码唯一硬真值**: `https://github.com/lyosvne/Aetheris-link.git` 的 `origin/master`；各 agent 工作分支 `agent/<name>`
- 全局协作标准: `https://github.com/lyosvne/agent-collaboration-standard`
- 本地协作入口: `C:\Users\Admin\.agent-collaboration\`
- 运行时真值层: ECS `aetherisonline.xyz` 上的 Aetheris（真值层+记忆，非控制平面）
- 知识库: `C:\Users\Admin\Documents\Codex\knowledge-audit-2026-07\Knowledge`

---

## 2. 编队注册（最终态，用户裁定）

### 协调层
| 智能体 | 角色 | 关键授权/边界 |
|--------|------|--------------|
| **Pi** | 中央协调（ECS 24h daemon）：实时路由、漂移治理、审批门、任务板运行时、记忆运行时积累 | 持用户常设授权：代劳 push 限 `agent/*` 分支、禁 master、禁 force、必须审计+飞书通知；不持久化权威状态（真值在 Aetheris/git） |

### 主控层
| 智能体 | 角色 | 边界 |
|--------|------|------|
| **ZCode** | 主调度（PC 驾驶舱）+ 深度编程 + ECS 运维灾备 + 复杂 Extension 实现 + 规格 review | 无入站 API；调 Qoder(MCP+API)/Kimi(经 Pi) |
| **Qoder** | 主架构 + 单项规划（协议/规格/记忆层/安全）+ 基础设施治理(arkcli) + 知识调研 + 批量任务(Cloud Sessions fan-out) + Extension 规格 | 计费/部署类操作为 T3 需用户审批 |

### 执行层
| 智能体 | 角色 | 边界 |
|--------|------|------|
| **Kimi** | 前端实现主力 | `agent/kimi` 分支；Pi subprocess 调度 |
| **Trae 本机** | 平行实现 + 本地集成 + **产品测试/QA/E2E**（吸收原 Trae SOLO 职能） | 与 ZCode 互不调度，git 为同步层 |
| **Mira** | 生图（编队独有）+ 代码评审 + 架构评审 + Extension 评审 | 云端特化，Pi 调度；无本地能力 |

### 孤岛/退役
| 智能体 | 状态 |
|--------|------|
| Trae SOLO（云端） | 孤岛独立使用（网络白名单锁死） |
| Claude Code | ⛔ 退役中（CC→ZCode 迁移进行） |
| Codex | ⛔ 已淘汰（用户确认） |
| QoderWork | ⛔ 已退役（Qoder 接管） |

---

## 3. 任务路由（G+M 分工定稿）

| 任务类型 | 首选 | 备注 |
|----------|------|------|
| 实时协调/调度/漂移治理 | Pi | 已授权 |
| 深度编程/核心实现 | ZCode | — |
| 前端实现 | Kimi | Trae 备选 |
| 平行实现/本地集成/动态测试 QA | Trae | G3 |
| 生图 | Mira | 编队独有 |
| 代码/架构/Extension 评审 | Mira | 静态验证 |
| 主架构/单项规划/协议文档 | Qoder | — |
| 基础设施治理/知识调研 | Qoder | G5 |
| 批量任务 | Qoder Cloud Sessions fan-out | G4，Pi 派发 |
| PM/优先级 | 三分治：用户(战略)+Pi(任务板)+Qoder(规划) | G1，无单点 PM |
| 记忆层规划/记忆老化治理 | Qoder 规划 + Pi 运行时积累 | G2/M4 |
| ECS 运维/灾备 | ZCode + Pi 自愈 + 飞书告警 | G7 |
| 北极星校准 | 用户定锚，Pi 节律，Qoder 报告，Mira 评审 | M1 |
| 紧急制动 | 用户（飞书一键）→ Pi 停全部自动化 | M5 |

对等互检：Qoder ↔ ZCode（指定路径 mtime + git diff），最终验收权在用户。

---

## 4. 安全边界 (Red Lines)

以下操作必须先获用户确认（T3）：
- Secrets、`.env`、tokens、credentials、CI/CD 密钥
- 数据库 schema 变更/迁移；生产数据访问；SSH/部署/服务重启
- `git push`（**例外**: Pi 代劳 push 在常设授权范围内）、rebase、reset --hard、clean、force 操作
- 删除文件/目录/分支/Git 历史；安装全局依赖；计费操作（plans buy/renew、+deploy）

铁律：**每个 agent 只在自己的 `agent/<name>` 分支工作，绝不直接 commit master**；合并 master 走 Pi 集成窗口 + 用户审批。

密钥三层分级：T1 身份凭证（一次性入云端安全库）/ T2 常规凭证（会话级 TTL）/ T3 高权限通行证（JIT，本地守卫，移动端仅审批）。

---

## 5. 完成契约 (Finish Contract)

每次有意义的完成必须报告：Changed / Verified / Not verified / Risk / Commit-PR / Handoff / Next owner / Owner reason。涉及代码/配置/数据/部署/规则变更时附 Rollback target/method/verification。

---

## 6. 协作与同步规则

- 上下文共享粒度是 **commit（产物+决策）**，不是 keystroke；拒绝 live session 共享
- 各自独立 clone + 独立分支，绝不共享工作目录
- 漂移治理：Pi cron 体检（只读）→ 分级报告 → 代劳 push（授权内）/提醒 pull（不代劳）
- 交互分层：飞书 = 对话窗口（指令/通知/移动审批）；Aetheris 网页 = 工作台（任务板/状态/知识）
- Qoder↔Pi 回传：**Webhook 主通道**（Pi 注册 endpoint 订阅 session.status_idled 等生命周期事件，HMAC-SHA256 签名，at-least-once 投递）+ **SSE 补充**（token 级流式输出，用于进度展示）+ **轮询兜底**（webhook 失败降级）
- **执行纪律（终局已定）**：①不偏离既定架构——执行中如发现需要改变架构方向（新增模块、改变设计、扩大范围），必须停下来向用户确认，不得自行决定；②不被技术分支带偏——遇到问题先回到终极目标问"这对目标有用吗"，无用则立即收手转向，不在技术细节里深挖。

---

## 7. 实施优先级（用户裁定，2026-07-23）

**当前唯一优先级：把协作底座跑顺。**

```
P0 底座: ① CC→ZCode 迁移收尾 → ② Pi ECS 部署验证(ZCode)
        → ③ Pi 漂移治理上线(规格已备,授权已签) → ④ Qoder SSE 消费器
        → ⑤ pi-feishu 桥接 → ⑥ Mira/Kimi 接入
后置:   M2 具体 KPI（运行后定义）| G6/M3 自动化质量门（先人工评审）
       | OpenViking 记忆层（先规划适时建）| Pi 自进化（现阶段为"他进化"：亲属反哺建设 Pi）
```

---

## 8. 双环治理模型（长期框架，M 系列已批准）

- **运转环 G1-G7**: 感知→决策→执行→验证→沉淀→进化（详见 fleet-division-v1.1 §2-4）
- **方向环 M1-M5**: 北极星锚→度量→校准→回轨/回滚/修剪/制动（详见 fleet-division-v1.1 §7）
- **北极星文档**: `north-star-v1.2.md`（**用户已定稿生效，2026-07-23**；M1 唯一校准基准；v1.2 §五第一性原则：立足宏观，找最大范围内最优解）
- 原则：点状偏差容忍并记录，趋势偏航触发回轨；系统最终必须能回到轨道

---

## 9. 过渡期协调与治理文档管理（v2.1 最终版新增）

### 9.1 过渡期协调（Pi 上线前的临时机制）

Pi 部署验证完成前，协调按以下临时机制运行，Pi 上线后自动废止：
- **指令中继**: 用户在各 agent 会话间转发提示词（现行做法，正式承认为过渡机制）
- **文件信箱**: `C:\Users\Admin\.agent-collaboration\templates\` 为异步回执/交接通道
- **PC 端调度**: ZCode 驾驶舱可先行（MCP 调 Qoder），不等 Pi
- **漂移应急**: Pi 体检上线前，任何 agent 发现漂移异常应主动报告用户

### 9.2 治理文档必须入 git（第一性修正）

**发现的自相矛盾**: 本协议宣称"硬同步以 git commit 为准"，但协议/架构/分工/规格文档自身散落在非 git 目录——治理层自己没有版本控制。

**修正要求**（待用户批准执行）:
- 全部治理文档（协议/架构真值/分工/北极星/三份规格）提交至 git 真值：首选 `github.com/lyosvne/agent-collaboration-standard`，或 Aetheris-link 的 `docs/governance/`
- 提交动作由用户授权后执行（commit+push 属受控操作）
- 此后治理文档修订 = git commit，历史可溯，杜绝"文件被谁改了不知道"

### 9.3 存活性事实（2026-07-23 实测）

- ECS `aetherisonline.xyz`: HTTP 200（Caddy 在线），Aetheris API 运行中（/api/auth/session 返回 401 = 服务+鉴权正常）——**架构地基已验证为实**

---

## 元数据

- 协议版本: **v2.1 最终版（用户裁定生效 + 第一性原理补全）**
- 生效日期: 2026-07-23
- 关联文档: `agent-matrix-architecture-v1.0.md`、`fleet-division-v1.1-proposal.md`、`north-star-v1.0.md`（已定稿）、三份实施规格
- 修订机制: 任何智能体可提议修订，生效需用户裁定
- §9.2 执行记录: **已完成**（2026-07-23，用户授权）——治理文档已入 `github.com/lyosvne/agent-collaboration-standard` 的 `governance/` 目录，commit `c604f08`（master + agent/qoder）；自此治理文档修订以该仓库 git commit 为准，本地 `.agent-collaboration\standards\` 为镜像
