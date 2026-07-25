---
title: asgeirtj/system_prompts_leaks
tags: [oss-project, a, hermes-system-prompt, js]
created: 2026-07-20
updated: 2026-07-20
source: code-scan:asgeirtj__system_prompts_leaks
stars: 58950
tier: A
module: hermes:system-prompt
fit_score: 6
---

# asgeirtj/system_prompts_leaks

> ⭐ 58,950 | js | CC0-1.0 | 最后更新: 2026-07-19

Extracted system prompts from Anthropic - Claude Fable 5, Opus 4.8, Claude Code, Claude Design. OpenAI - ChatGPT GPT-5.6, Codex GPT-5.6, GPT-5.5. Google - Gemini 3.5 Flash, 3.1 Pro, Antigravity. xAI - Grok, Cursor, Copilot, VS Code, Perplexity, and more. Updated regularly.

**Topics**: ai, ai-agents, ai-prompts, anthropic, chatbot, chatgpt, claude, claude-code, codex, cursor, gemini, generative-ai, google, grok, llm, openai, prompt, prompt-engineering, system-prompt, system-prompts

## 项目概览

| 指标 | 值 |
|------|-----|
| 代码文件 | 3 |
| 代码行数 | 899 |
| 包含技能 | 9 |
| 有测试 | ❌ |
| 有文档 | ❌ |
| 模块适配 | 系统提示词构建 (fit: 6) |

## 适配分析

目标模块: **系统提示词构建**

**参考价值** — A级，作为系统提示词构建的参考方案。

- 与Aetheris现有模块重合度: 43%
- 置信度优先级: A级-评估采纳
- 决策依据: 星级(⭐58,950) × 模块适配度(6) × 时效性(2026-07-19)

## 核心文件（架构入口）

- `Anthropic\Claude Code\bundled-skills\deep-research\scripts\workflow-script.js` (351行)
- `Anthropic\Claude Code\bundled-skills\dataviz\scripts\validate_palette.js` (281行)
- `Anthropic\Claude Code\bundled-skills\dataviz\scripts\validate_palette.py` (267行)

## 关键代码注释（设计意图）

  - [Anthropic\Claude Code\bundled-skills\deep-research\scripts\workflow-script.js] deep-research: Scope → pipeline(Search → URL-dedup → Fetch+Extract) → 3-vote Verify → Synthesize
  - [Anthropic\Claude Code\bundled-skills\deep-research\scripts\workflow-script.js] Ported from bughunter architecture. WebSearch/WebFetch instead of git/grep.
  - [Anthropic\Claude Code\bundled-skills\deep-research\scripts\workflow-script.js] Question is passed via Workflow({name: 'deep-research', args: '<question>'}).
  - [Anthropic\Claude Code\bundled-skills\dataviz\scripts\validate_palette.js] ── thresholds ────────────────────────────────────────────────────────────────
  - [Anthropic\Claude Code\bundled-skills\dataviz\scripts\validate_palette.js] ΔE is Euclidean distance in OKLab ×100. The CVD thresholds are calibrated to
  - [Anthropic\Claude Code\bundled-skills\dataviz\scripts\validate_palette.js] the Machado-Oliveira-Fernandes (2009) severity-1.0 simulation below — the sim
  - [Anthropic\Claude Code\bundled-skills\dataviz\scripts\validate_palette.py] usr/bin/env python3
  - [Anthropic\Claude Code\bundled-skills\dataviz\scripts\validate_palette.py] ── thresholds ────────────────────────────────────────────────────────────────

## 集成建议

### 如何融入Aetheris
- **目标模块**: `hermes:system-prompt`
- **优先级**: 🟡 高
- **行动**: 对比现有实现，选择性采纳优秀模式

### 与已有项目的关系







## 链接

- GitHub: [asgeirtj/system_prompts_leaks](https://github.com/asgeirtj/system_prompts_leaks)

---
*由gen-sa-wiki-pages.cjs自动生成，基于代码级扫描数据*
