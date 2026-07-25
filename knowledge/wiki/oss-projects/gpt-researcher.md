---
title: assafelovic/gpt-researcher
tags: [oss-project, a, frontend, py]
created: 2026-07-20
updated: 2026-07-20
source: code-scan:assafelovic__gpt-researcher
stars: 28432
tier: A
module: frontend
fit_score: 7.66
---

# assafelovic/gpt-researcher

> ⭐ 28,432 | py | Apache-2.0 | 最后更新: 2026-07-18

An autonomous agent that conducts deep research on any data using any LLM providers

**Topics**: agent, ai, automation, deepresearch, llms, mcp, mcp-server, python, research, search, webscraping

## 项目概览

| 指标 | 值 |
|------|-----|
| 代码文件 | 237 |
| 代码行数 | 35,487 |
| 包含技能 | 1 |
| 有测试 | ❌ |
| 有文档 | ✅ |
| 模块适配 | 前端UI (fit: 7.66) |

## 适配分析

目标模块: **前端UI**

**参考价值** — A级，作为前端UI的参考方案。

- 与Aetheris现有模块重合度: 55%
- 置信度优先级: A级-评估采纳
- 决策依据: 星级(⭐28,432) × 模块适配度(7.66) × 时效性(2026-07-18)

## 核心文件（架构入口）

- `backend\server\app.py` (468行)
- `cli.py` (363行)

## 关键代码注释（设计意图）

  - [backend\server\app.py] Suppress Pydantic V2 migration warnings
  - [backend\server\app.py] Add the parent directory to sys.path to make sure we can import from server
  - [backend\server\app.py] MongoDB services removed - no database persistence needed
  - [cli.py] =============================================================================
  - [cli.py] =============================================================================
  - [cli.py] Enables the use of newlines in the help message

## 集成建议

### 如何融入Aetheris
- **目标模块**: `frontend`
- **优先级**: 🟡 高
- **行动**: 对比现有实现，选择性采纳优秀模式

### 与已有项目的关系




- 可作为前端UI参考/组件来源


## 链接

- GitHub: [assafelovic/gpt-researcher](https://github.com/assafelovic/gpt-researcher)

---
*由gen-sa-wiki-pages.cjs自动生成，基于代码级扫描数据*
