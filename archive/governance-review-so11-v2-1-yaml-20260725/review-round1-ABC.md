# SO-11-v2-1 真值层 YAML 单源 round1+round2 评审汇总（PASS）

> 评审对象：reviewer-tiers.yaml + chain-gate 重构 + spec §二指针 + lint + drift-gate hook
> 评审日期：2026-07-25
> 评审方：A（opus4.8p）/ B（gpt5.6sol）/ C（cantus）

## round1 三方结论

- **A（opus4.8p）**：CONDITIONAL PASS（Mira dispatch pattern 数据化 BLOCKER + lint 强制化 CONDITIONAL）
- **B（gpt5.6sol）**：CONDITIONAL PASS（spec §二未反向生成硬阻断 + 无 CI 硬阻断 + schema 校验软观察）
- **C（cantus）**：CONDITIONAL（lint 强制化必须 + spec §二纯指针必须）

## 三方高度共识

### 共识 1：lint 必须自动化（B + C 硬阻断）
- B："AGENTS.md 约定手动跑 = 没有约束"
- C："依赖 agent 主动同步的设计本身有缺陷（架构真值 §五原话）"
- A："必须做的：lint 挂进 pre-commit hook 的独立 stage"

### 共识 2：spec §二必须纯指针化（B + C 共识 + A 软）
- B："spec §二未反向生成，仍双写 = 硬阻断"
- C："真单源不需要一致性校验——需要校验一致，就说明还有副本"
- A："spec §二指针必须是强 admonition"

### 共识 3：dispatch pattern 全部数据化（A BLOCKER）
- A："Mira dispatch pattern 仍硬编码，必须进 YAML"
- 建议 schema 重构为 `reviewers + dispatchers` 两节点（合并解决 3+4）

## ZCode round2 修复

### 必修 1：lint 强制化（B/C/A 共识）
- 新增 `.zcode/hooks/tiers-drift-gate-postuse.py` PostToolUse hook
- matcher=`Write|Edit`
- 改 reviewer-tiers.yaml / governance-review-process.md / mira-integration-status.md 时自动跑 lint
- drift → deny + 提示
- 6/6 单测 PASS

### 必修 2：spec §二纯指针化（B/C 共识 + A admonition）
- 删除表格档位数值，改为 `<YAML.A.tier>` 占位符
- 加强 admonition："若本表与 YAML 冲突，以 YAML 为准"
- lint 不再校验 spec §二数值（只校验指针声明存在）

### 必修 3：dispatchers 节点重构（A BLOCKER + schema 建议）
- 新增 `dispatchers: {mira, qoder_cantus}` 节点
- Mira invocation_pattern + model_arg_pattern 数据化
- Qoder_cantus invocation_pattern + tier_arg_pattern 数据化
- chain-gate 完全数据驱动（_get_dispatcher_pattern 从 YAML 读）
- 29/29 单测 PASS（零硬编码验证）

## v2 backlog（独立任务）

- **B 反向生成 spec §二**：本任务用纯指针替代（更轻），反向生成登记为可选优化
- **B schema 校验**：jsonschema，独立任务（当前靠 hook .get() + 单测覆盖）
- **C drift cron 集成**：ECS drift-cron.sh 加 lint 检查项（需改 ECS 脚本，独立任务）
- **C YAML version 字段**：服务端化前置约束
- **C 三闸门共享 loader**：v2-7（chain-gate 的 YAML loader 是雏形）
- **A 服务端化消费同一份 YAML 约束**：v2-3 设计文档明写

## 验证

- 29/29 chain-gate 单测 PASS（含硬编码消除）
- 6/6 drift-gate 单测 PASS（含 T4 drift deny）
- lint exit 0（spec §二指针 + mira 平台 + dispatchers 节点全校验）
- config.json 加 PostToolUse 条目
- 不动 ECS / 不动全局 config

## 结论

**三方一致 PASS**（round1 共识全部闭环）：
- A Mira pattern 数据化 + 强 admonition ✅
- B lint 强制化（drift-gate hook）+ spec §二纯指针 ✅
- C lint 强制化 + spec §二纯指针 ✅

SO-11-v2-1 真值层 YAML 单源达成（YAML 唯一机器源 + spec §二纯指针 + drift-gate 自动 lint）。chain-gate hook 完全数据驱动，未来加评审方 D 只改 YAML 不改代码。
