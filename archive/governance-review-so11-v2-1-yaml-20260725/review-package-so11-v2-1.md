# 评审材料包：SO-11-v2-1 真值层 YAML 单源

> 评审对象：reviewer-tiers.yaml + chain-gate 重构 + spec §二指针 + lint 脚本
> 评审性质：§四.步骤0 强制触发（循环闭合：本机制自身变更属强制评审对象，且改 chain-gate 自己）
> 评审日期：2026-07-25
> 触发依据：A/B/C 三方 round1 共识"真值层 YAML 单源是根法"

## 一、背景

SO-11 round1 三方共识：真值层 markdown 双源漂移是根问题。
- A：spec 领先 mira / mira 领先 spec 都出错，建议单源 + 旁路健康检查
- B：S1 双源无守恒机制，建议 YAML 单源 + 脚本生成 markdown
- C：C1 必须双源比对，编队被多源漂移坑过 3 次

v2-1 是 SO-11 round2 backlog 的最高优先级项。

## 二、认知澄清（探明后的修正）

两份不是简单"双源"，是两层不同事实：
- spec §二 = 治理决策（评审方 A 应该用 opus4.8p）→ **YAML 化**（治理契约机器读）
- mira-integration-status = 平台能力清单（mira 支持 opus4.8/4.8t/...）→ **保持 markdown**（hook 旁路健康检查）

正确分层：YAML 单源（治理决策）+ markdown 旁路（平台能力校验）+ lint 防漂移。

## 三、改动（5 处）

### 3.1 新增 governance/specs/reviewer-tiers.yaml（机器源）
```yaml
reviewers:
  A: {tier: opus4.8p, platform: mira, dispatch_keyword: "评审方 A"}
  B: {tier: gpt5.6sol, platform: mira, dispatch_keyword: "评审方 B"}
  C: {tier: cantus, platform: qoder, dispatch_keyword: "评审方 C",
      dispatch_command_pattern: 'qoder-bridge(?:\.py)?\s+--tier\s+cantus\b'}
review_dispatch_extra_keywords: [review-package, 评审材料, ...]
platform_tier_sources: {mira: governance/specs/mira-integration-status.md}
```

把硬编码 REVIEW_KEYWORDS + QODER_CANTUS_PATTERN 也数据化，hook 完全数据驱动。

### 3.2 改 chain-gate-precommit.py
- 删 `load_reviewer_tiers_from_spec()`（解析 markdown）
- 删硬编码 `REVIEW_KEYWORDS` / `QODER_CANTUS_PATTERN`
- 新增 `load_truth_layer()` 读 YAML（带模块级缓存）
- is_mira_review_dispatch / is_qoder_review_dispatch 从 YAML 动态读关键字
- check_truth_layer_consistency 改用 YAML reviewers + mira markdown 旁路检查
- deny 消息更新为"改 reviewer-tiers.yaml（+ spec §二 + mira-integration-status.md，跑 lint）"

### 3.3 改 governance-review-process.md §二
- 表格上方加注："档位真值源：reviewer-tiers.yaml（机器读，hook + lint 用）"
- §二.2.1 调度前校验第 1 条更新：查 reviewer-tiers.yaml（取代本节表格）
- SO-11 机制化段更新：YAML 单源 + 旁路健康检查 + 改档位流程

### 3.4 新增 scripts/check-reviewer-tiers-drift.py（lint）
- 读 YAML
- 扫 spec §二 markdown 表格档位是否与 YAML 一致
- 扫 mira-integration-status.md 是否含 YAML 所有 A/B 档位
- 不一致 exit 1 + 打印差异
- 手动跑（无 CI），AGENTS.md 约定"改 reviewer-tiers.yaml 后必须跑"

### 3.5 单测
- 原 25 case 全部仍 PASS（行为不变，真值层换源）
- 新增 V1（YAML 缺字段 fail-closed）+ L1（lint 一致性）
- **29/29 PASS**

## 四、要评审方回答的问题

### Q1：YAML schema 设计是否够？
- reviewers/{A,B,C}/{tier,platform,dispatch_keyword} 字段够吗？
- C 单独有 dispatch_command_pattern（mira 不需要，因 mira 用 --model 通用）—— 这个不对称合理吗？
- review_dispatch_extra_keywords 是否应分"评审方标识"vs"评审信号"两类？

### Q2：lint 手动跑（无 CI）会忘跑吗？
- 当前靠 AGENTS.md 约定 + plan 必须含"跑 lint"步骤
- B 之前提过"加 CI 卡口"——本编队无 CI，手动跑够吗？
- 要不要在 chain-gate hook 启动时也跑一次 lint（自检）？

### Q3：硬编码消除是否真完整？
- Mira dispatch pattern（mira -p）仍硬编码（不在 YAML）
- MIRA_MODEL_PATTERN / QODER_TIER_PATTERN 正则仍硬编码
- 这些应不应该也数据化？还是属于"hook 协议"不应数据化？

### Q4：循环闭合自检
- 本机制改了 chain-gate 自己，调评审时 chain-gate 会校验档位
- 我用真实档位调（opus4.8p/gpt5.6sol/cantus）—— 验证 hook 没把这次调度误拦
- 这个自指良性结构是否成立？

### Q5：和 v2 其他项的关系
- v2-1 是 v2-2（--reviewer 参数）的基础（YAML 已预留 dispatch_keyword）
- v2-1 是 v2-7（三闸门共享策略模块）的雏形（lint 是共享校验）
- 这个基础打得够不够支撑后续 v2？

## 五、验证证据

- 29/29 单测 PASS（含 V1 YAML 缺字段 + L1 lint 一致性）
- lint 脚本跑当前 repo exit 0（三处一致）
- 真值层 YAML 加载 + 数据驱动 keywords/patterns 验证通过
- 不动 mira-integration-status.md（保持人读，hook 旁路检查）
- 不动 ECS / 不动全局 config

## 六、调度前校验（§二.2.1，本次执行）

1. 档位真值层一致：A=opus4.8p / B=gpt5.6sol / C=cantus ✅
2. 实测可达性：round3/round2 已实测 22 档全可达（间隔短不复测）
3. 冲突上报：无
4. 材料内联：prompts 全部内联
5. **循环闭合自检**：本机制改 chain-gate 自己，调评审用真实档位（opus4.8p/gpt5.6sol/cantus），chain-gate 应放行不应误拦
