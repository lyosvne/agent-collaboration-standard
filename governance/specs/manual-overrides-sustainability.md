# 维护规格：manual-history-overrides 可持续性方案

> 签发: ZCode（出规格）| Review: 待对等互检 | 裁定: 用户 | 日期: 2026-07-28
> 状态: active（方案 spec，改进项待排期）
> 依据: `scripts/rebuild-exceptions.py` + `scripts/gate-checks.py`（双 `_load_manual_overrides` 实现）+ `archive/retired-terms-manual-history-overrides-20260726.md`（67 条）+ `archive/retired-terms-exceptions-20260726.md`（146 条）
> 缺口来源: `global-roadmap-v1.1.md` L248「manual-history-overrides 可持续性（人工 override + 双解析函数会漂移；每次文档增行要 rebuild-exceptions）」
> 变更前置: 改本文件 → 走 `governance-review-process.md §四` pre-commit 三方评审

---

## 1. 机制是什么（现状描述）

### 1.1 两个文件

| 文件 | 条目数 | 职能 |
|------|--------|------|
| `archive/retired-terms-exceptions-20260726.md` | 146 | 例外清单（ROLE 替换表 + HISTORY 逐条登记），gate4 集合比对的基准 |
| `archive/retired-terms-manual-history-overrides-20260726.md` | 67 | 人工确认 HISTORY 覆盖清单，classify raise 时的"逃生通道" |

### 1.2 为什么需要 overrides

**问题链**（round1→round4 演进）：
- round1 v3.4：classify() 所有分支返回 HISTORY，永不抛错 → 现行角色引用被静默吸收成 HISTORY → **tautology fail-open**（A/B round1 阻断）
- round2：信任 exceptions + 历史关键词兜底 → classify 仍宽泛 → 同样 fail-open（A/B/C round2 阻断）
- round3：完全移除 exceptions 信任，纯启发式判定 → 但合法 HISTORY（知识资产/迁移/兼容性方案代码）不含历史关键词，会被误判为现行角色 → **过度阻断**
- round4（当前）：classify 最严收窄，未命中已知模式 → raise `UnclassifiedHit` 强制人工判定；人工判定为 HISTORY 的写入 overrides 文件，gate3/gate4 信任它

**本质**：overrides 是"启发式判不准时的人工兜底"。它**不是 tautology**（round4 设计关键）——因为是 ZCode 逐条人工判定，不是自动分类后自我登记。

### 1.3 数据流

```
新增文档（含退役词命中）
    │
    ▼
rebuild-exceptions.py 扫描 → classify() 收到最严收窄
    │
    ├── 命中已知 HISTORY 模式（退役/归档/历史关键词 + archive/ 目录）→ 自动归 HISTORY
    │
    └── 未命中 → raise UnclassifiedHit（fail-closed，不默认归 HISTORY）
                │
                ▼
        ZCode 逐条人工判定
            ├── 现行角色 → 走 Phase A 替换（不入 overrides）
            └── 合法 HISTORY → 写入 manual-history-overrides（附判定理由）
                                │
                                ▼
                    下次 rebuild：命中 overrides → 直接归 HISTORY（跳过 classify）
                    gate3/gate4：信任 overrides（人工确认，非 tautology）
```

---

## 2. 三个可持续性问题（roadmap L248 指出）

### 2.1 文件名带日期 `20260726`（语义错位）

**问题**：文件名 `retired-terms-manual-history-overrides-20260726.md` 暗示"2026-07-26 的一次性产物"，但实际是**持续维护的活文件**（头注写"新增退役工具引用若被 raise 且确属 HISTORY, 加到此清单"）。日期后缀让人误以为可归档/可删。

**风险**：未来 agent 看到 `20260726` 后缀，可能误判为历史快照而不维护，或 rebuild 时写新日期文件名导致路径断裂。

### 2.2 双解析函数漂移（`_load_manual_overrides`）

**问题**：同一个解析逻辑在两处独立实现：
- `scripts/rebuild-exceptions.py` L48-71 `load_manual_overrides()`
- `scripts/gate-checks.py` L384-404 `_load_manual_overrides()`

两者解析同一个文件，但实现独立。若 overrides 文件格式微调（如改分隔符、加新字段段），改了一处忘另一处 → rebuild 生成的 exceptions 与 gate-checks 校验的基准不一致 → **静默漂移**。

**实证**：当前两份实现解析逻辑一致（都按 `file:line|tool` 键解析），但无单一真值源保证。

### 2.3 rebuild 门槛高（每次文档增行触发）

**问题**：新增 governance 文档若含退役词（如讨论 Claude Code 退役历史），会触发新命中 → classify raise → 必须人工判定 + 跑 rebuild-exceptions + 跑 gate-checks 验证。这是**每次写治理文档的隐性成本**。

**现状缓解**：round4 已收窄到"最严"，合法 HISTORY 多数能被关键词/archive 目录命中自动归类，raise 频率低。但只要 raise，就必须人工介入。

---

## 3. 改进方案（按可行性排序）

### 方案 A：去日期后缀 + 文件名稳定化（低成本，立即可做）

**改动**：
- `retired-terms-manual-history-overrides-20260726.md` → `retired-terms-manual-history-overrides.md`
- `retired-terms-exceptions-20260726.md` → `retired-terms-exceptions.md`
- 改 rebuild-exceptions.py / gate-checks.py 的 `EXC_FILE` / `OVERRIDES_FILE` 常量
- 旧文件 git mv（保留历史）或建 symlink

**收益**：消除"日期后缀暗示一次性"的语义错位。
**成本**：改 2 个脚本常量 + git mv 2 个文件。
**前置**：改脚本属 lint/门禁类，走 pre-commit 评审（§变更前置）。

### 方案 B：解析函数提取共享模块（中成本，根除双源漂移）

**改动**：
- 新建 `scripts/_exceptions_common.py`，含 `load_manual_overrides()` + `load_exception_keys()` 单一实现
- rebuild-exceptions.py / gate-checks.py 改为 `from _exceptions_common import ...`

**收益**：单一真值源，格式变更只改一处。
**成本**：新建共享模块 + 改 2 个脚本 import + 测试。
**前置**：同方案 A，走评审。
**风险**：import 失败时两个脚本都崩（参考 SO-12 `_bootstrap_common.py` 的 try import + fallback 经验，建议加 fallback）。

### 方案 C：overrides 自描述化（高成本，根除 rebuild 门槛）

**改动**：overrides 文件每条加"判定理由 + 触发条件"结构化字段，让 classify 能自动识别多数合法 HISTORY，减少 raise：
```markdown
| file:line|tool | 判定理由 | 触发模式 |
|---|---|---|
| specs/foo.md:42\|kimi | 知识资产迁移描述 | 含"迁移"+"Documents" |
```
classify 先扫 overrides 的"触发模式"列，命中则自动归类，无需人工逐条登记。

**收益**：新增文档时，若命中已登记的触发模式，自动归类，无需人工。
**成本**：重写 classify + 回填 67 条触发模式 + 测试。
**前置**：走评审（改门禁核心逻辑）。
**风险**：触发模式过宽会回退到 round2 的 fail-open。需保留"未命中任何模式 → raise"的 fail-closed 底线。

### 方案 D：保持现状 + 文档化（零成本，本 spec 即是）

**改动**：不改代码，仅本 spec 固化"双解析函数必须同步"规则 + 加 lint 校验。

**收益**：零风险，但漂移隐患仍在。
**成本**：写 lint（校验两份 `_load_manual_overrides` 实现一致）。

---

## 4. 推荐路径

**短期（本 spec 落地即做）**：方案 D —— 本 spec 已固化机制理解 + 漂移风险声明，加一条 lint（校验双解析输出一致）作为最小防护。

**中期（下次动 gate-checks/rebuild 时顺手）**：方案 A + B 合并做 —— 去日期后缀 + 提取共享模块，一次性根除两个低风险但高频的漂移源。

**长期（SO-13 / v2 后续）**：方案 C —— overrides 自描述化，降低每次写治理文档的隐性成本。优先级低于 SO-13 现有 backlog（hook 机制加固），但应在"治理文档写作频繁到 raise 成痛点时"启动。

---

## 5. 变更前置

| 改动 | 前置 |
|------|------|
| 改 overrides / exceptions 文件内容 | 跑 rebuild-exceptions + gate-checks 验证一致性 |
| 改文件名（方案 A）| 走 pre-commit 评审 + 改脚本常量 + git mv |
| 改解析函数（方案 B）| 走评审 + 加 fallback + 测试 |
| 改 classify 逻辑（方案 C）| 走评审（门禁核心逻辑，fail-closed 边界）|
| 新增 overrides 条目 | 头注「判定原则」自检：现行角色不入，合法 HISTORY 入（附理由）|

---

## 6. 与其他 spec 的关系

| 关联 spec | 关系 |
|-----------|------|
| `scripts-ownership.md` | rebuild-exceptions / gate-checks 的归属 + 变更前置 |
| `governance-review-process.md §8.4` | 本机制变更的前置评审触发条款 |
| `review-process-lessons.md` | round1→round4 fail-open→fail-closed 演进教训来源 |

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-07-28 | ZCode 起草：机制现状（2 文件 + 数据流）+ 3 可持续性问题（日期后缀/双解析/rebuild 门槛）+ 4 改进方案（A/B/C/D）+ 推荐路径（短期 D / 中期 A+B / 长期 C）。闭合 roadmap 缺口 #8 |
