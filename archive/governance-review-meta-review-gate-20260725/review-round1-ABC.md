# Pre-commit 评审闸门机制 round1 评审汇总

> 评审对象：本方案 4 改动（文档迁移 + 闸门表 + hook 脚本 + config 挂载）
> 评审日期：2026-07-25
> 评审方：A（opus4.6 via mira）/ B（gpt5.6sol via mira）/ C（cantus via ECS qoder-bridge）

## 三方结论

- **A（opus4.6）**：BLOCKER（材料不可达）→ C 裁定重新归类为"弃权 + 附架构意见"（基础设施故障不应有否决权）
- **B（gpt5.6sol）**：CONDITIONAL（4 硬阻断 + 2 软观察）
- **C（cantus）**：CONDITIONAL（3 项放行条件，全部低成本）

## 三方共识（必须修，B/C 一致 + A 方向认同）

### 共识 1：Q3 子串误匹配 → 结构化 + 精确 key（真阻断）

**问题**：当前 `object_name in obj_clean or object_name in obj_no_pi or obj_no_pi in object_name` 双向子串匹配，会导致 `c-layer-drift-check` 的 PASS 放行 `c-layer-failopen-fix` 的 patch——闸门假阳性放行，击穿闸门存在的意义。

**C 的第三方案（采纳）**：
1. 闸门表从 markdown 改为 `pre-commit-review-gate-log.yaml`，每条目含显式字段：`gate_id` / `files`（patch 文件名精确列表）/ `verdict: PASS` / `reviewer` / `expires`
2. patch 脚本命名规约强制：`apply-<gate_id>.py`
3. hook 从文件名提取 gate_id，做**字典 key 精确等值查找**，零子串逻辑
4. 匹配失败时 deny 消息列出当前表中所有 open gate_id（把"猜"的负担移给人）

**为何不采纳 A 的完整方案（register 命令 + patch SHA）**：C 裁定——过重的闸门比没有闸门更危险，它训练所有人绕闸门。SHA 绑定在防恶意场景才有价值，防忘记模型下"评审过这个对象"粒度已足够。A 的完整方案标注为 v2 演进方向。

### 共识 2：Q4 双源漂移 → 单源化（真阻断）

**问题**：lessons §8.4 还保留了 6 项清单（虽改了指针措辞），与 spec §四.步骤0 形成 6 项 × 2 处的双源。编队核心病灶就是漂移治理，治理方案自己埋漂移种子。

**修复**（C 裁定）：lessons §8.4 删除 6 项清单内容，只留一行指针 + 历史成因反思。spec §四.步骤0 为唯一规范源。

### 共识 3：config scope 收窄 → project 级（真阻断）

**问题**：`~/.zcode/cli/config.json` 是用户级配置，挂 hook 后所有 ZCode session（含无关项目）每条 Bash 都过 review-gate-precommit.py。

**修复**（B/C 一致）：改挂 `<repo>/.zcode/config.json`（agent-collaboration-standard repo 内）。
**额外收益**（C 指出）：project 级配置进 git，闸门本身被版本控制、可评审、可回滚——闸门配置进入 GitHub 硬真值层。

**陷阱**（C 指出）：repo 目录外起 session 去 scp 没有闸门。缓解：spec 写流程约束"ECS patch 必须在编队 repo 工作目录内执行"，不追求 hook 层 100% 覆盖（威胁模型是防忘记）。

## 三方分歧（已收敛）

### Q1 正则绕过（B 标硬阻断 14 种手法 → C 裁定过严）

**B**：列 14 种绕过手法（rsync/sftp/管道/IP 直连/git push/curl/lftp/tar/跳板机/paramiko/control socket/nc/环境变量拼接/base64 变形），标硬阻断。

**C 裁定**：14 种里大部分预设 agent *主动改写命令绕闸门*——那是恶意模型，超出声明边界。"忘记审"的 agent 不会突然从 scp 换成 sftp。

**采纳**（C 方案）：只补 2 项高概率**无意**路径：
- `rsync`（有些 agent 默认用它同步）
- IP 直连（domain/IP 混用是真实日常，非绕过手法）

其余 12 种不修（plan §五.5 已声明 hook 是防忘记非防恶意，这是设计边界）。

### 循环依赖（A/B 材料不可达）

**A**：材料不可达给 BLOCKER。
**B**：材料可达（能列 14 种绕过 + 具体文件名互穿案例），盲评给 CONDITIONAL。
**C 裁定**：A 的 BLOCKER 重新归类为"弃权 + 附架构意见"——基础设施故障（mira 沙箱看不到 Windows 文件）不应有否决权。但暴露评审流水线漏洞：**评审材料投递没有确认回执**。

**根因**：mira -p 调度时 prompt 里只给了文件路径，没内联文件内容。C 调度时 prompt 内联了方案核心（4 改动 + 6 类清单 + hook 设计 + A/B 结论），所以 C 拿到了细节。

**改进**（非本方案范围，记 backlog）：调度评审时材料必须内联文本随任务下发，不依赖评审方主动 fetch 外部 URL。

## ZCode 综合判断

三方意见高度收敛，C 的裁决专业且符合本方案威胁模型。采纳 C 的 3 项放行条件 + 2 项软观察：

### 必修（3 项，round2 修）
1. **Q3**：闸门表 markdown → YAML + gate_id 精确等值（C 第三方案）
2. **Q4**：lessons §8.4 删除 6 项清单，只留指针
3. **config scope**：改挂 `<repo>/.zcode/config.json`

### 软观察（2 项，round2 顺带修）
4. **Q1 补 rsync + IP 直连**：hook 正则加这两条无意路径
5. **override 留痕**：override 使用必须在闸门表留一行（标 `override` 状态）

### 元改进（spec 补充，非代码）
6. **循环闭合**：spec §四.步骤0 加声明"本机制自身的变更属强制评审对象"
7. **覆盖缺口声明**：spec 写明"本闸门只覆盖 ZCode 路径"（Kimi/Trae 碰 ECS 不受控，过去 3 次跳审全是 ZCode，先修出血点）

## 三方软观察 backlog

- **SO-1**（B/C）：评审材料投递无确认回执 → 调度时内联文本（独立任务，非本方案）
- **SO-2**（C，v2 演进）：闸门 PASS 记录写入 Aetheris（decision 类型），让 Pi 在漂移治理中消费 → v2
- **SO-3**（A，v2 演进）：显式 register 命令 + patch SHA 绑定 → 防恶意场景升级时再做
- **SO-4**（C）：spec 声明"闸门只覆盖 ZCode 路径" → round2 顺带修

## round2 计划

修 3 项必修 + 2 项软观察 + 2 项元改进，全部低成本（C 判定一天内完成）。修完按闸门自己的规则登记 gate_id + 快速复核，无需二轮全量评审。

## 纪律违规累计

本方案是治理流程改动，按用户要求走 Plan Mode（已完成）+ 三方评审（本步）。**首次正面案例**：本方案自身严格遵守了 §四.步骤0（虽然 hook 还没挂，但流程已对齐）。
