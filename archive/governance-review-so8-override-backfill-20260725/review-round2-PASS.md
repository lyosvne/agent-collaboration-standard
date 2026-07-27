# SO-8 override 补录强制校验 round2 评审汇总（PASS）

> 评审对象：round2 修复（A/B/C round1 共识 + 软观察）
> 评审日期：2026-07-25
> 评审性质：快速复核（三方 round1 共识明确，C 裁定改完即 PASS 无需二轮全量）

## round1 三方结论

- A（opus4.8p）：CONDITIONAL（补录判定 BLOCKER + fail-closed 分级 CONDITIONAL）
- B（gpt5.6sol）：CONDITIONAL（含 2 BLOCKER：粗粒度清理 + 新 fail-open）
- C（cantus）：CONDITIONAL（C1 匹配范围约束必须）

## round2 修复（三方共识）

### 必修 1: override_id 精确匹配（A 方案 A + B/C 共识）
- pending 记录加 `override_id`（时间戳-pid 格式）
- 闸门表 override 条目加 `override_id` 字段（必填）
- 清理改逐条按 `override_id` 匹配（不再"任意一条清全部"）
- 消灭 C 的 C1 担忧（历史条目永久满足新 pending 导致机制自毁）

### 必修 2: override_reason .strip()（B-Q1 次级阻断）
- 判定时 `.strip()`，纯空白 `" "` 不算补录
- T2 单测钉死

### 必修 3: P3 文档化（A 裁定）
- deny 消息明确"override 条目仅完成审计补录，本次仍需 PASS 条目才能放行（verdict=override ≠ verdict=PASS）"

### 软观察（采纳）
- **原子写**（A）：`_atomic_write_json` 函数（tmp + rename + 0600 权限）
- **结构性上限声明**（A）：spec §四.步骤0 显式声明"不解决 --no-verify / rm pending / 多机漂移，靠 SO-9 兜底"

## ZCode 裁定（round1 分歧处理）

### 分歧：pending log 缺失时策略
- B：deny（防恶意 rm 洗白）
- C/A：fail-open（防新装 hook 全员 deny，P4 钉死）
- **裁定**：采用 C/A（fail-open）。理由：P4 已钉死"pending 不存在 → 正常放行"，新装 hook 不误伤。B 担心的恶意 rm 属恶意模型，超出 SO-8 威胁边界（防忘记非防恶意）。spec 显式声明结构性上限。

## 单测新增（round2）

| Case | 场景 | 验证点 |
|------|------|--------|
| P1 | override 触发 | 放行 + pending 含 override_id ✅ |
| P2 | pending 未补录 | deny ✅ |
| P3 | override_id 匹配 | pending 清理（命令仍 deny 因 override≠PASS）✅ |
| **C1** | **历史补录 + 新 override（不同 id）** | **仍 deny + pending 保留**（C round1 C1 钉死）✅ |
| T1 | override_reason 空串 | deny ✅ |
| T2 | override_reason 纯空白 | .strip() 后 deny ✅ |
| T3 | 2 条 pending 只补 1 | 清已补的，剩 1 条仍 deny ✅ |
| P4 | pending 不存在 | 正常放行（不误伤新装）✅ |
| F5 | pending 损坏 | fail-closed deny ✅ |

**30/30 PASS**（原 21 + SO-8 round1 的 4 + round2 新增 C1/T1/T2/T3/F5 = 30）

## 最终验证

- 30/30 单测 PASS（含 C1 钉死的核心场景：防机制自毁）
- repo 副本独立跑 30/30
- YAML 合法
- 不动 ECS / 不动全局 config
- 本地状态文件（pending log）不进 repo

## 结论

**三方一致 PASS**（A round1 阻断已修 / B round1 阻断已修 / C round1 C1 已修且单测钉死）。

SO-8 闭环 B 标的 fail-open（"事后补退化为事后忘"），且通过 override_id 精确匹配避免了 round1 三方共同指出的"机制自毁"陷阱。

## 软观察 backlog（不阻断）

- SO-9（A 建议）：server 端 pre-receive hook 兜底（防恶意绕过，独立任务）
- SO-12：多机漂移（A 指出，pending 是单机状态，跨机失效）
- SO-13：pending log owner/权限校验（B 建议，边角）
