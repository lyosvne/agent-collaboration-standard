# 跨智能体知识库接入指南 (INTEGRATION.md)

本知识库遵循 Karpathy LLM Wiki 方法，所有智能体（Codex / Trae / Claude Code / 未来云端Agent）均可读写。

## 快速接入（3步）

### 1. 知道位置
知识库根目录:
```
C:\Users\Admin\Documents\Codex\knowledge-audit-2026-07\Knowledge\
```

### 2. 读规则
任何智能体首次进入此目录，必须先读:
1. `AGENTS.md` — 目录结构、命名规范、Lint规则、摄取流程
2. `README.md` — 页面导航入口

### 3. 读数据
- `wiki/` 目录下是提炼后的知识页面（Markdown + YAML frontmatter）
- `wiki/` 子目录按类别组织: agents/, projects/, rules/, insights/, skills/, oss-projects/
- 使用 `[[页面名]]` 格式做双向链接（Obsidian/任何Markdown工具可读）
- `raw/data-index.md` 指向原始审计数据文件
- `index.json` 是机器可读的全量页面索引

## 智能体分工协议

> 更新 2026-07-25：Codex退役，知识库迁入git仓库（agent-collaboration-standard/knowledge/）。
> 权限模型从"Codex单点管理员"改为"git仓库管理 + Pi定期调度摄取"。

| 智能体 | 职责 | 读写权限 |
|--------|------|----------|
| ~~Codex~~ | ~~知识库管理员（摄取/Lint/重构）~~ | **已退役** |
| **Pi** | 定期调度摄取Pipeline（cron触发→调度agent→结果写回git） | git仓库读写（经部署key） |
| **ZCode** | 主控，深度读写，知识库重构主力 | 读写全部 |
| **Qoder（Cloud Agent）** | 摄取执行者（被Pi调度时fetch/分析/建wiki） | 会话内读写（经Pi派发） |
| Trae | 项目开发时查阅知识库，更新项目状态 | 读写projects/和insights/ |
| 其他Agent | 通过WebFetch/git读取 | 只读 |

**摄取Pipeline新模式**（替代Codex原"Windows Task Scheduler每5小时"）：
- 触发：Pi cron定期触发 + 用户主动指令（"存知识库"）
- 执行：Pi调度Qoder Cloud Agent（或Kimi）做fetch→分析→建wiki
- 写回：结果提交到agent-collaboration-standard的knowledge/目录（走git分支+review）
- Lint：git pre-commit hook自动跑lint.js
- dashboard：定期cron跑build-dashboard.cjs重新生成

## 摄取知识（任何Agent收到新文章/资料时）

1. 将原始资料URL或内容放到 `raw/` 或记录来源
2. 读取现有wiki页面，不要重复创建
3. 拆解为独立知识点（不要整篇长摘要）
4. 每个知识点关联已有 `[[页面]]`
5. 创建/更新的wiki页面必须包含:
   - YAML frontmatter (title, tags, created, source)
   - `## 相关` section 列出关联页面链接
6. 运行 `node scripts/lint.js` 检查后退出

## 查询知识

### 方法1: 直接读Markdown（最简单）
所有页面是纯Markdown，直接文件读取即可。
```
wiki/insights/oss-fit-recommendations.md
wiki/oss-projects/mem0.md
```

### 方法2: 使用index.json（程序化）
```javascript
const index = JSON.parse(fs.readFileSync('index.json','utf8'));
// index.pages = [{path, title, tags, category, links: [...]}]
const memory = index.pages.filter(p => p.tags.includes('memory'));
```

### 方法3: grep搜索
```bash
rg "mem0" wiki/
```

### 方法4: Obsidian UI
人类用Obsidian打开此目录，Ctrl+O切换页面，Ctrl+G看图谱。

## 知识页面结构规范

```markdown
---
title: 页面标题
tags: [tag1, tag2]
created: YYYY-MM-DD
source: 来源说明
---

# 页面标题

正文内容，事实陈述，引用来源。

## 相关
- [[其他页面]]
- [[另一页面]]
```

## 关联的全局规范

本知识库遵守全局协作标准:
- `governance/unified-agent-collaboration-standard.md`（git 仓库真值，相对仓库根）
- 使用统一的 目标/范围/验证/风险/handoff 语言
- 项目级规则不覆盖全局红线

## 同步机制

- **硬同步点**: git commit（此知识库应纳入git版本控制）
- **上下文同步**: wiki/ 内Markdown文件是跨工具上下文载体
- 新Agent接入时，先读AGENTS.md + README.md + index.json，即可理解全貌

## 知识库规模（2026-07-19）

- 26个wiki页面
- 89个双向链接
- 0 orphan pages
- 覆盖: 智能体/项目/规则/洞察/技能/OSS项目
- 数据源: 323 OSS仓库代码扫描 + 489篇微信文章全文 + Aetheris代码审计 + ECS实查
