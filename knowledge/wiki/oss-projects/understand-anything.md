---
title: Lum1104/Understand-Anything
tags: [oss-project, a, hermes-skill-extractor, ts]
created: 2026-07-20
updated: 2026-07-20
source: code-scan:Lum1104__Understand-Anything
stars: 75288
tier: A
module: hermes:skill-extractor
fit_score: 5.25
---

# Lum1104/Understand-Anything

> ⭐ 75,288 | ts | MIT | 最后更新: 2026-07-20

Graphs that teach > graphs that impress. Turn any code into an interactive knowledge graph you can explore, search, and ask questions about. Works with Claude Code, Codex, Cursor, Copilot, Gemini CLI, and more.

**Topics**: antigravity-skills, business-knowledge, claude-code, claude-skills, codebase-analysis, codex, codex-skills, developer-tools-ai-agent, gemini-cli-skills, karpathy-llm-wiki, knowledge-base, knowledge-graph, memory, opencode-skills, pi-agent, understandcode, vibe-coding

## 项目概览

| 指标 | 值 |
|------|-----|
| 代码文件 | 187 |
| 代码行数 | 30,826 |
| 包含技能 | 9 |
| 有测试 | ✅ |
| 有文档 | ✅ |
| 模块适配 | 技能提取/管理 (fit: 5.25) |

## 适配分析

目标模块: **技能提取/管理**

**参考价值** — A级，作为技能提取/管理的参考方案。

- 与Aetheris现有模块重合度: 38%
- 置信度优先级: A级-评估采纳
- 决策依据: 星级(⭐75,288) × 模块适配度(5.25) × 时效性(2026-07-20)

## 核心文件（架构入口）

- `understand-anything-plugin\packages\core\src\persistence\index.ts` (198行)
- `understand-anything-plugin\packages\core\src\index.ts` (131行)

## 关键代码注释（设计意图）

  - [understand-anything-plugin\packages\core\src\persistence\index.ts] Absolute path of the project's data directory (see resolveUaDirName). */
  - [understand-anything-plugin\packages\core\src\persistence\index.ts] Already relative — nothing to do.
  - [understand-anything-plugin\packages\core\src\persistence\index.ts] Inside the project root — make it relative.

## 集成建议

### 如何融入Aetheris
- **目标模块**: `hermes:skill-extractor`
- **优先级**: 🟡 高
- **行动**: 对比现有实现，选择性采纳优秀模式

### 与已有项目的关系
- 与现有skills体系（superpowers/mattpocock/anthropics）同类，择优合并






## 链接

- GitHub: [Lum1104/Understand-Anything](https://github.com/Lum1104/Understand-Anything)

---
*由gen-sa-wiki-pages.cjs自动生成，基于代码级扫描数据*
