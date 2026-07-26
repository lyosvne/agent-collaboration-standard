---
version: 1.2
status: ready
type: spec
created: 2026-07-26
updated: 2026-07-26
owner: ZCode
title: Mira vs lark-cli 飞书能力对比与编队集成定位
scope: 比对 Mira CLI 与本地 lark-cli（标准飞书开放平台封装）的能力边界，明确 Mira 的独有价值，作为编队操作飞书系统的补充节点定位依据
related:
  - specs/mira-integration-status.md
  - standards/global-roadmap-v1.1.md
  - specs/mira-deep-dive-backlog.md
supersedes: []
---

## 更新日志

- **v1.2 (2026-07-26)**：Mira 沙箱 c360 接入打通（绕过本机风控），补 §6.1 真实路径 + §6.1.1 数据分层策略（c360 为主，风神为辅）。
- **v1.1 (2026-07-26)**：补 §六 CSM 数据链路 + 风神看板发现限制实测结论，新增深度挖掘待办索引（见 specs/mira-deep-dive-backlog.md）。
- **v1.0 (2026-07-26)**：初次比对，明确 5 类独有能力 + 任务路由策略。

# Mira vs lark-cli 飞书能力对比与编队集成定位

## 一、定位结论（先看这个）

| 工具 | 定位 | 边界 |
|---|---|---|
| **lark-cli（本地）** | 飞书开放平台标准封装（27 个 skill） | 只能做飞书开放平台 API 暴露的事，无字节内部系统访问 |
| **Mira CLI** | 字节内部业务+生成式AI+长期记忆的超级入口 | 覆盖飞书 + 字节内部系统 + AI 生成 + 跨系统检索 + 记忆 |

**编队集成意义**：Mira 不是"另一个 lark-cli"，而是**编队操作飞书生态+字节内部系统的补充节点**。它能做 lark-cli 做不到的 5 类事，是编队接入字节内部数据的关键通道。

---

## 二、能力对比矩阵

### A. 重叠能力（Mira 和 lark-cli 都有，27 项）

两者**调用同一套飞书开放平台 API**，能力等价。Mira 内部封装的 lark-* skill 跟本地同名 skill 同源：

| Skill | 能力 | 状态 |
|---|---|---|
| lark-base | 多维表格 | 重叠 |
| lark-calendar | 日程 | 重叠 |
| lark-contact | 通讯录 | 重叠 |
| lark-doc | 文档 | 重叠 |
| lark-drive | 云空间 | 重叠 |
| lark-im | 即时消息 | 重叠 |
| lark-sheets | 电子表格 | 重叠 |
| lark-wiki | 知识库 | 重叠 |
| lark-whiteboard | 画板 | 重叠 |
| lark-task | 任务 | 重叠 |
| lark-minutes | 妙记 | 重叠（但 Mira 还能调用妙记 AI 产物，见 D）|
| lark-apps | 应用 | 重叠（但 Mira 还能部署到妙搭，见 D）|
| lark-approval | 审批 | 重叠 |
| lark-attendance | 假勤 | 重叠 |
| lark-mail | 邮件 | 重叠 |
| lark-okr | OKR | 重叠 |
| lark-vc / lark-vc-agent | 视频会议 | 重叠 |
| lark-event | 事件订阅 | 重叠 |
| lark-note | 会议笔记 | 重叠 |
| lark-markdown | Drive 原生 Markdown | 重叠 |
| lark-slides | 幻灯片 | 重叠 |
| lark-openapi-explorer | OpenAPI 探索 | 重叠 |
| lark-skill-maker | Skill 制作 | 重叠 |
| lark-shared | 共享基础 | 重叠 |

**编队策略**：重叠能力**不走 Mira**（避免消耗 Mira token），优先用本地 lark-cli 直接调（零成本、ZCode 自己能跑）。

### B. Mira 独有能力（lark-cli 完全做不到）—— ⭐ 编队价值所在

#### B.1 字节内部业务系统（最强独有）

| Skill | 能力 | 实测 | 编队价值 |
|---|---|---|---|
| **cis-cli** | CIS 一站式：人事/假勤/审批/差旅/报销/团建/采购/合同/法务/职场服务 | ✅ 已测（权限正常） | ⭐ 字节内部审批流接入 |
| **people-performance** | 绩效评估全流程 | 未测 | 个人绩效数据 |
| **people-level-comp-review** | 调级调薪评审 | 未测 | |
| **perf-review-helper** | 绩效评审辅助 | 未测 | |
| **aeolus-query** | 风神 Aeolus 仪表盘/数据集/血缘查询（6 区域） | 未测 | ⭐ 数据分析 |

#### B.2 跨系统语义检索（lark-cli 无语义层）

| Skill/工具 | 能力 | 实测 | 编队价值 |
|---|---|---|---|
| **one_context** (`mcp__proxy___one_context__retrieve_context`) | 跨飞书文档/Wiki/群消息/妙记/Hive/Prism 统一语义检索 | ✅ 已测，命中"飞书客户端专版打包 CSM 流程"文档 | ⭐⭐⭐ 编队知识检索核心 |
| **list_data_domains** | 列出可检索的数据域 | 未测 | |

**实测结果**：搜"飞书客户成功经理日常工作职责"，直接命中**林于炜本人创建的 CSM 流程文档**，并返回语义摘要+文档链接。lark-cli 只能按文档 ID/标题精确查，做不到语义检索。

#### B.3 长期记忆系统（Mira 独有，跨设备持久）

| Skill | 能力 | 实测 | 编队价值 |
|---|---|---|---|
| **mira-memory-recall** | 召回长期记忆 | ✅ 已测 | ⭐⭐⭐ 上下文连续性核心 |
| **mira-memory-edit** | 写入/删除/修改记忆 | 未测 | |
| **memory-import** | 跨平台导入记忆片段 | 未测 | |

**实测结果**：召回"飞书客户成功/CSM/编队"关键词，Mira 完整记住了：
- 2026-05-12 你的 CSM 岗位自述（含工具栈、KPI、项目经理角色）
- 2026-05-23 Aetheris P0 基座规划、M08 CSM 工作流模块设计
- 2026-05-24 `aetheris-identity/soul.yaml` 落盘（价值观与决策偏好）

**这些是你在 Mira 客户端长期积累的工作记忆，本地任何工具都没有**。这是 Mira 接入编队后**最不可替代的价值**——它是你过去半年工作上下文的载体。

#### B.4 生成式 AI（lark-cli 无生成能力）

| Skill/工具 | 能力 | 实测 | 编队价值 |
|---|---|---|---|
| **Nano Draw** (`generate_pictures` / `edit_pictures`) | 文生图/图生图（一次 4 张） | ✅ 已测 | ⭐ 生图主力 |
| **gpt-image-2** | OpenAI 独立生图模型 | ✅ 已测 | ⭐ 单图高质量 |
| **mira-html-ppt** | HTML PPT 生成 | 未测 | |
| **mira-generative-ui** | GenUI 卡片（数据可视化） | 未测 | |
| **frontend-design** / **design-super-taste-frontend** | 前端/UI 设计 | 未测 | |
| **docx** | .docx 深度编辑（含 tracked changes/comments） | 未测 | |
| **pdf** | PyMuPDF + OCR | 未测 | |

#### B.5 飞书生态的非开放平台产物

| Skill | 能力 | 实测 | 编队价值 |
|---|---|---|---|
| **lark-apps（妙搭部署）** | 本地 HTML/静态站一键部署到妙搭 Miaoda，生成公网链接 | 未测 | ⭐ 应用快速发布 |
| **lark-minutes（AI 产物）** | 妙记总结/待办/章节/逐字稿 + 音视频上传转纪要 | 未测 | ⭐ 会议纪要自动化 |
| **mira-share-viewer** | 读取 mira.byteintl.net / bytedance.com 的 /share/ /chat/ 对话链接 | 未测 | |
| **mira-usage** | 本人的 Mira 用量统计 + Kaboo 排行榜 | ✅ 已测（27天/384会话/6.66亿token） | ⭐ Pi 成本治理数据源 |
| **mira-remote-browser** | 远程沙箱浏览器（表单/截图/爬取，含 JS 渲染） | 未测 | ⭐ 自动化数据采集 |
| **mira_system** | Mira 产品/合规/隐私知识库 | 未测 | |

#### B.6 编排与自动化

| Skill | 能力 | 实测 | 编队价值 |
|---|---|---|---|
| **mira-scheduler** | 定时任务 + 事件触发（群消息/@bot 触发自动化） | 未测 | ⭐⭐ Pi 调度补充 |
| **mira-chat-organizer** | 历史会话按主题聚类归 Project | ✅ 已测（拉了 7 天 23 条会话） | ⭐ 远端任务整理 |
| **ai-engineering-pm** | 规格驱动多 Agent 协作交付 | 未测 | |
| **SpecCoding (lume)** | spec.md → design → tasks → apply 全流程 | 未测 | |
| **skill-creator** / **find-skills** | Skill 全生命周期管理 | 未测 | |

---

## 三、编队集成定位（更新版）

### 3.1 Mira 在编队里的真实定位（修订）

**之前的认知**：Mira = 生图 + 代码/架构评审特化节点

**修正后的认知**：Mira = **字节内部业务系统的接入节点 + 用户长期工作记忆的载体 + 生成式 AI 中心**

具体四角色：

| 角色 | 能力 | 编队独占性 |
|---|---|---|
| **字节内部业务接入** | CIS/绩效/Aeolus/妙搭/妙记 AI 等内部系统 | ⭐ 编队唯一通道 |
| **长期工作记忆载体** | 跨设备 session 恢复 + mira-memory 召回 | ⭐ 编队唯一拥有用户半年工作上下文 |
| **私域语义检索** | one_context 跨系统语义搜索 | ⭐ 编队唯一语义检索能力 |
| **生成式 AI 中心** | 生图 + PPT + GenUI + 前端设计 | ⭐ 多模型多模态 |
| **代码/架构评审** | gpt5.6sol + opus4.8p 双审 | 与 Qoder 部分重叠 |

#### 关于"工具支持"的归因原则（2026-07-26 用户纠正）

**Mira 能调用某工具，是因为该工具做了 Mira 适配，不是 Mira 的能力**。

举例：
- c360 CLI 在 Mira 里能用，是因为 **c360 团队官方适配了 Mira**（飞书文档列出支持 Claudecode/Codex/Trae/Aily/Mira）
- lark-cli 系列、cis-cli 等同理——是工具方做了适配

**不要把工具的能力记成 Mira 的能力**。Mira 的能力是：被工具适配后，能调度该工具。

#### 关于"本机环境"的诚实声明（2026-07-26 用户纠正）

之前说"本机 lark-c360 被风控拦截 code=100001"——**code=100001 的真实根因未查清**。

可能的原因（未排除）：
- c360 后端安全检测（IP/UA/请求模式异常）
- 本机登录态需要刷新
- lark-c360 v1.2.4 的 bug（v1.2.5 可能修复）
- 网络环境（CorpLink VPN）

之前用"风控"一词概括是**模糊带过**，未来涉及本机工具阻塞时，必须查清根因再下结论，不能用"风控"糊弄。

### 3.2 任务路由策略（修订）

#### 操作飞书标准能力 → 不走 Mira
- 任何 lark-cli 能做的事（多维表格/日程/文档/IM/审批...）
- **走本地 lark-cli**（ZCode 自己跑，零成本，无 token 消耗）

#### 操作字节内部系统 → 走 Mira
- CIS 审批/报销/差旅查询
- 绩效/调薪数据
- Aeolus 数据分析
- 妙搭应用部署
- 妙记 AI 产物提取

#### 跨系统知识检索 → 走 Mira
- 任何"在公司文档/Wiki/群里找 XXX"的需求
- 走 Mira one_context（语义检索）
- 不走 lark-cli（只能精确查）

#### 召回历史工作上下文 → 走 Mira
- "我之前跟谁讨论过 XXX" / "上次那个方案的核心是啥"
- 走 Mira mira-memory-recall（长期记忆）
- 或 mira-chat-organizer（会话整理）

#### 生成式任务 → 走 Mira
- 生图（Nano Draw / gpt-image-2）
- PPT / GenUI / 前端设计
- 走 Mira（多模型多模态）

#### 代码/架构评审 → 按复杂度分流
- 默认：Qoder cantus（Cantus 模型）
- 复杂/需要双审：Mira gpt5.6sol + opus4.8p

---

## 四、关键约束与风险

### 4.1 不走 Mira 的情况（避免 token 浪费）

| 场景 | 原因 | 替代方案 |
|---|---|---|
| 操作飞书多维表格/文档/IM | lark-cli 等价能力 | 本地 lark-cli |
| 读取已知文档 ID 的内容 | lark-cli docs +fetch | 本地 lark-cli |
| 简单代码评审 | Qoder cantus | Qoder |
| 前端实现 | Kimi | Kimi |

### 4.2 Mira 调用成本

- Mira 是内部工具，`total_cost_usd` 始终为 0（不消耗预算）
- 但 token 消耗计入了你的 Mira 账号用量（27 天用了 6.66 亿 token，已属重度）
- **编队策略**：能本地做的不要走 Mira，保留 Mira 给独有能力用

### 4.3 安全与权限边界

- Mira 用你的飞书身份调用所有 Skill（权限 = 你本人）
- 写操作（CIS 提交审批/修改绩效数据等）需谨慎
- **编队红线**：Mira 不做任何"以你身份提交"的动作，只做查询和只读分析，写入需你确认

### 4.4 cookie 30 天过期

- Mira 登录 cookie 有效期 30 天（到 2026-08-24 左右）
- 过期后需手动重登（参考 `mira-integration-status.md` 登录踩坑记录）
- Pi 后续可以做 cookie 过期监控告警

---

## 五、待评估项（不阻塞当前）

详见 `specs/mira-deep-dive-backlog.md`（已落盘的深度挖掘待办清单）。

## 六、CSM 数据链路与风神看板发现限制（2026-07-26 实测）

### 6.1 完整 CSM 数据链路（已打通，2026-07-26）

**c360 CLI 官方支持 Mira 作为 Agent 工具**（飞书文档列出支持 Claudecode/Codex/Trae/Aily/Mira）。在 Mira 里安装 c360 CLI 并完成 OAuth 授权后，可正常调用。

```
[Mira 内 lark-c360 v1.2.5]   → 你名下所有客户（account_id + name）
    ↓
[lark-c360 tenant list]      → 每客户下的租户（display_id = F 码）
    ↓
[Mira aeolus-query]          → 用每个 F 码去风神拉使用数据
    ↓
[结构化落盘]                 → 你名下所有客户的活跃度/用量/健康度汇总
```

**已验证**：
- ✅ Mira 装 c360 CLI v1.2.5（路径 `/home/mira/.npm-global/bin/lark-c360`）
- ✅ 10 个 c360 skill 装到 `/home/mira/.agents/skills`
- ✅ 登录成功（林于炜，6876235310229880833，online 环境）
- ✅ 实测拉客户列表：total 12 条，返回前 3（歌尔生活/海尔集团/歌尔光学）

**关于本机 lark-c360 阻塞（code=100001）**：
- 本机调用 lark-c360 业务接口返回 code=100001（"安全检测未通过"）
- **根因未查清**（可能是登录态/版本/网络/请求模式，未排除任何一项）
- 之前用"风控"一词概括是模糊带过
- 本机路径阻塞**不影响 Mira 路径**——c360 在 Mira 里是独立调用，不经过本机

**剩余约束**：
- Mira 登录态有效期未知（可能需要定期重新授权）
- Mira 会话隔离性未验证（不同会话是否需要重新登录）

### 6.1.1 CSM 数据分层策略（用户裁决 2026-07-26）

**c360 为主，风神为辅**——明确数据获取优先级：

| 数据需求 | 走哪 | 理由 |
|---|---|---|
| **客户维度信息**（owner/CSM/付费状态/ARR/产品/服务单/跟进记录/商机）| **c360 优先** | c360 是客户主数据系统，权威完整 |
| 客户名下租户列表 + F 码 | **c360** | `lark-c360 tenant list` |
| **应用明细数据**（某租户的 Aily 额度/工作助手活跃/Nexus Bot DAU 等）| **风神补充** | 风神按 F 码 + 看板 ID 拉应用级数据 |
| 客户整体健康度评估 | **c360 为主 + 风神补充** | c360 给客户基本面，风神给应用使用深度 |

**编队调度约定**：
- CSM 任务默认先走 c360 拉客户维度数据
- 需要应用使用明细时，从 c360 拿到 F 码后调风神
- 不要直接跳到风神（会丢失客户维度上下文）

### 6.2 风神看板发现的硬限制（实测结论）

**风神没有"列出我有权限的看板"的公开 API**——这是物理限制，不是工具问题：

| 尝试的路径 | 结果 | 原因 |
|---|---|---|
| Mira aeolus-query + home URL | ❌ | home/dashboardList 路径不受 skill 支持 |
| Mira aeolus-query + dashboardList URL | ❌ | 同上 |
| Mira one_context 私域检索 | ❌ | 不索引个人风神操作日志 |
| 风神直连 API | ❌ | 需登录认证，且无公开"列看板"接口 |

**aeolus-query skill 仅支持三种页面**：
- `/dashboard/{id}` ✅（按 URL 拉单个看板数据）
- `/dataQuery`
- `/dataManage/detail/{id}`

**编队现实路径**：
- 看板 URL 清单：**一次性手动收集**（你在浏览器复制常用的，落盘成清单）
- 看板数据拉取：**Mira aeolus-query 自动跑**（已验证可行）
- 多租户查询：每个看板切租户 F 码跑（需 c360 解风控后批量拿 F 码）

### 6.3 已验证可拉的风神看板（CSM 常用）

| 看板 | URL | 状态 |
|---|---|---|
| 工作助手 & Aily 额度单租户信息查询 for CSM | `https://data.bytedance.net/aeolus/pages/dashboard/1151988?appId=1161&sheetId=1495137` | ✅ 已实测，7 报告 6 成功 1 超时，默认租户 FLM94RDKZBJ |

后续你提供更多看板 URL，追加到这张表。
