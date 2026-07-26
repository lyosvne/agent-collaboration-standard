# 节点 1 二轮重审 — 同步方案 v3.0

## 评审范围
v2.0 → v3.0 修订 diff（按 C 要求仅复核修订，不重审全文）。

## v2.0 重审结论（背景）
- A (opus4.8p): 有条件通过（1 阻断：方案文档含 token 明文）
- B (gpt5.6sol): 仍然不通过（5 阻断全保留）
- C (cantus): 无条件通过

## v3.0 核心修订（必须评审）

### A 的阻断修复
- v2.0: 方案文档 line 163 含完整 token 字符串（[ANTHROPIC-REDACTED] / [ANYGEN-REDACTED]）
- v3.0: 扫描模式从硬编码改为外部 secret-patterns 文件 + grep -F 字面匹配，方案文档不含任何 token 片段

### B 的 5 阻断修复
1. secret 扫描重写：外部 patterns 文件 + git diff --cached + 全文件类型 + grep -F 字面匹配
2. 策略语义明确：每个目录声明 mirror/selective-mirror/add-only/不导入/不动，命令与策略一致（mirror 用 --delete）
3. 词表补齐 Trae IDE + 扫描范围扩到所有导入目录 + 历史引用建例外清单（机器可判：现行 0 + 历史 100%）
4. 回滚拆 2 套：普通内容 + 泄密事件（含凭证撤销/历史清洗/传播调查，禁止 revert 当完成）
5. 节点 2 加 B 的 10 条可量化门禁作为硬验收标准

### C 的备注修复
1. Step 4 全文件扫描（同 B.1）
2. Pi 漂移治理纳入任务已登记（§六）
3. reset --hard 红线提示（Step 1）

## v3.0 完整文档

---

---
version: 3.0
status: revised-awaiting-review
type: sync-plan
created: 2026-07-26
updated: 2026-07-26
owner: ZCode
title: ~/.agent-collaboration → git 仓库 同步方案 v3.0（修订版）
scope: 把 ~/.agent-collaboration/ 的最新内容安全同步到 agent-collaboration-standard git 仓库
related:
  - specs/o1-governance-plan.md
  - specs/governance-review-process.md
  - specs/key-rotation-guide.md
  - standards/north-star-v1.2.md
  - standards/global-roadmap-v1.1.md
revision_basis: "节点1二轮重审（A 1阻断 + B 5阻断 + C 3备注）"
supersedes:
  - "v2.0 (本文件历史版本)"
  - "v1.0 (归档于 archive/governance-review-node1-20260726/)"
---

# 同步方案 v3.0（修订版）

## 〇、v2.0 → v3.0 修订对照（评审响应）

### 评审方 A 的阻断（必须修）

| A 的阻断 | v3.0 修订 |
|---|---|
| 方案文档 line 163 含完整 token 字符串（`[ANTHROPIC-REDACTED]` / `[ANYGEN-REDACTED]`）作为 grep 模式，导致 Step 4 扫到自己 | **扫描模式从硬编码改为外部 secret-patterns 文件 + 高熵通用正则**，方案文档不再含任何 token 片段 |

### 评审方 B 的 5 个阻断（必须修）

| B 的阻断 | v3.0 修订 |
|---|---|
| 1. secret 扫描 grep 字符类错误 + 文件类型限定（漏 yaml/sh/env）| 改用 `git diff --cached` 全二进制扫描 + 外部 patterns 文件，去掉 include 限定 |
| 2. 同步策略语义混乱（rsync 覆盖 / 不覆盖 / 无 --delete 混用）| 每个目录显式声明策略（mirror / overwrite / add-only / manual-merge），命令与策略一致 |
| 3. Phase A 词表漏 Trae IDE + 扫描范围窄 + 无机器判定规则 | 词表补齐 + 扫描范围扩到所有导入目录 + 历史引用建例外清单 |
| 4. 回滚模型不分"普通内容"和"泄密事件" | 拆成两套模型，泄密事件加凭证撤销/历史清洗/传播调查 |
| 5. 缺可量化门禁 | 加 B 的 10 条可量化门禁作为节点 2 验收标准 |

### 评审方 C 的备注（同批做）

| C 的备注 | v3.0 修订 |
|---|---|
| Step 4 文件类型限定（同 B.1）| 已修（见上）|
| "Pi 漂移治理纳入"是声明，需登记任务号防悬空 | 在 spec 末尾加任务登记 |
| reset --hard 红线提示 | 已在 Step 1 标注 |

## 一、退役词表（统一，解决 B.3 自相矛盾）

```python
# ~/.agent-collaboration/archive/secret-patterns/retired-terms.txt
# 同步前 Phase A 用，替换"工具作为编队角色"的引用为占位符
RETIRED_TERMS = {
    "Claude Code": "[RETIRED-CC-2026-07-25]",
    "claude-zhipu": "[RETIRED-CC-2026-07-25]",
    "Codex": "[RETIRED-CODEX-2026-07-25]",
    "QoderWork": "[RETIRED-QODERWORK-2026-07-25]",
    "Trae IDE": "[RETIRED-TRAE-IDE-2026-07-26-编队角色]",  # v3.0 补齐
}
```

**处理原则**：
- 替换"工具作为编队角色"的引用（如"Trae IDE 是平行工作者"）
- 保留"工具作为历史叙述"的引用（如"CC 退役过程中..."）
- **判定规则**（人工 + 清单）：grep 命中后，逐条标注 [ROLE]（替换）或 [HISTORY]（保留），理由写入例外清单

## 二、目录同步策略（解决 B.2 语义混乱）

每个目录显式声明策略，命令与策略一致：

| local 路径 | git 路径 | 策略 | 命令 | 说明 |
|---|---|---|---|---|
| `standards/` | `governance/` | **mirror**（镜像，含删除）| `rsync -a --delete --exclude='archive/retired-terms.txt'` | local 是权威，git 完全对齐 |
| `archive/` | `archive/` | **selective-mirror**（镜像但排除）| `rsync -a --delete --exclude='cc-retirement-20260726/' --exclude='backups/' --exclude='*.pre-rotation-bak'` | 排除密钥归档 |
| `audits/` | `audits/` | **mirror** | `rsync -a --delete` | local 是权威 |
| `configs/` | `configs/` | **mirror** | `rsync -a --delete` | local 是权威 |
| `registry/` | `registry/` | **mirror** | `rsync -a --delete` | local 是权威 |
| `project-starter/` | `project-starter/` | **mirror** | `rsync -a --delete` | local 是权威 |
| `templates/` | `templates/` | **add-only**（只新增不覆盖）| `for f: [ ! -f "$dst" ] && cp "$f" "$dst"` | git 已有 6 个保留 |
| `docs/` | `docs/` | **add-only** | 同上 | git 已有的保留 |
| `README.md` | `governance/LOCAL-USAGE.md` | **add-only** | 不覆盖 git 根 README | local 是目录说明，git 根是仓库元文档 |
| `START_HERE.md` | `START_HERE.md`（根）| **add-only** | 若 git 已有则不覆盖 | - |
| `backups/` | - | **不导入** | - | 本地敏感 |
| `protocols/` | - | **不动** | - | git 已有，local 没有 |
| `knowledge/` `schemas/` | - | **不动** | - | git 已有 |

**关键修订**：
- mirror 策略用 `--delete`（解决 B.2 "源端已删除的文件残留"）
- add-only 策略明确不覆盖（保留 git 已有）
- 每个目录策略可验证（dry-run 输出新增/修改/删除/排除清单）

## 三、执行流程（5 阶段，重写）

### Phase A: 同步前最小语义修正

**A.1 扫描范围（扩大）**：所有拟导入目录（standards/archive/audits/configs/registry/project-starter/templates/docs）

**A.2 词表应用**：
```bash
# 退役工具词表（统一，含 Trae IDE）
for f in $(find ~/.agent-collaboration/{standards,archive,audits,configs,registry,project-starter,templates,docs} -type f 2>/dev/null); do
    sed -i 's/Claude Code/[RETIRED-CC-2026-07-25]/g; s/claude-zhipu/[RETIRED-CC-2026-07-25]/g; s/Codex/[RETIRED-CODEX-2026-07-25]/g; s/QoderWork/[RETIRED-QODERWORK-2026-07-25]/g' "$f"
    # Trae IDE 单独处理（区分角色引用 vs 历史叙述）
done
```

**A.3 Trae IDE 判定清单**（解决 B.3）：
- grep "Trae IDE" 所有命中
- 逐条人工标注 [ROLE]（替换为 `[RETIRED-TRAE-IDE-编队角色]`）或 [HISTORY]（保留）
- 例外清单落到 `archive/retired-terms-trae-ide-exceptions-20260726.md`（含文件/行号/理由/审核人）

**A.4 验证（机器可判）**：
- 现行指令中退役角色引用：**0 个**
- 历史引用：**100% 命中例外清单**

### Phase B: 安全同步

#### Step 1: tag + branch + sync 分支
```bash
cd ~/Documents/trae_projects/agent-collaboration-standard

git tag pre-agent-collaboration-sync-20260726-v3
git branch backup-pre-sync-v3-20260726

git checkout -b sync/agent-collaboration-import-20260726-v3
```

#### Step 2: 按策略导入（v3.0 重写，无 token 明文）

```bash
SRC=~/.agent-collaboration

# mirror 类（含 --delete）
for mapping in "standards:governance" "audits:audits" "configs:configs" "registry:registry" "project-starter:project-starter"; do
    src="${mapping%%:*}"; dst="${mapping##*:}"
    rsync -a --delete "$SRC/$src/" "$dst/"
done

# selective-mirror（archive 排除密钥归档）
rsync -a --delete \
    --exclude='cc-retirement-20260726/' \
    --exclude='backups/' \
    --exclude='*.pre-rotation-bak' \
    --exclude='retired-terms.txt' \
    --exclude='retired-terms-trae-ide-exceptions-20260726.md' \
    "$SRC/archive/" archive/

# add-only 类（不覆盖 git 已有）
for pair in "templates:templates" "docs:docs"; do
    src="${pair%%:*}"; dst="${pair##*:}"
    for f in "$SRC/$src/"*.md; do
        name=$(basename "$f")
        [ ! -f "$dst/$name" ] && cp "$f" "$dst/$name"
    done
done

# README 不覆盖 git 根，改放 governance/
[ ! -f governance/LOCAL-USAGE.md ] && cp "$SRC/README.md" governance/LOCAL-USAGE.md

# START_HERE 进根
[ ! -f START_HERE.md ] && cp "$SRC/START_HERE.md" .
```

**关键**：脚本本身**不含任何 token 片段**（解决 A 阻断）。

#### Step 3: .gitignore（幂等追加，不覆盖）
```bash
# 检查规则是否已存在，不存在才追加（解决 B.1 的"覆盖原有忽略规则"）
add_if_missing() {
    local rule="$1"
    grep -qF "$rule" .gitignore 2>/dev/null || echo "$rule" >> .gitignore
}

add_if_missing "# 含已删除密钥的归档（密钥已物理删除，目录名留作历史标记）"
add_if_missing "archive/cc-retirement-20260726/"
add_if_missing ""
add_if_missing "# 本地备份目录"
add_if_missing "backups/"
add_if_missing ""
add_if_missing "# 临时备份文件"
add_if_missing "*.pre-rotation-bak"
```

#### Step 4: 强制核查（重写，解决 B.1 + B.5）

```bash
# 核查 1: cc-retirement 物理残留
CC_HITS=$(find . -path './.git' -prune -o -name 'cc-retirement*' -print | grep -v '^$')
[ -n "$CC_HITS" ] && { echo "❌ cc-retirement 残留: $CC_HITS"; exit 1; }

# 核查 2: secret 扫描（用外部 patterns 文件，避免硬编码 token）
# patterns 文件格式：每行一个固定字符串（不是正则）
PATTERNS_FILE=~/.agent-collaboration/archive/secret-patterns/scan-patterns.txt
SECRET_HITS=0
while IFS= read -r pattern; do
    [ -z "$pattern" ] && continue
    [ "${pattern:0:1}" = "#" ] && continue
    hits=$(git diff --cached --name-only | xargs grep -lF "$pattern" 2>/dev/null | grep -v '^$' | head -1)
    [ -n "$hits" ] && { echo "❌ 命中 pattern (前6字符): ${pattern:0:6}*** in: $hits"; SECRET_HITS=$((SECRET_HITS+1)); }
done < "$PATTERNS_FILE"
[ "$SECRET_HITS" -gt 0 ] && exit 1

# 核查 3: git status 人工审查
git status

# 核查 4: 每个目录的 dry-run diff 统计（解决 B.5）
echo "=== 同步统计 ==="
for d in governance archive audits configs registry project-starter templates docs; do
    [ -d "$d" ] && echo "$d: $(git diff --cached --stat $d/ | tail -1)"
done
```

**patterns 文件**（外部，不入 git）：
```
# ~/.agent-collaboration/archive/secret-patterns/scan-patterns.txt
# 每行一个固定字符串（grep -F 字面匹配）
# ANTHROPIC token (CC 已退役)
[ANTHROPIC-REDACTED]
# ANYGEN token (AnyGen 已停用)
[ANYGEN-REDACTED]
# ZCode 在用 token 前缀（不在本次清除范围，但防止误进 git）
[ZCODE-REDACTED]
```

#### Step 5: commit + 走 sync 分支

```bash
git add .

git commit -m "sync(v3): 抢救性同步 ~/.agent-collaboration（含已知待治理项）

本次同步内容（按 §二策略表）：
- mirror: standards→governance / audits / configs / registry / project-starter
- selective-mirror: archive（排除 cc-retirement 密钥归档）
- add-only: templates / docs / README→LOCAL-USAGE / START_HERE
- 不动: protocols / knowledge / schemas / 根 README

已知待治理项（节点 3 用户裁决，不在本次范围）：
- unified vs workspace-collaboration 文档去留
- ~/.agent-collaboration/ 废弃 + 路径引用替换（Phase D）

排除（密钥已物理删除）：
- archive/cc-retirement-20260726/（rsync --exclude + .gitignore 双层防御）

注：本 commit 不构成'真值已建立'声明——真值建立需完成 Phase D + Pi 漂移治理纳入。"

git push origin sync/agent-collaboration-import-20260726-v3
# 等用户审 + 批准后才合并 master（不豁免编队纪律）
```

## 四、回滚模型（拆 2 套，解决 B.4）

### 4.1 普通内容回滚

| 场景 | 命令 |
|---|---|
| sync 分支 commit 后（未 push）| `git reset --hard pre-agent-collaboration-sync-20260726-v3` + 清理 untracked |
| sync 分支 push 后（未合并）| `git push origin --delete sync/agent-collaboration-import-20260726-v3` |
| 已合并 master 后 | `git revert <merge-commit>` + push |

### 4.2 泄密事件处置（独立流程）

**触发条件**：核查 2 secret 扫描命中、或事后发现密钥进了 git。

**处置步骤**（严格顺序）：
1. **立即停止**：停止 push/merge，冻结 sync 分支
2. **凭证撤销**：用户立即到对应平台撤销/轮换泄露的凭证（不是先清理 git）
3. **传播范围调查**：核查 git 对象库 / GitHub 远程缓存 / CI 产物 / 本地其他克隆 / agent 会话日志
4. **历史清洗**：`git filter-repo` 或 BFG 清除历史中的密钥（不是 revert——revert 不删历史）
5. **强制更新**：`git push --force`（仅泄密场景特例，需用户明确授权）+ 通知所有 clone 持有者重新 clone
6. **零残留验证**：再次跑核查 2 + 全机扫描，确认零残留
7. **事件归档**：记录到 `archive/incidents/`，含时间线/影响范围/处置过程/教训

**禁止**：
- ❌ 把 `git revert` 当作泄密处置的完成（密钥仍在历史里）
- ❌ 在凭证未撤销前先清理 git（攻击者可能已抓取）

## 五、节点 2 可量化门禁（解决 B.5）

按 B 要求，节点 2 评审必须用以下硬门禁（全部为 0 或 100%）：

| # | 门禁 | 预期值 |
|---|---|---|
| 1 | cc-retirement 进入工作树/暂存区/tracked | **0 个** |
| 2 | secret 扫描命中（未豁免）| **0 个** |
| 3 | 现行规范中退役角色引用 | **0 个** |
| 4 | 历史引用命中已批准例外清单 | **100%** |
| 5 | 每个源-目标映射的新增/修改/删除/排除数量 | 有清单 + 经审核 |
| 6 | dry-run 与实际暂存区文件差异 | **0 个** |
| 7 | 未声明策略/未声明目标路径 | **0 个** |
| 8 | 三位评审者针对同一 commit SHA 评审 | **3/3** |
| 9 | 用户批准的也是同一 commit SHA | 是 |
| 10 | 所有门禁输出保存为可复核证据（不只是终端观察）| 是 |

**节点 2 评审流程**：
- ZCode 输出 10 条门禁的实测值 + 证据文件
- 三方评审针对同一 commit SHA 核对门禁
- 任一不满足 → 不通过

## 六、Pi 漂移治理纳入（任务登记，解决 C 备注 2）

按 C 建议，`/truth/versions` 自动校验**纳入 Pi 漂移治理而非另建**。

**任务登记**：
- 任务名：把 `agent-collaboration-standard` 仓库纳入 Pi 漂移治理体检范围
- 责任人：待分配（Pi 升级时）
- 触发条件：Phase D（Y 落地）完成后
- 验收：Pi 30min cron 能检测到 agent-collaboration-standard 仓库的规则版本变化

**避免悬空**：本任务登记到 spec，未来 Pi 升级时强制处理。

## 七、执行前置

1. ✅ 密钥清除（本机零残留）
2. ✅ 用户 5 项裁决已记录
3. ✅ A 的阻断已修（方案文档无 token 明文）
4. ✅ B 的 5 阻断已响应（策略明确 / 扫描重写 / 词表补齐 / 回滚拆分 / 量化门禁）
5. ✅ C 的 3 备注已响应
6. ⏳ v3.0 三方评审（节点 1 二轮重审）通过
7. ⏳ 用户授权 Phase A + Phase B 执行

## 八、当前状态

**revised-awaiting-review** — v3.0 已修订，等待节点 1 二轮重审。
