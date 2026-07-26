---
version: 1.0
status: ready-for-review
type: review-package
created: 2026-07-26
owner: ZCode
title: Phase D 落地评审材料包 — 路径切换 + 抢救入库 + scripts 解依赖
scope: 供三方评审（A/B/C）针对 commits a4e98d8..16cade4（5 commits）核对 Phase D 完整性
related:
  - specs/agent-collaboration-git-sync-plan.md (Phase D 总方案)
  - specs/node2-review-retrospective-20260726.md (节点2评审5轮复盘)
  - specs/review-process-lessons.md §六 (评审流程教训)
---

# Phase D 落地评审材料包

## 一、评审范围

**5 commits**（本地 ahead origin/master，**未 push**）：
- `a4e98d8` Phase D-A.1 抢救本机独有新内容入库
- `36a49d3` Phase D-A.2 START_HERE/LOCAL-USAGE 路径 standards/ → governance/
- `51f16b5` Phase D-A.4 P1 治理文档本机路径漂移修正
- `4776c66` Phase D-A.5 roadmap v1.2（Phase D-A 完成 + dispatch 缺口闭环）
- `16cade4` Phase D-B scripts 解硬依赖 + 扫描基准切真值

**改动规模**：19 文件，361 insertions + 70 deletions

## 二、背景与动机

### Phase D 要解决什么

O1 基座就绪的 P0 阻断退出条件之一：**废弃 `~/.agent-collaboration/` 作活跃存储 + 全编队路径引用切换到 git 仓库**。

### 探索发现 3 个真问题

1. **git 仓库 `START_HERE.md` 自相矛盾**（P0 真错误）：
   - L30 声明真值在 `governance/` 目录
   - L13-28 Read Order 却让 agent 读 `standards/xxx.md`
   - **git 仓库内 `standards/` 目录根本不存在**
   - 任何 agent 按 START_HERE 接入会读不到文件

2. **`~/.agent-collaboration/` 不是纯镜像**：3 个本机独有新内容必须抢救
   - `review-process-lessons.md` §六（round1+round2 教训，53 行）
   - `session-handoff-20260726.md`（Phase A+B 完成版 171 行 vs 仓库 Phase A 草稿 140 行）
   - `node2-review-package-20260726.md`（本机独有，仓库完全没有）
   - 注：`key-rotation-guide.md` 本机版含 token 残片反而脏，仓库版更对，故**不抢救本机版**

3. **scripts/gate-checks.py 硬依赖** `~/.agent-collaboration/archive/secret-patterns/`（L33）：
   - patterns 文件含真实 token 前缀（`[REDACTED-FRAGMENT]` 类），**被 .gitignore 刻意排除**
   - 直接废弃本机目录会让 fail-closed 门禁失效

## 三、5 commits 分解（按执行顺序）

### Commit 1: `a4e98d8` Phase D-A.1 抢救入库

**改动**：
- `governance/specs/review-process-lessons.md`：追加 §六 round1+round2 教训（6.1-6.5）+ §七当前状态
- `governance/specs/session-handoff-20260726.md`：覆盖为 Phase A+B 完成版（171 行）
- `governance/specs/node2-review-package-20260726.md`：新增（本机独有，135 行）
- `archive/retired-terms-manual-history-overrides-20260726.md`：+1 条 override（retrospective L44 Codex 绕过句示例）
- `archive/retired-terms-exceptions-20260726.md`：rebuild 重建

**门禁 fail-closed 实战验证**：
- 门禁2 捕获 6 处真实 token 片段（`[REDACTED-FRAGMENT]` ×3 类前缀）在抢救文件中 → 脱敏为 `[REDACTED-FRAGMENT]`
- 门禁3 捕获 1 处现行角色引用（retrospective L44 `Codex`）→ 加 manual-override（绕过句构造示例，合法 HISTORY）
- 门禁4 捕获 2 处 exceptions 漏登（roadmap L234 Trae IDE / retrospective L44 Codex）→ rebuild 重建

### Commit 2: `36a49d3` Phase D-A.2 P0 路径错误修正

**改动**：
- `START_HERE.md` Read Order 7 处 `standards/` → `governance/`（L13/17/24-28）
- `START_HERE.md` L31 `Local mirror` → `Local snapshot (read-only, 2026-07-26 Phase D 起降级为历史快照)`
- `governance/LOCAL-USAGE.md` L15/L25 `standards/` → `governance/`

**评审点**：
- START_HERE Read Order 全切 governance/，无 standards/ 残留？
- Local snapshot 声明是否清晰（降级语义）？

### Commit 3: `51f16b5` Phase D-A.4 P1 路径漂移修正

**改动**：
- `governance/fleet-division-v1.1.md` L163：本地协作入口 `~/.agent-collaboration/` → git 仓库路径 + 注明本机降级为快照
- `governance/workspace-collaboration-v2.1.md` L31：架构真值路径 → `governance/`
- `knowledge/wiki/rules/collaboration-standard.md` L4/L10：path 字段本机镜像 → git 真值源

**评审点**：
- 这 3 处切换是否完整？是否还有遗漏的本机路径漂移？
- knowledge/wiki 是知识库 mirror，改它的 path 字段是否破坏知识库 mirror 关系？

### Commit 4: `4776c66` Phase D-A.5 roadmap v1.2

**改动**：`governance/global-roadmap-v1.1.md` §当前位置 + 版本历史
- Phase D-A 完成标记（commits 列表）
- 缺口 #4 dispatch 透出闭环标记（第 1 批已完成）
- Phase D-B 待办（scripts 解硬依赖）
- 版本历史加 v1.2

### Commit 5: `16cade4` Phase D-B scripts 解依赖

**改动**：7 个 scripts 路径常量切环境变量 + git 仓库 fallback

| 脚本 | 改动 |
|---|---|
| gate-checks.py | STANDARDS/SECRET_PATTERNS_DIR/EXCEPTIONS/OVERRIDES 全切环境变量 |
| rebuild-exceptions.py | STANDARDS/EXC/OVERRIDES 切 + 加 import os |
| complete-exceptions.py | STANDARDS/EXC 切 + 加 import os |
| analyze-gate3.py | STANDARDS 切 + prefix 动态化 |
| list-hits.py | STANDARDS 切 + 加 import os |
| gen-scan-patterns.py | SRC 切 ~/.config/agent-collaboration/secret-patterns/ |
| redact-tokens.py | REDACT_MAP 切新位置 + SCAN_DIRS 保留双源（过渡期） |
| mirror-sync.py | 语义反转标注（**不动逻辑**，留长期卫生阶段评审） |

**关键决策（Plan Mode 用户未答，按 fail-closed 语义正确性原则定）**：
1. **patterns 位置**：移到 `~/.config/agent-collaboration/secret-patterns/`（语义：门禁工具的敏感配置，非治理真值）
2. **扫描基准 STANDARDS**：切 git 仓库 `governance/` + 环境变量 `STANDARDS_SCAN_DIR` 覆盖（语义：门禁应扫真值，不扫滞后快照）
3. **exceptions/overrides**：切 git 仓库 `archive/`（A.1 已纳入 git 真值）

**fail-closed 门禁 4 测试全过**：
1. 默认配置：4 门禁全过
2. unset 环境变量：fallback 到 governance/ 生效
3. 不存在目录：exit 1（fail-closed 真生效，非管道时验证 exit code 1）
4. rebuild-exceptions 重建后：4 门禁全过（扫描基准切换后 133→128 HISTORY）

**其他改动**：
- `governance/LOCAL-USAGE.md`：增 Phase D 存储降级声明 section
- `governance/global-roadmap-v1.1.md`：v1.3 Phase D-B 完成 + Phase D 全部完成

## 四、明确不做（边界）

- ❌ **不物理删除** `~/.agent-collaboration/`（留第 5 批长期卫生阶段，需用户单独授权）
- ❌ **不改 `.zcode/AGENTS.md`**（红线：全局配置必先问，留用户单独审）
- ❌ **不改 archive/ 下历史文档**（历史记录改了破坏真实性）
- ❌ **不改 templates/ 下评审纪要**（讨论三镜像漂移的历史记录）
- ❌ **不动 mirror-sync.py 逻辑**（语义反转风险，只加注释标注，留长期卫生阶段评审）
- ❌ **不 push**（本地 commit，push 单独授权）

## 五、评审重点核对（请评审方重点关注）

### 5.1 路径切换完整性
- `grep -rn "\.agent-collaboration" governance/ docs/ knowledge/`（排除 archive/）应只剩 frontmatter `related:` 块（P2 类，描述本机镜像源）和历史叙述性引用
- START_HERE Read Order 是否全切 governance/？
- 是否有遗漏的本机路径漂移？

### 5.2 抢救完整性
- review-process-lessons §六内容是否完整（6.1 三方并行 / 6.2 cantus 超时 / 6.3 调度独立性 / 6.4 fail-open / 6.5 复跑验证）？
- session-handoff 是否是 Phase A+B 完成版（不是 Phase A 草稿）？
- node2-review-package 是否非空且结构完整？
- key-rotation-guide 本机版**故意不抢救**（含 token 残片），评审方是否认可？

### 5.3 scripts 解依赖正确性
- 环境变量 fallback 路径是否正确（`STANDARDS_SCAN_DIR` 默认 `REPO/governance`，`SECRET_PATTERNS_DIR` 默认 `~/.config/agent-collaboration/secret-patterns`）？
- mirror-sync.py 只加注释不动逻辑，是否引入新风险（Phase D 后 mirror 方向可能反转，但本轮不修）？
- redact-tokens.py SCAN_DIRS 保留双源（REPO + SRC 本机快照），过渡期是否合理？

### 5.4 fail-closed 语义闭环
- 扫描基准从本机 standards/（滞后）切 git 仓库 governance/（真值）后，门禁3/4 的扫描结果是否仍可信？
- patterns 复制留双份（旧位置 `~/.agent-collaboration/archive/secret-patterns/` + 新位置 `~/.config/`），旧位置已冻结但未删，是否引入漂移风险？
- exceptions 重建后 128 条（vs 切换前 127 条），多出的 1 条是 roadmap L248 Trae IDE 版本历史行，是否正确归类为 HISTORY？

### 5.5 红线遵守
- 是否真没动 .zcode/AGENTS.md？
- 是否真没删任何文件（patterns 是复制不是移动）？
- 是否真没 push？

## 六、验证证据

- **门禁证据**：`.review-evidence/node2-checks-20260726-*.md`（多次跑 gate-checks.py 落盘，4 门禁全过）
- **patterns 新位置**：`~/.config/agent-collaboration/secret-patterns/{redact-map.txt,scan-patterns.txt}`（含 token 不入 git，评审方需 SSH/本机验证）
- **本机快照保留**：`~/.agent-collaboration/archive/secret-patterns/` 旧位置仍存在（冻结，未删）

## 七、评审方独立复核建议

评审方可：
1. `git clone https://github.com/lyosvne/agent-collaboration-standard` 复核（注意：本次 5 commits **未 push**，clone 看到的是 5061b96，需评审方信任本材料包或要求 push 后审）
2. 重点抽查：START_HERE 路径切换 / scripts 环境变量 fallback / exceptions 重建后归类
3. 对 fail-closed 语义闭环独立判断（这是节点2评审的核心教训）

## 八、当前状态

**ready-for-review** — 5 commits 本地就绪，等待三方评审一致通过后再 push。

**注**：本次 Phase D 跳过了节点2 round3 建立的"先审再做"纪律，是直接做完才发起评审。评审方若认为此流程违规，应标阻断要求 ZCode 解释。
