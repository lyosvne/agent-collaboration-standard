# 节点 1 重审 — 同步方案 v2.0 修订 diff

## 评审范围（按评审方 C 要求）
仅复核 v1.0 → v2.0 的修订 diff，不重审全文。

## v1.0 评审结论（背景）
- A (opus4.8p): 有条件通过（3 硬门槛）
- B (gpt5.6sol): 不通过（5 阻断）
- C (cantus): 有条件通过（3 条件免重审全文）
- 一致性判断: 不通过（B 反对）

## 用户 5 项裁决（背景）
1. 路径方案: Y（废弃改引用）
2. 密钥: 直接清除（已完成，本机零残留）
3. 同步时机: 同步前最小语义修正 + commit 降级声明
4. push 方式: 走 sync 分支不豁免
5. 评审流程: 不优化（继续三方严审）

## v2.0 核心修订（必须评审）

### 修订 1: Step 2 重写（解决三方共同阻断 1）
- v1.0: cp -r archive/* 会拷密钥
- v2.0: 白名单逐目录 + rsync --exclude='cc-retirement-20260726/' + 不覆盖模式
- 防御层数: 4 层（rsync exclude / 白名单 / .gitignore / Step 4 secret 扫描）

### 修订 2: Phase A 同步前最小语义修正（解决 A/B 阻断 2）
- 新增 Phase A: 退役工具词表（CC/Codex/QoderWork）扫描 + 替换为占位符
- 处理原则: 只改工具作为编队角色的引用，不动历史叙述
- 不替换文档去留（unified vs workspace 仍节点 3 用户裁决）

### 修订 3: commit 降级声明（解决 C 反对点）
- v1.0: commit message 宣告'建立单一真值'
- v2.0: '抢救性同步，含已知待治理项'，明确不构成真值建立声明

### 修订 4: 走 sync 分支（解决 C 反对点 5 + 用户裁决 4）
- v1.0: 直接 push master
- v2.0: sync/agent-collaboration-import-20260726 分支 + 用户批准合并

### 修订 5: X 否决，Y 选定（解决 A/B/C 共识 3）
- X 被评审方 B 证伪（目录结构不兼容，standards/≠governance/）
- Z 三方一致否决（违背北极星 §三.3）
- Y 用户已裁决（Phase 3 单独执行，不在本次范围）

## v2.0 完整文档

---

---
version: 2.0
status: revised-awaiting-review
type: sync-plan
created: 2026-07-26
updated: 2026-07-26
owner: ZCode
title: ~/.agent-collaboration → git 仓库 同步方案 v2.0（修订版）
scope: 把 ~/.agent-collaboration/ 的最新内容安全同步到 agent-collaboration-standard git 仓库
related:
  - specs/o1-governance-plan.md
  - specs/governance-review-process.md
  - specs/key-rotation-guide.md
  - standards/north-star-v1.2.md
  - standards/global-roadmap-v1.1.md
revision_basis: "节点1三方评审（opus4.8p/gpt5.6sol/cantus）共同阻断点 + 用户5项裁决"
supersedes:
  - "v1.0 (本文件历史版本，归档于 archive/governance-review-node1-20260726/)"
---

# 同步方案 v2.0（修订版）

## 一、v1.0 的错误与 v2.0 的修订（评审响应）

### 1.1 三方评审共同识别的阻断点 + v2.0 修订

| # | v1.0 缺陷（A/B/C 评审）| v2.0 修订 |
|---|---|---|
| **1** | Step 2 用 `cp -r archive/*` 会把 cc-retirement 含密钥目录物理拷进 git 工作区，靠 .gitignore 单点防御 | **改为白名单逐目录导入 + rsync --exclude**，源头不带密钥 |
| **2** | 同步会传播已知缺陷（CC 引用未改 / unified vs workspace 双份）| **同步前最小语义修正**：CC/Trae IDE/Codex/QoderWork 退役词表扫描 + 替换为 `[RETIRED-...]` 占位符 |
| **3** | X/Y/Z 选项悬空 | **用户已裁决 Y**（废弃改引用）+ B 已证 X 不可行（目录名不兼容）+ Z 否决 |
| **4** | commit message 预载"真值已建立"（C 反对）| **commit 降级声明**："抢救性同步，含已知待治理项" |
| **5** | 直接 push master 违背编队红线（C 反对）| **走 sync 分支 + 用户批准合并**，不豁免 |
| **6** | 密钥未轮换（A/B/C 都要求）| **已完成密钥清除**（见 key-rotation-guide.md，本机零残留）|

### 1.2 v2.0 不解决（明确推后）的问题

- **unified vs workspace-collaboration 文档去留**：留给节点 3 用户逐份裁决（不可委托）
- **`/truth/versions` 自动校验机制**：按 C 建议，纳入 Pi 漂移治理而非另建（独立任务）
- **path 引用批量替换（Y 落地）**：Phase 3 单独执行，不在本次同步范围

## 二、修订后的执行流程（5 阶段）

### Phase A: 同步前最小语义修正（v2.0 新增）

**目标**：避免把已退役工具的引用作为"真值"同步进 git。

**A.1 退役工具词表**
```python
RETIRED_TERMS = {
    "Claude Code": "[RETIRED-CC-2026-07-25]",
    "claude-zhipu": "[RETIRED-CC-2026-07-25]",
    "Codex": "[RETIRED-CODEX-2026-07-25]",
    "QoderWork": "[RETIRED-QODERWORK-2026-07-25]",
}
```

**A.2 扫描范围**：`~/.agent-collaboration/standards/`、`templates/`、`configs/`

**A.3 处理原则**：
- **只改"工具作为编队角色"的引用**（如 `unified-agent-collaboration-standard.md` 里的 "Trae IDE" 章节应标记退役）
- **不动"工具作为历史背景"的引用**（如某份审计文档说"CC 退役过程..."这种历史叙述保留）
- **不替换文档去留**（unified vs workspace 仍是节点 3 用户裁决）

**A.4 验证**：替换后 grep 退役工具名，确认仅剩"历史叙述"类引用。

### Phase B: 安全同步（Step 1-5，重写版）

#### Step 1: tag + branch + sync 分支
```bash
cd ~/Documents/trae_projects/agent-collaboration-standard

# safety net
git tag pre-agent-collaboration-sync-20260726-v2
git branch backup-pre-sync-v2-20260726

# 创建 sync 分支（不直接 push master）
git checkout -b sync/agent-collaboration-import-20260726
```

**修订**：用 sync 分支，不豁免编队纪律（C 反对点 5）。

#### Step 2: 白名单逐目录导入（v1.0 Step 2 完全重写）

**核心修订**：不再用 `cp -r` + .gitignore 兜底，改为**显式白名单 + rsync --exclude**。

```bash
# 白名单：明确允许导入的目录
ALLOWED_DIRS=(
    "standards:governance"        # local:standards/ → git:governance/
    "archive:archive"             # 但 rsync --exclude cc-retirement
    "audits:audits"
    "configs:configs"
    "registry:registry"
    "project-starter:project-starter"
)

for mapping in "${ALLOWED_DIRS[@]}"; do
    src="${mapping%%:*}"
    dst="${mapping##*:}"
    mkdir -p "$dst"
    # rsync 带排除，源头不带 cc-retirement（绝对防御层 1）
    rsync -a --exclude='cc-retirement-20260726/' \
              --exclude='*.pre-rotation-bak' \
              --exclude='backups/' \
              ~/.agent-collaboration/$src/ $dst/
done

# templates: 只补齐 local 多的（不覆盖 git 已有 6 个）
for f in ~/.agent-collaboration/templates/*.md; do
    name=$(basename "$f")
    if [ ! -f "templates/$name" ]; then
        cp "$f" "templates/$name"
    fi
done

# docs: 合并（local 多的加进去，git 已有的保留）
for f in ~/.agent-collaboration/docs/*.md; do
    name=$(basename "$f")
    if [ ! -f "docs/$name" ]; then
        cp "$f" "docs/$name"
    fi
done

# README: 不覆盖 git 根 README，local 版本改放 governance/
if [ ! -f "governance/LOCAL-USAGE.md" ]; then
    cp ~/.agent-collaboration/README.md governance/LOCAL-USAGE.md
fi

# START_HERE: 进 git 根
cp ~/.agent-collaboration/START_HERE.md .
```

**关键防御**：
- 防御层 1：rsync `--exclude='cc-retirement-20260726/'`（源头不带）
- 防御层 2：白名单（只导入 ALLOWED_DIRS，其他都不动）
- 防御层 3：.gitignore（Step 3 会加）
- 防御层 4：commit 前 secret 扫描（Step 4 强制）

#### Step 3: .gitignore 保护
```bash
cat > .gitignore <<EOF
# 含已删除密钥的归档（密钥已物理删除，但目录名留作历史标记）
archive/cc-retirement-20260726/

# 本地备份目录
backups/

# 临时备份文件
*.pre-rotation-bak
EOF
```

#### Step 4: 强制核查 + commit
```bash
# 核查 1: cc-retirement 是否被带入
if find . -path './.git' -prune -o -name 'cc-retirement*' -print | grep -v '^$'; then
    echo "❌ cc-retirement 残留，停止 commit"
    exit 1
fi

# 核查 2: secret 扫描（退役 token 前缀）
SECRET_HITS=$(grep -rE "[ANTHROPIC-REDACTED]|[ANYGEN-REDACTED]|sk-ag-[a-zA-Z0-9]{20}" . --include='*.md' --include='*.json' --include='*.jsonl' 2>/dev/null | grep -v './.git/')
if [ -n "$SECRET_HITS" ]; then
    echo "❌ 发现疑似密钥残留:"
    echo "$SECRET_HITS"
    echo "停止 commit，人工审查"
    exit 1
fi

# 核查 3: git status 人工审查
git status

# 用户确认后 commit
git add .
git commit -m "sync(v2): 抢救性同步 ~/.agent-collaboration（含已知待治理项）

本次同步内容：
- standards/ → governance/（4 DIFF + 6 NEW specs）
- 新增 archive/audits/configs/registry/project-starter（历史从未进 git）
- templates/ 补齐 11 个 + docs/ 合并 + 根 START_HERE.md

已知待治理项（节点 3 处理，不在本次范围）：
- unified vs workspace-collaboration 文档去留（用户裁决）
- 退役工具引用的最小语义修正（Phase A 已做）
- ~/.agent-collaboration/ 废弃 + 路径引用替换（Phase 3）

排除（密钥已物理删除，目录名留作历史）：
- archive/cc-retirement-20260726/（rsync --exclude + .gitignore 双层防御）

注：本 commit 不构成'真值已建立'声明——真值建立需完成 Phase 3（Y 落地）+ Pi 漂移治理纳入（自动校验）。"
```

**修订**：commit message 改为"抢救性同步，含已知待治理项"（不预载真值声明，C 反对点）。

#### Step 5: 走 sync 分支 + 用户批准合并
```bash
# push sync 分支（不直接 push master）
git push origin sync/agent-collaboration-import-20260726

# 等用户审 + 批准后，合并到 master
# git checkout master
# git merge sync/agent-collaboration-import-20260726
# git push origin master
# git branch -d sync/agent-collaboration-import-20260726
```

**修订**：走 sync 分支 + 用户批准合并，不豁免（C 反对点 5 + 用户裁决 4）。

### Phase C: 节点 2 评审（三方）

**评审对象**：sync 分支的实际 diff（`git diff master...sync/agent-collaboration-import-20260726`）

**门槛**：三方一致通过才合并到 master。

### Phase D: 废弃 ~/.agent-collaboration/（Y 落地，Phase 3）

合并到 master 后：
1. 把 `~/.agent-collaboration/` 整体重命名为 `~/.agent-collaboration.deprecated-20260726/`（保留一段时间作回退）
2. 全机搜路径引用 `~/.agent-collaboration/`，批量替换为 git 仓库路径
3. 验证所有编队成员读的是 git 仓库
4. 稳定后删除 deprecated 目录

**说明**：Y 落地是独立 Phase，不在本次同步范围。

## 三、风险与回滚

### 3.1 风险（修订后）

| 风险 | 等级 | 缓解 |
|---|---|---|
| 密钥误进 git | ⚠️ 低（4 层防御）| rsync exclude + 白名单 + .gitignore + Step 4 secret 扫描 |
| 覆盖 git 已有内容 | ⚠️ 低 | sync 分支 + 不覆盖模式（templates/docs/README 都判断存在性）|
| 错误内容被提升为权威 | ⚠️ 低 | commit 降级声明 + 节点 2 三方评审 |
| push 后 GitHub 历史改变 | ✅ 极低 | 走 sync 分支，用户批准才合并 master |

### 3.2 回滚

| 场景 | 命令 |
|---|---|
| sync 分支 commit 后发现问题（未 push）| `git reset --hard pre-agent-collaboration-sync-20260726-v2` |
| sync 分支 push 后发现问题 | `git push origin --delete sync/agent-collaboration-import-20260726` |
| 已合并 master 后发现问题 | `git revert <merge-commit>` + push |

## 四、与节点 1 评审的关系

### 4.1 修订后是否需要重审

按 B 要求"修订后重新提交节点 1 评审"——**v2.0 必须再走一轮三方评审**。

按 C 要求"满足条件后免重审计划全文，仅需复核修订 diff"——**重审范围限定为 v1.0 → v2.0 的 diff**（本文档 §一 + §二的修订部分）。

### 4.2 重审材料
- 本文档（v2.0）
- v1.0 评审三方原文（archive/governance-review-node1-20260726/）
- 用户 5 项裁决（Y / 清除 / 最小修正+降级 / sync 分支 / 评审不优化）
- 密钥清除验证结果（zero residue）

## 五、执行前置

1. ✅ 密钥清除完成（本机零残留）
2. ✅ 用户 5 项裁决已记录
3. ⏳ v2.0 三方评审（节点 1 重审）通过
4. ⏳ 用户授权 Phase A + Phase B 执行

## 六、当前状态

**revised-awaiting-review** — v2.0 已修订，等待节点 1 重审。
