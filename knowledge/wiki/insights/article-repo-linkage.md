---
title: 文章到项目深度关联分析
tags: [insight, articles, linkage, evidence]
created: 2026-07-20
source: 489-wechat-articles-fulltext
---

# 文章到项目深度关联分析

> 基于489篇微信公众号文章全文分析，提取OSS项目引用并与代码扫描结果交叉校准

## 统计概览

| 指标 | 值 |
|------|-----|
| 文章总数 | 489 |
| 提及OSS项目的文章 | 174 |
| 提及skill的文章 | 140 |
| 不同项目被提及 | 296 |
| 项目推荐类文章 | 446 |
| 技能包类文章 | 427 |

## 多源校准原则

按你的要求：置信度不高的反复多源校准。优先级：
1. **文章提及次数多** → 社区共识强
2. **星级高** → 项目成熟度高
3. **时间近** → 时效性好
4. **文章类型为project_recommend** → 专门推荐，置信度高

## 高频提及项目（≥2次）与星级校准

| 项目 | 提及次数 | 验证Tier | ⭐Stars | 模块适配 | 置信度 |
|------|----------|----------|---------|----------|--------|
| obra/superpowers | 9 | A | 257,687 | hermes:skill-extractor | 高 |
| Leonxlnx/taste-skill | 7 | A | ? | frontend | 高 |
| affaan-m/everything-claude-code | 5 | A | 231,054 | hermes:skill-extractor | 高 |
| nextlevelbuilder/ui-ux-pro-max-skill | 5 | A | 107,872 | frontend | 高 |
| mattpocock/skills | 4 | A | 177,801 | hermes:skill-extractor | 高 |
| colbymchenry/codegraph | 4 | A | 60,929 | knowledge | 高 |
| addyosmani/agent-skills | 4 | B | ? | hermes:skill-extractor | 高 |
| NousResearch/hermes-agent | 4 | S | 217,354 | hermes:agent-loop | 高 |
| anthropics/claude-plugins-official | 4 | S | 32,318 | hermes:skill-extractor | 高 |
| nashsu/llm_wiki | 3 | A | 14,918 | knowledge | 中高 |
| Lum1104/Understand-Anything | 3 | A | 75,288 | hermes:skill-extractor | 中高 |
| stablyai/orca | 3 | A | 22,601 | hermes:agent-loop | 中高 |
| DeusData/codebase-memory-mcp | 3 | A | 32,953 | hermes:memory | 中高 |
| JCodesMore/ai-website-cloner-template | 3 | A | 28,879 | hermes:agent-loop | 中高 |
| KKKKhazix/khazix-skills | 3 | B | 17,430 | knowledge | 中高 |
| shanraisshan/claude-code-best-practice | 3 | B | 63,138 | hermes:context | 中高 |
| bytedance/deer-flow | 3 | B | 77,391 | frontend | 中高 |
| tinyhumansai/openhuman | 3 | B | 35,126 | hermes:agent-loop | 中高 |
| CloakHQ/CloakBrowser | 3 | B | 28,632 | hermes:context | 中高 |
| penpot/penpot | 3 | B | 56,945 | frontend | 中高 |
| calesthio/OpenMontage | 3 | B | 40,108 | hermes:tool-orchestration | 中高 |
| phuryn/pm-skills | 3 | C | 24,057 | hermes:skill-extractor | 中高 |
| VoltAgent/awesome-design-md | 3 | C | 103,271 | frontend | 中高 |
| kangarooking/cangjie-skill | 3 | D | ? | hermes:skill-extractor | 中高 |
| abhigyanpatwari/GitNexus | 3 | S | 44,353 | hermes:skill-extractor | 中高 |
| thedotmack/claude-mem | 3 | S | 87,898 | hermes:memory | 中高 |
| anthropics/skills | 3 | S | 162,583 | hermes:skill-extractor | 中高 |
| anthropics/financial-services | 2 | A | 33,610 | hermes:skill-extractor | 中 |
| warpdotdev/warp | 2 | A | 63,433 | model-router | 中 |
| nexu-io/open-design | 2 | A | 79,787 | frontend | 中 |
| coreyhaines31/marketingskills | 2 | A | 40,742 | hermes:skill-extractor | 中 |
| github/spec-kit | 2 | A | 122,434 | matters | 中 |
| CopilotKit/CopilotKit | 2 | A | 36,163 | frontend | 中 |
| freeCodeCamp/freeCodeCamp | 2 | A | 452,108 | hermes:tool-orchestration | 中 |
| rohitg00/agentmemory | 2 | B | 25,410 | hermes:memory | 中 |
| Imbad0202/academic-research-skills | 2 | B | 38,519 | model-router | 中 |
| ruvnet/RuView | 2 | B | 81,317 | frontend | 中 |
| coleam00/Archon | 2 | B | 22,946 | matters | 中 |
| lsdefine/GenericAgent | 2 | B | 13,494 | frontend | 中 |
| can1357/oh-my-pi | 2 | B | 18,481 | hermes:agent-loop | 中 |
| humanlayer/12-factor-agents | 2 | B | 24,533 | hermes:agent-loop | 中 |
| rohitg00/ai-engineering-from-scratch | 2 | B | 40,079 | hermes:agent-loop | 中 |
| HKUDS/ViMax | 2 | B | 11,224 | hermes:agent-loop | 中 |
| Fission-AI/OpenSpec | 2 | B | 61,597 | matters | 中 |
| microsoft/markitdown | 2 | B | 167,470 | hermes:tool-orchestration | 中 |
| nexu-io/html-video | 2 | B | 4,091 | hermes:agent-loop | 中 |
| apple/container | 2 | B | 48,014 | frontend | 中 |
| Panniantong/Agent-Reach | 2 | B | 58,439 | hermes:agent-loop | 中 |
| NVIDIA/cosmos | 2 | B | 11,130 | model-router | 中 |
| chatwoot/chatwoot | 2 | B | 34,558 | frontend | 中 |
| NVIDIA/SkillSpector | 2 | B | 13,448 | hermes:skill-extractor | 中 |
| LMCache/LMCache | 2 | B | 10,721 | knowledge | 中 |
| AgriciDaniel/claude-obsidian | 2 | B | 9,604 | matters | 中 |
| makeplane/plane | 2 | B | 54,743 | hermes:security | 中 |
| DietrichGebert/ponytail | 2 | B | 86,077 | hermes:agent-loop | 中 |
| mvanhorn/last30days-skill | 2 | B | 52,834 | hermes:skill-extractor | 中 |
| JuliusBrussee/caveman | 2 | B | 90,929 | hermes:skill-extractor | 中 |
| instructkr/claude-code | 2 | C | ? | hermes:agent-loop | 中 |
| joeynyc/hermes-skins | 2 | C | 523 | hermes:agent-loop | 中 |
| Cocoon-AI/architecture-diagram-generator | 2 | C | 6,588 | ? | 中 |
| lewislulu/html-ppt-skill | 2 | C | 7,244 | hermes:skill-extractor | 中 |
| eze-is/web-access | 2 | C | 8,344 | hermes:tool-orchestration | 中 |
| supertone-inc/supertonic | 2 | C | 13,434 | frontend | 中 |
| Lordog/dive-into-llms | 2 | C | 43,363 | ? | 中 |
| MiniMax-AI/skills | 2 | C | 13,127 | hermes:skill-extractor | 中 |
| karpathy/autoresearch | 2 | C | 91,583 | hermes:memory | 中 |
| s0xDk/ghostty-blackhole | 2 | C | 1,470 | hermes:context | 中 |
| microsoft/Intelligent-Terminal | 2 | C | 1,579 | hermes:tool-orchestration | 中 |
| forrestchang/andrej-karpathy-skills | 2 | D | ? | hermes:skill-extractor | 中 |
| ruvnet/ruflo | 2 | S | 65,219 | knowledge | 中 |
| affaan-m/ECC | 2 | S | 231,054 | hermes:skill-extractor | 中 |
| google-labs-code/design | 2 | ? | ? | ? | 中 |

## 单提及但高星级项目（偶然提及但质量高）

以下项目在文章中仅提及1-2次，但GitHub星级高或已评为S/A级，值得关注：

- [[gstack|garrytan/gstack]] ⭐123,029 [A] → hermes:skill-extractor
- [[mirofish|666ghj/MiroFish]] ⭐68,836 [A] → frontend
- [[free-claude-code|Alishahryar1/free-claude-code]] ⭐40,814 [A] → model-router
- [[rowboat|rowboatlabs/rowboat]] ⭐16,652 [A] → knowledge
- [[pilotdeck|OpenBMB/PilotDeck]] ⭐3,849 [A] → hermes:task-orchestration
- [[automa|automaapp/automa]] ⭐21,491 [A] → matters
- [[plugins|openai/plugins]] ⭐4,622 [A] → hermes:skill-extractor
- [[agent-toolkit-for-aws|aws/agent-toolkit-for-aws]] ⭐1,971 [A] → hermes:skill-extractor
- [[system-prompts-leaks|asgeirtj/system_prompts_leaks]] ⭐58,950 [A] → hermes:system-prompt
- [[areal|areal-project/AReaL]] ⭐5,571 [A] → model-router
- [[video-use|browser-use/video-use]] ⭐17,203 [A] → hermes:skill-extractor
- [[omniroute|diegosouzapw/OmniRoute]] ⭐20,204 [A] → model-router
- [[gpt-researcher|assafelovic/gpt-researcher]] ⭐28,432 [A] → frontend
- [[claude-video|bradautomates/claude-video]] ⭐9,193 [A] → hermes:skill-extractor
- [yikart/AiToEarn](https://github.com/yikart/AiToEarn) ⭐23,979 [B] → model-router
- [bytedance/UI-TARS-desktop](https://github.com/bytedance/UI-TARS-desktop) ⭐38,120 [B] → hermes:agent-loop
- [earendil-works/pi](https://github.com/earendil-works/pi) ⭐72,749 [B] → hermes:agent-loop
- [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) ⭐36,306 [B] → hermes:agent-loop
- [shareAI-lab/learn-claude-code](https://github.com/shareAI-lab/learn-claude-code) ⭐71,626 [B] → hermes:agent-loop
- [moeru-ai/airi](https://github.com/moeru-ai/airi) ⭐42,874 [B] → frontend

## 文章类型分布

- **教程/How-to** (359篇): 使用方法、实践指南
- **项目推荐** (446篇): 新工具/项目介绍
- **技能包** (427篇): prompt/skill分享
- **对比评测** (255篇): 多工具横向对比
- **深度研究** (377篇): 技术趋势/论文
- **案例研究** (377篇): 实际应用案例
- **新闻/观点** (445篇): 行业动态

## 证据链说明

本分析的置信度来源：
1. 每篇文章全文抓取（非摘要/非预览）
2. 项目名从正文中提取（非仅标题）
3. 交叉验证GitHub实际star数据（非文章声称数字）
4. 代码级扫描结果与文章描述对比校准

## 相关
- [[final-optimization-plan]]
- [[oss-fit-recommendations]]
- [[skills-classified]]
- [[article-analysis]]
