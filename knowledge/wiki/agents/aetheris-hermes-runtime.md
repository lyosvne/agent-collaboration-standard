---
title: Aetheris Hermes Runtime
tags: [agent, runtime, typescript, core]
created: 2026-07-19
source: code-scan:backend/src/hermes/
---

# Aetheris Hermes Runtime

## 概述
Aetheris核心agent runtime, TypeScript, backend/src/hermes/

## 核心模块
- agent-loop.ts: 主循环
- agent-runtime.ts: 运行时
- tool-orchestration/registry/factory: 工具编排
- system-prompt-builder.ts: 提示词构建
- memory-provider/extractor.ts: 记忆
- decision-policy/: 决策引擎(evolution+regression)
- context-manager.ts: 上下文管理
- task-orchestrator.ts: 任务编排
- skill-extractor.ts: 技能提取
- shield.ts + path-blacklist.ts: 安全

## 参考
- [[hermes-agent]] (NousResearch上游)
- [[agent-native]] (BuilderIO TS参考)
- [[ruflo]] (多agent编排)

## 已知问题
- hermes-sidecar冗余需删除
- skill四套并存需统一