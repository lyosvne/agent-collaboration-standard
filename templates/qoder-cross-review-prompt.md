# 交叉对抗式论证提示词（交给 Qoder 客户端）

> 来源: ZCode 全量资产调研 + Qoder(cantus) 架构分析
> 用途: 请你对以下结论做交叉对抗式论证——找出错误、遗漏、风险，给出你的独立判断

## 背景

ZCode 和 Qoder(cantus) 完成了一次全量资产调研和架构分析，形成了以下结论。请你独立审查，特别关注：

1. 你在 Qoder 客户端里实际掌握的信息（Ark CLI 操作、知识库 Pipeline、前端开发经验）是否和这些结论一致
2. 有没有事实性错误
3. 有没有遗漏的风险
4. 执行顺序有没有依赖问题

## 待论证的结论

### 结论1：三层面路线图
- 层面A（Aetheris产品）：当前阻塞是W5.5数据流闭环（matters的account_id全null，前端看不到真实数据）
- 层面B（编队协作）：P0底座5/6完成，剩Mira/Kimi接入
- 层面C（云端迁移）：所有协作资产上云，本机轻量化
- 优先级：B-1(P0收尾) + A-1(W5.5) 并行 > C(云端迁移)。但C-0(ECS治理)插队立即做

### 结论2：ECS必须先治理再迁移
- 加swap（无swap，aetheris-backend占1.79GB，7.7GB机器OOM风险）
- 修时钟漂移（系统时间快1-2天）
- 清孤儿cloudflared（2个进程指向同一端口）
- 脱敏明文密钥

### 结论3：Codex退役有严格顺序
- 知识库先迁入git独立仓库（不灌入M05，因为M05才15%）
- Pipeline从Windows Task Scheduler迁到ECS cron
- 停用Codex → 修hook断链（.codex/hooks.json引用.claude/hooks/）→ 配置归档
- CC清理在Codex退役之后（因为hook依赖）
- QoderWork退役前先把docx/pptx/pdf/frontend-design等skill迁入.agents共享库

### 结论4：知识库已有完整技术选型建议
- S级14个+A级33个项目的逐项采纳决策已有
- 6个自动化方案已有（前3个<100行减80%介入）
- 知识库建议删hermes-sidecar（三份文档一致列为P0）、修model-router 3个bug、统一skill目录、飞书URL自动摄取、知识库MCP server
- 这些在ZCode的路线图里都没覆盖

### 结论5：M19认知转译 vs Pi意图路由是两层
- M19=Aetheris产品内的语义解析能力（可被任何调用方消费）
- Pi=编队协调层，消费M19输出做路由决策
- Pi先用自己的轻量意图判断跑起来，不等M19成熟，接口先定

## 请你回答的具体问题

1. **Ark CLI现状**：你在Qoder客户端里做过哪些Ark CLI操作？当前登录状态如何？已验证哪些命令？model-router的3个bug（glm映射/minimax映射/ARK key 401）你了解吗？

2. **hermes-sidecar**：知识库建议删除（src空+ECS零流量+backend已有hermes/）。但ECS调研显示它还在跑（348MB，运行2个月）。你知道为什么还没删吗？有依赖吗？

3. **知识库Pipeline**：每5小时的Windows Task Scheduler你了解吗？迁到ECS cron需要注意什么？lark-cli在Windows和ECS上的配置差异？

4. **QoderWork专属skill**：docx/pptx/pdf/frontend-design这些skill，云端Qoder（Cloud Agent）有等价能力吗？还是只有QoderWork本地客户端有？

5. **你对执行顺序的独立判断**：上面的10步执行序列，你有不同意见吗？特别是哪些步骤应该提前/延后？

6. **ZCode遗漏了什么**：基于你在Qoder客户端的实操经验，ZCode的调研有什么盲区？
