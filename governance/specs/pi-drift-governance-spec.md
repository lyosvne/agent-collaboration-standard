# 设计规格：Pi 漂移治理（cron 体检 + 代劳 push + 集成窗口）

> 签发: Qoder（出规格）| Review: ZCode（对等互检）| 裁定: 用户 | 日期: 2026-07-23
> 状态: **用户已签发「Pi 代劳 push 常设授权」（2026-07-23），§4.1 解锁，待 ZCode review 后可实施**
> 依据: 架构真值 v1.0 §五 + 本机资产审计实证（8 副本分叉/主仓库落后 200 commits）

---

## 1. 问题与根因（审计实证）

- 主仓库曾落后 origin/master 200 commits；6 个 clone 中 solo ahead 71/behind 333、trae ahead 14/behind 196
- 根因（v1.0 诊断，与审计一致）：**依赖 agent 主动同步的设计本身有缺陷**——agent 不会主动 pull、忘了 push

## 2. 治理对象清单

| Clone | 分支 | 状态基线（2026-07-22 审计） |
|-------|------|---------------------------|
| Aetheris-link（主，ZCode 接管中） | master | 落后 200（ZCode 同步中） |
| Aetheris-clones/claude → ZCode 接管 | agent/claude | 与 origin 同步 |
| Aetheris-clones/kimi | agent/kimi | 活跃，已合并 master 真值 |
| Aetheris-clones/qoder | agent/qoder | 3 untracked 待处理 |
| Aetheris-clones/trae | agent/trae | 5 modified 待处理 |
| Aetheris-clones/solo | agent/solo | 31 untracked（归档候选） |
| agent/mira（GitHub 分支） | agent/mira | 活跃（Mira 角色待用户澄清） |

清单以配置文件维护（`drift-config.json`），编队变更时更新，不硬编码。

## 3. 第一层：漂移体检 cron

### 3.1 执行（每 15-30 分钟，可配）

```
对 drift-config.json 中每个 clone：
  git -C <clone> fetch origin              # 只 fetch，绝不改工作区
  ahead  = rev-list origin/<branch>..HEAD --count
  behind = rev-list HEAD..origin/<branch> --count
  dirty  = status --porcelain | wc -l
  branch_vs_master = rev-list origin/master..origin/<branch> --count（分支领先 master 量）
产出 DriftReport(JSON) → 写 Aetheris（真值层） + 经 pi-feishu 发卡片
```

### 3.2 分级

| 级别 | 条件 | 动作 |
|------|------|------|
| OK | ahead=0, behind≤3, dirty=0 | 仅记录，不打扰 |
| NOTICE | behind 4-10 或 dirty>0 | 计入日报卡片 |
| WARN | behind>10 或 ahead>0 超过 2 个体检周期未 push | 飞书漂移报告卡 |
| CRITICAL | behind>50 或分支间冲突预检失败 | 飞书告警卡（立即） |

### 3.3 安全边界（硬约束）

- 体检**只读**：只 fetch + rev-list + status，绝不 pull/merge/checkout/reset
- 对 dirty 工作区绝不做任何写操作

## 4. 第二层：主动纠正

### 4.1 代劳 push（前置：用户常设授权，见 §6）

```
条件（全部满足才执行）：
  1. clone 在自己的 agent/<name> 分支上（HEAD 分支名匹配）
  2. ahead>0 且 dirty=0（有未推 commit 且工作区干净）
  3. 目标分支 ∈ 白名单（agent/* 分支），绝非 master
  4. push 为 fast-forward（远端无分叉），绝不 --force
动作：git push origin <branch>
审计：每次代劳 push 写 Aetheris + 飞书通知（谁的分支、几个 commit、SHA 范围）
```

### 4.2 提醒 pull（不代劳）

- behind>0 → 仅通知（飞书 NOTICE/WARN），绝不代劳 pull（可能冲突，需 agent 在自己会话中处理）

## 5. 第三层：源头预防

1. **铁律**（写入协议 v2.1）：agent 只在 `agent/<name>` 分支工作，绝不直接 commit master
2. **pre-commit hook**（各 clone 安装）：commit 时检测 behind 量，>10 输出警告（不阻断）
3. **集成窗口**：Pi 定期（建议每周）生成「集成提案」卡片——列出各 agent 分支可合并 master 的 commit 集与冲突预检结果；**合并动作本身走审批卡（T3），由用户批准后执行或指派 agent 执行**，Pi 不擅自合 master

## 6. 前置授权（待用户签发，写入协议）

> 「Pi 漂移治理常设授权」草案：
> 授权 Pi daemon 在满足 §4.1 全部条件时自动执行 `git push origin agent/<name>`。
> 范围限定：仅 agent/* 分支；禁止 master/main；禁止 --force / --delete / tag；
> 每次执行必须审计留痕并飞书通知。违反任一限定即视为越界，Pi 停用该功能并告警。

## 7. 实现形态

- Pi Extension `pi-drift-guard`（TypeScript）：cron 调度 + git 只读探测 + 分级报告 + 代劳 push（授权后启用）
- 与 pi-feishu 的接口：`DriftReport → 漂移报告卡/告警卡`；集成提案 → 审批卡
- 与 Aetheris 的接口：体检记录/代劳 push 审计写真值层
- Trae PC↔Mobile：按 v1.0，统一监控 agent/trae 分支，不区分提交来源

## 8. 验收标准

1. 体检正确性：人工制造 ahead/behind/dirty 场景，报告与 `git status`/`rev-list` 实况一致
2. 只读保证：体检运行前后，各 clone 工作区与 HEAD 无任何变化（mtime + rev-parse 校验）
3. 代劳 push 边界：构造 master 分支/dirty 工作区/非 ff 场景 → 全部拒绝执行并记录原因
4. 告警链路：CRITICAL 场景 5 分钟内飞书收到告警卡
5. ZCode review 通过 + 用户授权签发后，方可启用 §4.1

## 9. 分工

- 本规格：Qoder 出（本文档）
- Review：ZCode（对等互检，重点审 §4.1 边界与 §3.3 只读保证）
- 实施：待用户裁定（建议随 Pi ECS 部署验证后作为 Pi 第一个实战任务，v1.0 §八已建议）
