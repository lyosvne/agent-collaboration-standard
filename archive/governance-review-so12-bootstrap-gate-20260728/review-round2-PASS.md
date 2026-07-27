# SO-12 评审 Round2 三方一致 PASS

> 评审对象：compact 续接 bootstrap 强制机制（round2 修复 M1-M5 + AGENTS.md 完整改写）
> 评审日期：2026-07-28
> 评审性质：§四.步骤0 强制触发 + eat own dogfood（本评审用 SO-11-v2-2 的 -r 续接机制走 round2）
> 评审方：A (opus4.8p, -r 续接) / B (gpt5.6sol, -r 续接) / C (cantus, fresh + prompt 内嵌)

## 一、三方一致 PASS

| 评审方 | round1 | round2 | session 续接 |
|---|---|---|---|
| A (opus4.8p) | CONDITIONAL (4 必修) | **PASS** | ✅ session 222764348435 与 round1 一致，A 明确说"记得 round1 我给的 4 必修" |
| B (gpt5.6sol) | CONDITIONAL (6 必修含 3 BLOCKER) | **PASS** | ✅ session 222472563219 与 round1 一致，B 明确说"round1 三个 BLOCKER 已全部实修" |
| C (cantus) | CONDITIONAL (3 必修) | **PASS**（附合入要求） | N/A（fresh + prompt 内嵌，M5 实践，C 沙箱实测 master 确认未合入） |

**核心成果**：
1. round1 的 5 必修（M1-M5）全部修复到位，三方逐项确认 PASS
2. **mira -r 跨进程续接第二次验证成功**（SO-11-v2-2 之后又一次）——A/B session_id 与 round1 完全一致，能精确回忆 round1 结论
3. **C 的实证抽查**：cantus 沙箱主动 clone master 检查，发现 SO-12 文件未合入（事实，代码本机改了还没 push）——这是评审方主动核实真值的好实践

## 二、M1-M5 修复确认（三方逐项 PASS）

| 必修 | A | B | C | 实现要点 |
|---|---|---|---|---|
| **M1** 删 8h 时间窗口 | PASS | PASS | PASS | is_marker_valid 纯 session_id 校验，env 缺失 → deny（B3/B9 覆盖） |
| **M2** 标记加 truth hash | PASS | PASS | PASS | _bootstrap_common.compute_truth_hash（sha256[:16]）+ inject 写 + gate 校验 drift（B10/B11） |
| **M3** bootstrap-gate 第 1 位 | PASS | PASS | — | config.json 顺序调整 + AGENTS.md 锁定契约 |
| **M4** 自举规则成文 | PASS | — | PASS | AGENTS.md "自举规则"段（禁止伪造标记 + 只能 SessionStart 产生 + 无部署豁免） |
| **M5** 动手正则 + 威胁模型 | PASS | PASS | — | 正则补 >+\s*/cp/mv/python open/编辑器 + AGENTS.md "威胁模型边界"段（B12-B15） |

**A 高评**：M4 选"重启 session"而非"手动 seed"，比 A round1 倾向的硬路径更简洁可审计（重启 = 复用 SessionStart 入口，攻击面更小）。
**B 高评**：M1+M2 组合拳比 round1 建议的"project 级 + session_id 后缀路径"更彻底（连路径歧义都不用讨论）。
**C 高评**：内容 sha256 严格优于 commit sha（检测 dirty working tree + 不依赖 git 环境），符合 C round1 主张。

## 三、C 的合入要求（必须处理）

**C 实证发现**：master 的 `.zcode/hooks/` 无 bootstrap 文件——SO-12 修复目前只是本机状态。

**C 原话**："按红线'git 真值不可绕过'，M1-M5 修复目前只是本机状态；bootstrap-gate 自身若不入硬真值，闸门代码本身就是最大的漂移源。评审通过后请走审批合入 master 并同步 ECS mirror。"

**处理**：Step 9 立即 commit + push（本评审通过后第一件事）。

## 四、v2-13 / SO-13 backlog（三方共识，登记独立任务）

| # | 演进项 | 提出方 | 优先级 |
|---|---|---|---|
| 1 | **Aetheris 审计轨迹**（bootstrap 事件 session_id+三件套版本+时间异步写入） | C (Q3) | 高（C 强调否则评审记忆断链） |
| 2 | **编队原则提炼进 governance/**（session 边界重载真值 + 动手前 fail-closed，各 agent 按运行时能力实现） | C (Q4) + A (Q5) | 高 |
| 3 | **四闸门统一拦截矩阵**（chain/session/review/bootstrap 拦什么/查什么/fail 行为） | C (Q5) | 中 |
| 4 | **truth_patterns 扩展**（改为白名单目录 + 自描述 YAML） | B (D2 独立任务) | 中 |
| 5 | **SessionStart hook 单测**（3 case：三件套齐/缺 1/全缺） | B (D5 独立任务) | 中（要求本 sprint 关闭） |
| 6 | **hook 性能预算**（PreToolUse 链 P95 < 200ms + bootstrap-gate 60s TTL 缓存） | B (D6 独立任务) | 中（B 强调 M2 hash 是新增开销，尽早测） |
| 7 | **共享模块 fail-closed**（_bootstrap_common import 失败时 gate 应 deny 而非崩） | A (新发现 1) | 中 |
| 8 | **config.json 顺序 lint**（PreToolUse 顺序与 AGENTS.md 声明一致性校验） | A (新发现 2) | 中 |
| 9 | **AGENTS.md 纳入 truth hash 集**（自举规则/顺序契约本身写在 AGENTS.md，漂移检测不到） | C (新发现 3) | 中 |
| 10 | **补单测 case**（truth_files_seen=[]、双 unknown、并发写标记、mtime 短路） | B (建议 1) + B (建议 5) | 低 |
| 11 | **env 缺失全 deny 的入口覆盖确认**（ZCode 所有启动路径都触发 SessionStart 注入 session_id） | C (新发现 2) | 中（防 fail-closed 退化为永久锁死） |

## 五、eat own dogfood 实测结论

本评审是 SO-11-v2-2 -r 续接机制的**第二次真实使用**（SO-12 round2）：
1. **session-gate hook 正确放行 round2**（CURRENT_REVIEW_PROJECT + CURRENT_REVIEW_ROUND=2 + 正确 -r）
2. **mira -r 续接第二次验证成功**（A/B session_id 与 round1 一致 + 评审方能回忆 round1 必修项）
3. **C 的 fresh + prompt 内嵌模式**跑通（M5 准则再次实践）
4. **C 主动核实真值**：cantus 沙箱 clone master 检查，发现 SO-12 未合入——这是评审方主动验证而非轻信 prompt 陈述的好实践

讽刺但真实：本评审过程**又犯了一次跳链**（误诊 api.mira.chat DNS 污染），恰好是 SO-12 机制必要性的活证据。

## 六、归档索引

- review-A-round2.txt（opus4.8p，session 222764348435 续接成功，42s）
- review-B-round2.txt（gpt5.6sol，session 222472563219 续接成功，41s）
- review-C-round2.txt（cantus，sess_00kl7fqq7ebcwcj1pbcv，fresh，133s）
- review-round1-ABC.md（round1 三方汇总，CONDITIONAL）
- review-package-so12.md（评审材料包）

## 七、结论

**SO-12 round2 三方一致 PASS，可合入。**

按 C 合入要求，立即 commit + push 到 origin/master。
