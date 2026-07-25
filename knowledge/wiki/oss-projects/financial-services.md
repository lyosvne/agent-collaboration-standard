---
title: anthropics/financial-services
tags: [oss-project, a, hermes-skill-extractor, py]
created: 2026-07-20
updated: 2026-07-20
source: code-scan:anthropics__financial-services
stars: 33610
tier: A
module: hermes:skill-extractor
fit_score: 7.35
---

# anthropics/financial-services

> ⭐ 33,610 | py | Apache-2.0 | 最后更新: 2026-06-26



**Topics**: N/A

## 项目概览

| 指标 | 值 |
|------|-----|
| 代码文件 | 17 |
| 代码行数 | 2,923 |
| 包含技能 | 117 |
| 有测试 | ✅ |
| 有文档 | ❌ |
| 模块适配 | 技能提取/管理 (fit: 7.35) |

## 适配分析

目标模块: **技能提取/管理**

**参考价值** — A级，作为技能提取/管理的参考方案。

- 与Aetheris现有模块重合度: 53%
- 置信度优先级: A级-评估采纳
- 决策依据: 星级(⭐33,610) × 模块适配度(7.35) × 时效性(2026-06-26)

## 核心文件（架构入口）

- `plugins\agent-plugins\pitch-agent\skills\ib-check-deck\scripts\extract_numbers.py` (306行)
- `plugins\vertical-plugins\financial-analysis\skills\ib-check-deck\scripts\extract_numbers.py` (306行)
- `plugins\agent-plugins\model-builder\skills\dcf-model\scripts\validate_dcf.py` (293行)
- `plugins\agent-plugins\pitch-agent\skills\dcf-model\scripts\validate_dcf.py` (293行)
- `plugins\vertical-plugins\financial-analysis\skills\dcf-model\scripts\validate_dcf.py` (293行)

## 关键代码注释（设计意图）

  - [plugins\agent-plugins\pitch-agent\skills\ib-check-deck\scripts\extract_numbers.py] usr/bin/env python3
  - [plugins\agent-plugins\pitch-agent\skills\ib-check-deck\scripts\extract_numbers.py] Remove commas and spaces
  - [plugins\agent-plugins\pitch-agent\skills\ib-check-deck\scripts\extract_numbers.py] Apply unit multipliers
  - [plugins\vertical-plugins\financial-analysis\skills\ib-check-deck\scripts\extract_numbers.py] usr/bin/env python3
  - [plugins\vertical-plugins\financial-analysis\skills\ib-check-deck\scripts\extract_numbers.py] Remove commas and spaces
  - [plugins\vertical-plugins\financial-analysis\skills\ib-check-deck\scripts\extract_numbers.py] Apply unit multipliers
  - [plugins\agent-plugins\model-builder\skills\dcf-model\scripts\validate_dcf.py] usr/bin/env python3
  - [plugins\agent-plugins\model-builder\skills\dcf-model\scripts\validate_dcf.py] Search for terminal growth and WACC values

## 集成建议

### 如何融入Aetheris
- **目标模块**: `hermes:skill-extractor`
- **优先级**: 🟡 高
- **行动**: 对比现有实现，选择性采纳优秀模式

### 与已有项目的关系
- 与现有skills体系（superpowers/mattpocock/anthropics）同类，择优合并






## 链接

- GitHub: [anthropics/financial-services](https://github.com/anthropics/financial-services)

---
*由gen-sa-wiki-pages.cjs自动生成，基于代码级扫描数据*
