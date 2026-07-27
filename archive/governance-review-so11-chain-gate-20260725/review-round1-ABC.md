# SO-11 跳链检测 hook round1 评审汇总

> 评审对象：chain-gate-precommit.py + 单测 + config 挂载 + 文档
> 评审日期：2026-07-25
> 评审方：A（opus4.8p）/ B（gpt5.6sol）/ C（cantus）

## 三方结论

- **A（opus4.8p）**：CONDITIONAL（3 升 PASS 硬要求）
- **B（gpt5.6sol）**：CONDITIONAL（3 BLOCKER + 4 软观察 + 10 单测补齐）
- **C（cantus）**：CONDITIONAL（4 通过条件 C1-C4，C1-C3 必须）

## 三方高度共识（真问题）

### 共识 1：真值层双源漂移（A/B/C 三方一致标最大风险）

**A**：spec §二（应然）+ mira-integration-status（实然）双源，spec 领先 mira / mira 领先 spec 都出错。建议单源 + 旁路健康检查。

**B**：S1 双源无守恒机制，必然漂移。建议 YAML 单源 + 脚本生成 markdown。

**C**：C1 必须双源比对，不一致 fail-closed + 告警。"编队被多源漂移坑过 3 次以上，治理工具自己不做漂移自检，是把已付过学费的坑重新挖开。"

### 共识 2：识别机制脆弱（A/B 一致）

**A**：prompt 关键字是临时止血，D8/D10 已发现循环识别 bug。建议 `--reviewer` 参数为主 + 关键字兜底（迁移期打 WARN）。

**B**：B1 BLOCKER，关键字是 fail-open 篮子（"架构评审"/"review this"/"审查代码" 全放行）。应改 caller-tier ≥ callee-tier 调用图谱层。

### 共识 3：真值层解析 fail-closed 是反模式（B/C 部分冲突）

**B**：B3 markdown 解析失败全站 deny 是单点脆弱，应降级缓存 + 24h TTL。

**C**：C1 双源不一致 fail-closed + 告警（C 强调自检，B 强调降级）。

**ZCode 裁定**：解析失败（文件不存在/格式坏）保持 fail-closed（与 review-gate 一致原则）；双源不一致（两边都解析成功但内容矛盾）fail-closed + 告警（采纳 C）。B 的缓存降级是 v2 演进方向。

## B 额外要求（部分采纳）

- **B2 override 不可续期 + 日次上限 + 审计**：合理但工程量大，登记 v2 backlog（本轮 override 沿用 review-gate 同款 30 分钟窗口）
- **B N1-N10 单测**：
  - N8（`--tier=cantus` 等号）/ N9（大小写）→ **round2 修**
  - N1（stdin pipe）/ N2（`--prompt-file`）/ N3（env 变量）→ hook 拦不到（非 Bash 通道），登记 v2（mira proxy 覆盖）
  - N4-N7 → 部分已是 round1 覆盖（D11 解析失败 / D12 override）

## C 关键贡献

- **三闸门应共享单一策略模块**（防三份独立漂移）→ v2 演进方向
- **C2 回归测试**：回放 round1 事故路径，确认在覆盖集 → **round2 补**
- **C3 缺口可观测**：HTTP 直连不要求拦截但要留痕 → v2（dispatch-server 审计标记）
- **v2 演进顺序**：YAML 单源 → 服务端化 → 实测缓存化

## ZCode 综合判断

三方共识明确：**真值层双源 → YAML 单源是根法**，但这是较大架构改动（迁真值层 + 改 hook + 双源比对 + 回归测试 + `--reviewer` 参数），不是 round2 能做完的。

### round2 部分修（低成本）
1. **C1 双源比对 fail-closed**（C 必须条件）
2. **C2 回归测试**（回放 round1 事故路径）
3. **deny 消息加 `[chain-gate]` prefix**（A 建议，便于和 review-gate 区分）
4. **N8/N9 等号形式 + 大小写**（B 单测补齐）

### v2 backlog（独立任务）
- **SO-11-v2-1**：真值层抽 YAML 单源（A/B/C 共识，最优先）
- **SO-11-v2-2**：`--reviewer` 参数机制（A 主张 + 关键字兜底迁移）
- **SO-11-v2-3**：服务端化（策略校验移 dispatch-server，C v2 步骤 2）
- **SO-11-v2-4**：实测可达性异步缓存（cron 探活写状态，hook 只读）
- **SO-11-v2-5**：HTTP 直连/mira proxy 缺口审计留痕（C3）
- **SO-11-v2-6**：override 不可续期 + 日次上限 + 审计（B2）
- **SO-11-v2-7**：三闸门共享单一策略模块（C 拓扑优化）

## round2 计划

修 4 项低成本 + 登记 v2 backlog。改完按闸门规则快速复核（无需二轮全量评审，C 裁定）。
