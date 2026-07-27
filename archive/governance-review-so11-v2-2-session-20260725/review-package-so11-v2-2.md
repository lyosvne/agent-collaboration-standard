# 评审材料包：SO-11-v2-2 Mira 会话归类 + session 续接

> 评审对象：session-gate-precommit.py + review-sessions-index.yaml + spec §二.2.2 + reviewer-tiers.yaml 加 session_continuity
> 评审性质：§四.步骤0 强制触发（循环闭合：改 hook + spec + YAML）
> 评审日期：2026-07-25（待走，本轮 push 标 REVIEWING，下 session 走完整评审）
> 触发依据：用户需求"评审 Mira 调用归类 + 同会话续接 + 准则机制化"

## 状态

**REVIEWING**（2026-07-25 push，代码 + 单测 + lint 全 PASS，待下 session 走三方评审）。
理由：本 session 上下文 72%（接近 warning），评审中途冒 compact 风险。下个 fresh session 用 mira -r 续接走完整评审（eat own dogfood 测试续接机制）。

## 一、需求（用户原话）

1. 本项目所有评审的 Mira 调用归类为一个项目
2. 后续在同一个会话中调用 Mira CLI（有上下文）
3. 这个要求加入调度准则被所有协作矩阵遵循

## 二、关键技术验证（已通过）

mira `-r <session_id>` 跨进程续接实测（2026-07-25）：
- `mira -p "记住代号 ALPHA-001" → session_id 222342108435`
- 新进程 `mira -p "代号？" -r 222342108435` → 返回 "ALPHA-001" ✅
- 同档续接（opus4.8p round1 → round2）✅
- session 至少几小时内不过期 ✅

## 三、改动（5 处，全部 PASS）

### 3.1 新增 archive/review-sessions-index.yaml
会话归类索引（所有评审项目集中登记），4 个历史项目标 ARCHIVED + 未来项目模板。

### 3.2 spec §二.2.2 新增"会话归类与续接"准则
6 条规则（归类/续接/记录/归档/C 例外/历史项目）+ session-gate hook 机制化说明。

### 3.3 reviewer-tiers.yaml 加 session_continuity 配置
enabled / strategy / platforms_with_continuity / resume_arg / record_index / current_project_env / archived_status。

### 3.4 新增 .zcode/hooks/session-gate-precommit.py
PreToolUse hook，matcher=Bash：
- 识别 mira 评审调度 + roundN 标识
- 查 review-sessions-index.yaml 当前项目 roundN-1 session_id
- 有 session_id 且未用 -r → deny + 提示
- -r id 不匹配 → deny
- 首轮/ARCHIVED → 放行
- **8/8 单测 PASS**

### 3.5 .zcode/config.json 加 session-gate 挂载

## 四、验证

- session-gate 8/8 单测 PASS（S1 首轮/S2 无-r deny/S3 正确-r/S4 错-r deny/S5 ARCHIVED/S6 非评审/S7 C 例外/S8 无 round 标识）
- chain-gate 29/29（不破坏）
- drift-gate 6/6（不破坏）
- lint exit 0（reviewer-tiers.yaml 加字段后三处仍一致）
- mira -r 跨进程实测通过

## 五、待评审问题（下 session 走）

- Q1: roundN-1 上下文误导 roundN 的风险（用户已选 roundN 续接方案，但评审方可能质疑）
- Q2: 当前项目识别靠环境变量 + 兜底扫描，健壮性
- Q3: session_id 过期处理（mira 时效待长观察）
- Q4: C 无续接是否应在 qoder-bridge 侧补
- Q5: 评审材料内联 + session 续接的组合（续接后是否还需全量内联）

## 六、红线遵守

- 改 spec §二.2.2（调度准则）+ reviewer-tiers.yaml + 新增 hook → §四.步骤0 强制触发
- 不动 ECS / 不动全局 config
- 本轮 push 标 REVIEWING，不造假 PASS
