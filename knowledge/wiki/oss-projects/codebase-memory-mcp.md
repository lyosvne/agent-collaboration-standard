---
title: DeusData/codebase-memory-mcp
tags: [oss-project, a, hermes-memory, c]
created: 2026-07-20
updated: 2026-07-20
source: code-scan:DeusData__codebase-memory-mcp
stars: 32953
tier: A
module: hermes:memory
fit_score: 7
---

# DeusData/codebase-memory-mcp

> ⭐ 32,953 | c | MIT | 最后更新: 2026-07-19

High-performance code intelligence MCP server. Indexes codebases into a persistent knowledge graph — average repo in milliseconds. 158 languages, sub-ms queries, 99% fewer tokens. Single static binary, zero dependencies.

**Topics**: aider, ast, claude-code, code-analysis, code-intelligence, codex, cursor, cypher, developer-tools, gemini-cli, graph-visualization, kilocode, knowledge-graph, mcp, mcp-server, model-context-protocol, opencode, sqlite, tree-sitter, windsurf

## 项目概览

| 指标 | 值 |
|------|-----|
| 代码文件 | 463 |
| 代码行数 | 97,316 |
| 包含技能 | 0 |
| 有测试 | ✅ |
| 有文档 | ✅ |
| 模块适配 | 记忆管理 (fit: 7) |

## 适配分析

目标模块: **记忆管理**

**参考价值** — A级，作为记忆管理的参考方案。

- 与Aetheris现有模块重合度: 50%
- 置信度优先级: A级-评估采纳
- 决策依据: 星级(⭐32,953) × 模块适配度(7) × 时效性(2026-07-19)

## 核心文件（架构入口）

- `pkg\go\cmd\codebase-memory-mcp\main.go` (344行)
- `graph-ui\src\App.tsx` (136行)

## 关键代码注释（设计意图）

  - [pkg\go\cmd\codebase-memory-mcp\main.go] codebase-memory-mcp — Go installer wrapper.
  - [pkg\go\cmd\codebase-memory-mcp\main.go] On first run, downloads the pre-built binary for the current platform from
  - [pkg\go\cmd\codebase-memory-mcp\main.go] GitHub Releases, caches it, and replaces the current process with it.

## 集成建议

### 如何融入Aetheris
- **目标模块**: `hermes:memory`
- **优先级**: 🟡 高
- **行动**: 对比现有实现，选择性采纳优秀模式

### 与已有项目的关系

- 与claude-mem/mem0/lat.md竞争记忆层方案





## 链接

- GitHub: [DeusData/codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp)

---
*由gen-sa-wiki-pages.cjs自动生成，基于代码级扫描数据*
