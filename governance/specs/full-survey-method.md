# 全量资产调研方法

> 目标：为全局路线图建立完整事实基础。不基于部分信息出判断。

## 调研范围（四类全量资产）

### 资产1: Codex知识库（已盘点，需深读）
位置：C:\Users\Admin\Documents\Codex\knowledge-audit-2026-07\Knowledge\
已盘点：304 OSS仓库 + 489文章 + 4238 skills + 87 wiki页面
**调研重点**：战略洞察（first-principles / action-roadmap / adoption-decisions / automation-design / redundancy-audit）、S/A级采纳决策、技术选型依据

### 资产2: GitHub全量代码
位置：github.com/lyosvne/Aetheris-link.git
分支：master + agent/claude + agent/kimi + agent/qoder + agent/solo + agent/trae + agent/mira + agent/zcode
**调研重点**：master真实进度（不是文档说的进度，是代码说的）、各分支漂移量、核心模块真实完成度、技术债

### 资产3: ECS全量代码
位置：SSH root@aetherisonline.xyz
路径：/opt/pi-orchestrator/ + /opt/aetheris-controlplane-backend/ + /var/www/aetheris-frontend/ + /opt/aetheris-runtime/ + 其他
服务：所有 systemd 服务 + cron + Caddy 配置
**调研重点**：实际跑着什么、各服务健康度、代码vs部署漂移、运维债、资源占用

### 资产4: 本地协作资产（所有智能体）
```
C:\Users\Admin\.agent-collaboration\     协作治理（北极星/协议/分工/规格）
C:\Users\Admin\.zcode\                   ZCode配置/hooks/skills/AGENTS
C:\Users\Admin\.claude\                  CC配置（待退役，需盘点残留）
C:\Users\Admin\.codex\                   Codex配置（待退役，需盘点残留）
C:\Users\Admin\.qoderwork\               QoderWork（已退役，需确认残留）
C:\Users\Admin\Aetheris-link\            主仓库工作副本
C:\Users\Admin\Aetheris-clones\          各agent独立clone
C:\Users\Admin\.agents\                  共享skills库（4238+ skills）
C:\Users\Admin\Documents\trae_projects\  Trae项目 + agent-collaboration-standard clone
C:\Users\Admin\AGENTS.md                 全局规则
```
**调研重点**：每个智能体的配置/规则/工具/skills、哪些是活跃的、哪些是退役残留、哪些需要云端迁移

## 调研维度（每个资产统一提取）

对每项资产，产出：
1. **有什么**：资产清单（文件/目录/模块/配置项）
2. **什么状态**：完成度/活跃度/健康度/最后更新时间
3. **和谁有关**：依赖关系、关联资产
4. **缺什么**：计划了没做的、已知的断点/缺口
5. **要迁移吗**：是否涉及退役/迁移到云端、迁移目标

## 分工

### ZCode 负责
- 资产4（本地协作资产）——我本机，我能直接读
- 资产2（GitHub代码）——我已有clone，能git操作
- 资产1（Codex知识库）的盘点索引——读README/INTEGRATION/index.json，提取主题分类和战略洞察

### Qoder(cantus) 负责
- 资产3（ECS全量代码）——通过WebFetch读dispatch上下文 + 我把ECS信息喂给它做架构分析
- 资产1（Codex知识库）的深读——战略洞察的架构级解读、采纳决策的优先级判断
- 四个架构问题的分析（路线图末尾列的）

### 各自产出
统一格式的调研报告，存到：
- ZCode: C:\Users\Admin\.agent-collaboration\standards\specs\survey-zcode.md
- Qoder: 通过dispatch history落盘，ZCode拉取整合

### 共创
两份调研报告完成后：
1. ZCode整合成全局路线图v1.0（基于双方调研事实）
2. Qoder做架构审查
3. 用户裁定
