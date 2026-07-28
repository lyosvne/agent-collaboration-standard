---
version: 1.0
status: active
type: ground-truth
created: 2026-07-28
owner: ZCode
title: 治理基础设施现状（hooks + 闸门 + 漂移面）
scope: ZCode 应用层治理 hook 的真值清单，含生效路径 / 单测 / 已知漂移面 / 待实测项
related:
  - specs/governance-review-process.md
  - specs/reviewer-tiers.yaml
  - specs/pre-commit-review-gate-log.yaml
  - ../hooks-so12-bootstrap-gate-20260728/post-deploy-verification.md
supersedes: []
---

# 治理基础设施现状

> **fresh session 必读**。compact 续接后凭此文件重建治理 hook 的完整心智模型，不依赖 summary 记忆。
> 本文件随 hook 闸门表同步更新（改 hook 必须改本文件 + 闸门表 + AGENTS.md）。

## 一、生效的 hook 清单（5 个，全部 project 级）

config.json 挂载点：`.zcode/config.json`（`${ZCODE_PROJECT_DIR}/.zcode/hooks/`）

| 顺序 | 事件 | matcher | hook 文件 | 作用 | SO 编号 |
|---|---|---|---|---|---|
| — | SessionStart | compact\|resume\|clear\|startup | `bootstrap-inject-sessionstart.py` | compact 续接 bootstrap 注入真值三件套 + 写标记（含 truth_hashes） | SO-12 |
| 1 | PreToolUse | Bash | `bootstrap-gate-precommit.py` | 动手类操作前校验 bootstrap 标记（session_id + truth hash），未完成 deny | SO-12 |
| 2 | PreToolUse | Bash | `review-gate-precommit.py` | 拦 ECS patch（apply-*.py / ssh 到 aetherisonline.xyz），查闸门表 PASS | meta-review-gate / SO-8 |
| 3 | PreToolUse | Bash | `chain-gate-precommit.py` | 拦 mira 评审调度，校验 --model 与 reviewer-tiers.yaml 一致 | SO-11 / v2-1 |
| 4 | PreToolUse | Bash | `session-gate-precommit.py` | 拦 mira 评审调度，强制 roundN -r 续接 roundN-1 | SO-11-v2-2 |
| — | PostToolUse | Write\|Edit | `tiers-drift-gate-postuse.py` | 改 reviewer-tiers.yaml/spec §二/mira-integration-status.md 后自动跑 lint | SO-11-v2-1 |

**共享模块**：`_bootstrap_common.py`（compute_truth_hash + TRUTH_FILES 路径，被 bootstrap-inject + bootstrap-gate import）

**PreToolUse 执行顺序契约**（AGENTS.md 锁定）：bootstrap-gate 必须第 1 位——hook 链短路，前置条件必须先跑。

## 二、单测覆盖（每改 hook 必跑全套）

| 单测文件 | case 数 | 覆盖 hook |
|---|---|---|
| `test-bootstrap-gate.py` | 15 | bootstrap-gate（M1 删时间窗/M2 hash/M5 正则） |
| `test-session-gate.py` | 14 | session-gate（M1 项目识别/M2 round/M3 配置/M5 过期） |
| `test-chain-gate.py` | 29 | chain-gate（档位校验/双源比对/override） |
| `test-tiers-drift-gate.py` | 6 | drift-gate（PostToolUse lint 触发） |
| `test-review-gate.py` | 30 | review-gate（apply-*.py/override 补录） |

**全套验证命令**：
```bash
cd C:/Users/Admin/Documents/trae_projects/agent-collaboration-standard
python .zcode/hooks/test-bootstrap-gate.py
python .zcode/hooks/test-session-gate.py
python .zcode/hooks/test-chain-gate.py
python .zcode/hooks/test-tiers-drift-gate.py
python .zcode/hooks/test-review-gate.py
python scripts/check-reviewer-tiers-drift.py  # 档位真值层 lint
python scripts/check-hook-order.py            # PreToolUse 顺序契约 lint（SO-13 #8）
```

**当前全绿状态**（2026-07-28，commit 9c6d8c1）：bootstrap 15/15 + session 14/14 + chain 29/29 + drift 6/6 + review 30/30 + lint exit 0

## 二·五、四闸门拦截矩阵（C round2 Q5 诉求：防闸门本身成漂移面）

> 单点看每个 hook 的文档不够——必须有一张统一矩阵，横向比对"拦什么 / 查什么 / fail 行为"，发现重叠或漏洞。

| 闸门 | 事件 | matcher | 拦什么动作 | 查什么条件 | fail 行为 | 威胁模型 |
|---|---|---|---|---|---|---|
| **bootstrap-gate** | PreToolUse（第1位） | Bash | 动手类：mira 评审调度 / ECS 操作（aetherisonline.xyz, apply-*.py）/ 改真值层（>file,cp,mv,python open 等） | bootstrap 标记：session_id 匹配 + truth_hashes（三件套 sha256）匹配 | 缺失/不匹配/损坏 → **deny + 提示重启 session** | 防诚实健忘，不防主动规避（变量拼接/eval 可绕，设计边界） |
| **review-gate** | PreToolUse（第2位） | Bash | ECS patch 部署：scp/rsync apply-*.py 到 ECS / ssh 写 /opt/pi-orchestrator | 闸门表（pre-commit-review-gate-log.yaml）有对应 files 的 verdict=PASS；SO-8 override 补录闭环 | 无 PASS 条目 / override 未补录 → **deny + 提示走三方评审** | 防漏评审，不防恶意绕过（git --no-verify / rm pending 可绕） |
| **chain-gate** | PreToolUse（第3位） | Bash | mira 评审调度（mira -p + 评审关键字）/ qoder C 调度 | --model/--tier 与 reviewer-tiers.yaml 一致 + 双源比对（YAML A/B 档位在 mira 平台清单） | 档位不一致 / 真值层解析失败 / 双源漂移 → **deny + 提示真值层期望档位** | 防跳链（凭 --help 换档），不防改 prompt 绕关键字 |
| **session-gate** | PreToolUse（第4位） | Bash | mira 评审调度（同 chain-gate，但只校验 mira 平台 reviewer） | CURRENT_REVIEW_PROJECT + CURRENT_REVIEW_ROUND 环境变量齐备 + roundN 用 -r 续接 roundN-1 的正确 session_id | 未 export / 未用 -r / -r 错 id / 配置缺失 → **deny + 提示正确 id** | 防忘续接，不防故意不写关键字 |
| **tiers-drift-gate** | PostToolUse | Write\|Edit | 改真值层文件（reviewer-tiers.yaml / governance-review-process.md / mira-integration-status.md） | 改后跑 lint（check-reviewer-tiers-drift.py）：reviewers/dispatchers/平台清单/session_continuity 必填字段一致 | lint exit≠0 → **deny + 提示 drift 详情** | 防手动 lint 靠自觉，不防 git checkout 旧版（独立任务） |

**重叠与互补分析**：
- bootstrap-gate（第1位）是**前置条件**：没 bootstrap，下游 3 个 gate 的"放行"决策不可信（hook 链短路，bootstrap-gate deny 了后面不跑）
- chain-gate 与 session-gate 都拦 mira 评审调度，但**查的条件不同**（档位 vs 续接），互补不冲突
- review-gate 只管 ECS patch，不与 mira 调度重叠
- drift-gate 是 PostToolUse，与 PreToolUse 闸门正交（改后校验 vs 调用前校验）

**已知覆盖缺口**（SO-13 待补）：
- 改 review-sessions-index.yaml / pre-commit-review-gate-log.yaml / AGENTS.md 不被任何 gate 拦（truth_patterns 未含，B round2 D2）
- hook 执行顺序无 lint 校验（A round2 新发现 2）
- AGENTS.md 漂移不被 bootstrap truth hash 检测（C round2 新发现 3）

## 三、闸门表（pre-commit-review-gate-log.yaml）

每个 hook 改动必须有对应 PASS 条目，否则下次部署被 review-gate 拦。

| gate_id | verdict | pass_round | commit_sha |
|---|---|---|---|
| meta-review-gate | PASS | round3 | 0645929 |
| so8-override-backfill | PASS | round2 | d4f3008 |
| so11-chain-gate | PASS | round2 | 81cd6df |
| so11-v2-1-yaml-single-source | PASS | round2 | af4e5a1 |
| so11-v2-2-session-continuity | PASS | round2 | d694bc9 |
| so12-bootstrap-gate | PASS | round2 | f66b2be |

历史回填（闸门机制建立前）：pi-b-layer / pi-c-layer-drift-check / pi-failopen（均"事后补审"）。

## 四、评审会话归类（review-sessions-index.yaml）

所有 mira 评审调用按项目归类，roundN -r 续接 roundN-1。

| project | status | A session 链 | B session 链 |
|---|---|---|---|
| meta-review-gate | ARCHIVED | (历史未记) | (历史未记) |
| so8-override-backfill | ARCHIVED | (历史未记) | (历史未记) |
| so11-chain-gate | ARCHIVED | (历史未记) | (历史未记) |
| so11-v2-1-yaml-single-source | ARCHIVED | (历史未记) | (历史未记) |
| so11-v2-2-session-continuity | ARCHIVED | 235302197011→235302197011 | 222347143699→222347143699 |
| so12-bootstrap-gate | ARCHIVED | 222764348435→222764348435 | 222472563219→222472563219 |

C（cantus via qoder-bridge）无 -r 续接，每轮 fresh + prompt 内嵌上轮结论。

## 五、已知漂移面（待治理）

### 5.1 home 级 vs project 级 hooks 双源（SO-11-v2-2 时发现，未消除）

**现状**：
- `C:\Users\Admin\.zcode\hooks\`（home 级）和 repo `.zcode/hooks/`（project 级）**两处都有 hook 文件**
- 全局 config（`~/.zcode/v2/config.json`）**不挂任何 hook**（hooks: {}），只有 project 级 config 挂
- 实际生效的是 **project 级**（config.json `${ZCODE_PROJECT_DIR}` 指向它）

**冗余副本**（两处一致，hash 相同，但双份）：
- chain-gate-precommit.py / review-gate-precommit.py / session-gate-precommit.py / tiers-drift-gate-postuse.py
- 对应的 test-*.py

**home 级孤儿文件**（project 级没有，全局 config 不引用，疑似 Claude Code 时代遗留）：
- context-monitor-gate.py / context-monitor.py / execution-discipline-gate.py

**风险**：未来改 hook 只改一处（如改 project 级忘了同步 home 级，或反之），导致"改了但没生效"或"生效的不是真值层版本"。SO-11-v2-2 时我就改错过（改到 home 级，实际生效的是 project 级）。

**治理方案**（待用户裁决，删文件是红线）：
- 方案 A：删 home 级所有 hook 副本 + 孤儿文件，只留 project 级（最彻底，但需红线授权）
- 方案 B：home 级改为 symlink 指向 project 级（保持兼容，但 Windows symlink 需管理员权限）
- 方案 C：保留现状，在 AGENTS.md 加规则"改 hook 必须两处同步"，drift-gate 加 lint 校验两处一致

### 5.2 ZCode hook 执行的可观测性（SO-12 排查时发现）

**现状**：ZCode 日志（`~/.zcode/v2/logs/*.log`）INFO 级别**不记录 hook 执行**（fired / timed out / blocked / exit code）。SKILL.md §3 说"execution recorded in log"，但实测 2026-07-28.log 里 grep 不到 chain-gate/session-gate 等任何 hook 痕迹。

**影响**：无法从日志确认 hook 是否真在跑。SO-12 上线验证清单的阻断点之一。

**治理方案**（登记 SO-13）：
- 写一个 env-dump 诊断 hook（留痕到文件），下次 ZCode 启动时采集 hook 进程的真实 env
- 或提升 ZCode 日志级别到 DEBUG（看是否记录 hook）

### 5.3 ZCODE_SESSION_ID 注入范围未实测（SO-12 阻断点）

**现状**：SKILL.md §2 承诺 `${CLAUDE_SESSION_ID}` / `${ZCODE_SESSION_ID}` 会注入到 hook 进程的 env，但：
- Bash 工具子进程的 env **没有** ZCODE_SESSION_ID（实测）
- hook 进程是否有，**未实测**（本 session 测不了，需重启 ZCode）

**影响**：SO-12 bootstrap-gate 的 M1（纯 session_id 校验，env 缺失 → deny）依赖这个。如果 hook 进程也没 session_id，会**永久锁死所有动手类**（C 新发现 2 警告）。

**验证方法 + 应急方案**：见 `archive/governance-review-so12-bootstrap-gate-20260728/post-deploy-verification.md`

## 六、fresh session 必读文件清单（compact 续接 bootstrap 三件套 + 2 扩展）

SessionStart hook（SO-12）自动注入以下三件套到 additionalContext：
1. **reviewer-tiers.yaml**（档位 + dispatchers + session_continuity）
2. **governance-review-process.md §二**（A/B/C 调度 + C 完整 ssh 命令 + 续接准则）
3. **.zcode/config.json**（hook 实际生效路径）

**扩展必读**（SO-13 应纳入 bootstrap 集合，当前需手动查）：
4. **本文件**（governance-infrastructure-status.md）—— 5 hook 全景 + 拦截矩阵 + 漂移面
5. **cross-boundary-state-transfer-principle.md** —— 跨边界状态传递元原则（A round2 Q5 抽象，指导未来新场景）

## 七、SO-13 / v2-13 backlog（13 项，三方评审共识 + 本文件派生）

按优先级：

### 高优先级（C 强调否则评审记忆断链）
1. **Aetheris 审计轨迹**：bootstrap 事件（session_id + 三件套版本 + 时间）异步写入 Aetheris 审计轨迹，作为"已读真值"的编队级审计证据（C round2 Q3）
2. ~~**编队原则提炼进 governance/**~~ ✅ **已完成**（2026-07-28，`cross-boundary-state-transfer-principle.md` 落地，含各 agent 实现方式标注）
3. ~~**四闸门统一拦截矩阵**~~ ✅ **已完成**（2026-07-28，本文件 §二·五 落地，含重叠互补分析 + 覆盖缺口）

### 中优先级
4. truth_patterns 扩展：改为白名单目录 + `.agents/rules/truth-file.yaml` 自描述清单（B round2 D2）
5. SessionStart hook 单测：3 case（三件套齐 / 缺 1 / 全缺），验证 additionalContext + 标记写入（B round2 D5）
6. hook 性能预算：PreToolUse 链 P95 < 200ms + bootstrap-gate 60s TTL 缓存（B round2 D6）
7. 共享模块 fail-closed：`_bootstrap_common.py` import 失败时 gate 应 deny 而非崩（A round2 新发现 1）
8. ~~config.json 顺序 lint~~ ✅ **部分完成**（2026-07-28，`scripts/check-hook-order.py` 落地，校验 bootstrap-gate 第 1 位硬契约）。**子任务待做**：接入 drift-gate 的 TRIGGER_PATTERNS（改 config.json 时自动跑此 lint），需改 hook 代码（触发 §四.步骤0）
9. AGENTS.md 纳入 truth hash 集：自举规则/顺序契约本身写在 AGENTS.md，漂移检测不到（C round2 新发现 3）
10. env 缺失全 deny 的入口覆盖确认：ZCode 所有启动路径都触发 SessionStart 注入 session_id（C round2 新发现 2）

### 低优先级
11. 补单测 case：truth_files_seen=[]、双 unknown、并发写标记、mtime 短路（B round2 建议）

### 本文件派生的 backlog
12. **消除 home/project hooks 双源**（见 §5.1，需用户裁决方案 A/B/C）
13. **本文件纳入 bootstrap 三件套**（见 §6，SO-13 改进）

## 八、维护约定

- 改任一 hook → 改本文件（生效清单 / 单测数 / 闸门表）+ 走 §四.步骤0 三方评审
- 改 reviewer-tiers.yaml → drift-gate 自动跑 lint（PostToolUse）
- 改本文件 → 不触发 drift-gate（本文件不在 TRIGGER_PATTERNS，SO-13 可加）
- 闸门表（pre-commit-review-gate-log.yaml）是 hook 改动的真值层审计，每次 PASS 后回填 commit_sha
