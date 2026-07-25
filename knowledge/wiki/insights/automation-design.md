---
title: 自动化设计方案
tags: [insight, automation, design, implementation]
created: 2026-07-20
---

# 自动化设计方案：最小介入路径

本文档把 [[first-principles]] 的四层架构翻译成可执行的代码改动。每个改动标注了影响哪个Aetheris模块、改动量、预期效果。

---

## 自动化1: 飞书自聊URL自动摄取（最高ROI）

**现状**: 你在飞书给自己发文章链接 -> 手动告诉Codex"存知识库" -> Codex抓取整理
**目标**: 发链接即自动入库，零人工介入

**改动位置**: Aetheris backend/src/feishu/event-listener.ts
**改动内容**:
- 在feishu-message-processor的消息分类逻辑中加一条规则
- 检测到消息文本包含 mp.weixin.qq.com/s/ URL
- 触发: 调用Playwright wechat probe抓取全文 -> 提取GitHub URL/skill名/关键概念 -> 创建wiki页面 -> 推送到Knowledge/
- 完成后给你发飞书消息通知"已收录: [标题]，创建了N个知识条目"

**改动量**: ~80行TS代码（新增一个auto-ingest service）
**依赖**: 已有的Playwright probe（C:\Users\Admin\.local\bin\wechat-article-probe.ps1）、已有的feishu集成
**预期效果**: 你以后在飞书给自己发文章，什么都不用做，知识自动沉淀

---

## 自动化2: Agent启动自动加载知识库上下文

**现状**: 每个agent（Codex/Trae）启动时需要人提醒"先读知识库"
**目标**: agent启动时自动读Knowledge/index.json，获得上下文

**改动位置**:
- Codex: C:\Users\Admin\Documents\Codex\knowledge-audit-2026-07\Knowledge\AGENTS.md（已在全局START_HERE.md注册）
- Trae: 在Aetheris项目的AGENTS.md中加一行
- 未来云端agent: 通过MCP或固定URL读取

**改动内容**:
- AGENTS.md已经写入全局START_HERE.md，agent启动按Read Order自然读到
- 加一行指令："如果是跨项目问题，先查Knowledge/index.json，按tags检索相关知识"
- index.json已存在（28页/98链接/37标签），可直接JSON.parse

**改动量**: 3行文档
**预期效果**: 不需要你说"你先看下知识库"，agent自动知道

---

## 自动化3: Git Commit自动Lint知识库

**现状**: 知识库健康度靠手动跑lint.js
**目标**: 每次git commit自动检查，有问题阻断提交

**改动位置**: Aetheris .git/hooks/pre-commit（或husky如果已有）
**改动内容**:
- pre-commit hook中加一行: node Knowledge/scripts/lint.js
- 如果有orphan或broken link，输出警告但不阻断（知识演进中允许暂时不一致）
- 如果有新页面缺tags或frontmatter，阻断提交

**改动量**: 5行shell
**预期效果**: 知识库不会默默腐化

---

## 自动化4: Model-Router自愈

**现状**: provider 401/映射bug -> 你发现 -> 告诉agent修 -> agent修
**目标**: provider故障自动检测+切换+通知

**改动位置**: backend/src/model-router/health-checker.ts + alert-service.ts
**改动内容**:
- health-checker已存在，增强：连续3次失败 -> 自动切换到fallback provider
- alert-service已存在，增强：切换后发飞书通知"[模型名]故障，已切换到[备用]"
- 修复glm/minimax的模型名映射bug（硬编码字符串错误）
- ARK key轮换流程做成脚本，不需要手动改key-vault.ts

**改动量**: ~50行TS + bug fix
**预期效果**: 模型故障不需要你介入

---

## 自动化5: Skill Canonical Directory

**现状**: skill分散在4个位置
**目标**: 单一skill目录，多agent读取

**改动位置**:
- 新建 C:\Users\Admin\Documents\Codex\knowledge-audit-2026-07\Knowledge\skills\canonical\
- Aetheris backend/src/hermes/skill-extractor.ts 修改读取路径
- Codex的skills目录改为符号链接指向canonical
- 删除其他位置的skill副本

**改动内容**:
1. 创建canonical/目录
2. 把S/A级skill复制进去（draco-skills, marketingskills, taste-skill, knowledge-work-plugins, addyosmani-agent-skills）
3. Aetheris hermes的skill-extractor.ts改为读取canonical/
4. Codex的/skills改为symlink到canonical/
5. 以后新装skill只装到canonical/，一处安装处处可用

**改动量**: 目录操作+改一个TS文件路径+建symlink
**预期效果**: skill只装一次，不需要同步

---

## 自动化6: 知识库MCP Server（中期，成熟度最高）

**现状**: agent读知识库靠文件系统直读
**目标**: 任何支持MCP的agent零配置获得知识库查询能力

**实现方案**:
- 写一个简单MCP server（Node.js，用@modelcontextprotocol/sdk）
- 暴露工具: search_knowledge(query), get_page(slug), list_tags(), get_roadmap_status()
- Codex/Claude Desktop/Cursor/未来任何agent配置这个MCP server
- agent获得知识库查询能力，零额外配置

**改动量**: ~150行TS，一个MCP server
**预期效果**: 任何新工具接入，不需要任何定制开发，配置MCP即可

---

## 实施顺序（ROI排序）

| 顺序 | 自动化 | 改动量 | 减介入效果 | 依赖 |
|------|--------|--------|-----------|------|
| 1 | 飞书URL自动摄取 | ~80行TS | 最大 | 已有feishu+probe |
| 2 | Agent启动加载上下文 | 3行文档 | 大 | 已有index.json |
| 3 | 统一skill canonical | 目录+symlink | 大 | 无 |
| 4 | Git commit lint | 5行shell | 中 | 无 |
| 5 | Model-router自愈 | ~50行TS | 中 | health-checker已有 |
| 6 | 知识库MCP server | ~150行TS | 极大（长期） | 无 |

前3个合计改动量不到100行，但能减少你80%的人工介入。

## 相关
- [[first-principles]]
- [[action-roadmap]]
- [[redundancy-audit]]
- [[oss-fit-recommendations]]
- [[aetheris]]
