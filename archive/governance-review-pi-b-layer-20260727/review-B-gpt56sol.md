# 评审方 B（gpt5.6sol via Mira）— Pi 治理纳入 B 层事后补审

> 评审日期: 2026-07-27
> 评审对象: commit bac6e95

## 评审结论：CONDITIONAL

改动是 additive（2 个 GET 端点 + 1 常量 + 404 串更新），可逆（有 .bak 备份），ECS 健康回归通过——所以不到 FAIL。但 8 条里有 4 条触及实质缺陷（commit-hash 缺失、过程违规未落账、C 层 §5 真空、drift 透传无安全网），不满足 PASS 门槛。

## 阻断项

- **B1（设计）**：`/truth/versions` 必须补 `commit-hash` 字段（理想再加 `updated`），对齐 node1 §5.3 原设计。无 commit-hash，"各域自校验对齐"是无依据的口号，B 层核心价值未达成。
- **B2（过程）**：过程违规必须落账——更新 `archive/retired-terms-manual-history-overrides-20260726.md`（或新建 process-violations 记录），并在 roadmap v1.9 条目补承认违规 + 设先例。当前 v1.9 只庆祝不认账，不可接受。

## 逐条判断

### 1. 端点设计 — CONDITIONAL（偏 FAIL）

核对 `archive/governance-review-node1-20260726/governance-plan-review-package.md §5.3`（L480-485）原设计明确为：返回所有关键文档的 **version / updated / commit-hash**。

当前实现只返回 `filename / version / source`。缺字段：
- `commit-hash`（最关键）——"各域自校验对齐"的密码学信号
- `updated`（last-modified / commit time）——时序版本自动化的"时序"二字落空
- `source` 是新增的运维字段，有用，但不能替代 commit-hash

### 2. 版本解析正则 — PASS（带前向兼容软观察）

实测对 5 个文件名全部正确。边界：
- `foo-v1.0.0.md` → null（三段 semver 不匹配）
- `foo-v1.0-rc1.md` → null（预发布不匹配）
- `foo-V1.0.md` → null（大小写敏感）
- `foo-v01.02.md` → "01.02"（前导零字典序错位）

建议改 `-v(\d+\.\d+(?:\.\d+)?)\.md$` 兜底。

### 3. drift 透传 — CONDITIONAL

raw 透传的问题：
- dispatch-server 不校验 drift-cron.sh 的产出。若 cron 写出 malformed JSON，端点直接把垃圾透给消费者
- drift-latest.json 含 emoji（✅🔴），透传是否真按 UTF-8 编码字节依赖 `_send_text` 实现——评审包未给出 `_send_text` 源码，是 load-bearing 未验证项

建议至少包一层 try/except 兜底 malformed JSON。

### 4. 幂等 MARKER — CONDITIONAL

`MARKER = "DRIFT_LATEST = os.environ.get"`：
- 当前文件内应唯一
- 脆弱点：可能未来出现在 docstring/注释里造成假阳性；或某次重构改成 `os.getenv("DRIFT_LATEST")`，MARKER 失配 → patch 重复应用

更稳的做法：用哨兵注释 `# PATCH-B-LAYER-20260727-APPLIED` 单独占一行。

### 5. 404 字符串 — PASS

24 空格缩进对齐"可用: "列，多行折行可读，格式无破坏。软观察：help string 越来越长，未来考虑独立 `/help` 端点。

### 6. 安全 — CONDITIONAL

drift 端点暴露分支名 / ahead-behind 计数 / commit SHA / 冲突文件路径。无 auth。

review-package §五.6 的辩护"与现有 GET 端点一致"是弱辩护——现有 GET 端点不暴露开发节奏情报；drift 端点首次暴露"谁在改什么、改得多快、哪里冲突"。这是攻击面扩张。

若 ECS 端口仅内网/localhost 可达，CONDITIONAL 可放行；若公网可达，需 AUTH_KEY。**评审包未给出 ECS 端口暴露范围证据，无法定级**——这本身就是条件项。

### 7. C 层收窄 — CONDITIONAL（有真空）

spec §10 收窄只覆盖 §3（体检），**§5 完全未提**。spec §5 第三层"源头预防"包含 pre-commit hook（§5.2）+ 集成窗口周报提案卡（§5.3）+ T3 审批卡。收窄后这些无主——这是真真空。

"shell cron 已覆盖 §3 90%"是自评估数字，review-package 内无映射表证明。

建议：spec §10 补 §3 覆盖矩阵，并显式声明 §5 预防层归属。

### 8. 过程纪律 — CONDITIONAL（偏 FAIL）

未走 pre-commit 三方评审就 ECS 改动 + push + 重启服务，违反节点纪律。

不强制回滚（改动 additive + 备份 + 回归通过 + blast radius 低）。

但不能就此放行：
- v1.9 roadmap 版本历史只庆祝完成，未承认违规
- 此违规必须落账，并写明"今后 T3 邻接 ECS 动作必须 pre-commit 三方评审，本次为反例先例"

## 软观察

- S1（drift 透传）：包 try/except，malformed JSON 时返回错误信封
- S2（MARKER）：改哨兵注释
- S3（安全）：补 ECS 端口暴露范围证据
- S4（C 层真空）：spec §10 补 §3 覆盖矩阵 + §5 预防层归属
- S5（regex 前向兼容）：考虑 `-v(\d+\.\d+(?:\.\d+)?)\.md$`
- S6（404 串膨胀）：未来考虑独立 `/help` 端点
