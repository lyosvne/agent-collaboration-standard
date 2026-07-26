# 节点 1 四轮重审（定点复核）— v3.2

## 复核范围（极小）
v3.1 → v3.2 修了 6 点：
1. 方案文档修订对照表的 token 引用清除（A v3.1 阻断）
2. 扫描改 git grep --cached（B.1 + C）
3. patterns 文件空转断言（B + C）
4. 暂存区空校验（B）
5. 词表分两步（B.3 真问题）
6. .review-evidence 加 .gitignore（A v3.1 小瑕）

请仅核对你之前提的阻断是否在 v3.2 闭环。

## v3.2 完整文档

---

---
version: 3.2
status: revised-awaiting-review
type: sync-plan
created: 2026-07-26
updated: 2026-07-26
owner: ZCode
title: ~/.agent-collaboration → git 仓库 同步方案 v3.2（修订版）
scope: 把 ~/.agent-collaboration/ 的最新内容安全同步到 agent-collaboration-standard git 仓库
related:
  - specs/o1-governance-plan.md
  - specs/governance-review-process.md
  - specs/key-rotation-guide.md
  - standards/north-star-v1.2.md
  - standards/global-roadmap-v1.1.md
revision_basis: "节点1定点复核（A token残留 / B.1扫描实现 + B.3词表 + patterns空转 / C git grep建议）"
supersedes:
  - "v3.1 / v3.0 / v2.0 / v1.0 (历史版本)"
---

# 同步方案 v3.2（修订版）

## 〇、v3.1 → v3.2 修订（响应 A/B/C 定点复核）

| 评审方阻断/备注 | v3.2 修订 |
|---|---|
| **A**: 方案文档修订对照表引用 token 片段作为"错误示例" | 已清除（修订对照表用"已退役 ANTHROPIC + ANYGEN token"描述，不写明文）|
| **B.1 / C**: 扫描用 `xargs grep` 读工作树不是 staged blob，文件名空格断裂 | 改用 `git grep --cached -l -F`（直接扫暂存区 blob，无 xargs）|
| **B / C**: patterns 文件空转风险（全占位符时 SECRET_HITS=0 假通过）| Step 4 加 patterns 有效性校验（< 1 个有效 pattern 直接 fail）|
| **B**: 暂存区空时静默通过 | Step 4 加暂存区非空校验（STAGED_COUNT=0 直接 fail）|
| **B.3**: 词表无差别全局替换跟"历史叙述保留"原则冲突 | Phase A 改分两步：生成命中清单 → 人工标注 [ROLE]/[HISTORY] → 只替换 [ROLE]，例外清单归档 |
| **A v3.1 小瑕**: `.review-evidence/` 游离 untracked | Step 4 加 `.gitignore` 排除 |

## 〇、v2.0 → v3.0 修订对照（评审响应）

### 评审方 A 的阻断（必须修）

| A 的阻断 | v3.0 修订 |
|---|---|
| 方案文档 line 163 含完整 token 字符串（已退役 ANTHROPIC + ANYGEN token）作为 grep 模式，导致 Step 4 扫到自己 | **扫描模式从硬编码改为外部 secret-patterns 文件 + 高熵通用正则**，方案文档不再含任何 token 片段 |

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

### Phase A: 同步前最小语义修正（v3.2 修订：词表分两步，区分角色 vs 历史）

**v3.0/v3.1 错误**：A.2 用 sed 无差别全局替换退役词，跟"历史叙述保留"原则冲突（B.3）。
**v3.2 修订**：词表分两步——先生成命中清单 + 人工标注 [ROLE]/[HISTORY]，再只替换 [ROLE]。

**A.1 扫描范围**：所有拟导入目录（standards/archive/audits/configs/registry/project-starter/templates/docs）

**A.2 第一步：生成命中清单（机器）**
```bash
# 扫描所有退役工具的命中位置，输出待人工标注的清单
RETired_TERMS_LIST=(
    "Claude Code"
    "claude-zhipu"
    "Codex"
    "QoderWork"
    "Trae IDE"
)

OUTPUT=~/.agent-collaboration/archive/retired-terms-hits-20260726.md
echo "# 退役工具引用命中清单（待人工标注）" > "$OUTPUT"
echo "" >> "$OUTPUT"

for term in "${RETired_TERMS_LIST[@]}"; do
    echo "## $term" >> "$OUTPUT"
    grep -rn "$term" ~/.agent-collaboration/{standards,archive,audits,configs,registry,project-starter,templates,docs} 2>/dev/null | \
    while IFS=: read -r file line content; do
        # 简单启发式预标注（人工复核）
        if echo "$content" | grep -qE "退役|retire|历史|归档|已删|previous|was|had been"; then
            tag="[HISTORY?]"
        else
            tag="[ROLE?]"
        fi
        echo "- [ ] $tag $file:$line: $(echo "$content" | head -c 100)" >> "$OUTPUT"
    done
    echo "" >> "$OUTPUT"
done

echo "清单已生成: $OUTPUT"
echo "请人工逐条复核 [ROLE?]/[HISTORY?] 标注，确认后改为 [ROLE]/[HISTORY]"
```

**A.3 第二步：人工标注（用户或 ZCode 逐条确认）**

逐条核对：
- `[ROLE]`：工具作为编队角色（如"Trae IDE 是平行工作者"）→ 替换为 `[RETIRED-...]`
- `[HISTORY]`：工具作为历史叙述（如"CC 退役过程中..."）→ 保留

**例外清单格式**（落到 `archive/retired-terms-exceptions-20260726.md`）：
```markdown
| 文件 | 行号 | 工具 | 标注 | 理由 | 审核人 |
|---|---|---|---|---|---|
| standards/unified-...md | 130 | Trae IDE | HISTORY | "Trae IDE 退役过程" 历史叙述 | ZCode |
| standards/unified-...md | 24 | Trae IDE | ROLE | "Trae IDE 是平行工作者" 当前角色 | ZCode |
```

**A.4 第三步：仅替换 [ROLE]（保留 [HISTORY]）**
```bash
# 读取例外清单，只替换标注为 [ROLE] 的行
while IFS='|' read -r _ file line tool tag reason _; do
    file=$(echo "$file" | tr -d ' ')
    line=$(echo "$line" | tr -d ' ')
    tag=$(echo "$tag" | tr -d ' ')
    tool=$(echo "$tool" | tr -d ' ')

    if [ "$tag" = "ROLE" ]; then
        # 替换该行的工具名为占位符
        case "$tool" in
            "Claude Code") placeholder="[RETIRED-CC-2026-07-25]" ;;
            "claude-zhipu") placeholder="[RETIRED-CC-2026-07-25]" ;;
            "Codex") placeholder="[RETIRED-CODEX-2026-07-25]" ;;
            "QoderWork") placeholder="[RETIRED-QODERWORK-2026-07-25]" ;;
            "Trae IDE") placeholder="[RETIRED-TRAE-IDE-编队角色]" ;;
        esac
        sed -i "${line}s/$tool/$placeholder/g" "$HOME/.agent-collaboration/$file"
    fi
done < <(grep '| ROLE |' ~/.agent-collaboration/archive/retired-terms-exceptions-20260726.md)
```

**A.5 验证（机器可判，对应 B 的门禁 3/4）**
```bash
# 门禁 3: 现行规范中退役角色引用 = 0
REMAINING_ROLE=$(grep -rn "Claude Code\|Codex\|QoderWork\|Trae IDE" ~/.agent-collaboration/standards/ 2>/dev/null | \
    grep -v "\[RETIRED-\|退役\|retire\|历史\|归档\|已删" | head -1)
[ -n "$REMAINING_ROLE" ] && { echo "❌ 现行角色引用未清零: $REMAINING_ROLE"; exit 1; }
echo "✅ 现行角色引用: 0"

# 门禁 4: 历史引用 100% 命中例外清单
EXCEPTION_COUNT=$(grep -c '| HISTORY |' ~/.agent-collaboration/archive/retired-terms-exceptions-20260726.md)
HISTORY_HITS=$(grep -rn "Claude Code\|Codex\|QoderWork\|Trae IDE" ~/.agent-collaboration/standards/ 2>/dev/null | \
    grep -E "退役\|retire\|历史\|归档\|已删" | wc -l)
echo "历史引用: $HISTORY_HITS 处 / 例外清单: $EXCEPTION_COUNT 条"
# 注：可能不完全相等（一处例外清单条目可能对应多处引用），需人工核对覆盖率
```

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

#### Step 4: git add + 强制核查（v3.2 修订：git grep --cached + patterns 校验）

**v3.0 错误**：扫描在 git add 之前执行，暂存区为空，扫描永远零命中（B/C 阻断）。
**v3.1 修订**：先 `git add .` 把变更放入暂存区，再扫描暂存区实际内容。
**v3.2 修订**：扫描改用 `git grep --cached`（直接扫暂存区 blob，不读工作树，解决 B.1 + C 备注）；patterns 文件加有效性校验（解决 B 的 patterns 空转风险 + C 备注）。

```bash
# 1. 先把所有变更放入暂存区
git add .

# 2. 核查：cc-retirement 物理残留
CC_HITS=$(find . -path './.git' -prune -o -name 'cc-retirement*' -print | grep -v '^$')
[ -n "$CC_HITS" ] && { echo "❌ cc-retirement 残留: $CC_HITS"; git reset; exit 1; }

# 3. 校验 patterns 文件存在且有效（解决 B/C 的 patterns 空转风险）
PATTERNS_FILE=~/.agent-collaboration/archive/secret-patterns/scan-patterns.txt
[ ! -f "$PATTERNS_FILE" ] && { echo "❌ patterns 文件不存在"; git reset; exit 1; }
[ ! -r "$PATTERNS_FILE" ] && { echo "❌ patterns 文件不可读"; git reset; exit 1; }

# 提取有效 patterns（跳过注释、空行、占位符）
VALID_PATTERNS=$(grep -vE '^\s*#|^\s*$|^\s*<' "$PATTERNS_FILE")
VALID_COUNT=$(echo "$VALID_PATTERNS" | grep -c .)
[ "$VALID_COUNT" -lt 1 ] && { echo "❌ patterns 文件无有效 pattern（全占位符？）"; git reset; exit 1; }
echo "有效 pattern 数: $VALID_COUNT"

# 4. 暂存区非空校验（解决 B：暂存区空不能静默通过）
STAGED_COUNT=$(git diff --cached --name-only | wc -l)
[ "$STAGED_COUNT" -eq 0 ] && { echo "❌ 暂存区为空（同步未生效？）"; exit 1; }

# 5. secret 扫描：用 git grep --cached 直接扫暂存区 blob（解决 B.1 + C）
# 不读工作树，避免文件名空格/换行导致 xargs 断裂
SECRET_HITS=0
while IFS= read -r pattern; do
    [ -z "$pattern" ] && continue
    # git grep --cached 扫暂存区，-l 只显示文件名，-F 字面匹配
    hits=$(git grep --cached -l -F "$pattern" 2>/dev/null | head -1)
    [ -n "$hits" ] && {
        echo "❌ 命中 pattern (前6字符): ${pattern:0:6}*** in: $hits"
        SECRET_HITS=$((SECRET_HITS+1))
    }
done <<< "$VALID_PATTERNS"

if [ "$SECRET_HITS" -gt 0 ]; then
    echo "❌ secret 扫描未通过（$SECRET_HITS 处命中），已 reset 暂存区"
    git reset
    exit 1
fi
echo "✅ secret 扫描通过（0 命中）"

# 6. 核查：git status 人工审查
git status

# 7. 暂存区统计（解决 B.5）
echo "=== 暂存区统计 ==="
git diff --cached --stat

# 8. 保存核查证据（解决 B.5 门禁 10）+ 加入 .gitignore（解决 A v3.1 小瑕）
mkdir -p .review-evidence
grep -qF '.review-evidence/' .gitignore 2>/dev/null || echo '.review-evidence/' >> .gitignore
{
    echo "# 节点 2 核查证据 $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo ""
    echo "## cc-retirement 检查"
    [ -z "$CC_HITS" ] && echo "✅ 0 命中" || echo "$CC_HITS"
    echo ""
    echo "## patterns 文件"
    echo "有效 pattern 数: $VALID_COUNT"
    echo ""
    echo "## 暂存区"
    echo "文件数: $STAGED_COUNT"
    echo ""
    echo "## secret 扫描"
    echo "命中数: $SECRET_HITS"
    echo ""
    echo "## 暂存区统计"
    git diff --cached --stat
} > .review-evidence/node2-checks-$(date +%Y%m%d-%H%M%S).md
echo "证据已保存到 .review-evidence/（已加入 .gitignore，不入 git）"
```

**patterns 文件**（外部，不入 git；**本方案文档不含任何真实 token 片段**，执行时由用户/ZCode 在 patterns 文件里填入）：
```
# ~/.agent-collaboration/archive/secret-patterns/scan-patterns.txt
# 每行一个固定字符串（grep -F 字面匹配）
# 执行时由 ZCode 填入真实 token 前缀（不写入本方案文档，避免文档本身成泄露源）
<anthropic-token-prefix>     # 例：8-12 字符前缀，足以唯一定位
<anygen-token-prefix>        # 例：8-12 字符前缀
<zcode-active-token-prefix>  # ZCode 在用 token 前缀（防误进 git）
```

#### Step 5: commit + 走 sync 分支（v3.1：git add 已在 Step 4 前移）

```bash
# git add . 已在 Step 4 执行（v3.1 前移）
# 此处只做 commit（前提：Step 4 全部核查通过）

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
