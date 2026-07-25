---
title: S/A级项目采纳决策
tags: [insight, decision, adoption, oss]
created: 2026-07-20
updated: 2026-07-20
---

# S/A级项目采纳决策（逐项目，含Star验证）

决策优先级: 需求 > 已建项目 > 已建智能体 > 已有规则 > 已有skill
置信度优先级: 时间近 > 星级高 > 提及次数多

## S级（14个，立即行动）

| 项目 | Stars | 决策 | 理由 | 行动 |
|------|-------|------|------|------|
| NousResearch/hermes-agent | 217K | **参考不替换** | Python上游，你的hermes已TS实现。skill自进化+feishu插件可移植 | 精读skill-evolution机制 |
| mattpocock/skills | 177K | **直接安装** | TS工程方法论，4篇文章提及 | 安装到canonical/engineering |
| obra/superpowers | 257K | **已用验证** | 9篇文章提及，已安装 | 确认版本最新 |
| anthropics/skills | 162K | **直接安装** | Anthropic官方18 skills | 安装到canonical/hermes |
| affaan-m/ECC | 231K | **参考架构** | 231K stars agent OS，200 skills | 架构思路参考不直接集成 |
| anthropics/knowledge-work-plugins | 22K | **直接安装** | Anthropic官方200知识工作skill | 安装到canonical/knowledge |
| anthropics/claude-plugins-official | 32K | **评估安装** | Anthropic官方30 plugins | 筛选相关skill安装 |
| github/spec-kit | 122K | **已用验证** | spec驱动开发，你已openspec | 确认版本同步 |
| nextlevelbuilder/ui-ux-pro-max-skill | 107K | **直接安装** | 107K stars UI skill，5篇提及 | 安装到canonical/frontend |
| nexu-io/open-design | 79K | **评估集成** | HTML设计系统200 skills | 评估frontend设计集成 |
| BuilderIO/agent-native | 3.7K | **参考采纳** | 100% TS栈，loop/memory/tool全套 | 精读observational-memory融入hermes |
| thedotmack/claude-mem | 87K | **采纳集成** | auto-memory-extract，3篇提及 | 移植extract逻辑到memory-extractor |
| ruvnet/ruflo | 65K | **参考采纳** | TS knowledge-graph-adapter | 参考改造knowledge/graph-service |
| mem0ai/mem0 | 61K | **采纳集成** | MCP server生产级memory | 通过MCP集成做memory层 |
| abhigyanpatwari/GitNexus | 44K | **评估采纳** | TS代码智能引擎zero-server | 评估code-knowledge MCP |
| alibaba/page-agent | 27K | **参考** | TS frontend agent | 参考frontend交互模式 |
| diegosouzapw/OmniRoute | 20K | **采纳集成** | 20K stars! TS, 268+ providers AI gateway | 替换/增强model-router |
| warpdotdev/warp | 63K | **参考** | Rust llms.rs+mode_policy | 参考mode_policy增强decision-policy |
| DeusData/codebase-memory-mcp | 32K | **评估采纳** | C高性能代码记忆MCP | 评估代码索引方案 |
| assafelovic/gpt-researcher | 28K | **评估** | research agent | 评估news/research pipeline |
| coreyhaines31/marketingskills | 40K | **直接安装** | 47 marketing/CSM skills匹配你工作 | 安装到canonical/csm |
| CopilotKit/CopilotKit | 36K | **参考** | React agent UI组件 | frontend UI参考 |
| Alishahryar1/free-claude-code | 40K | **跳过** | free claude code hack | 不采纳，非正当用途 |

## A级（按优先级）

| 项目 | Stars | 决策 | 行动 |
|------|-------|------|------|
| Leonxlnx/taste-skill | 待补 | **直接安装** | 19篇提及，前端审美，13 skills |
| addyosmani/agent-skills | 待补 | **直接安装** | Google工程lead，24 skills |
| aws/agent-toolkit-for-aws | 1.9K | **直接安装** | 131 AWS/ECS skills |
| OpenBMB/PilotDeck | 3.8K | **参考** | multi-agent框架 |
| keli-wen/agentic-harness-patterns-skill | 待补 | **直接安装** | Agent安全模式 |
| openai/plugins | 4.6K | **评估安装** | OpenAI官方200 plugins |
| nashsu/llm_wiki | 14K | **方法论采纳** | Karpathy LLM Wiki，本库已基于此 |
| stablyai/orca | 22K | **评估** | 待深入分析 |
| automaapp/automa | 21K | **评估** | 浏览器自动化 |
| nexu-io/html-anything | 待补 | **评估** | HTML生成 |

## Skill统一目录方案

canonical/
  csm/ — marketingskills (40K★)
  engineering/ — addyosmani(24), mattpocock(41), superpowers(257K★)
  frontend/ — taste-skill(19 mentions), ui-ux-pro-max(107K★), open-design(79K★)
  ops/ — aws-toolkit(131 skills)
  safety/ — agentic-harness-patterns
  hermes/ — draco-skills(44), anthropics-skills(162K★), knowledge-work-plugins(22K★)
  knowledge/ — claude-plugins-official(32K★)
  reference/ — ECC(231K★,参考架构)

## 冲突解决案例

1. **hermes-agent(Python 217K★) vs 你的hermes(TS)**: 需求是TS栈→你的TS实现保留，参考上游架构
2. **OmniRoute(20K★) vs model-router(自有)**: 需求是多provider路由→OmniRoute功能更全(268+ providers)，采纳融合
3. **mem0(61K★) vs @xenova/transformers+LanceDB**: 项目需要成熟memory→mem0通过MCP集成
4. **claude-mem(87K★) extract逻辑 vs memory-extractor.ts**: 采纳claude-mem的auto-extract增强自有模块

## 相关
- [[oss-fit-recommendations]]
- [[first-principles]]
- [[automation-design]]
- [[action-roadmap]]
- [[module-hermes-memory]]
- [[module-model-router]]
- [[module-hermes-skill-extractor]]
