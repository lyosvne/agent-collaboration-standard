# 维护规格：scripts/ 工具脚本归属与生命周期

> 签发: ZCode（出规格）| Review: 待对等互检 | 裁定: 用户 | 日期: 2026-07-28
> 状态: active（源码可直读，无待补完项）
> 依据: `scripts/*.py` 10 个文件 docstring + `global-roadmap-v1.1.md` Phase D-B 历史（L197-203）
> 缺口来源: `global-roadmap-v1.1.md` L247「scripts/ 工具脚本长期维护归属（5 个 .py 无 spec）」——**实际为 10 个，roadmap 数字滞后，本 spec 修正**
> 变更前置: 改本文件 → 走 `governance-review-process.md §四` pre-commit 三方评审（spec 属真值层）

---

## 1. 为什么需要这个 spec

**问题**：scripts/ 下积累了 10 个 Python 脚本，分属 4 类职能、3 个历史阶段，但**没有任何一个 spec 声明它们的归属、生命周期、依赖关系**。后果：
- 不知道哪些是"常驻被依赖"（删了会断 hook）、哪些是"一次性用完可删"
- Phase D-B 时已经因"路径硬编码"踩过坑（roadmap L198：7 个脚本路径常量切环境变量 + git 仓库 fallback）
- 新增脚本无规范，会继续无序积累

**本 spec 的职能**：给 scripts/ 每个文件钉死「分类 / 谁依赖它 / 何时可删 / 改动前置」，让后续维护有据可依。

---

## 2. 分类总表（10 个脚本，源码 docstring 直读）

### 2.1 Lint 类（常驻，被 hook/governance 依赖，**不可删**）

| 脚本 | 职能 | 谁依赖 | 触发时机 |
|------|------|--------|----------|
| `check-hook-order.py` | 校验 `.zcode/config.json` PreToolUse Bash 顺序契约（bootstrap-gate 必须第 1 位）| AGENTS.md「全套验证命令」+ governance-infrastructure-status.md | 改 config.json 后手动跑（SO-13 #8 子任务：接入 drift-gate 自动跑，待做）|
| `check-reviewer-tiers-drift.py` | 校验 reviewer-tiers.yaml（档位）与 spec §二 markdown 表 + mira-integration-status 平台清单一致 | `tiers-drift-gate-postuse.py` hook（PostToolUse）+ AGENTS.md 验证命令 | 改 reviewer-tiers.yaml 后自动跑（drift-gate）+ 手动跑 |

**生命周期**：常驻。只要 hook 机制在，这两个 lint 就在。删除 = 断 hook 依赖 = 治理失效。

### 2.2 门禁执行器（Phase B v3.4，一次性主任务但保留作回溯）

| 脚本 | 职能 | 状态 |
|------|------|------|
| `gate-checks.py` | v3.4 Phase B Step 4 门禁执行器（fail-closed）：4 条门禁（cc 残留=0 / secret=0 / 现行角色=0 / 历史引用 100% 命中例外）+ 证据落盘 | 一次性主任务已完成（Phase D 验收），保留作"退役清理回溯"工具 |

**生命周期**：保留。CC 退役清理虽已完成，但未来若有新 agent 退役（如 Codex 残留复查），此脚本可复用。无主动依赖，但删除会损失回溯能力。

### 2.3 门禁辅助（Phase B v3.4，生成/维护门禁数据）

| 脚本 | 职能 | 依赖关系 |
|------|------|----------|
| `complete-exceptions.py` | 补全例外清单 HISTORY 部分（逐条 file:line\|tool，供门禁 4 集合比对）| 产出门禁 4 消费的数据 |
| `rebuild-exceptions.py` | 重建例外清单（ROLE 保留 + HISTORY 逐条登记），覆盖重写 | complete-exceptions 的"全量重建"版本 |
| `gen-scan-patterns.py` | 从 redact-map.txt 派生 scan-patterns.txt（节点2 round2 修复：覆盖退役 token 4d0b/bcVs/JaZK）| 产出门禁 2 消费的 patterns |
| `list-hits.py` | 列出门禁命中明细 + 分类，供人工过目 | gate-checks 的只读诊断版 |
| `analyze-gate3.py` | 临时分析门禁 3 命中分布（**docstring 自标"用完可删"**）| ⚠️ 可删 |
| `redact-tokens.py` | 脱敏 archive 评审归档 + specs 的 token 片段（不硬编码 token，从 redact-map.txt 读）| 产出门禁 2 消费的脱敏数据 |

**生命周期**：
- `complete-exceptions` / `rebuild-exceptions` / `gen-scan-patterns` / `redact-tokens`：保留，门禁数据维护工具，未来 token 轮换 / 角色退役时会再用
- `list-hits`：保留，只读诊断，无害
- `analyze-gate3`：**可删**（docstring 自标"用完可删"，是临时分析脚本）——删除需用户授权（红线：删文件）

### 2.4 同步工具（Phase B.2，已降级）

| 脚本 | 职能 | 状态 |
|------|------|------|
| `mirror-sync.py` | rsync 语义的 Python 实现（mirror/selective-mirror/add-only），git 仓库无 rsync 时的替代 | **`--apply` 已禁用**（Phase D 后原方向会覆盖 git 真值，roadmap L201）|

**生命周期**：保留但功能受限。`--apply` 禁用后只剩只读镜像能力。未来若清理本机 `~/.agent-collaboration/` 快照（roadmap 第 5 批长期卫生），此脚本可一并评估退役。

---

## 3. 共性约定（Phase D-B 已建立，本 spec 固化）

### 3.1 路径常量（roadmap L198 实证）

7 个脚本（gate-checks / rebuild-exceptions / complete-exceptions / analyze-gate3 / list-hits / gen-scan-patterns / redact-tokens）的路径常量已切**环境变量 + git 仓库 fallback**：

```python
REPO = Path(__file__).resolve().parents[1]  # 统一从脚本位置推导，避免跨 checkout 混读
STANDARDS = os.environ.get("STANDARDS_DIR") or REPO / "governance"  # 扫描基准切 git 仓库真值
```

**红线**：新增脚本**禁止硬编码**本机绝对路径（如 `C:\Users\Admin\...`）。必须用 `Path(__file__).resolve().parents[N]` 推导 + 环境变量 fallback。违反 = 跨机器/跨 checkout 漂移（round4 A+B 共识阻断教训）。

### 3.2 敏感配置归属（roadmap L200）

- `secret-patterns/`（门禁工具的敏感配置：redact-map.txt / scan-patterns.txt）→ 迁到 `~/.config/agent-collaboration/secret-patterns/`（**非治理真值，不进 git**）
- 治理真值（reviewer-tiers.yaml / specs）→ 留 git 仓库 `governance/`

**判断准则**：脚本是"读治理真值做校验"还是"持有敏感配置"？前者路径指向 git 仓库，后者指向 `~/.config/`。

### 3.3 fail-closed 语义（roadmap L203）

门禁类脚本（gate-checks / check-*）必须 fail-closed：
- 默认配置缺失 → exit 1（不是静默通过）
- fallback 目录不存在 → exit 1
- rebuild 重建后 → exit 0

**已验证**：4 个 fail-closed 测试全过（默认 / fallback / 不存在目录 exit 1 / rebuild 后，roadmap L203）。

---

## 4. 新增脚本的准入门槛

未来往 scripts/ 加新脚本，必须满足：

1. **docstring 头部**声明：职能 / 所属分类（§2.1-2.4 之一）/ 依赖方 / 生命周期（常驻 or 一次性）
2. **路径常量**用 `Path(__file__).resolve().parents[N]` + 环境变量 fallback（§3.1）
3. **敏感配置**不硬编码（§3.2），token 类从外部文件读
4. **本 spec §2 总表登记**：新增行声明分类 + 依赖 + 生命周期
5. **若属 lint 类**（§2.1）：必须接入 AGENTS.md「全套验证命令」+ 评估是否接入 drift-gate 自动触发

---

## 5. 变更前置

| 改动类型 | 前置 |
|----------|------|
| 新增脚本 | §4 准入门槛 + 本 spec 登记 |
| 改 lint 类脚本（check-*）| 走 `governance-review-process.md §四` pre-commit 三方评审（被 hook 依赖，改错 = 治理失效）|
| 改门禁执行器（gate-checks）| 走评审（fail-closed 语义是安全边界）|
| 改门禁辅助（complete/rebuild/gen/redact）| 走评审（产出数据被门禁消费）|
| 改同步工具（mirror-sync）| 走评审（roadmap L201 `--apply` 禁用是红线）|
| 删除任何脚本 | **红线：必须先问用户**（AGENTS.md 自主边界）|
| 改 docstring / 注释 | 无需评审（非逻辑变更）|

---

## 6. 与其他 spec 的关系

| 关联 spec | 关系 |
|-----------|------|
| `governance-infrastructure-status.md` | check-hook-order / check-reviewer-tiers-drift 在「生效 hook 清单 + 验证命令」中引用 |
| `governance-review-process.md §8.4` | 本目录脚本变更的前置评审触发条款 |
| `pi-drift-governance-spec.md` | mirror-sync 的上游语义（governance-mirror 同步方向）|
| `review-process-lessons.md` | Phase D-B 路径硬编码 / fail-closed 教训来源 |

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-07-28 | ZCode 起草：盘点 10 个脚本（修正 roadmap「5 个」滞后数字）+ 4 分类 + 共性约定 + 准入门槛 + 变更前置。闭合 roadmap 缺口 #7 |
