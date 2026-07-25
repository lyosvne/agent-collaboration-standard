---
title: nashsu/llm_wiki
tags: [oss-project, a, knowledge, ts]
created: 2026-07-20
updated: 2026-07-20
source: code-scan:nashsu__llm_wiki
stars: 14918
tier: A
module: knowledge
fit_score: 8
---

# nashsu/llm_wiki

> ⭐ 14,918 | ts | NOASSERTION | 最后更新: 2026-07-20

LLM Wiki is a cross-platform desktop application that turns your documents into an organized, interlinked knowledge base — automatically. Instead of traditional RAG (retrieve-and-answer from scratch every time), the LLM incrementally builds and maintains a persistent wiki from your sources。

**Topics**: N/A

## 项目概览

| 指标 | 值 |
|------|-----|
| 代码文件 | 229 |
| 代码行数 | 69,083 |
| 包含技能 | 0 |
| 有测试 | ✅ |
| 有文档 | ❌ |
| 模块适配 | 知识图谱/RAG (fit: 8) |

## 适配分析

目标模块: **知识图谱/RAG**

**建议采纳** — A级高适配，可选择性集成到知识图谱/RAG。

- 与Aetheris现有模块重合度: 57%
- 置信度优先级: A级-评估采纳
- 决策依据: 星级(⭐14,918) × 模块适配度(8) × 时效性(2026-07-20)

## 核心文件（架构入口）

- `extension\Turndown.js` (804行)
- `mcp-server\src\index.ts` (516行)
- `mcp-server\src\api-client.ts` (459行)
- `extension\popup.js` (294行)

## 关键代码注释（设计意图）

  - [extension\Turndown.js] avoid match-at-end regexp bottleneck, see #370
  - [extension\Turndown.js] Node.TEXT_NODE or Node.CDATA_SECTION_NODE
  - [extension\Turndown.js] `text` might be empty at this point.
  - [extension\popup.js] Only retry idempotent reads across host aliases. Retrying POST /clip can
  - [extension\popup.js] duplicate a clip if the server handled the first request but the response
  - [extension\popup.js] failed before the extension received it.

## 集成建议

### 如何融入Aetheris
- **目标模块**: `knowledge`
- **优先级**: 🟡 高
- **行动**: 对比现有实现，选择性采纳优秀模式

### 与已有项目的关系





- 知识图谱/RAG方案参考

## 链接

- GitHub: [nashsu/llm_wiki](https://github.com/nashsu/llm_wiki)

---
*由gen-sa-wiki-pages.cjs自动生成，基于代码级扫描数据*
