---
title: bradautomates/claude-video
tags: [oss-project, a, hermes-skill-extractor, py]
created: 2026-07-20
updated: 2026-07-20
source: code-scan:bradautomates__claude-video
stars: 9193
tier: A
module: hermes:skill-extractor
fit_score: 6.09
---

# bradautomates/claude-video

> ⭐ 9,193 | py | MIT | 最后更新: 2026-07-01

Give Claude the ability to watch any video. /watch downloads, extracts frames, transcribes, hands it all to Claude.

**Topics**: N/A

## 项目概览

| 指标 | 值 |
|------|-----|
| 代码文件 | 10 |
| 代码行数 | 2,537 |
| 包含技能 | 1 |
| 有测试 | ❌ |
| 有文档 | ❌ |
| 模块适配 | 技能提取/管理 (fit: 6.09) |

## 适配分析

目标模块: **技能提取/管理**

**参考价值** — A级，作为技能提取/管理的参考方案。

- 与Aetheris现有模块重合度: 44%
- 置信度优先级: A级-评估采纳
- 决策依据: 星级(⭐9,193) × 模块适配度(6.09) × 时效性(2026-07-01)

## 核心文件（架构入口）

- `skills\watch\scripts\frames.py` (757行)
- `skills\watch\scripts\setup.py` (365行)
- `skills\watch\scripts\download.py` (181行)
- `skills\watch\scripts\transcribe.py` (97行)
- `skills\watch\scripts\config.py` (75行)

## 关键代码注释（设计意图）

  - [skills\watch\scripts\frames.py] usr/bin/env python3
  - [skills\watch\scripts\frames.py] Keep scene-detection results once we have at least this many distinct shots.
  - [skills\watch\scripts\frames.py] Below this the video is effectively static (screen recording, talking head),
  - [skills\watch\scripts\setup.py] usr/bin/env python3
  - [skills\watch\scripts\setup.py] Whisper transcription fallback — used only when yt-dlp cannot get captions
  - [skills\watch\scripts\setup.py] (or when you point /watch at a local file with no subtitles).
  - [skills\watch\scripts\download.py] usr/bin/env python3
  - [skills\watch\scripts\download.py] yt-dlp may exit non-zero if a subtitle variant fails (e.g. 429) even when

## 集成建议

### 如何融入Aetheris
- **目标模块**: `hermes:skill-extractor`
- **优先级**: 🟡 高
- **行动**: 对比现有实现，选择性采纳优秀模式

### 与已有项目的关系
- 与现有skills体系（superpowers/mattpocock/anthropics）同类，择优合并






## 链接

- GitHub: [bradautomates/claude-video](https://github.com/bradautomates/claude-video)

---
*由gen-sa-wiki-pages.cjs自动生成，基于代码级扫描数据*
