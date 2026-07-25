# 全局路线图 v1.0（草案）

> 签发: ZCode | Review: Qoder(cantus) | 裁定: 用户
> 日期: 2026-07-24
> 性质: 从全部资产（蓝图v1.11 + 编队P0 + 知识库 + ECS/GitHub代码）提取整合的全局路线图
> 依据: 北极星v1.2终极目标 + Aetheris蓝图终局定义 + soul.yaml

## 终极目标（不变）

**用户只需制定战略和确认关键决策，其余一切围绕设定轨道自动运转。**

## 路线图分三个层面

```
层面A: Aetheris 产品（身体）— 蓝图定义的产品本体
层面B: 编队协作系统（神经+免疫）— Pi+飞书+Qoder+漂移治理
层面C: 云端迁移（基础设施演进）— 本地资产→云端，本机轻量化
```

三个层面并行推进，相互依赖。

---

## 层面A: Aetheris 产品

### 当前真实状态
- 蓝图v1.11，原型融合5阶段完成，Wave 2进行中
- "管道搭好无流水"——578个后端TS文件+178个前端TS文件，但数据流多处断链
- 前端能看到界面，看不到真实业务数据

### A-1: W5.5 数据流闭环（最高优先，当前阻塞）
- 建真实客户 account（如海信）
- 修 feishu-matter-importer E18（飞书摘要→matter时填 account_id）
- backfill value_score
- prototype-src 18文件全重构融入
- **验收标准**: csm "按客户"视图有真实数据

### A-2: 核心"接线"修复（W5.5之后）
按 current-source-of-truth.v0.3 完成度矩阵优先级：
- M03 matters 去重（checkDuplicate 死代码→实现）
- Echo 智能体消费 memory（多轮对话真正生效）
- M19 认知转译（intent-parser 全正则→加LLM）
- M05 知识图谱（nodes/edges=0→灌数据）

### A-3: Wave 3-5（蓝图总纲）
- Wave 3: Mira异步调度 + matter学习闭环 + 安全治理 + 治理面板
- Wave 4: 外部Agent接入 + 产品研发Agent + 多端延续
- Wave 5: 迁移收尾 + 旧worktree清理 + 全链路回归

---

## 层面B: 编队协作系统

### 当前真实状态
- P0底座6项完成5项，剩 Mira/Kimi 接入
- Pi 4个服务active（server/bridge/callback/dispatch）
- 飞书桥接+三档Qoder+调度上下文+模型追踪全部上线
- 漂移治理cron每30分钟

### B-1: P0收尾（当前）
- ⑥ Mira/Kimi 接入（最后一项P0）
- CC完全下线验收清单（~/.claude/清理 + 配置归档）
- Codex知识库归属转移（331项目调研→迁入协作标准仓库或Aetheris知识层）

### B-2: 智能路由（P0之后）
当前用户需手动说"qoder/前端/架构"指定档位。目标：
- 用户说一句话，系统自己判断该调哪个agent
- Pi做意图理解→路由→执行→回报
- 对应Aetheris的 M19 认知转译（intent-parser升级）

### B-3: 自动运转（终局形态）
- 漂移治理已自动（cron）
- 目标：任务推进、状态公示也自动
- Pi任务板运行时 + 定期飞书汇报

---

## 层面C: 云端迁移

### 设计目标
所有协作资产上云，本机是轻量加强型和坐下时的PC终端。
PC关机后系统仍能运转（Pi已上云，Qoder已上云）。

### 当前障碍
- 蓝图无此规划，需从零设计
- 本机有大量资产：Codex知识库、Aetheris-clones、配置、历史会话
- ZCode支持SSH远程连接（可连ECS工作），Qoder本身就是云的

### C-1: 识别需迁移的本地资产
| 资产 | 位置 | 迁移目标 | 优先级 |
|---|---|---|---|
| Codex知识库 | Documents\Codex\knowledge-audit-2026-07\ | ECS或Aetheris知识层 | 高 |
| 协作治理文档 | .agent-collaboration\ | 已在GitHub（agent-collaboration-standard） | ✅已迁移 |
| Aetheris代码 | Aetheris-link\ + Aetheris-clones\ | 已在GitHub | ✅已迁移 |
| Pi extensions | 本地workspace→SCP到ECS | ECS git仓库 | 中 |
| 用户配置 | .zcode\ .codex\ .claude\ | 需评估哪些上云 | 中 |

### C-2: ZCode远程工作空间
- 用ZCode SSH连接ECS作为工作空间
- 代码在ECS上直接编辑，不用本地clone+SCP
- Qoder Cloud Agent已有此能力（WebFetch读ECS上下文）

### C-3: 轻量本机终端
- 本机只保留：ZCode（SSH连ECS）、飞书（移动端入口）、Obsidian（知识浏览）
- 不再在本机维护完整开发环境
- 对应 ground-truth/43 定义的"本地=管理/审阅终端"

---

## 三层面依赖关系

```
层面B(P0收尾) ──→ 层面B(智能路由) ──→ 层面B(自动运转)
       │                                    │
       │     ┌──────────────────────────────┘
       ▼     ▼
层面A(W5.5数据流) ──→ 层面A(接线修复) ──→ 层面A(Wave3-5)
       │
       │
       ▼
层面C(资产识别) ──→ 层面C(ZCode远程) ──→ 层面C(轻量终端)
```

**当前最优先**: B-1(P0收尾) + A-1(W5.5数据流闭环) 并行

---

## 退役收尾清单

### Codex 退役
- [x] 裁定淘汰（用户确认）
- [ ] 知识库归属转移（331项目调研→迁入协作标准或Aetheris知识层）
- [ ] ~/.codex/ 配置归档
- [ ] 知识库每日自动Pipeline（Windows Task Scheduler）迁移到ECS cron

### Claude Code 完全下线
- [x] 代码迁移（c9627016）
- [x] 身份标识替换（CC→ZCode）
- [ ] ~/.claude/ 配置清理
- [ ] .fusion 操作记忆归档
- [ ] Aetheris-clones/claude 分支处理
- [ ] 验收：确认无CC残留依赖

### QoderWork 退役
- [x] 裁定退役（Qoder接管）
- [ ] 确认无残留依赖

---

## 待和Qoder(cantus)交接的架构问题

1. **层面A和层面B的融合点**：Aetheris的M19认知转译 vs Pi的意图路由，是同一个东西还是两层？谁做主？
2. **层面C的云端迁移路径**：ZCode SSH远程工作空间怎么配？ECS需要什么准备？
3. **知识库归属**：Codex的331项目调研，归入Aetheris知识层（M05）还是独立维护？
4. **退役顺序**：CC下线、Codex退役、QoderWork退役，谁先谁后？有没有依赖关系？
