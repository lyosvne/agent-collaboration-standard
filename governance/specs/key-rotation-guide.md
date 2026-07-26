---
version: 1.0
status: awaiting-approval
type: security-spec
created: 2026-07-26
owner: ZCode
title: O1 治理 — 密钥无风险轮换指引
scope: 对本次治理发现已暴露的明文密钥制定无风险轮换流程
related:
  - specs/agent-collaboration-git-sync-plan.md
  - standards/north-star-v1.2.md（§三.2 密钥主权）
supersedes: []
---

# 密钥无风险轮换指引（待审批）

## 一、轮换目标（三方评审一致要求 + 用户裁决）

按"曾以明文形态落盘=视为已暴露"的安全惯例，对以下密钥执行无风险轮换。用户 2026-07-26 明确授权"制定无风险轮换指引"。

## 二、待轮换密钥清单（实测盘点）

| # | 密钥名 | 值特征 | 指向服务 | 当前是否在用 | 扩散范围（实测）|
|---|---|---|---|---|---|
| 1 | **ANTHROPIC_AUTH_TOKEN** | `[ANTHROPIC-REDACTED]...[ANTHROPIC-REDACTED]` (len=49) | open.bigmodel.cn（智谱AI）| ❌ CC 退役后不再使用 | ⚠️ **本机扩散到 6 个位置**：5 个 ZCode 会话日志 + 1 个 CC 迁移历史 |
| 2 | **ANYGEN_API_KEY** | `sk-ag-...` 前缀 | AnyGen 服务 | ❌ AnyGen 已停用（`~/.anygen/` 仅剩 device-id）| 仅在 cc-retirement 归档 + 本次会话日志 |
| 3 | ~~settings.local.json~~ | - | - | - | ❌ **误判**：是权限白名单（Bash 命令允许列表），不是密钥。**不轮换** |

**关键发现**：
- 两个密钥都已不再使用（CC/AnyGen 已退役/停用）
- ANTHROPIC_AUTH_TOKEN 扩散到本机会话日志（最大风险面）
- 两者都在 `archive/cc-retirement-20260726/` 归档（本次会话刚创建的备份）

## 三、轮换策略（按"无风险"原则）

### 3.1 核心原则：先验证再删，永远有回退

**禁止**：
- ❌ 先删旧 token 再创建新 token（如果新 token 创建失败，旧 token 已废，无法回退）
- ❌ 在未确认新 token 可用前，删除任何位置的旧 token
- ❌ 跨步骤合并操作（每步独立可验证）

**要求**：
- ✅ 每一步都可独立验证 + 回退
- ✅ 每一步执行前先备份当前状态
- ✅ 涉及平台操作（智谱/AnyGen 控制台）必须用户本人完成，ZCode 不代操作

### 3.2 风险等级评估

| 密钥 | 轮换风险 | 理由 |
|---|---|---|
| ANTHROPIC_AUTH_TOKEN | **极低** | CC 已退役，这个 token 不再被任何在用工具使用。轮换纯属安全卫生，无功能影响 |
| ANYGEN_API_KEY | **极低** | AnyGen 服务已停用，token 已自然失效。轮换只是"确认失效"动作 |

**两个都是"已废弃 token 的安全卫生轮换"**，不是"在用 token 的紧急轮换"，风险极低。

## 四、分步执行流程

### 阶段 A：ANTHROPIC_AUTH_TOKEN 轮换

#### A.1 用户在智谱平台操作（必须本人，不可委托）
1. 登录 `https://open.bigmodel.cn/` 用户控制台
2. 进入 API Keys 管理页面
3. 找到以 `[ANTHROPIC-REDACTED]` 开头的旧 key
4. **先创建一把新 key**（不要先删旧的）
5. 验证新 key 能正常调用（用 curl 跑一个最小测试请求）
6. 确认新 key 可用后，**删除旧 key**（`[ANTHROPIC-REDACTED]...`）
7. 记录新 key 的前 12 位 + 后 6 位（不要记完整值）

**回退方案**：如果新 key 创建/验证失败，旧 key 还在，无影响。

#### A.2 ZCode 清理本机扩散副本（用户授权后）
旧 key 删除后，本机扩散副本虽然"失效"但仍占空间。清理：
- `~/.zcode/cli/agents/sess_*/transcript.jsonl`（5 个会话日志）
- `~/.zcode/cli/rollout/model-io-*.jsonl`
- `~/.zcode/migrated-from-claude/projects/*/*.jsonl`

**注意**：这些是历史会话日志，含完整对话记录。**不能直接删**（可能有用），按以下策略：
- 选项 a：保留日志但用 sed 替换 token 为 `[REDACTED-ROTATED-2026-07-26]`
- 选项 b：归档到 `archive/zcode-session-logs-pre-rotation-20260726/` 后从活跃位置移除

**推荐选项 a**（保留日志可用性 + 消除 token）。

#### A.3 归档目录清理
`archive/cc-retirement-20260726/settings.json.retired-backup` 里的旧 token 也需要同步处理：
- 用 sed 把旧 token 替换为 `[REDACTED-ROTATED-2026-07-26]`
- 保留文件结构（历史可追溯）

### 阶段 B：ANYGEN_API_KEY 轮换

#### B.1 用户尝试登录 AnyGen 平台
1. 尝试访问 AnyGen 控制台
2. 如果能登录：按 A.1 流程（创建新 key → 验证 → 删旧 key）
3. **如果不能登录**（服务已停用）：跳过平台轮换，直接进入 B.2（本机清理）

#### B.2 ZCode 清理本机副本
- `archive/cc-retirement-20260726/.env.anygen`：sed 替换 token 为 `[REDACTED-ROTATED-2026-07-26]`

## 五、验证清单（轮换完成的判定标准）

轮换全部完成后，必须满足：

- [ ] 智谱平台：旧 key `[ANTHROPIC-REDACTED]...` 已删除（用户确认）
- [ ] 本机所有日志文件中搜 `[ANTHROPIC-REDACTED]` 零命中
- [ ] `archive/cc-retirement-20260726/settings.json.retired-backup` 中 token 已脱敏
- [ ] AnyGen：平台旧 key 已删除（或确认服务已停用无法操作）
- [ ] `archive/cc-retirement-20260726/.env.anygen` 中 token 已脱敏
- [ ] 新 token（如创建）只存在用户指定的安全位置（不在任何日志/归档/git 里）

## 六、不在本指引范围

- **settings.local.json**：误判（是权限白名单不是密钥），不轮换
- **ZCode 当前在用的 token**（`[ZCODE-REDACTED]` / `eyJ...`）：未暴露，不在本次轮换范围
- **Mira 沙箱的 c360 OAuth**：是会话级授权，不是持久密钥，不轮换
- **ECS 上的密钥**：另立审计项（在 O1 治理后续批次）

## 七、执行前置条件

1. ⏳ 用户审阅本指引（特别是阶段 A.1 的平台操作步骤）
2. ⏳ 用户明确授权 ZCode 执行 A.2 / A.3 / B.2 的本机清理（命中红线：修改含密钥的文件）
3. ⏳ 用户决定 A.2 用选项 a（sed 替换）还是选项 b（归档移除）

## 八、与同步方案的关系

按用户裁决"同步前最小语义修正"——**密钥脱敏属于同步前的最小语义修正**：
- 阶段 A.3 + B.2（归档文件 token 脱敏）**必须在 Phase 2 同步之前完成**
- 否则同步会把含明文 token 的归档文件带进 git 工作区（即使 .gitignore 排除，也是单点防御）

**修订顺序**：
1. **Phase 0.5 密钥轮换**（本指引）→ 阶段 A.3 + B.2 完成归档脱敏
2. Phase 2 同步（rsync 排除 + 白名单导入）
3. 其他 Phase

## 九、当前状态

**awaiting-approval** — 指引已出，等待用户审阅 + 授权。
