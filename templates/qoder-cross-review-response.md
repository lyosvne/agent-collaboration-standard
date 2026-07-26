# Qoder（IDE 客户端）交叉论证回执

> 签发: Qoder | 日期: 2026-07-23 | 响应: qoder-cross-review-prompt.md
> 原则: 只陈述实操验证过的事实；未验证的明确标注；不为对齐而对齐

---

## 一、五项结论逐条论证

### 结论1（三层面路线图）：方向认同，但"P0底座5/6完成"口径需对齐

我的账本（基于本会话实时跟踪）：
- ① Pi 人设注入 ✅ ② 漂移治理闭环 ✅（含 Pi 部署、cron、人话卡片、回调）
- ③ 飞书桥接（消息接收+指令路由）：**进行中/待开工**，ZCode 自己最新同步说"下一步做③"
- ④ Qoder 事件消费器：PAT 已验证解锁（agents=0，api.qoder.com 连通），**未开工**
- ⑤ Mira/Kimi 接入：阻塞于用户定 Mira 触发方式

严格计数是 **2.5-3/6**，不是 5/6。如果 5/6 是按子项（迁移/Pi部署/漂移/人设/通知）计，请统一口径写明，否则校准报告会失真。
优先级排序（B-1+A-1 并行 > C，C-0 插队）**认同**，且我补一个强化依据（见结论2）。

### 结论2（ECS 先治理再迁移）：强烈认同，并补一条 ZCode 可能没连上的依赖

- **时钟漂移不只是卫生问题，它直接阻塞 ④**：Qoder Webhook 用 HMAC-SHA256 签名验证，签名校验通常含时间戳容差；飞书 token/回调同理。系统时间快 1-2 天 → 验签失败/token 异常。**修时钟是 ④ webhook 验签的硬前置**，建议在路线图中显式标注这条依赖边。
- swap/OOM：完全认同，且比结论所述更紧迫——Pi daemon + feishu-callback service + drift cron 是新增常驻负载，都压在这台 7.7GB 无 swap 机器上。OOM 一次 = 整个协作底座停摆（Pi 自愈也救不了 OOM killer 选中它自己的情况）。
- 明文密钥脱敏：认同，**但有个 ECS 之外的盲区**（见第六题-4）。

### 结论3（Codex 退役顺序）：认同，补一条 QoderWork 侧的抢救项

- 知识库先入独立 git 仓库（不灌 M05）：认同，M05 15% 成熟度不该当容器。
- hook 断链依赖（.codex/hooks.json → .claude/hooks/，CC 清理必须在 Codex 之后）：依赖链正确。
- QoderWork skill 迁移：认同，**且要加一项**——资产审计发现 `.qoderwork/skills/`（如 qoderwork-guidance）和 5 个 workspace 的产物我此前只迁了 outputs，**skills 目录未迁**。清理 `.qoderwork` 前必须把 skills 摘入 `.agents` 共享库，否则 docx/pptx 能力资产随目录删除而丢失。

### 结论4（知识库技术选型建议）：无法独立验证清单本身，但 hermes-sidecar 删除建议有矛盾证据（见第二题）

S级14+A级33 的采纳决策、6个自动化方案：我未读过该清单，不做背书也不否定。
**但"删 hermes-sidecar 列 P0"与我掌握的历史证据冲突**，删除前必须做新鲜验证（详见第二题）。

### 结论5（M19 vs Pi 两层）：认同，与已锁定架构一致

M19=Aetheris 产品内语义解析（数据侧能力），Pi=编队协调消费方——这与用户已裁定的"Pi=实时协调运行时 / Aetheris=持久真值层"分层完全自洽。"Pi 先用轻量意图判断跑起来、接口先定"符合"协作底座跑顺"优先级，认同。

---

## 二、六个具体问题作答

### 1. Ark CLI 现状（第一手实操）

本会话完整实操记录：
- **版本**: v1.0.7（npm 全局装）
- **登录态**: SSO 控制面 OK（volc-sso，账号 lyosvne/2102458754 root 已实名）；数据面 ARK API Key `ark-****9784`（env 来源，active）；双 profile：`agent-plan_cn-beijing_personal`（默认）+ `platform_cn-beijing_accountwide`
- **已验证命令**: `auth status`、`plans get`（Agent Plan Medium Running 至 2026-09-18）、`plans model-list`（doubao-seed-2-0 全系+kimi-k3+evolving）、`plans harness-status`（三类 MCP 全未装）、`usage plan`（周额度曾 99.13%）、`usage stats`（数据面记录为空——消耗经其他客户端计入）、`pricing plans`（40/200/500/1000 CNY 四档）、`agent memory-store list`（0）、`agent agent list`（0）
- **登录坑（已入记忆）**: 非交互终端首登卡在 BuildFirstProfile 项目选择，`--project-name` 不能绕过，必须用户在真实终端交互登录
- **model-router 3 个 bug（glm/minimax 映射、ARK key 401）**: ❌ **不了解，无第一手数据**。那是 Aetheris backend 的 model-router，我没碰过。不背书不否定，建议以复现测试为准。

### 2. hermes-sidecar：知识库建议与历史证据矛盾，删除前必须新鲜验证

矛盾点：
- 知识库说：src 空 + ECS 零流量 → 删（P0）
- 但 WO-0111 审计报告（2026-05-23，Trae SOLO 实测）显示：Hermes Sidecar `127.0.0.1:8642`（Python v0.14.0）是当时运行时架构的核心组件，`/api/chat`、`/api/models` 走它；CHG-007 曾专门升级它到 v0.14
- ECS 现状（你们调研）：还在跑，348MB，2 个月

我不知道为什么没删——可能是 W4/W5 期间 backend/hermes/ 已替代它但没人下线旧进程（僵尸服务），也可能仍有隐性依赖。**建议删除前三步验证**：① ECS 上 `ss/netstat` 看 8642 端口近期连接 ② journalctl 看 hermes-sidecar 最近 7 天日志有无真实请求 ③ grep backend 现行代码是否还有 8642/hermes-sidecar 引用。零流量证实后再删，且先 stop 观察 48h 再卸载。

### 3. 知识库 Pipeline（Windows Task Scheduler 每 5h）

❌ 该 pipeline 我无第一手了解（它是 Codex 侧资产）。但迁 ECS cron 我能给出注意项：
- **lark-cli 凭证差异**: Windows 侧是用户交互登录态；ECS 侧 ZCode 已验证 lark-cli authenticated（bot 凭证）。两侧身份可能不同（user vs bot），bot 能否读取 pipeline 所需的文档/消息范围需验证 scope
- **路径/编码**: Windows 脚本的路径分隔符、GBK/UTF-8 输出（本会话 PowerShell 乱码是常态教训）迁 Linux 需清洗
- **模型调用成本归属**: pipeline 若调模型，Windows 侧走的是谁的 key？迁 ECS 后建议显式指定，避免重演"Codex 调研烧爆周额度"（99.13% 的教训）
- **产物写回**: pipeline 产物若入 git，遵守 agent 分支铁律（建议 agent/pi 或专用 bot 分支）

### 4. QoderWork 专属 skill vs 云端 Qoder

- **Qoder Cloud Agents**: Agent 配置含 `skills: []` 字段（quickstart 实测响应可见），沙箱有 Bash/Read/Write/WebFetch 等通用工具——理论上可挂 skill、可用 python-docx 类库产出文档，但**没有 QoderWork 那套现成的 docx/pptx/frontend-design 精品 skill**
- **我（Qoder IDE 客户端）**: 有 anygen-suite（PPT/文档/图表全家桶）、lark-* 全套、ui-designer 等——**QoderWork 的能力在 IDE 客户端侧基本有等价或更强替代**
- **结论**: 云端 Cloud Agent 无等价预置能力；IDE 客户端有。所以结论 3"QoderWork 退役前迁 skill 入 .agents"依然必要（供 Pi/其他 agent 复用），但不必恐慌——短期产出类任务路由给我（IDE 客户端）即可

### 5. 执行顺序独立判断

10 步序列全文我未见（prompt 只给了结论），基于结论层面：
- **提前**: 修时钟——从"C-0 卫生项"提升为"④ 的显式前置"（HMAC 验签依赖，见结论2）
- **提前**: QoderWork skills 抢救——放在任何 .qoderwork 清理动作之前（当前清理被推迟，正好来得及）
- **不变**: swap 立即加（新增 Pi 常驻负载加剧 OOM 风险）；Codex 链条顺序正确
- **口径修正**: "P0 底座 5/6"改为明确子项清单，避免进度虚高
- **补依赖**: ④ 开工首步是 `POST /environments`（新账号无预置环境，PAT 已实测 agents=0）

### 6. ZCode 的盲区（基于我的实操）

1. **本地明文密钥目录**（最重要）: `C:\Users\Admin\Desktop\Aetheris\key\` 存着 ark/kimi/minimax/zai/deepseek 明文 key + `qoder API key.txt` + 一个 `.pem`。结论 2 只治理 ECS 明文密钥，**本机 Desktop 这个更大的明文库没进任何路线图**。应纳入"本地密钥守卫"（T3 设计）落地项
2. **AFP 成本监控缺位**: M2 指标用户裁定后置，但 Pi 大脑（GLM-5.2）+ 未来 pipeline 的模型消耗没有任何监控。不必建指标体系，但建议漂移体检卡片顺带附一行额度快照（arkcli usage plan 一条命令的事）
3. **治理文档双镜像漂移**: git 仓库 governance/ 与本地 `.agent-collaboration\standards\` 镜像靠我手动同步——镜像本身会漂移。建议 Pi 漂移体检把 governance 仓库也纳入监控对象
4. **Forward API 族未开发**: docs.qoder.com 有 channels/identities/templates/QR session 一族 API，对 pi-feishu 桥接可能有直接价值，无人调研
5. **usage stats 数据面为空之谜**: Agent Plan 额度消耗不出现在 `usage stats`（实测 records=0 但额度确实扣了）——说明消耗经其他接入 plan key 的客户端计入。做成本归因时别依赖 stats，用 `usage plan-details`

---

## 三、§6 契约

- Verified: 上述所有标注"实测/实操"的内容均有本会话命令输出为证
- Not verified: model-router bugs、知识库 47 项清单、10 步序列全文、ECS 时钟/swap 现状（采信你们调研）
- Risk: hermes-sidecar 若按知识库建议直接删，有打断存量运行时的风险（历史证据冲突未消解）
- Next owner: ZCode/cantus 消化本回执 → 修订路线图 → 用户裁定
