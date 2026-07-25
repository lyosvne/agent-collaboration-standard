---
title: 第一性原理洞察
tags: [insight, first-principles, design, philosophy]
created: 2026-07-20
---

# 第一性原理洞察：你的智能体系统应该长什么样

## 你真正的需求是什么（本质，不是表述）

你说"梳理智能体、优化协作、降本提效、沉淀知识"。这些是手段。本质需求只有三个：

1. **我不想操心系统怎么运转，我只想下达意图，系统自己跑通**
2. **我看到的好东西，不要让我手动整理，它自己进知识库，下次能用**
3. **多个工具不要让我重复说同一件事，它们共享上下文**

所有冗余、复杂度、介入成本，都源于这三件事没做好。

---

## 当前系统的根本问题（是结构性冗余，不是bug）

### 问题1: 你是消息总线（最大的冗余）

现在的协作模式：你告诉Codex做X -> Codex做完 -> 你告诉Trae做Y -> 你告诉Codex同步。你充当了两个agent之间的消息路由。这是最脆弱的单点故障。

第一性原理：agent之间应该直接同步，不需要人转发。git commit是硬同步点，但人不是消息队列。

### 问题2: 知识要你主动喂，不是自动流

现在的流程：你看到文章 -> 复制URL -> 告诉Codex"存知识库" -> Codex整理。你是数据入口。

第一性原理：你是决策者，不是数据录入员。你在飞书给自己发消息这个动作，已经是"我要记住这个"的意图表达。系统应该自动捕获这个意图。

### 问题3: Skill四套并存的根因是没有Canonical Registry

不是因为你想搞四套，是因为没有人定义"唯一的skill目录在哪、格式是什么、谁是权威"。

第一性原理：一套skill，一个位置，一个格式，多agent消费。不需要"同步"，因为只有一份。

### 问题4: 规则是文档不是执行

START_HERE.md写了规则，但agent每次都要读、理解、判断。规则是死的文字。

第一性原理：规则应该是可执行的约束，不是需要阅读的文档。红线（删除/密钥/git push）应该被工具自动拦截，不靠agent"记住不要做"。

---

## 最小介入设计：四层架构

### 第一层：Canonical层（唯一真相）

- 技能: Knowledge/wiki/skills/ + Aetheris统一skill目录，SKILL.md格式
- 项目知识: Knowledge/wiki/projects/
- 协作规则: Knowledge/wiki/rules/ + AGENTS.md
- 每个信息只有一个权威位置，其他地方只是引用

### 第二层：自动同步层（去掉人这个消息总线）

- Git hooks: pre-commit自动跑lint.js，post-commit自动通知
- 飞书自聊自动摄取: feishu/event-listener检测到mp.weixin URL自动抓取拆解入库
- Agent启动自动加载: 每个agent启动时自动读Knowledge/index.json

### 第三层：自服务层（agent自维护，人只做决策）

- 自Lint: cron定期跑，orphan/dead link自动报告飞书
- 自更新: upstreams/每月git pull + diff检测，自动创建更新条目
- 自清理: 检测冗余代码自动生成insights报告
- 自修复: model-router检测401自动切换fallback

### 第四层：意图层（人的接口只有一个）

你只做两类事：
1. 下达意图："做X"——不需要知道哪个agent做、在哪做
2. 确认决策：agent提方案->你确认->执行

你不需要：告诉路径、提醒同步、解释规则、转发消息、整理知识、选择工具。

---

## 具体建议（按影响×可行性排序）

### 立即做（1天，减50%介入）

1. **删hermes-sidecar**: 代码+ECS+配置，两套runtime并存是结构性冗余
2. **统一skill目录**: 所有skill移到Aetheris单一skills/目录，Codex和hermes都从这里读
3. **飞书消息自动摄取**: feishu/event-listener加一条规则：收到mp.weixin URL自动抓取拆解入库

### 短期做（1周，减80%介入）

4. **agent启动hook**: AGENTS.md加"启动时读Knowledge/index.json"
5. **git commit自动Lint**: pre-commit hook跑lint.js
6. **知识库日报**: node-cron每天检查orphan/dead link/上游更新，推飞书

### 中期做（1个月，接近零介入）

7. **规则强制执行**: 红线做成pre-commit或guard脚本自动拦截
8. **model-router自愈**: 检测provider失败自动切换+通知+尝试刷新
9. **知识主动推荐**: agent查Knowledge/graph找相关知识，不需要你提醒

### 长期方向（3个月，成熟度最高）

10. **agent发现协议**: 新agent读固定文件自动发现知识库/规则/其他agent
11. **知识库即MCP**: 把Knowledge做成MCP server，任何支持MCP的agent零配置接入
12. **从知识库反向生成代码**: wiki/agents/定义自动生成Aetheris配置和prompt

---

## 为什么这是最优的

- **人工最少**: 人从"操作员"变成"决策者"，介入点缩减到只有确认/否决
- **冗余最低**: 每个信息一个位置，每个功能一个实现，没有副本就没有同步问题
- **成熟度最高**: 用成熟组件（Obsidian/git/MCP/pre-commit），不自建轮子
- **最直达需求**: 你是CSM不是程序员，时间花在客户和业务判断上，不是协调agent

## 相关
- [[automation-design]] (自动化实施方案)
- [[action-roadmap]]
- [[redundancy-audit]]
- [[oss-fit-recommendations]]
- [[collaboration-standard]]
- [[integration]]
