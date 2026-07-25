# 全局路线图 v1.0

> 签发: ZCode + Qoder（共创，经交叉对抗式论证）
> 裁定: 用户
> 日期: 2026-07-24
> 依据: 全量资产调研 + Qoder(cantus)架构分析 + Qoder客户端交叉论证
> 血统: 北极星v1.2终极目标 + Aetheris蓝图v1.11终局定义 + soul.yaml + Codex知识库战略洞察

## 终极目标（不变）

**用户只需制定战略和确认关键决策，其余一切围绕设定轨道自动运转。**

## 三层面

```
层面A: Aetheris 产品（身体）— 蓝图定义的产品本体
层面B: 编队协作系统（神经+免疫）— Pi+飞书+Qoder+漂移治理
层面C: 云端迁移（基础设施演进）— 本地资产→云端，本机轻量化
```

---

## 执行序列（经交叉论证修订）

### 第一优先：立即做（本周，C-0+ECS治理+密钥守卫）

| 序 | 动作 | 归属 | 依据 |
|---|---|---|---|
| 1 | **ECS加swap（2G）** | C-0 | 无swap+aetheris-backend 1.79GB+Pi常驻=OOM风险。OOM一次=整个协作底座停摆 |
| 2 | **修ECS时钟漂移（NTP）** | C-0 | 不只是卫生问题——飞书token/HMAC验签/回调都依赖正确时间。时钟错1-2天→验签失败 |
| 3 | **清孤儿cloudflared** | C-0 | 2个进程指向同一端口 |
| 4 | **本机Desktop明文密钥守卫** | 新增（Qoder盲区指出） | `Desktop\Aetheris\key\` 有ark/kimi/minimax/zai/deepseek明文key+.pem，比ECS风险更大。纳入T3密钥守卫设计 |
| 5 | **ECS+本机明文密钥脱敏** | C-0 | .claude/settings.json、.zcode/v2/config.json、credentials.json |

### 第二优先：并行推进（B-1 P0收尾 + A-1 W5.5数据流）

| 序 | 动作 | 归属 | 依赖 |
|---|---|---|---|
| 6 | **Mira/Kimi接入** | B-1⑥ | ⑥Mira阻塞于用户定触发方式 |
| 7 | **W5.5数据流闭环** | A-1 | 建真实客户account + 修feishu-matter-importer E18（填account_id）+ backfill value_score |
| 8 | **飞书回调/token时钟验证** | 新增 | 序2修时钟后，验证飞书回调/token是否正常（时钟可能是历史问题的根因） |

### 第三优先：Codex退役链（严格顺序）

| 序 | 动作 | 依赖 | 注意 |
|---|---|---|---|
| 9 | **Codex知识库→git独立仓库** | 用户已裁定方案乙 | 不灌入M05（15%成熟度）。M05成熟后再灌 |
| 10 | **Pipeline→ECS cron** | 序1+9 | 注意：lark-cli凭证差异(user vs bot)、路径/编码清洗、模型调用成本归属(避免重演99%额度教训)、产物写回走agent/pi分支 |
| 11 | **停Codex+修hook断链+配置归档** | 序10 | .codex/hooks.json引用.claude/hooks/，必须改向.zcode/hooks/（或Codex已停则废弃hook） |
| 12 | **.claude清理** | 序11 | 先脱敏ANTHROPIC_AUTH_TOKEN，再清理131M残留 |
| 13 | **QoderWork skill迁移后退役** | 独立 | 先把docx/pptx/pdf/frontend-design等skill迁入.agents共享库。短期产出类任务可路由给Qoder IDE客户端 |

### 第四优先：云端迁移

| 序 | 动作 | 依赖 | 注意 |
|---|---|---|---|
| 14 | **ECS升配8G** | 用户已批准 | 当前4G可能不够支撑远程开发负载 |
| 15 | **ZCode SSH远程工作空间** | 序1+14 | ECS上建独立工作目录+独立clone（绝不共享工作目录），验证编辑-commit-push链路 |
| 16 | **轻量本机终端** | 全部完成 | 本机只剩ZCode(SSH连ECS)+飞书+Obsidian+Qoder客户端+Trae SOLO PC |

### 第五优先：知识库建议的技术债（来自Codex知识库5份洞察）

| 序 | 动作 | 来源 | 状态 |
|---|---|---|---|
| 17 | **hermes-sidecar新鲜验证** | 知识库P0+Qoder交叉论证 | **不能直接删！** 知识库说零流量，但WO-0111审计说是核心组件。三步验证：①端口连接②7天日志③代码引用。零流量证实后先stop观察48h再卸载 |
| 18 | **修model-router 3个bug** | 知识库P0 | glm映射/minimax映射/ARK key 401。ECS health显示model_gateway=offline。需复现测试确认 |
| 19 | **统一skill canonical目录** | 知识库三份一致 | skill分散4处，canonical方案已有 |
| 20 | **飞书URL自动摄取** | 知识库最高ROI | ~80行TS，发链接即自动入库 |
| 21 | **知识库MCP server** | 知识库中期 | ~150行TS，任何agent零配置接入 |

---

## 架构裁定

### M19认知转译 vs Pi意图路由（两层）
- M19=Aetheris产品内语义解析能力（数据侧），可被任何调用方消费
- Pi=编队协调层，消费M19输出做路由决策
- Pi先用自己的轻量意图判断跑起来，不等M19成熟
- 接口先定（intent→route契约），实现各自演进

### P0进度口径（经Qoder客户端校正）
- ①CC→ZCode迁移✅ ②Pi部署✅ ③飞书桥接✅ ④Qoder SSE消费器✅ ⑤漂移治理✅
- 实际完成5/6，剩⑥Mira/Kimi接入
- 注：Qoder客户端07-23回执基于旧时间点判断④未开工，07-24已验证完成

---

## 待验证风险

1. **hermes-sidecar**：知识库建议删 vs WO-0111审计说是核心组件。矛盾未消解，必须新鲜验证
2. **model-router 3个bug**：知识库记录但未经复现测试确认。ECS model_gateway=offline可能是症状
3. **飞书回调时钟依赖**：修时钟后需验证飞书回调/token是否受影响（可能一直是隐患）
4. **Desktop明文密钥**：`Desktop\Aetheris\key\` 未进任何治理，Qoder客户端指出的最大盲区
5. **治理文档双镜像漂移**：git仓库governance/与本地.agent-collaboration\standards\镜像靠手动同步，建议Pi漂移体检纳入监控
6. **AFP成本监控缺位**：Pi大脑(GLM-5.2)+未来pipeline的模型消耗无监控。建议漂移体检卡片附额度快照

---

## 不做的事（Non-goals）

- 不自建知识库（蓝图修正案v1.2已裁定选Obsidian集成）
- 不做live session共享（已付过学费的并发风险）
- 不在M05成熟前灌入知识库
- 不直接删hermes-sidecar（必须先验证）
- 不让ZCode自己长能力（现阶段是他进化，亲属反哺）

---

## 版本历史

| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-07-24 | 全量资产调研+Qoder(cantus)架构分析+Qoder客户端交叉论证，共创定稿 |
| draft | 2026-07-24 | 初稿（基于部分信息，已废弃） |
