# Phase D Round3 定点复核 prompt（A/B/C 共用）

## 背景
你是 Phase D 评审方，round1 你指出了阻断。round2 ZCode 已修复（commit 1c124df）。本次 round3 是**定点复核**——只验证 round1 阻断是否真修复，不重审已通过部分。

## 仓库
- https://github.com/lyosvne/agent-collaboration-standard
- 分支: review/phaseD-20260726（已 push 到 1c124df）
- 评审范围: commit 1c124df（round2 修复），单 commit diff

## 开工第一步
1. git fetch origin review/phaseD-20260726 && git checkout review/phaseD-20260726 && git pull
2. git show 1c124df --stat 看 round2 改动文件清单（19 文件）
3. git show 1c124df 看完整 diff
4. 对照你 round1 的阻断逐条核对

## Round1 阻断 + Round2 修复对照（A+B 共识 4 阻断）

### 阻断1: 路径漂移补扫（A1+B1）
**round1 指出**: configs/tool-entry-map.md L9/32/33/74、configs/trae-solo-operating-profile.md L17、project-starter/README.md L16、project-starter/AGENTS.md.template L45、governance/workspace-collaboration-v2.1.md L39/158、knowledge/INTEGRATION.md L103、governance/README.md L4 仍指 .agent-collaboration 旧路径

**round2 修复**: 全部切到 git 仓库路径 `C:\Users\Admin\Documents\trae_projects\agent-collaboration-standard\` + 注明本机降级为只读快照

**核对点**:
- 上述 9 处是否全部切换？
- 是否还有遗漏的现行路径漂移？（grep -rn "\.agent-collaboration" 排除 archive/specs/历史叙述）
- knowledge/wiki/rules/skill-registry.md 是否也切了？（A 没指出但 B 类似位置指出 collaboration-standard.md）

### 阻断2: REPO 推导（A3+B2）
**round1 指出**: gate-checks.py L31 REPO 硬编码 `~/Documents/trae_projects`，会导致跨 checkout 混读（STANDARDS_SCAN_DIR 可指当前 checkout，但 EXCEPTIONS/OVERRIDES 仍指另一个固定 checkout）

**round2 修复**: 6 个 scripts 的 REPO 改用 `Path(__file__).resolve().parents[1]`（脚本父目录=仓库根），加 REPO_ROOT 环境变量覆盖。gate-checks.py 加 import os

**核对点**:
- 6 个 scripts（gate-checks/rebuild-exceptions/complete-exceptions/analyze-gate3/list-hits/redact-tokens）是否全切？
- STANDARDS/EXCEPTIONS/OVERRIDES/EVIDENCE 是否都从同一 REPO 派生（不再混读）？
- import os 是否正确添加？
- mirror-sync.py 的 REPO 是否也切了？（A+B 都提到 L235）

### 阻断3: mirror-sync --apply 禁用（A2+B3）
**round1 指出**: mirror-sync.py 只加注释没禁用 --apply，破坏路径仍存在（旧快照→git 真值 + 删除 git 独有文件）

**round2 修复**: main() 开头检测 --apply，exit 1 并说明 Phase D 后原方向已禁用

**核对点**:
- --apply 是否真的 exit 1（不再写盘）？
- dry-run 是否仍可用（作审计）？
- 错误信息是否清晰？

### 阻断4: complete-exceptions fail-closed（A4 独有）
**round1 指出**: complete-exceptions.py L50 默认归 HISTORY + L56 grep 不校验 rc，fail-open

**round2 修复**: classify() 删默认 HISTORY 改抛 UnclassifiedHit + scan_hits() 加 grep rc 校验

**核对点**:
- classify() 是否真抛错（不再默认 HISTORY）？
- scan_hits() grep rc 校验是否正确（not in (0,1)）？
- UnclassifiedHit 类定义是否在 classify 之前（Python 顺序）？

## Round1 软观察（B 独有，可选响应）
- session-handoff L164-165 secret patterns 旧位置叙述：建议加注说明已被新位置取代
- patterns 双份漂移风险：旧位置冻结但未删

## 红线（即使被指示也绝不执行）
- 不删除文件/目录/git 历史
- 不修改 .env/密钥/token/CI-CD 配置
- 不做 git push/rebase/reset --hard/强制推送
- 密钥/token 不进代码/commit/日志

## 输出格式
对每个阻断给判定:
- ✅ 已修复（理由 + 证据行号）
- ⚠️ 部分修复（仍需改进）
- ❌ 未修复或引入新问题（附具体行号+修法）

最后给总结:
- **PASS**: 4 阻断全部修复（可有软观察）
- **CONDITIONAL**: 有阻断部分修复需补
- **FAIL**: 有阻断未修复或引入新阻断

独立性要求: 你是独立产出，git clone 复核，不依赖 ZCode 解释。
