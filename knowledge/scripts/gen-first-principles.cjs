const fs = require('fs');
const path = require('path');
const kb = path.join(__dirname, '..');
const wiki = path.join(kb, 'wiki');

const firstPrinciples = `---
title: 第一性原理洞察
tags: [insight, first-principles, design, philosophy]
created: 2026-07-20
---

# 第一性原理洞察：你的智能体系统应该长什么样

## 你真正的需求是什么（不是你说的，是本质的）

你说"梳理智能体、优化协作、降本提效、沉淀知识"。这些是手段。本质需求只有三个：

1. **我不想操心系统怎么运转，我只想下达意图，系统自己跑通**
2. **我看到的好东西（文章/项目/skill），不要让我手动整理，它自己进知识库，下次能用**
3. **多个工具（Codex/Trae/未来云端Agent）不要让我重复说同一件事，它们共享上下文**

所有冗余、复杂度、介入成本，都源于这三件事没做好。

---

## 当前系统的根本问题（不是bug，是结构性冗余）

### 问题1: 你是消息总线（最大的冗余）

现在的协作模式：你→告诉Codex做X→Codex做完→你→告诉Trae做Y→你→告诉Codex同步。你充当了两个agent之间的消息路由。这是最脆弱的单点故障。

第一性原理：**agent之间应该直接同步，不需要人转发**。git commit是硬同步点，但人不是消息队列。

### 问题2: 知识要你主动喂，不是自动流

现在的流程：你看到文章→复制URL→告诉Codex"存知识库"→Codex整理。你是数据入口。

第一性原理：**你是决策者，不是数据录入员**。你在飞书给自己发消息的动作，已经是"我要记住这个"的意图表达。系统应该自动捕获这个意图，不需要你再口述一遍。

### 问题3: Skill四套并存的根因是没有Canonical Registry

Aetheris hermes有一套skill，Codex本地有一套，hermes-agent上游有一套，draco-skills有一套。不是因为你想搞四套，是因为没有人定义"唯一的skill目录在哪、格式是什么、谁是权威"。

第一性原理：**一套skill，一个位置，一个格式，多agent消费**。不需要"同步"，因为只有一份。

### 问题4: 规则是文档不是执行

.agent-collaboration/START_HERE.md写了规则，但agent每次都要读、要理解、要判断"这条规则适用于当前场景吗"。规则是死的文字。

第一性原理：**规则应该是可执行的约束，不是需要阅读的文档**。AGENTS.md的红线应该被工具自动强制（比如删除/密钥/git push的拦截），不是靠agent"记住不要做"。

---

## 最小介入设计：四层架构

从第一性原理出发，你需要的不是更多agent、更多skill、更多工具，是四层清晰的架构：

### 第一层：Canonical层（唯一真相）

| 内容 | 唯一位置 | 格式 |
|------|----------|------|
| 技能 | Knowledge/wiki/skills/ + Aetheris统一skill目录 | SKILL.md（已有标准） |
| 项目知识 | Knowledge/wiki/projects/ | Markdown + frontmatter |
| 协作规则 | Knowledge/wiki/rules/ + AGENTS.md | Markdown + 可执行pre-commit hook |
| 决策记录 | Knowledge/wiki/insights/ | Markdown |
| Agent定义 | Knowledge/wiki/agents/ | Markdown |

**原则**：任何信息只有一个权威位置。其他地方出现只是引用，不是副本。

### 第二层：自动同步层（去掉人这个消息总线）

- **Git hooks**: pre-commit自动跑lint.js检查知识库健康度；post-commit自动通知其他agent
- **飞书自聊监听**: Aetheris feishu/event-listener.ts已经在监听飞书消息。扩展它：检测到你发了mp.weixin URL，自动触发全文抓取→知识拆解→wiki页面创建，不需要你说"存入知识库"
- **agent启动时自动加载**: 每个agent启动脚本自动读Knowledge/AGENTS.md + index.json，不需要人提醒"先读规则"

### 第三层：自服务层（agent自维护，人只做决策）

- **自Lint**: scripts/lint.js定期自动跑（cron），发现orphan/broken link自动报告到飞书
- **自更新**: coordination/upstreams/的12个参考仓库，每月自动git pull + diff检测，有更新时自动创建"上游更新"wiki条目
- **自清理**: 检测到冗余（如hermes-sidecar代码存在但runtime不使用），自动在insights/下生成报告
- **自修复**: model-router检测到provider 401，自动尝试key轮换或切换fallback

### 第四层：意图层（人的接口只有一个）

你只需要做两类事：

1. **下达意图**："做X"、"帮我看Y"、"这个项目要怎么优化"——不需要知道哪个agent做、在哪做、怎么同步
2. **确认决策**：agent提出方案→你确认/修改→agent执行。你不需要执行，只需要判断。

**你不需要**：告诉agent路径、提醒同步、解释规则、转发消息、整理知识、选择工具。

---

## 具体建议（按影响×可行性排序）

### 立即做（1天，零成本，减50%介入）

1. **删掉hermes-sidecar**：代码+ECS+配置。它是结构性冗余的象征——两套agent runtime并存。
2. **统一skill目录**：把所有skill移到Aetheris的单一目录（如`skills/`），Codex和hermes runtime都从这里读。删除其他位置的skill副本。
3. **飞书消息自动摄取**：在feishu/event-listener.ts加一条规则：收到mp.weixin.qq.com URL→自动调wechat probe→存全文→拆解知识点→创建wiki页面。零人工介入。

### 短期做（1周，减80%介入）

4. **agent启动hook**：在Codex的AGENTS.md和Trae的配置里，加一行"启动时先读Knowledge/index.json"。这一步让agent自动有上下文，不需要你每次解释。
5. **git commit自动Lint**：在Aetheris的pre-commit hook里加`node Knowledge/scripts/lint.js`，知识健康度自动检查。
6. **知识库日报**：node-cron每天跑一次，检查orphan、dead link、上游更新，结果推送到飞书。

### 中期做（1个月，接近零介入）

7. **规则强制执行**：AGENTS.md里的红线（删除/密钥/git push），做成pre-commit hook或Codex guard脚本自动拦截，不靠agent自觉。
8. **model-router自愈**：health-checker检测到provider失败→自动切换→自动通知→自动尝试key刷新。
9. **知识图谱主动推荐**：当你在Codex里说"做X"，agent先查Knowledge/graph找相关知识，不需要你提醒"看看知识库"。

### 长期方向（3个月，成熟度最高）

10. **agent发现协议**：新agent（不管是Codex/Trae/云端）接入时，通过读一个固定URL/文件自动发现：知识库在哪、规则是什么、其他agent是谁、怎么通信。类似服务发现，但对agent。
11. **知识库即MCP**：把Knowledge做成一个MCP server，任何支持MCP的agent（Claude Desktop/Cursor/Codex）自动获得知识库查询能力，零配置。
12. **从知识库反向生成代码**：wiki/agents/里定义的agent行为，能自动生成Aetheris的配置和prompt，而不是手写。

---

## 为什么这样是最优的

**人工介入最少**：人的角色从"操作员"变成"决策者"，介入点从每个步骤缩减到只有确认/否决。

**冗余最低**：每个信息只有一个位置，每个功能只有一个实现。没有"同步"问题因为没有副本。

**成熟度最高**：优先用成熟组件（Obsidian做存储/git做同步/MCP做协议/pre-commit做强制），不自建轮子。

**最直达你的需求**：你是飞书CSM不是程序员，你的时间应该花在客户沟通和业务判断上，不是在协调agent和整理文件上。

## 相关
- [[action-roadmap]]
- [[redundancy-audit]]
- [[oss-fit-recommendations]]
- [[collaboration-standard]]
- [[integration]]
`;

fs.writeFileSync(path.join(wiki, 'insights', 'first-principles.md'), firstPrinciples, 'utf8');
console.log('first-principles.md written');
