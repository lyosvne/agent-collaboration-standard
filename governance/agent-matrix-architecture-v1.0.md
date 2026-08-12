---
version: "v1.1"
status: "active"
type: "architecture-truth"
title: "架构真值"
signoff: "用户 2026-08-08（Pi 运行与六角色同步）"
---
# 智能体矩阵架构真值 v1.1

> 签发: ZCode | 裁定: 用户（林于炜）| 日期: 2026-07-23
> 性质: 编队架构真值文档，后续所有实施以此为准
> 依据: aily 实测 + Pi/ruflo 源码精读 + 知识库 331 项目调研 + 官方文档逐项验证 + 用户多轮讨论裁定

---

## 一、架构总览

```
                    【移动端入口】
                  飞书移动端(pi-feishu)
                        │
                        ▼
                【中央协调"孩子"】
              Pi orchestrator(ECS 24h daemon)
              ├─ 漂移治理 cron(核心实用功能)
              ├─ SSE 接收队列(Qoder 回传) + 轮询兜底（2026-07-26 用户裁定：Qoder 无 Webhook，本机实证 SSE+轮询）
              ├─ subprocess 调度(Kimi)
              └─ 状态/任务接口（统一 Trae 与外部 App 回传）
                        │
        ┌───────────────┼───────────────────┐
        ▼               ▼                   ▼
   【本地执行】      【被调度节点】      【云端特化】
   Trae(实现/集成/测试) Qoder(云端API) Mira(生图+治理)
   ZCode(非终端评审)    Kimi(终端/数据)
                        │
                        ▼
              【共享真值层】
         GitHub origin/master(唯一硬真值)
         + Aetheris(Pi 思维平面：认知外显、反馈、记忆与审计)
         + ECS 共享文件系统(Pi↔ZCode)
```

---

## 二、各智能体定位（锁定）

### 主控层

| 智能体 | 定位 | 调度能力 | 被调度能力 | 云沙箱 |
|---|---|---|---|---|
| **ZCode** | 非终端评审/分析/反哺 | ❌ 不承担中央调度 | 通过结构化 handoff 接收评审任务 | ❌ 无终端、SSH 和 Git 执行 |
| **Trae(本机)** | 统一实现/集成/测试主体 | 可调用本地工具，不承担中央协调 | 接收 Pi 派单和跨角色 handoff | Mac 独立 clone |

### 被调度层

| 智能体 | 定位 | 被调度方式 | 云沙箱 | 模型 |
|---|---|---|---|---|
| **Qoder** | 可调度云执行节点 | REST API + SSE(唯一支持外部调度的云沙箱；无 Webhook，2026-07-26 用户裁定) | ✅ 官方托管(2vCPU/8GB) | 自有套餐 |
| **Kimi** | 可调度云执行节点 | Pi subprocess(ECS sandbox) | ❌ 纯CLI,Pi sandbox补 | kimi-code/k3 |
| **Mira** | 云端特化(生图+评审) | Pi 调度(类Kimi) + webhook外发 + git推送 | 云端原生 | 自有套餐 |

### 淘汰/孤岛

| 智能体 | 状态 | 原因 |
|---|---|---|
| **Codex** | ⛔ 淘汰 | 本地用方舟模型,云沙箱绑OpenAI调不动,GUI/CLI两套维护重 |
| **独立 Solo** | ⛔ 已退役并入统一 Trae | 历史分支和测试记忆只作证据；当前实现、集成和 product-test 均由 Trae 承接 |
| **Claude Code** | ⛔ 退役完成 | 2026-07-25 退役，2026-07-26 密钥清理完成（详见 `.claude/RETIREMENT-STATUS.md`） |

---

## 三、Pi：自闭环认知智能体

> v1.1 措辞同步（2026-08-12，联动北极星 v1.5）：本节原标题为"中央协调智能体:Pi"。Pi 运行时已演进出完全自闭环形态，不调度其他智能体。本节同步措辞；Pi Agent Harness 的技术选型事实（orchestrator 包、Extensions、Skills 等）不变。

### 选型结论
经 aily 实测 + ruflo 源码精读 + DeerFlow/LangGraph 对比,选定 **Pi Agent Harness(@earendil-works/pi)** 作为"孩子"。

**淘汰 ruflo 的关键事实(源码精读,非README营销):**
- ruflo 本质是 claude-flow 换皮(npm 包名就是 claude-flow)
- federation 是 742 行空壳(native feature 默认关,Cargo.toml 注释承认 Rust 仅"让评分工具看到")
- "SONA 自我学习"实际是 MongoDB 存储,非真机器学习

**Pi 命中的核心诉求(源码确认):**
1. **成长性三层机制**:Extensions(自定义工具,70+现成示例) + Skills(能力包) + Pi Packages(npm分享)
2. **协调中枢**:orchestrator 包(supervisor + IPC protocol + serve daemon + Radius联邦心跳)
3. **OS级沙箱**:sandbox extension(bubblewrap on Linux/ECS)
4. **技术栈**:TypeScript(与Aetheris同栈,用户可驾驭)
5. **模型无关**:pi-ai 多 provider(可接 GLM-5.2,有 custom-provider 示例)
6. **技能兼容**:直接读 ~/.agents/skills(现有200+ skill零迁移)

### Pi 部署形态（ECS 已运行）
```
ECS aetherisonline.xyz
└── Pi orchestrator (serve 模式, 24h daemon, 自闭环认知)
    ├── OrchestratorSupervisor(Pi 自身进程监督)
    ├── IPC server(接收治理 mirror / 飞书输入)
    ├── Radius 联邦(跨机心跳)
    ├── Extensions(链接Aetheris API + 飞书桥接)
    ├── Skills(~/.agents/skills 复用)
    ├── sandbox(Pi 自身工具隔离执行)
    └── pi-ai(GLM-5.2 当大脑)
```

### Pi 的成长机制
- **自进化成长**:Pi 通过 Extensions 积累新工具,通过 Skills 学新能力；认知和能力成长受独立质量门约束
- **用户战略引导 + 工具箱反哺**:用户定目标和反馈；能力自改提案需要时由用户即席指派工具箱 agent 评审和反哺

---

## 四、协作模式(按关系分层)

> v1.1 措辞同步（联动北极星 v1.5）：以下关系描述原为"Pi 中央协调→派发/派单/调度"。Pi 现为自闭环认知系统，不调度其他智能体。需要多 agent 协作时由用户即席指派。Pi 与各 agent 的技术接口（API/SSE/subprocess）保留为可用通道，但触发权在用户，不在 Pi。

### 4.1 Pi 与 Qoder（认知系统↔设计/云端工具箱）
- **用户即席指派 Qoder**：用户需要设计/云端任务时直接指派给 Qoder，通过 Qoder API/SSE
- **Qoder→Pi**：SSE 回传，轮询兜底（Qoder 产出可流入 Pi 记忆作为认知素材）
- **ZCode**：按需接收产物做非终端评审，不承担调度或执行

### 4.2 Pi 与 Trae（认知系统↔统一执行工具箱）
- 用户即席指派 Trae 做实现、集成、Git/PR/CI 和产品验收
- Trae 使用独立 clone 和 `agent/trae-mac`
- 历史 Solo 能力作为 Trae 的 product-test 模式

### 4.3 Pi 与 Kimi(认知系统↔终端工具箱)
- 用户即席指派 Kimi 做终端实现；Kimi 也可经 subprocess 在 ECS sandbox 执行
- Kimi 纯CLI,无GUI,天然适合云端托管

### 4.4 Pi 与 Mira(认知系统↔云端特化工具箱)
- 用户即席指派 Mira 做生图 + 评审(代码评审/架构评审)
- Mira 特化能力:生图 + 评审(代码评审/架构评审)
- Mira 有 webhook 外发 + git 推送能力,可主动汇报
- **Mira 无本地能力**,所有执行在云端,不占本地资源

### 4.5 移动端 → 编队
- **统一入口:飞书移动端**(pi-feishu + 互动卡片审批)
- 不依赖任何PC开机(Pi常驻ECS)
- 移动端统一通过飞书/Pi，不建立独立 Solo 移动角色

---

## 五、漂移治理(核心实用功能,Pi 首要任务)

### 问题根源
- Agent 不会主动 pull(不知道别人有新东西)
- Agent 忘了 push(完成功能单元后跳过 commit/push)
- 6 agent 时漂移爆炸(已被坑过,见 current-source-of-truth 记载)
- **根因:依赖 agent 主动同步的设计本身有缺陷**

### 三层治理方案

**第一层:Pi 漂移体检公示(cron 每15-30分钟)**
```
对每个 agent clone:
  git fetch origin
  检测:本地 vs origin/<branch> 差几个 commit
  检测:各分支 vs master 差几个 commit
产出漂移报告 → 飞书/Aetheris 公示
严重漂移(>10 commits) → 飞书告警
```

**第二层:Pi 主动协调**
- **提醒 push**:检测到分支有未 push commit → Pi 通知对应执行 agent
- **提醒同步**:检测到分支落后 → 通知对应 agent；Pi 不代劳 pull/merge

**第三层:源头预防**
- 铁律:一个agent只在自己分支干活,绝不直接动master
- pre-commit hook:commit时检查漂移程度,警告
- Pi 集成提案:定期列出候选分支、冲突和验证状态；Trae 经 PR/CI 执行合并

### Trae ↔ Pi 同步
- Pi 读取 Trae handoff 与远端分支状态，不直接修改 Trae 工作区
- Trae 任务提交到项目规定的 `agent/trae-mac` 或受审 feature 分支
- 合并由 Trae 经 PR/CI 执行，Pi 负责协调和状态收敛

---

## 六、文件安全与上下文共享原则

### 文件安全(已被实践验证)
- **各自独立 clone + 独立分支**(Aetheris-clones/<agent> → agent/<agent>)
- 2026-06-27 已完成多agent隔离迁移(根治并发ref损坏)
- **绝不共享同一个工作目录**(会互相覆盖)

### 上下文共享粒度
| 层次 | 共享方式 | 实时性 | 说明 |
|---|---|---|---|
| 已提交产物 | git push/pull | 分钟级(commit频率) | 主要共享方式 |
| 未提交改动 | ❌ 不同步 | 不同步 | 独立clone必然代价 |
| Agent live session | ❌ 无法共享 | 无法同步 | 不应混在一起 |

**原则:上下文共享粒度是"commit(产物+决策)",不是"keystroke(实时改动)"**
- 追求 live 实时共享 = 重新引入并发风险(已付过学费)
- Pi 状态板(档位2)可作为后续优化,但非必需

---

## 七、交互层设计(用户裁定)

### 飞书侧(交互+通知)
- **排版决策通知**:Interactive Card(飞书交互卡片,有 card-2.0-schema)
- **快速审批按钮**:card.action.trigger 回调 + lark-approval skill
- **信息聚合简报**:飞书消息 + 多维表格
- 能力已齐(lark-im 卡片 + lark-approval),Pi Extension 桥接即可

### Aetheris 网页侧（Pi 思维平面）
- 认知日记/活看板/提案/反馈/任务状态/知识库/审计轨迹
- 结构化展示,群聊展示不了的东西放这

### 分层原则
- 飞书 = "对话窗口"(下命令/收通知/移动端遥控/审批)
- Aetheris网页 = "Pi 思维平面"(认知外显/反馈/状态/知识)
- Pi 同时接两者(Extension 多向桥接)

---

## 八、待验证风险

1. **Pi ECS 长期可靠性**
   - 基线闭环已运行
   - 继续跟踪 daemon、漂移门禁、审计和回滚可靠性

2. **Pi 第一个实战任务:漂移治理脚本**
   - 低风险,高ROI
   - 同时验证 Pi daemon + 飞书通知闭环

3. **Mira 的特化能力接入**
   - 生图/评审如何通过 Pi 调度
   - Mira 的 webhook 外发格式需对齐

---

## 九、实施优先级

1. **治理真源与六角色同步**
2. **认知自更新和能力自改质量门**
3. **Pi ECS 漂移、审计和回滚可靠性**
4. **Qoder/Kimi/Mira/Trae 反哺链路**
5. **Aetheris 思维平面与反馈闭环**

---

## 附:关键决策记录

| 决策点 | 结论 | 依据 |
|---|---|---|
| 中央协调体 | Pi(非ruflo/DeerFlow/aily) | 源码精读,成长性+协调+同栈 |
| Codex 去留 | 淘汰 | 云沙箱绑OpenAI+GUI/CLI两套+本地已换方舟 |
| Trae 与 Solo | 统一 Trae | Trae 承接实现、集成、Git/PR/CI、产品测试和浏览器验收；独立 Solo 退役 |
| 移动端入口 | 飞书(非Trae Mobile) | 审批按钮+统一收口+不依赖PC |
| 上下文共享粒度 | commit级(非keystroke) | 已被并发坑过,git是同步层 |
| 漂移治理 | Pi只读轮询+通知+集成提案 | Git 写入由执行 agent 完成 |
| Mira 角色 | 云端特化(生图+评审),Pi调度 | 无本地能力,优先类Kimi被调度 |
| MatterSource枚举 | 只改可见层(DB/类型/Kimi UA不动) | 选B,零数据迁移零红线 |
