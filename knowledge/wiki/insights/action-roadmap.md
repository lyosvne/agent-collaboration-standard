---
title: 落地行动路线图
tags: [insight, roadmap, action]
created: 2026-07-19
---

# 落地行动路线图

## Phase 1: 修复紧急问题（1-2天）

### P0 - 删除hermes-sidecar
- 删除 Aetheris/hermes-sidecar/ 目录
- ECS: kill PID 419015, 清理render.yaml/docker-compose
- 验证: backend/src/hermes/ 完整覆盖
- 相关: [[redundancy-audit]]

### P0 - 修复model-router
- 修复 profiles/glm.ts 模型名映射
- 修复 profiles/minimax.ts 模型名映射
- 轮换 ARK API key
- 相关: [[model-router]]

### P1 - 归档Desktop aetheris
- 移动旧checkout到archive/

## Phase 2: 安装核心Skills（2-3天）

1. [[draco-skills]]: Hermes中文skill, 44 skills
2. coreyhaines31/marketingskills: CSM工作
3. [[taste-skill]]: 前端审美, 13 skills
4. [[knowledge-work-plugins]]: Anthropic官方
5. addyosmani/agent-skills: Google工程规范
6. aws/agent-toolkit-for-aws: ECS运维

## Phase 3: 架构升级（1-2周）

### Memory升级
- 集成 [[mem0]] 替换当前方案
- 参考 [[claude-mem]] auto-extract

### Agent Runtime参考
- [[agent-native]] BuilderIO TS全套参考
- 重点: loop-settings, observational-memory

### Knowledge Graph
- [[ruflo]] graph-intelligence adapter

## Phase 4: 长期治理（持续）

- 每周运行 scripts/lint.js
- 新文章发URL给Codex自动入库
- upstream每月git pull同步

## 成功指标
- [ ] hermes-sidecar删除
- [ ] model-router 5 provider健康
- [ ] Top 5 skills安装
- [ ] mem0集成
- [ ] wiki>50页, 0 orphan

## 相关
- [[automation-design]] (具体自动化方案)
- [[first-principles]]
