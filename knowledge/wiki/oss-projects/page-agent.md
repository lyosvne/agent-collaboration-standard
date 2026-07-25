---
title: alibaba/page-agent
tags: [oss-project, s, frontend, tsx]
created: 2026-07-20
updated: 2026-07-20
source: code-scan:alibaba__page-agent
stars: 27097
tier: S
module: frontend
fit_score: 10.95
---

# alibaba/page-agent

> ⭐ 27,097 | tsx | MIT | 最后更新: 2026-07-17

JavaScript in-page GUI agent. Control web interfaces with natural language.

**Topics**: agent, ai, ai-agents, browser-automation, javascript, mcp, typescript, web

## 项目概览

| 指标 | 值 |
|------|-----|
| 代码文件 | 152 |
| 代码行数 | 22,161 |
| 包含技能 | 0 |
| 有测试 | ✅ |
| 有文档 | ✅ |
| 模块适配 | 前端UI (fit: 10.95) |

## 适配分析

目标模块: **前端UI**

**优先采纳** — S级推荐，直接参考架构/代码用于Aetheris的前端UI模块。

- 与Aetheris现有模块重合度: 78%
- 置信度优先级: S级-直接参考
- 决策依据: 星级(⭐27,097) × 模块适配度(10.95) × 时效性(2026-07-17)

## 核心文件（架构入口）

- `packages\core\src\tools\index.ts` (203行)
- `packages\core\src\utils\index.ts` (144行)

## 关键代码注释（设计意图）

  - [packages\core\src\tools\index.ts] @note main loop will handle this one
  - [packages\core\src\tools\index.ts] try to subtract LLM calling time from the actual wait time
  - [packages\core\src\tools\index.ts] @todo extract_structured_data
  - [packages\core\src\utils\index.ts] reason is a DOMException AbortError.
  - [packages\core\src\utils\index.ts] Fetch /llms.txt for a URL's origin. Cached per origin, `null` = tried and not found. */
  - [packages\core\src\utils\index.ts] about:blank, data:, file:

## 集成建议

### 如何融入Aetheris
- **目标模块**: `frontend`
- **优先级**: 🔴 最高
- **行动**: 直接研究其核心架构，移植关键设计模式

### 与已有项目的关系




- 可作为前端UI参考/组件来源


## 链接

- GitHub: [alibaba/page-agent](https://github.com/alibaba/page-agent)

---
*由gen-sa-wiki-pages.cjs自动生成，基于代码级扫描数据*
