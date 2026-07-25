---
title: anthropics/claude-plugins-official
tags: [oss-project, s, hermes-skill-extractor, py]
created: 2026-07-20
updated: 2026-07-20
source: code-scan:anthropics__claude-plugins-official
stars: 32318
tier: S
module: hermes:skill-extractor
fit_score: 8.72
---

# anthropics/claude-plugins-official

> ⭐ 32,318 | py | Apache-2.0 | 最后更新: 2026-07-19

Official, Anthropic-managed directory of high quality Claude Code Plugins.

**Topics**: claude-code, mcp, skills

## 项目概览

| 指标 | 值 |
|------|-----|
| 代码文件 | 46 |
| 代码行数 | 12,895 |
| 包含技能 | 30 |
| 有测试 | ✅ |
| 有文档 | ❌ |
| 模块适配 | 技能提取/管理 (fit: 8.72) |

## 适配分析

目标模块: **技能提取/管理**

**优先采纳** — S级推荐，直接参考架构/代码用于Aetheris的技能提取/管理模块。

- 与Aetheris现有模块重合度: 62%
- 置信度优先级: S级-直接参考
- 决策依据: 星级(⭐32,318) × 模块适配度(8.72) × 时效性(2026-07-19)

## 核心文件（架构入口）

- `external_plugins\telegram\server.ts` (1039行)
- `external_plugins\discord\server.ts` (901行)
- `external_plugins\imessage\server.ts` (876行)
- `plugins\code-modernization\workflows\extract-rules.js` (372行)
- `external_plugins\fakechat\server.ts` (296行)

## 关键代码注释（设计意图）

  - [external_plugins\telegram\server.ts] Load ~/.claude/channels/telegram/.env into process.env. Real env wins.
  - [external_plugins\telegram\server.ts] Plugin-spawned servers don't get an env block — this is where the token lives.
  - [external_plugins\telegram\server.ts] Token is a credential — lock to owner. No-op on Windows (would need ACLs).
  - [external_plugins\discord\server.ts] Load ~/.claude/channels/discord/.env into process.env. Real env wins.
  - [external_plugins\discord\server.ts] Plugin-spawned servers don't get an env block — this is where the token lives.
  - [external_plugins\discord\server.ts] Token is a credential — lock to owner. No-op on Windows (would need ACLs).
  - [external_plugins\imessage\server.ts] <reference types="bun-types" />
  - [external_plugins\imessage\server.ts] SMS sender IDs are spoofable; iMessage is Apple-ID-authenticated. Default

## 集成建议

### 如何融入Aetheris
- **目标模块**: `hermes:skill-extractor`
- **优先级**: 🔴 最高
- **行动**: 直接研究其核心架构，移植关键设计模式

### 与已有项目的关系
- 与现有skills体系（superpowers/mattpocock/anthropics）同类，择优合并






## 链接

- GitHub: [anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official)

---
*由gen-sa-wiki-pages.cjs自动生成，基于代码级扫描数据*
