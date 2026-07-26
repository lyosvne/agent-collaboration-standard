# O1主线：Codex退役链交接（交给Qoder客户端）

> 来源: ZCode | 日期: 2026-07-25
> 真值声明: agent-collaboration-standard @ commit 3e66a24
> 用途: O1主线是退役清理（Codex/CC/QoderWork）。Codex退役链里有两块适合你独立完成。
> 原则: 你做完产出方案，由用户裁定+ZCode实现。你不碰仓库/不删文件/不改系统。

## 背景

路线图O1（基座就绪）退出条件之一：**退役清理完成（Codex/CC/QoderWork退役收尾，知识库归属已定）**。

退役有严格顺序（经ZCode+Qoder cantus架构分析+你交叉论证定稿）：
1. 知识库先迁入git独立仓库（用户已裁定方案乙：不灌M05，独立维护）
2. Pipeline从Windows Task Scheduler迁到ECS cron
3. 停用Codex + 修hook断链 + 配置归档
4. .claude清理（在Codex之后，因hook依赖）
5. QoderWork skill迁移后退役

ZCode负责本机操作（hook修改、配置归档、停用流程）。**以下两块适合你独立完成方案设计**——你Codex客户端有第一手实操经验，且知识库是你的"管辖地盘"（INTEGRATION.md指定Codex=知识库管理员）。

路线图全文：`https://aetherisonline.xyz/dispatch/roadmap`（WebFetch可读）

---

## 任务1：知识库迁移方案细化（git独立仓库）

### 背景
Codex知识库位置：`C:\Users\Admin\Documents\Codex\knowledge-audit-2026-07\Knowledge\`
规模：304 OSS仓库 + 489文章 + 4238 skills + 87 wiki页面 + 5份战略洞察
用户裁定方案乙：迁入git独立仓库，不灌M05（M05才15%成熟度），M05成熟后再灌。

### 已知约束
- 知识库有每日自动Pipeline（Windows Task Scheduler每5小时跑）
- INTEGRATION.md定义的接入权限：Codex=管理员读写全部，Trae=读写projects+insights，其他=只读
- 仓库已有 `.skill-lock.json`（145个skill的github源记录）
- reports/目录有大文件（full-audit-report.md 604KB等）

### 你的任务
1. **设计git仓库结构**：
   - 新仓库名建议（如 `codex-knowledge-vault` 或并入agent-collaboration-standard的子目录？）
   - 目录结构如何组织（保留wiki/projects/agents/rules/insights/raw/scripts/reports的现有结构？）
   - 哪些进git，哪些不进（reports/的大文件？raw/原始数据？.skill-lock.json的skill源？）
   - .gitignore怎么写（排除临时产物/缓存）

2. **接入权限迁移**：
   - INTEGRATION.md的权限分工（Codex管理员/Trae读写/其他只读）怎么在新仓库落地？
   - 现在Codex退役后，谁接任"知识库管理员"？（Pi？ZCode？还是改为git权限管理，无单点管理员）

3. **与M05未来灌入的接口**：
   - 现在独立维护，未来M05成熟时怎么灌入？
   - 需要预留什么数据格式/接口？（如frontmatter标记category/tier，方便M05按类别灌入）

### 产出
**迁移方案文档**：
```
[PROPOSAL] 知识库迁移方案
- 仓库名：xxx
- 目录结构：xxx
- 进git：xxx / 不进：xxx
- .gitignore：xxx
- 权限模型：xxx（谁读谁写）
- M05灌入接口：xxx（预留什么）
- 迁移步骤：xxx（按顺序，每步可验证）
- 风险：xxx
```

**标注 `[NEED-USER]` 的决策点**（如新仓库名、是否并入现有仓库）。

---

## 任务2：Pipeline迁移注意项细化

### 背景
知识库每日自动Pipeline：Windows Task Scheduler每5小时跑（任务名 `KnowledgeAudit-DailyPipeline`）。
需迁到ECS cron。但有几个差异点你07-25回执已指出：
- lark-cli凭证差异（Windows交互登录 vs ECS bot凭证）
- 路径/编码清洗（Windows GBK/路径分隔符 → Linux）
- 模型调用成本归属（避免重演99%额度教训）
- 产物写回（遵守agent分支铁律）

### 你的任务
基于你对Pipeline的了解（虽然你说无第一手了解，但INTEGRATION.md和scripts/你能读到），细化迁移注意项：

1. **Pipeline实际做什么**（读scripts/看脚本逻辑）：
   - 输入：从哪拉数据（飞书消息？GitHub？微信文章？）
   - 处理：跑哪些步骤（抓取/分析/分类/wiki更新）
   - 输出：产出什么（daily-YYYY-MM-DD.md？index.json？）

2. **迁移到ECS的具体障碍**：
   - lark-cli在ECS的scope是否够（bot凭证能读pipeline所需的消息范围吗）
   - Pipeline如果调模型，Windows侧走谁的key？迁ECS后key从哪来？
   - Windows专属依赖（PowerShell脚本？.ps1？wsf？）在Linux怎么替代

3. **迁移后验证方案**：
   - 跑通一个完整周期怎么验证
   - 失败降级（Pipeline挂了不影响系统其他部分）

### 产出
**Pipeline迁移注意项文档**：
```
[FINDING] Pipeline实际逻辑：xxx（输入/处理/输出）
[OBSTACLE] 迁移障碍清单：
- 障碍1：xxx（解决方案）
- 障碍2：xxx
[VERIFICATION] 迁移后验证方案：xxx
[RISK] 如果不迁/迁失败的后果：xxx
[NEED-USER] 需要用户裁定的：xxx
```

---

## 协作约定

- **产出位置**：写到 `C:\Users\Admin\.agent-collaboration\templates\qoder-codex-retirement-response.md`
- **真值声明**：回执首部声明你读的governance commit hash（3e66a24）
- **不碰红线**：不删文件/不改密钥/不push/不改系统配置/不动知识库内容
- **需要ZCode配合时**：在回执里标注 `[NEED-ZCODE]`
- **需要用户裁定**：标注 `[NEED-USER]`

## 不做的事
- 不做hermes-sidecar验证（那是层面A的事，不在O1）
- 不做model-router诊断（知识库建议，未纳入路线图）
- 不直接执行迁移（只出方案，等用户授权后ZCode实现）

## 优先级
任务1（知识库迁移方案）和任务2（Pipeline注意项）可并行，都是方案设计不依赖彼此。
