---
title: affaan-m/everything-claude-code
tags: [oss-project, a, hermes-skill-extractor, js]
created: 2026-07-20
updated: 2026-07-20
source: code-scan:affaan-m__everything-claude-code
stars: 231054
tier: A
module: hermes:skill-extractor
fit_score: 6
---

# affaan-m/everything-claude-code

> ⭐ 231,054 | js | N/A | 最后更新: 2026-07-17

Claude Code is an agentic coding tool that lives in your terminal, understands your codebase, and helps you code faster by executing routine tasks, explaining complex code, and handling git workflows - all through natural language commands.

**Topics**: N/A

## 项目概览

| 指标 | 值 |
|------|-----|
| 代码文件 | 305 |
| 代码行数 | 79,846 |
| 包含技能 | 200 |
| 有测试 | ✅ |
| 有文档 | ✅ |
| 模块适配 | 技能提取/管理 (fit: 6) |

## 适配分析

目标模块: **技能提取/管理**

**参考价值** — A级，作为技能提取/管理的参考方案。

- 与Aetheris现有模块重合度: 43%
- 置信度优先级: A级-评估采纳
- 决策依据: 星级(⭐231,054) × 模块适配度(6) × 时效性(2026-07-17)

## 核心文件（架构入口）

- `ecc2\src\session\daemon.rs` (1323行)
- `ecc2\src\notifications.rs` (637行)
- `ecc2\src\observability\mod.rs` (424行)
- `ecc2\src\comms\mod.rs` (157行)

## 关键代码注释（设计意图）

  - [ecc2\src\session\daemon.rs] [derive(Debug, Clone, Copy, Default, PartialEq, Eq)]
  - [ecc2\src\session\daemon.rs] Background daemon that monitors sessions, handles heartbeats,
  - [ecc2\src\session\daemon.rs] and cleans up stale resources.
  - [ecc2\src\notifications.rs] [derive(Debug, Clone, Copy, PartialEq, Eq)]
  - [ecc2\src\notifications.rs] [derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
  - [ecc2\src\notifications.rs] [derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
  - [ecc2\src\observability\mod.rs] [derive(Debug, Clone, Serialize, Deserialize)]
  - [ecc2\src\observability\mod.rs] [derive(Debug, Clone, PartialEq, Serialize, Deserialize)]

## 集成建议

### 如何融入Aetheris
- **目标模块**: `hermes:skill-extractor`
- **优先级**: 🟡 高
- **行动**: 对比现有实现，选择性采纳优秀模式

### 与已有项目的关系
- 与现有skills体系（superpowers/mattpocock/anthropics）同类，择优合并






## 链接

- GitHub: [affaan-m/everything-claude-code](https://github.com/affaan-m/everything-claude-code)

---
*由gen-sa-wiki-pages.cjs自动生成，基于代码级扫描数据*
