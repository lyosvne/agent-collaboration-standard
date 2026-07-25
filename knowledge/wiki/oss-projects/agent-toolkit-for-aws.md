---
title: aws/agent-toolkit-for-aws
tags: [oss-project, a, hermes-skill-extractor, py]
created: 2026-07-20
updated: 2026-07-20
source: code-scan:aws__agent-toolkit-for-aws
stars: 1971
tier: A
module: hermes:skill-extractor
fit_score: 7
---

# aws/agent-toolkit-for-aws

> ⭐ 1,971 | py | Apache-2.0 | 最后更新: 2026-07-18

Official, AWS-supported MCP servers, skills, and plugins to help AI agents build on AWS

**Topics**: N/A

## 项目概览

| 指标 | 值 |
|------|-----|
| 代码文件 | 135 |
| 代码行数 | 44,428 |
| 包含技能 | 131 |
| 有测试 | ✅ |
| 有文档 | ❌ |
| 模块适配 | 技能提取/管理 (fit: 7) |

## 适配分析

目标模块: **技能提取/管理**

**参考价值** — A级，作为技能提取/管理的参考方案。

- 与Aetheris现有模块重合度: 50%
- 置信度优先级: A级-评估采纳
- 决策依据: 星级(⭐1,971) × 模块适配度(7) × 时效性(2026-07-18)

## 核心文件（架构入口）

- `plugins\aws-core\skills\amazon-bedrock\scripts\fetch_bedrock_agent.py` (344行)
- `plugins\aws-core\hooks\secret-safety.py` (158行)
- `plugins\aws-agents\skills\agents-build\scripts\x402_payment_tool.py` (151行)
- `plugins\aws-agents\skills\agents-build\scripts\setup_payment_user.py` (121行)
- `plugins\aws-core\skills\aws-observability\scripts\di_app_signals_client.py` (59行)

## 关键代码注释（设计意图）

  - [plugins\aws-core\skills\amazon-bedrock\scripts\fetch_bedrock_agent.py] usr/bin/env python3
  - [plugins\aws-core\skills\amazon-bedrock\scripts\fetch_bedrock_agent.py] boto3 is not in the stdlib. Exit with a distinct code so the caller can
  - [plugins\aws-core\skills\amazon-bedrock\scripts\fetch_bedrock_agent.py] cleanly fall back to the `aws bedrock-agent` CLI path (see
  - [plugins\aws-core\hooks\secret-safety.py] usr/bin/env python3
  - [plugins\aws-core\hooks\secret-safety.py] Match the operation regardless of casing/separators:
  - [plugins\aws-core\hooks\secret-safety.py] GetSecretValue, get_secret_value, get-secret-value, BatchGetSecretValue, ...
  - [plugins\aws-agents\skills\agents-build\scripts\x402_payment_tool.py] Transient on-chain settlement can leave the paid retry at 402 even though the
  - [plugins\aws-agents\skills\agents-build\scripts\x402_payment_tool.py] header was valid; re-settle (fresh header + idempotency token) up to this many times.

## 集成建议

### 如何融入Aetheris
- **目标模块**: `hermes:skill-extractor`
- **优先级**: 🟡 高
- **行动**: 对比现有实现，选择性采纳优秀模式

### 与已有项目的关系
- 与现有skills体系（superpowers/mattpocock/anthropics）同类，择优合并






## 链接

- GitHub: [aws/agent-toolkit-for-aws](https://github.com/aws/agent-toolkit-for-aws)

---
*由gen-sa-wiki-pages.cjs自动生成，基于代码级扫描数据*
