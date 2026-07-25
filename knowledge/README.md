# Knowledge Base

Karpathy LLM Wiki style | Obsidian vault | Codex maintained | Markdown assets

## Navigation

### Agents
- [[aetheris-hermes-runtime]] | [[model-router]] | [[codex]] | [[trae]]

### Projects
- [[aetheris]]

### Rules
- [[collaboration-standard]] | [[integration]]

### Insights
- [[first-principles]] (first-principles design)
- [[redundancy-audit]] | [[oss-fit-recommendations]] | [[article-analysis]]
- [[automation-design]] | [[adoption-decisions]] | [[action-roadmap]]

### Skills
- [[skills-ecosystem]]

### S-Tier OSS Projects (14)

- [[hermes-agent|NousResearch/hermes-agent]] ⭐217,354 → hermes:agent-loop
- [[mem0|mem0ai/mem0]] ⭐61,242 → hermes:memory
- [[agent-native|BuilderIO/agent-native]] ⭐3,794 → hermes:agent-loop
- [[ruflo|ruvnet/ruflo]] ⭐65,219 → knowledge
- [[gitnexus|abhigyanpatwari/GitNexus]] ⭐44,353 → hermes:skill-extractor
- [[claude-mem|thedotmack/claude-mem]] ⭐87,898 → hermes:memory
- [[page-agent|alibaba/page-agent]] ⭐27,097 → frontend
- [[open-generative-ai|Anil-matcha/Open-Generative-AI]] ⭐23,995 → hermes:agent-loop
- [[draco-skills-collection|dracohu2025-cloud/draco-skills-collection]] ⭐222 → hermes:skill-extractor
- [[skills|anthropics/skills]] ⭐162,583 → hermes:skill-extractor
- [[knowledge-work-plugins|anthropics/knowledge-work-plugins]] ⭐22,862 → hermes:skill-extractor
- [[bentopdf|alam00000/bentopdf]] ⭐14,178 → matters
- [[ecc|affaan-m/ECC]] ⭐231,054 → hermes:skill-extractor
- [[claude-plugins-official|anthropics/claude-plugins-official]] ⭐32,318 → hermes:skill-extractor

### A-Tier OSS Projects (33)

- [[marketingskills|coreyhaines31/marketingskills]] ⭐40,742 → hermes:skill-extractor
- [[omniroute|diegosouzapw/OmniRoute]] ⭐20,204 → model-router
- [[warp|warpdotdev/warp]] ⭐63,433 → model-router
- [[spec-kit|github/spec-kit]] ⭐122,434 → matters
- [[free-claude-code|Alishahryar1/free-claude-code]] ⭐40,814 → model-router
- [[gpt-researcher|assafelovic/gpt-researcher]] ⭐28,432 → frontend
- [[llm-wiki|nashsu/llm_wiki]] ⭐14,918 → knowledge
- [[open-design|nexu-io/open-design]] ⭐79,787 → frontend
- [[superpowers|obra/superpowers]] ⭐257,687 → hermes:skill-extractor
- [[financial-services|anthropics/financial-services]] ⭐33,610 → hermes:skill-extractor
- [[lat-md|1st1/lat.md]] ⭐1,781 → hermes:memory
- [[codebase-memory-mcp|DeusData/codebase-memory-mcp]] ⭐32,953 → hermes:memory
- [[everything-claude-code|affaan-m/everything-claude-code]] ⭐231,054 → hermes:skill-extractor
- [[ui-ux-pro-max-skill|nextlevelbuilder/ui-ux-pro-max-skill]] ⭐107,872 → frontend
- [[skills|mattpocock/skills]] ⭐177,801 → hermes:skill-extractor
- [[pilotdeck|OpenBMB/PilotDeck]] ⭐3,849 → hermes:task-orchestration
- [[copilotkit|CopilotKit/CopilotKit]] ⭐36,163 → frontend
- [[system-prompts-leaks|asgeirtj/system_prompts_leaks]] ⭐58,950 → hermes:system-prompt
- [[gstack|garrytan/gstack]] ⭐123,029 → hermes:skill-extractor
- [[areal|areal-project/AReaL]] ⭐5,571 → model-router
- [[automa|automaapp/automa]] ⭐21,491 → matters
- [[mirofish|666ghj/MiroFish]] ⭐68,836 → frontend
- [[taste-skill|Leonxlnx/taste-skill]] ⭐0 → frontend
- [[agent-toolkit-for-aws|aws/agent-toolkit-for-aws]] ⭐1,971 → hermes:skill-extractor
- [[plugins|openai/plugins]] ⭐4,622 → hermes:skill-extractor
- [[video-use|browser-use/video-use]] ⭐17,203 → hermes:skill-extractor
- [[understand-anything|Lum1104/Understand-Anything]] ⭐75,288 → hermes:skill-extractor
- [[claude-video|bradautomates/claude-video]] ⭐9,193 → hermes:skill-extractor
- [[codegraph|colbymchenry/codegraph]] ⭐60,929 → knowledge
- [[freecodecamp|freeCodeCamp/freeCodeCamp]] ⭐452,108 → hermes:tool-orchestration
- [[ai-website-cloner-template|JCodesMore/ai-website-cloner-template]] ⭐28,879 → hermes:agent-loop
- [[orca|stablyai/orca]] ⭐22,601 → hermes:agent-loop
- [[rowboat|rowboatlabs/rowboat]] ⭐16,652 → knowledge

### Module Reference Pages
- [[module-feishu]]
- [[module-frontend]]
- [[module-hermes-agent-loop]]
- [[module-hermes-context]]
- [[module-hermes-memory]]
- [[module-hermes-security]]
- [[module-hermes-skill-extractor]]
- [[module-hermes-system-prompt]]
- [[module-hermes-task-orchestration]]
- [[module-hermes-tool-orchestration]]
- [[module-knowledge]]
- [[module-matters]]
- [[module-model-router]]
- [[module-news]]
- [[module-rules]]
- [[module-unknown]]

---

Created: 2026-07-19 | Last updated: 2026-07-20 | Source: knowledge-audit-2026-07

## Cross-Agent Integration
- See INTEGRATION.md for integration guide
- index.json for machine-readable index
- scripts/lint.js for link validation

## Auto-Pipeline (Pi-scheduled)

> 更新 2026-07-25：Codex退役后，Pipeline从"Windows Task Scheduler每5小时"改为"Pi cron调度"。

- **触发**: Pi cron定期触发 + 用户主动指令（"存知识库"）
- **执行**: Pi调度Qoder Cloud Agent（或Kimi）做fetch→分析→建wiki
- **写回**: 提交到本仓库knowledge/目录（git分支+review）
- **产物**: wiki/insights/daily-YYYY-MM-DD.md
- **配置**: 见 INTEGRATION.md 的"摄取Pipeline新模式"
