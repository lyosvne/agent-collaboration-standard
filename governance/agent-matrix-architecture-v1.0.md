---
version: "v1.0"
status: "active"
type: "architecture-truth"
title: "架构真值"
signoff: "ZCode 2026-07-23"
---
# 智能体矩阵架构真值 v1.0

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
              ├─ webhook 接收队列(Qoder/Mira 回传)
              ├─ subprocess 调度(Kimi)
              └─ MCP server(Trae 主动汇报/外部读取)
                        │
        ┌───────────────┼───────────────────┐
        ▼               ▼                   ▼
   【主控 PC 端】    【被调度节点】      【云端特化】
   ZCode(驾驶舱)    Qoder(云端API)     Mira(生图+评审)
   Trae(平行工作者) Kimi(ECS沙箱)     
                        │
                        ▼
              【共享真值层】
         GitHub origin/master(唯一硬真值)
         + Aetheris(瘦身后,控制平面+记忆)
         + ECS 共享文件系统(Pi↔ZCode)
```

---

## 二、各智能体定位（锁定）

### 主控层

| 智能体 | 定位 | 调度能力 | 被调度能力 | 云沙箱 |
|---|---|---|---|---|
| **ZCode** | 主控驾驶舱 | 调 Qoder(MCP+API)、调 Kimi(Pi subprocess) | ❌ 无入站API,不能被外部push触发 | ❌ 无,SSH连ECS工作区 |
| **Trae(本机)** | 平行工作者 | ❌ 不能调度别人(无原生API) | ❌ 不能被ZCode调度(无入站) | 本地沙箱不限网络 |

### 被调度层

| 智能体 | 定位 | 被调度方式 | 云沙箱 | 模型 |
|---|---|---|---|---|
| **Qoder** | 可调度云执行节点 | REST API + Webhook + SSE(唯一支持外部调度的云沙箱) | ✅ 官方托管(2vCPU/8GB) | 自有套餐 |
| **Kimi** | 可调度云执行节点 | Pi subprocess(ECS sandbox) | ❌ 纯CLI,Pi sandbox补 | kimi-code/k3 |
| **Mira** | 云端特化(生图+评审) | Pi 调度(类Kimi) + webhook外发 + git推送 | 云端原生 | 自有套餐 |

### 淘汰/孤岛

| 智能体 | 状态 | 原因 |
|---|---|---|
| **Codex** | ⛔ 淘汰 | 本地用方舟模型,云沙箱绑OpenAI调不动,GUI/CLI两套维护重 |
| **Trae IDE（编队角色）** | ⛔ 退役为编队角色 | 2026-07-26 C 选项裁定：编队里 Trae 系只保留 SOLO 一个独立角色（端到端测试/QA）。Trae IDE 退到个人工具，不进 Pi 调度。软件保留，Aetheris 历史分支待合并入 `agent/solo` |
| **Claude Code** | ⛔ 退役完成 | 2026-07-25 退役，2026-07-26 密钥清理完成（详见 `.claude/RETIREMENT-STATUS.md`） |

---

## 三、中央协调智能体:Pi

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

### Pi 部署形态(待ECS实测验证)
```
ECS aetherisonline.xyz
└── Pi orchestrator (serve 模式, 24h daemon)
    ├── OrchestratorSupervisor(监督亲属实例)
    ├── IPC server(接收亲属RPC)
    ├── Radius 联邦(跨机心跳)
    ├── Extensions(链接Aetheris API + 飞书桥接)
    ├── Skills(~/.agents/skills 复用)
    ├── sandbox(每个agent隔离执行)
    └── pi-ai(GLM-5.2 当大脑)
```

### 孩子的成长机制
- **亲属矩阵培养**:各agent执行结果(Plans/trajectories/outcomes)流入共享记忆
- **越用越聪明**:Pi 通过 Extensions 积累新工具,通过 Skills 学新能力
- **成长由矩阵负责,用户只定目标**:用户不直接训练Pi,矩阵反哺

---

## 四、协作模式(按关系分层)

### 4.1 ZCode ↔ Qoder(主控↔被调度)
- **ZCode→Qoder**:MCP 包装 Qoder REST API,秒级近实时调度
- **Qoder→ZCode**:webhook 回传 Pi → Pi 写共享文件 → ZCode 读取(依赖ZCode活跃)
- **上下文共享**:产物级(git) + Pi 中转字段级,非 live session

### 4.2 ZCode ↔ Trae(主控↔平行工作者)
- **不能互相调度**(Trae无入站API,ZCode无触发本地应用能力)
- **产物共享**:各自独立 clone + 独立分支,git 是同步层
- **关系定位**:"共享工作区的同事",非"上下级调度"
- **可选增强**:Trae 通过 MCP 主动向 Pi 汇报状态(状态实时,非内容)

### 4.3 Pi ↔ Kimi(调度↔被调度)
- Pi 通过 subprocess 在 ECS sandbox 调度 Kimi
- Kimi 纯CLI,无GUI,天然适合云端托管

### 4.4 Pi ↔ Mira(调度↔云端特化)
- Pi 调度 Mira(类 Kimi 方式)
- Mira 特化能力:生图 + 评审(代码评审/架构评审)
- Mira 有 webhook 外发 + git 推送能力,可主动汇报
- **Mira 无本地能力**,所有执行在云端,不占本地资源

### 4.5 移动端 → 编队
- **统一入口:飞书移动端**(pi-feishu + 互动卡片审批)
- 不依赖任何PC开机(Pi常驻ECS)
- Trae SOLO Mobile 作为 Trae SOLO 的移动形态（编队里 Trae 系唯一角色的移动入口）

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

**第二层:Pi 主动纠正**
- **代劳 push(安全)**:检测到本地有未push commit → Pi 直接帮 push(不改工作区)
- **提醒 pull(不代劳)**:检测到本地落后 → 通知人/等agent空闲(pull可能冲突,不能盲动)

**第三层:源头预防**
- 铁律:一个agent只在自己分支干活,绝不直接动master
- pre-commit hook:commit时检查漂移程度,警告
- Pi 集成窗口:定期把各分支合并到master,控制漂移上限

### Trae PC ↔ Trae Mobile 同步
- Pi 监控 agent/trae 分支(不区分PC/Mobile来源)
- 要求 Trae 任务(无论PC/Mobile下发)必须 commit 到 agent/trae
- Pi 漂移治理逻辑完全适用

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

### Aetheris 网页侧(详细面板)
- 任务板/状态看板/决策记录/知识库/审计轨迹
- 结构化展示,群聊展示不了的东西放这

### 分层原则
- 飞书 = "对话窗口"(下命令/收通知/移动端遥控/审批)
- Aetheris网页 = "工作台/仪表盘"(任务板/状态/知识)
- Pi 同时接两者(Extension 多向桥接)

---

## 八、待验证风险

1. **Pi orchestrator 在 ECS 的 daemon 稳定性**(标 experimental,需实测)
   - Radius 联邦真实可用性
   - 24h 常驻可靠性
   - 这是整个架构的地基验证

2. **Pi 第一个实战任务:漂移治理脚本**
   - 低风险,高ROI
   - 同时验证 Pi daemon + 飞书通知闭环

3. **Mira 的特化能力接入**
   - 生图/评审如何通过 Pi 调度
   - Mira 的 webhook 外发格式需对齐

---

## 九、实施优先级

1. **CC→ZCode 迁移**(进行中,主仓库同步+身份/规则/配置迁移)
2. **Pi ECS 部署验证**(地基测试)
3. **Pi 漂移治理上线**(第一个实用功能)
4. **Qoder API 接入 Pi**(webhook 接收队列)
5. **飞书移动端 → Pi 桥接**(pi-feishu)
6. **Mira 接入**(特化能力)
7. **Trae MCP 主动汇报**(可选优化)

---

## 附:关键决策记录

| 决策点 | 结论 | 依据 |
|---|---|---|
| 中央协调体 | Pi(非ruflo/DeerFlow/aily) | 源码精读,成长性+协调+同栈 |
| Codex 去留 | 淘汰 | 云沙箱绑OpenAI+GUI/CLI两套+本地已换方舟 |
| Trae IDE 退役为编队角色 | 2026-07-26 C 选项裁定 | 编队里 Trae 系只保留 SOLO 独立角色（端到端测试/QA），Trae IDE 退到个人工具；Aetheris 分支合并见独立任务 |
| 移动端入口 | 飞书(非Trae Mobile) | 审批按钮+统一收口+不依赖PC |
| 上下文共享粒度 | commit级(非keystroke) | 已被并发坑过,git是同步层 |
| 漂移治理 | Pi轮询+代劳push+提醒pull | agent不可靠,系统强制同步 |
| Mira 角色 | 云端特化(生图+评审),Pi调度 | 无本地能力,优先类Kimi被调度 |
| MatterSource枚举 | 只改可见层(DB/类型/Kimi UA不动) | 选B,零数据迁移零红线 |
