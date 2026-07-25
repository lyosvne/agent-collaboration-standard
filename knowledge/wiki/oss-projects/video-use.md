---
title: browser-use/video-use
tags: [oss-project, a, hermes-skill-extractor, py]
created: 2026-07-20
updated: 2026-07-20
source: code-scan:browser-use__video-use
stars: 17203
tier: A
module: hermes:skill-extractor
fit_score: 6.46
---

# browser-use/video-use

> ⭐ 17,203 | py | MIT | 最后更新: 2026-07-01

Edit videos with coding agents

**Topics**: N/A

## 项目概览

| 指标 | 值 |
|------|-----|
| 代码文件 | 7 |
| 代码行数 | 1,946 |
| 包含技能 | 2 |
| 有测试 | ❌ |
| 有文档 | ❌ |
| 模块适配 | 技能提取/管理 (fit: 6.46) |

## 适配分析

目标模块: **技能提取/管理**

**参考价值** — A级，作为技能提取/管理的参考方案。

- 与Aetheris现有模块重合度: 46%
- 置信度优先级: A级-评估采纳
- 决策依据: 星级(⭐17,203) × 模块适配度(6.46) × 时效性(2026-07-01)

## 核心文件（架构入口）

- `helpers\render.py` (660行)
- `helpers\timeline_view.py` (393行)
- `helpers\grade.py` (376行)
- `helpers\pack_transcripts.py` (207行)
- `helpers\transcribe.py` (176行)

## 关键代码注释（设计意图）

  - [helpers\render.py] -------- Subtitle style (bold-overlay, proven at 1920×1080 and 1080×1920) --
  - [helpers\render.py] MarginV is NOT taste — it is a platform safe-zone rule.
  - [helpers\render.py] TikTok / IG Reels / Shorts UI (caption, username, music, right-rail actions)
  - [helpers\timeline_view.py] -------- Frame extraction ---------------------------------------------------
  - [helpers\timeline_view.py] -------- Audio envelope (librosa if available, ffmpeg fallback) ------------
  - [helpers\timeline_view.py] Read the WAV manually — avoid librosa as a hard dep
  - [helpers\grade.py] Subtle baseline — barely perceptible cleanup. No color shift.
  - [helpers\grade.py] Use when auto-analysis isn't available or when you want a safe floor.

## 集成建议

### 如何融入Aetheris
- **目标模块**: `hermes:skill-extractor`
- **优先级**: 🟡 高
- **行动**: 对比现有实现，选择性采纳优秀模式

### 与已有项目的关系
- 与现有skills体系（superpowers/mattpocock/anthropics）同类，择优合并






## 链接

- GitHub: [browser-use/video-use](https://github.com/browser-use/video-use)

---
*由gen-sa-wiki-pages.cjs自动生成，基于代码级扫描数据*
