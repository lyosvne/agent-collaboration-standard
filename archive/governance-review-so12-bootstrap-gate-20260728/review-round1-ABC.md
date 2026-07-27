# SO-12 评审 Round1 三方汇总

> 评审对象：compact 续接 bootstrap 强制机制（bootstrap-inject-sessionstart + bootstrap-gate + AGENTS.md）
> 评审日期：2026-07-28
> 评审性质：§四.步骤0 强制触发（改 hook + 治理规则）
> 评审方：A (opus4.8p) / B (gpt5.6sol) / C (cantus)

## 一、三方 verdict 一致

| 评审方 | verdict | 必修项数 | 视角 |
|---|---|---|---|
| A (opus4.8p) | **CONDITIONAL** | 4 | 架构级、第一性原理、引导悖论 |
| B (gpt5.6sol) | **CONDITIONAL** | 6（3 硬伤） | 结构化、顺序/路径/正则 |
| C (cantus) | **CONDITIONAL** | 3 | 编队主架构师、Aetheris 对齐 |

**三方一致**：方向正确（SO-11-v2-2 M1/M2 思路复用到 bootstrap 层是"元原则"），但有实质缺陷必修。

## 二、三方共识必修项（收敛后 5 项）

### M1【删除/收紧 8h 时间窗口兜底】（A-M3 / B-D4 / C-M1 三方完全共识）

**问题**：8h 时间窗口兜底本意防 `ZCODE_SESSION_ID` env 缺失，但副作用是"别的 session bootstrap 后 8h 内，新 session 静默通过"——这恰恰是 compact 跳链的复现路径。C 一针见血：**"fail-closed 被悄悄变成 fail-open"**。

**修复**（三方综合）：
- **删除时间窗口兜底**，改为纯 session_id 校验（C-M1 主张）
- session_id env 缺失 → deny + 提示重启 session（让 SessionStart hook 写正确标记）
- 不留静默兜底路径

### M2【标记加三件套 hash/sha 校验】（A-M3 / B-D4 / C-M3 三方完全共识）

**问题**：当前标记只校验 session_id，没校验真值三件套本身有没有变。场景：bootstrap 后改了 reviewer-tiers.yaml，additionalContext 已过期但标记仍有效 → 拿旧真值动手。

**修复**：
- bootstrap 标记存三件套的 sha256（或 commit sha）
- `is_marker_valid` 加一步：当前三件套 hash ≠ 标记 hash → 视为失效，强制重 bootstrap
- 对齐 START_HERE 的 [TRUTH-VERSION] 约定

### M3【bootstrap-gate 移到 PreToolUse 第 1 位】（B-D3 BLOCKER，A/C 未提但隐含同意）

**问题**：当前 config.json 顺序是 review-gate → chain-gate → session-gate → bootstrap-gate（第 4 位）。ZCode hook 链短路：前面 hook deny 了，bootstrap-gate 跑不了。但前面 hook 的"放行"决策建立在无 bootstrap 前提上，本身不可信。

**修复**：
- bootstrap-gate 移到 PreToolUse **第 1 位**
- 语义：它是所有下游 hook 的前置条件——"没 bootstrap 一切免谈"
- 文档锁定顺序契约（spec 或 AGENTS.md）

### M4【引导悖论 + 自举规则成文】（A-M2 / C-M2 共识）

**问题**：SO-12 round1 评审本身调 mira，但 bootstrap-gate 还没生效（hook 要重启 ZCode 才装载）。逻辑上：hook 已生效 → deny 评审（死锁）；hook 未生效 → 部署当天所有评审绕过一次。

**修复**（A 选硬路径，C 选成文）：
- AGENTS.md 写明自举规则：闸门自身评审时，通过方式是**重跑 bootstrap 或重启 session**，禁止手写/伪造标记文件
- 标记只能由 SessionStart hook 产生
- 部署 commit 不强制手动 seed（A 的硬路径），改为"重启 session 触发 SessionStart"（更简洁）

### M5【动手识别正则漏判 + 威胁模型显式声明】（A-M1 / B-D2 共识）

**问题**：
- 正则 `>\s` 要求 `>` 后有空格，`>file`（无空格）/ `cp` / `mv` / `python -c open()` 全漏
- `aetherisonline.xyz` 特征匹配，`ssh other-host` / 管道绕过（`cat | ssh`）漏
- 这些是**设计边界**（防诚实健忘，不防恶意），但**边界没显式声明**是 bug

**修复**：
- 写重定向正则改 `>+\s*` + 并列检测 cp/mv/install/truncate/python open
- 或反向判定：目标是真值层 + 命令非只读白名单（cat/less/head/tail/grep/wc/stat/ls/git diff/git log）
- AGENTS.md / spec 显式声明威胁模型："本 gate 防诚实健忘，不防主动规避"

## 三、A/B/C 分歧与互补

| 维度 | A | B | C |
|---|---|---|---|
| 时间窗口 | M3 hash 替代 | D4 收紧 1h 或禁用 | M1 删除/降级显式 | → 收敛为删除（M1） |
| 标记 hash | M3 必修 | D4 必修 | M3 必修 | 三方完全一致 |
| hook 顺序 | 未提 | D3 BLOCKER 第 1 位 | 未提 | B 单提但切中要害 |
| 引导悖论 | M2 硬路径手动 seed | 未提 | M2 自举规则成文 | A+C 共识 |
| 动手正则 | M1 ssh 白名单 | D2 >file/cp/mv/python | 未提 | A+B 共识 |
| truth_patterns 不全 | 未提 | D2 缺 4 文件 | 未提 | B 单提（建议项） |
| SessionStart 无单测 | 未提 | D5 必修 3 case | 未提 | B 单提 |
| AGENTS.md 写"为什么" | M4 深刻 | 未提 | 未提 | A 单提但深刻 |
| 编队原则提炼 | Q5 元原则 | 未提 | 建议项 1 提炼进 governance | A+C 共识 |

## 四、ZCode 综合判断

**必修 5 项**（M1-M5），三方共识度高：
- M1/M2 三方完全一致（8h 窗口 + hash 校验）
- M3 B 单提但切中要害（顺序错位是 BLOCKER 级）
- M4 A+C 共识（引导悖论）
- M5 A+B 共识（正则 + 威胁模型声明）

**降为建议项**（round2 可不做，登记 v2 backlog）：
- B-D2 truth_patterns 扩展（补 review-sessions-index/pre-commit-gate-log/AGENTS.md）—— 改为白名单目录 + 自描述 YAML（独立任务）
- B-D5 SessionStart hook 单测 —— 独立任务（SessionStart 事件触发需重启实测）
- B-D6 性能预算 + 缓存 —— 独立任务
- A-Q5 / C-建议项1 编队原则提炼进 governance —— 独立任务

## 五、round1 结论

**三方一致 CONDITIONAL，不可 round1 合入。**

M1-M5 修完后走 round2（用 mira -r 续接 round1 session：A=222764348435 / B=222472563219；C fresh + prompt 内嵌）。

## 六、待用户裁决

修复涉及：
- bootstrap-gate-precommit.py（M1 删时间窗口 / M2 加 hash / M5 正则）
- bootstrap-inject-sessionstart.py（M2 标记加 hash）
- config.json（M3 顺序调整）
- AGENTS.md（M4 自举规则 + M5 威胁模型声明 + A-M4 写"为什么"）

请确认是否按 M1-M5 全修后走 round2。

## 七、原文索引

- review-A-round1.txt（opus4.8p，session 222764348435，66s）
- review-B-round1.txt（gpt5.6sol，session 222472563219，71s）
- review-C-round1.txt（cantus，sess_00kl4r71q5a0wlsaqn4w，86s）
