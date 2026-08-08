# 设计规格：Pi 漂移治理（cron 体检 + 代劳 push + 集成窗口）

> 签发: Qoder（出规格）| Review: ZCode（对等互检）| 裁定: 用户 | 日期: 2026-07-23
> 状态: review 已过（2026-07-26 节点3 + Phase D 期间）；常设授权已编入 `workspace-collaboration-v2.1.md §4`；本 spec A 层（文档/配置真值）对齐 2026-07-26；B/C 层（dispatch-server `/truth/versions` 端点 + ECS `pi-drift-guard` Extension 实施）待后续任务（详见 §10）
> 依据: 架构真值 v1.0 §五 + 本机资产审计实证（8 副本分叉/主仓库落后 200 commits）

---

## 1. 问题与根因（审计实证）

- 主仓库曾落后 origin/master 200 commits；6 个 clone 中 solo ahead 71/behind 333、trae ahead 14/behind 196
- 根因（v1.0 诊断，与审计一致）：**依赖 agent 主动同步的设计本身有缺陷**——agent 不会主动 pull、忘了 push

## 2. 治理对象清单

> 真值层对照 `fleet-division-v1.1.md`（逻辑 v1.2）：Pi 中央协调、统一 Trae、ZCode 非终端、Qoder/Kimi Mac clone、Mira 云端 fresh checkout。
> 配置以文件维护（`governance/configs/drift-config.json`），编队变更时更新，不硬编码本地路径。

| Clone | 分支 | 状态基线（2026-07-26 重对齐） |
|-------|------|---------------------------|
| agent-collaboration-standard（本仓库）| master | ✅ 真值层（git-sync-plan §六验收对象，依赖 §10 C 层 Extension 上线后纳入体检）|
| Aetheris（主仓库） | master | 真值层（架构 v1.0） |
| Aetheris-clones/trae | agent/trae-mac | 活跃（统一 Trae = 实现/集成/测试）|
| Aetheris-clones/kimi | agent/kimi-mac | 活跃（Kimi = 终端/数据/飞书）|
| Aetheris-clones/qoder | agent/qoder-mac | 活跃（Qoder = 设计 + 受派实现）|
| Aetheris-clones/zcode | agent/zcode-mac | 受控上下文（ZCode 非终端，不执行 Git 写操作）|

**已退役**（drift-config.json `retired_clones` 显式记录，避免漂移报告误报）：
- `agent/claude`：Claude Code 2026-07-25 退役，分支冻结
- `agent/solo`：独立 Solo 已并入统一 Trae
- 旧 Windows `agent/trae` / `agent/zcode` / `agent/qoder` / `agent/kimi`：由 `agent/*-mac` 取代
- `agent/mira`：Mira 改用云端 fresh checkout

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

### 4.1 代劳 push —— 架构修正（2026-07-23，ZCode 实证发现）

**原设计缺陷**：规格假设 Pi 能直接访问各 agent clone 执行 push。
**事实**：代码 clone 分布在 Trae/Qoder/Kimi 的 Mac 环境；ZCode 只有非终端上下文。ECS 上的 Pi 不直接修改这些工作区。

**修正后方案**：
```
Pi（ECS）能做的：
  ✅ 远端体检（§3）：用 ECS 上的 git mirror fetch 检测漂移（已上线）
  ✅ 检测未 push commit：mirror 对比 origin/<branch> 发现 ahead
  ✅ 通知：飞书/Aetheris 告知对应 agent "你有 N 个未 push commit"
  ❌ 代劳 push：不可能（clone 不在 ECS）

代劳 push 的实际执行者：
  方案 A（当前）：Pi 通知 → Trae/Qoder/Kimi 在自己的受控分支执行
  方案 B（未来增强）：各 agent 本机装轻量 cron 自动 push 自己的 agent/<name> 分支
  方案 C（远期）：Pi 通过 agent 的通信通道（Qoder SSE/轮询，无 Webhook）下发 push 指令
```

当前边界：Pi 只有检测、通知和生成集成提案的权限，不执行 Git push。代码分支由 Trae/Qoder/Kimi 在各自授权范围内推送。

### 4.2 提醒 pull（不代劳）

- behind>0 → Pi 通知（飞书/Aetheris），绝不代劳 pull（可能冲突，需 agent 在自己会话中处理）
- 当前 4 CRITICAL 即属此类（分支落后 master = 集成问题，非 push 问题）

## 5. 第三层：源头预防

1. **铁律**（写入协议 v2.2）：代码执行 agent 只在隔离分支工作，绝不直接 commit master
2. **pre-commit hook**（各 clone 安装）：commit 时检测 behind 量，>10 输出警告（不阻断）
3. **集成窗口**：Pi 定期（建议每周）生成「集成提案」卡片——列出各 agent 分支可合并 master 的 commit 集与冲突预检结果；**合并动作本身走审批卡（T3），由用户批准后执行或指派 agent 执行**，Pi 不擅自合 master

## 6. Pi Git 权限

Pi 不持有代码 clone 的写权限，不执行 push、merge、rebase、reset、delete 或 tag。旧“Pi 代劳 push”草案已经失效。

## 7. 实现形态

- Pi Extension `pi-drift-guard`（TypeScript）：cron 调度 + git 只读探测 + 分级报告。**不得包含 Git 写操作**。
- 与 pi-feishu 的接口：`DriftReport → 漂移报告卡/告警卡`；集成提案 → 审批卡
- 与 Aetheris 的接口：体检记录、通知和集成提案写真值层
- 统一 Trae：监控 `agent/trae-mac`；历史 `agent/solo` 不参与活动体检

## 8. 验收标准

1. 体检正确性：人工制造 ahead/behind/dirty 场景，报告与 `git status`/`rev-list` 实况一致
2. 只读保证：体检运行前后，各 clone 工作区与 HEAD 无任何变化（mtime + rev-parse 校验）
3. 代劳 push 边界：构造 master 分支/dirty 工作区/非 ff 场景 → 全部拒绝执行并记录原因
4. 告警链路：CRITICAL 场景 5 分钟内飞书收到告警卡
5. review 与授权：ZCode 做非终端风险评审；Mira 审治理；Trae 执行验证；生产和 T3 操作仍需用户授权

## 9. 分工

- 本规格：Qoder 出（本文档）
- Review：ZCode（非终端风险分析）+ Mira（治理）+ Trae（可执行性验证）
- 实施：Trae/Kimi 在用户授权后执行；Pi 不直接 SSH 或部署

## 10. 实施状态（2026-07-26 实证，A 层对齐时固化）

| 层 | 内容 | 状态 |
|----|------|------|
| A 文档/配置 | spec 真值对齐 + `drift-config.json` 创建 | ✅ 2026-07-26 完成 |
| B 协议层 | dispatch-server `/truth/versions` 端点（时序版本自动化）| ✅ 2026-07-27 完成（加 `/dispatch/truth/versions` + `/dispatch/drift` 两端点，patch 见 `archive/dispatch-server-patches/apply-b-layer-20260727.py`）。**事后评审 round1→round3 修复**：(1) `/truth/versions` 加 commit_sha + content_sha12 + mtime + versioned（修字段不足）；(2) `/dispatch/drift` fail-closed（文件缺失/malformed 返回 502）；(3) `/dispatch/drift` 加 AUTH_KEY 鉴权（query param `?key=$DISPATCH_KEY`，修公网泄露——A round2 阻断）；(4) 正则放宽支持 semver 三段 + MARKER 改哨兵注释 + 消费者契约 docstring。3 个 patch 见 `archive/dispatch-server-patches/` |
| C ECS 工程 | `pi-drift-guard` Extension 代码 + systemd 托管 + spawn exports 修复 | ⏳ 具体增强仍需用户授权，由 Trae/Kimi 实施。现有 ECS shell cron 已覆盖主要只读体检；活动分支清单改读 `drift-config.json` v1.2。 |

**deployment 实证**（来源 `templates/zcode-claude-replacement-report.md`，非真值层）：
- Pi daemon 进程存活（部署验证时 PASS：daemon / 崩溃恢复 / IPC / Aetheris 连通）
- Pi 标 experimental，**未 systemd 托管**（建议加 `.service` + `Restart=always`，待用户授权）
- Extensions 实际 `registerTool` 未 verified（需建 extensions 目录 + 写 test extension）
- spawn exports 问题未修（Pi 能管理 instance 记录但不能启动真实 agent 子进程）

**验收依赖**（`agent-collaboration-git-sync-plan.md §六`）：
- "Pi 30min cron 能检测到 agent-collaboration-standard 仓库的规则版本变化" 依赖 C 层 `pi-drift-guard` Extension 上线
- A 层 `drift-config.json` 已登记本仓库为治理对象，Extension 上线后即可生效
