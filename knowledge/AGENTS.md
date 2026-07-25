# Knowledge Base — AGENTS.md

本知识库遵循 Karpathy LLM Wiki 方法论，由 Codex 作为 AI 知识管理员维护。

## 目录结构

- `raw/` — 原始资料（审计数据、文章全文、JSON数据文件的引用指针）
- `wiki/` — AI提炼后的知识页面（Markdown，带双向链接和标签）
  - `agents/` — 智能体条目
  - `oss-projects/` — 开源项目条目
  - `skills/` — 技能条目
  - `projects/` — 自有项目条目
  - `rules/` — 规则和方法论条目
  - `insights/` — 洞察和分析结论
- `scripts/` — 维护脚本（搜索、Lint、看板生成）

## 知识管理规则

1. **每个wiki页面必须包含**:
   - 标题（H1）
   - 标签（`tags: [tag1, tag2]`，放在文件开头frontmatter）
   - 创建日期和来源引用
   - 关联链接（`[[其他页面]]`格式）

2. **摄取流程**:
   - 新资料先放raw/或记录来源URL
   - AI提炼时拆解为独立知识点，不要生成整篇长摘要
   - 每个知识点关联已有wiki页面
   - 对可变信息（如star数、版本），主动验证外部资料

3. **Lint审查规则**（定期执行）:
   - 检查重复页面
   - 检查孤立页面（无入链）
   - 检查失效链接
   - 检查过时信息
   - 检查缺少来源的结论
   - 检查相互矛盾的观点

4. **命名规范**:
   - 文件名用英文kebab-case: `hermes-agent.md`, `mem0-memory.md`
   - 中文标题在文件内H1
   - 标签用小写英文: `agent`, `memory`, `typescript`, `feishu`

## 本次审计来源

- 审计目录: `C:\Users\Admin\Documents\Codex\knowledge-audit-2026-07\`
- 报告: `reports\ultimate-report.md`
- 数据: `analysis/`目录下所有JSON文件
- 创建时间: 2026-07-19
