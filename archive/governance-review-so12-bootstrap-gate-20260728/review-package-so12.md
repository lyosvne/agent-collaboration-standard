# 评审材料包：SO-12 compact 续接 bootstrap 强制机制

> 评审对象：bootstrap-inject-sessionstart.py + bootstrap-gate-precommit.py + AGENTS.md 准则
> 评审性质：§四.步骤0 强制触发（循环闭合：改 hook + 治理规则）
> 评审日期：2026-07-28
> 触发依据：SO-11-v2-2 实施时跳链 3 次（C 调用方式 / hook 生效路径 / typo 范围），根因是 compact 续接后忘全局信息

## 一、问题根因（不是 compact 机制本身，是记忆模型用错）

- compact summary 是有损摘要（保留"做了什么"，丢"事实在哪 + 为什么"）
- 新 session 不主动 reload 项目真值（system prompt 只加载 AGENTS.md，不读 reviewer-tiers.yaml/spec §二/config.json）
- "开工先 git log"只看 commit 历史，看不到调用方式/生效路径这些事实

**核心洞察**：SO-11-v2-2 的 M1/M2 设计思路（显式传入 + fail-closed）就是这个问题的答案——只是把原则用在了评审调度，没用回 session bootstrap 自己。

## 二、技术可行性（已验证）

ZCode 原生支持 `SessionStart` hook（matcher: `startup|resume|clear|compact`），hook 输出 `additionalContext` 可直接注入对话上下文。详见 `~/.zcode/cli/plugins/cache/zcode-plugins-official/zcode-guide/0.1.0/skills/diagnosing-hooks/SKILL.md` §2。

## 三、改动（4 处）

### 3.1 新增 `.zcode/hooks/bootstrap-inject-sessionstart.py`（SessionStart hook）
- matcher: `compact|resume|clear|startup`（覆盖所有 session 启动场景）
- 读真值三件套（reviewer-tiers.yaml 全文 + spec §二 + config.json 全文）
- 输出为 additionalContext JSON 注入对话上下文
- 写 bootstrap 标记文件（session_id + 时间戳 + 已读文件清单）
- fail-closed：三件套任一损坏 → 不写标记 → 后续动手被 bootstrap-gate 拦

### 3.2 新增 `.zcode/hooks/bootstrap-gate-precommit.py`（PreToolUse hook）
- matcher: Bash
- 只拦"动手类"操作（mira 评审调度 / ECS 操作 / 改真值层）
- 检查 bootstrap 标记（双来源校验：session_id 优先 + 时间窗口 8h 兜底）
- 标记缺失/损坏/失效 → deny + 提示修复
- 标记有效 → 放行

### 3.3 改 `.zcode/config.json`
- 加 SessionStart hook 挂载（bootstrap-inject）
- 加 PreToolUse 第 4 个 hook（bootstrap-gate，在 review/chain/session-gate 之后）

### 3.4 改 `~/.zcode/AGENTS.md`
- 加"compact 续接 bootstrap 准则"条款（全局规则，跨项目生效）

## 四、验证结果

- bootstrap-gate **9/9** PASS（B1 标记缺失 deny / B2 匹配放行 / B3 超时 deny / B4 非动手放行 / B5 改真值层 deny / B6 非评审放行 / B7 损坏 deny / B8 ECS deny / B9 时间窗口兜底放行）
- session-gate 14/14 + chain-gate 29/29 + drift-gate 6/6 不破坏
- lint exit 0

## 五、关键设计决策

| 决策 | 选择 | 理由 |
|---|---|---|
| bootstrap 强度 | 硬阻断（必读后才能动手） | 软提示今天已证明不够（summary 在眼前也会忘） |
| 注入文件 | 三件套（spec §二 + reviewer-tiers + config.json） | 治今天的两个断裂（C 调用 + 生效路径） |
| 拦截范围 | 只拦"动手类" | 不拦只读（cat/git log），避免过度阻塞 |
| session_id 校验 | 双来源（env 优先 + 时间窗口 8h 兜底） | 防 ZCODE_SESSION_ID env 缺失导致机制失效 |
| 覆盖范围 | startup/resume/clear/compact 全 matcher | resume 同样会丢上下文 |

## 六、边界与威胁模型

- **不防恶意**：agent 可手动伪造标记。威胁模型同 review-gate/chain-gate——防忘记，不防恶意
- **标记文件不进 repo**：本地状态，drift-check 监控不到（同 override-pending 模式）
- **SessionStart hook 失败**：三件套损坏 → 不写标记 → bootstrap-gate 拦，fail-closed
- **覆盖范围仅 ZCode**：Kimi/Trae/Pi 不加载 .zcode hooks（同 session-gate 边界）

## 七、待评审问题

- Q1: SessionStart hook 实际是否触发？（matcher compact 是文档说的，需实测重启 ZCode）
- Q2: additionalContext 体积（三件套 5-10KB）是否过大？要不要精简到关键段？
- Q3: 动手类识别是否漏判？（如 ssh 到其他 host、其他改真值层方式）
- Q4: 时间窗口 8h 是否合理？（太短频繁 bootstrap，太长失去 session 隔离意义）
- Q5: 与现有 4 hook 共存的执行顺序？（config.json 已明确，但 SessionStart 是新事件类型）
