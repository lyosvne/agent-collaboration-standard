# 全量资产调研报告（ZCode 产出）

> 调研者: ZCode | 日期: 2026-07-24
> 范围: 本地协作资产 + GitHub代码 + ECS代码 + Codex知识库
> 性质: 事实采集，供 Qoder(cantus) 架构分析 + 路线图共创

## 一、本地协作资产盘点

### 总览

| 目录 | 状态 | 大小 | 最后修改 | 云端迁移 |
|---|---|---|---|---|
| .zcode\ | 活跃（主控） | 292M | 07-24 | 部分 |
| .claude\ | 待清理（CC已退役） | 131M | 07-22 | 否（残留待删） |
| .codex\ | **悬空**（裁定退役但活跃运行中） | 953M | 07-24 | 否 |
| .qoderwork\ | 半活跃（未真正退役） | 721M | 07-22 | 否 |
| .agents\ | 活跃（共享skills库） | 12M | 07-22 | 是（已有GitHub源） |
| .agent-collaboration\ | 活跃（治理真值） | 262K | 07-24 | 是（已有GitHub镜像） |
| Aetheris-clones\ | 活跃（6个clone） | 4.8G | 07-21 | 否（git clone） |
| Aetheris-link\ | 活跃（主仓库） | 1.1G | 07-24 | 是（master已同步） |
| Documents\trae_projects\ | 混合 | 352M+ | 07-01 | 部分 |

### 关键发现

1. **Codex 悬空**：裁定退役但今天仍在活跃运行（logs_2.sqlite-wal 07-24 14:46写入）。config.toml用火山方舟ark-code-latest。**无退役执行计划，无知识库归属方案，未纳入协作体系。**

2. **CC残留**：.claude/ 131M，projects占114M（已归档到.zcode/migrated-from-claude/）。settings.json含明文ANTHROPIC_AUTH_TOKEN。

3. **CC退役断链风险**：.codex/hooks.json 硬编码引用 .claude/hooks/context-monitor.py。删除.claude前必须先改codex hook路径→.zcode/hooks/。

4. **QoderWork未真正退役**：721M，.cache/.models 07-22仍有更新。skills有docx/pptx/pdf/frontend-design等Qoder专属skill，云端Qoder无等价物。

5. **明文密钥风险**：.claude/settings.json、.zcode/v2/config.json、.zcode/v2/credentials.json含明文token。云端迁移前必须脱敏。

6. **三个clone有未提交改动**：solo(31个)、qoder(3个)、trae(5个)，违反commit纪律。

7. **可清理约600M冗余**：.codex/.tmp/ 5份tectonic.exe(~240M) + trae_projects/Aetheris-link重复(352M)。

## 二、GitHub 仓库真实状态

### 基本信息
- 远程: github.com/lyosvne/Aetheris-link.git
- HEAD: c9627016 migrate(cc->zcode)
- 蓝图版本: v1.11 (2026-06-20)
- 当前Sprint: 8

### 代码规模
- 后端TS文件: 578个
- 前端TS/TSX文件: 178个
- 测试文件: 132个（但test:unit glob不含services/__tests__）
- 7月提交: 207条（开发活跃）

### 分支漂移
| 分支 | ahead | behind | 状态 |
|---|---|---|---|
| agent/zcode | 0 | 0 | ✅ 完全同步 |
| agent/claude | 13 | 273 | 落后较多 |
| agent/trae | 0 | 318 | 纯落后 |
| agent/solo | 1 | 1666 | 严重落后（远古fork） |
| agent/kimi/qoder/mira | 仅remote | ? | 本地无 |

### 完成度矩阵（current-source-of-truth.v0.3）
核心诊断："管道搭好无流水"——组件都在，数据流几乎没接通。
- M11 ModelRouter ~85% | M02 资源注册 ~85%
- M03 matters ~40%（去重=0，死代码）
- Echo智能体 ~35%（不消费memory，路由不传history）
- M19认知转译 ~25%（全正则，0 LLM）
- M05知识 ~15%（图谱nodes/edges=0，从未跑）

## 三、ECS 运行真值

### 服务状态（9个active）
- aetheris-backend: 1.79GB内存（最大消耗者）
- aetheris-hermes-sidecar: 348MB（运行2个月未重启）
- aetheris-openclaw: 267MB（运行3个月+）
- pi-server: 75MB | pi-feishu-bridge: 46MB
- pi-feishu-callback: 65MB | pi-dispatch-server: 12MB
- caddy: 66MB | aetheris-cloudflared: 31MB

### 资源
- 磁盘: 23G/40G used (60%)，16G可用
- 内存: 3.6G used / 4.1G available，**无swap**
- ECS代码落后master 3提交（docs类）

### 健康检查
- 6 healthy（sqlite/hermes/sidecar/api_key/business/feishu_token）
- 1 warning（storage: Vault 4文件0MB，知识图谱未跑）
- 1 offline（model_gateway未配置）

### 业务数据真值
- matters_total=134（pending 129, active 3, 本月新增2）
- knowledge_count=264（但图谱nodes=0，可能不同表）

### 问题
1. **时钟漂移**：ECS系统时间比真实快1-2天
2. **内存瓶颈**：无swap，aetheris-backend占1.79GB，OOM风险
3. **2个cloudflared进程**指向同一端口，疑似孤儿
4. **working tree dirty**：未跟踪文件+疑似误建的重复hermes-sidecar/

## 四、Codex 知识库

### 规模（index.json 2026-07-20）
- OSS仓库追踪: 304
- 微信文章全文: 526（分析489）
- Skills分类: 4238（19类别）
- Wiki页面: 87（双向链接89，0 orphan）
- 每日自动Pipeline: Windows Task Scheduler每5小时

### 战略洞察（5份核心）
1. first-principles.md — 本质需求三件事+四层架构+12条建议
2. action-roadmap.md — 4阶段落地（P0删sidecar/装skills/架构升级/治理）
3. adoption-decisions.md — S/A级采纳决策
4. automation-design.md — 6个自动化方案（前3个<100行减80%介入）
5. redundancy-audit.md — 4大冗余清理

### 归属未定
Codex知识库的331项目调研是核心资产，但归入Aetheris知识层(M05)还是独立维护，未裁定。每日自动Pipeline跑在本机Windows Task Scheduler，Codex退役后需迁移到ECS cron。

## 五、待Qoder(cantus)架构分析的四个问题

1. **M19认知转译 vs Pi意图路由**：是同一个东西还是两层？谁做主？（Qoder已有初步判断：两层，M19=语义解析能力，Pi=调度决策，Pi消费M19）

2. **Codex退役执行计划**：知识库归属（M05 vs 独立）、Pipeline迁移、配置清理、hook断链修复

3. **云端迁移路径**：ZCode SSH远程工作空间怎么配？ECS内存够不够？哪些资产先迁？

4. **路线图三层面优先级**：A(Aetheris产品W5.5) / B(编队P0收尾) / C(云端迁移)，哪个先哪个后，依赖关系
