# 评审方 A（opus4.8p via Mira）— Pi 治理纳入 B 层事后补审

> 评审日期: 2026-07-27
> 评审对象: commit bac6e95
> 评审性质: 事后补审

## 评审结论：CONDITIONAL（3 阻断 + 多项软观察）

事后补审可以接受不等于放过设计问题。下面 3 项是真实阻断，必须修后再过。

## 阻断项

- **阻断 1（设计）**：`/truth/versions` 缺 commit SHA / content hash / mtime —— "时序版本自动化各域自校验"诉求无法满足，同版本号下的内容漂移检测不到。**修复**：documents 每项加 `commit_sha` + `content_sha12` + `mtime`，从 mirror git 取。
- **阻断 2（安全）**：`/dispatch/drift` 无 auth 暴露分支拓扑 + commit SHA + 冲突文件路径。**修复**：加 AUTH_KEY 校验或限内网；`/truth/versions` 可保持公开。
- **阻断 3（依据）**：C 层收窄依据是声称非实证，git 仓库内无 drift-cron.sh 等脚本源码或 ECS 实证，且与 `zcode-claude-replacement-report.md` 里"Pi 未 systemd 托管"表述矛盾。**修复**：归档三个脚本源码 + crontab/systemctl 实证到 `archive/ecs-scripts/`，spec §10 补实证链接；在此之前 C 层标"收窄待实证"而非"已收窄"。

## 逐条判断

### 1. [CONDITIONAL] 端点设计 — version 字段不够用

`version` 是从文件名正则解析的字符串，不是真值锚。两个不同 commit 都可以叫 `north-star-v1.2.md`，端点无法区分"v1.2 第一次提交"和"v1.2 第十次修改后还叫 v1.2"。spec §10 自己写的验收依赖是「检测到 agent-collaboration-standard 仓库的规则版本变化」——只看文件名版本号根本检测不到同版本号下的内容变化。

缺关键字段：`commit_sha`、`updated_at`、`content_hash`。任一即可让各域真正做"对齐校验"。

`START_HERE.md` 返回 `version: null` 应在响应里标注 `versioned: false`。

### 2. [CONDITIONAL] 版本解析正则 — 当前 5 文件全过，但未来必断

`-v(\d+\.\d+)\.md$` 有 4 个真实脆弱点：
- `v1.2.1`（三段语义化版本）会返回 null
- 大写 `V1.2.md` 会断
- `-draft.md` / `.bak` / `.markdown` 后缀全断
- 正则失败时返回 null 而非 raise，端点 HTTP 200

建议放宽为 `-v(\d+(?:\.\d+){0,2})\.md$`，或直接读文件前置元数据。

### 3. [CONDITIONAL] drift 透传 — 文件不存在返回 200 + "{}" 是真问题

- 文件不存在时返回 HTTP 200 + `{}`，消费者无法区分"drift 报告真的为空"和"drift-cron.sh 挂了 / 文件被删 / 路径配错"。这是 spec §3 漂移体检的核心产物——它的缺失本身就是 CRITICAL 事件。
- 透传 raw vs `_send_json` 规范化：raw 透传丧失 schema 校验机会。如果 drift-cron.sh 写坏了半截 JSON，端点会把坏 JSON 当 200 透传，下游消费者全部炸。

建议：文件不存在或解析失败 → HTTP 502 + `{"error": "drift report unavailable", "missing": true}`。

### 4. [CONDITIONAL] 幂等性 MARKER — 字符串会误匹配

`MARKER = "DRIFT_LATEST = os.environ.get"` 是变量名级匹配而非 patch 级匹配。如果将来有人在文件别处加了 `DRIFT_LATEST = os.environ.get(...)` 之类的二次配置，patch 会误判"已应用"并跳过。

建议：MARKER 改为更独特的字面量（如 `# B-LAYER-PATCH-20260727-APPLIED`）。

### 5. [PASS] 404 帮助字符串 — 渲染正常，仅美观

`\n` 正常换行，24 空格缩进在等宽字体下基本对齐。非阻断。

### 6. [CONDITIONAL] 安全 — drift 报告含分支名 + commit SHA + 冲突文件路径，无 auth

drift-config.json 显示监控对象是 5 个 agent 分支。drift-latest.json 含：
- 分支名（暴露编队结构）
- ahead/behind commit 数（暴露各 agent 工作节奏）
- conflicts 文件路径列表（暴露仓库内部结构）
- commit SHA（间接）

这是真泄露面扩大，不是"和现有端点一致就 OK"。现有 GET 端点不暴露分支拓扑和冲突细节。

建议：`/dispatch/drift` 加 AUTH_KEY 校验，`/truth/versions` 可保持公开。

### 7. [CONDITIONAL] C 层收窄 — 收窄方向合理但依据是"声称"非"实证"

整个 git 仓库内找不到 drift-cron.sh 等三个脚本的源码、systemd 单元文件、crontab 快照。只有 commit message 和 patch 注释里的自我声称。且 `zcode-claude-replacement-report.md` 写的是"Pi 标 experimental，未 systemd 托管 / Extensions 实际 registerTool 未 verified"——反而和"shell cron 生产运行"矛盾。

建议：补一份 ECS 实证（crontab -l 输出 + 三个脚本源码归档 + systemctl status / ps 截图）。在此之前 C 层收窄标 ⚠️ 待实证。

### 8. [CONDITIONAL] 过程纪律 — 事后补审可接受，但需留痕 + 流程修正

这是第二次类似违规（spec §10 注释提到"review 已过 2026-07-26 节点3 + Phase D 期间"——那次也是事后）。说明 pre-commit 评审纪律没有强制机制，全靠 agent 自觉。

commit bac6e95 author 显示 `Trae IDE` 而非 ZCode——进一步模糊责任链。

建议：commit 一条 ADR 记录"事后补审 + 教训 + pre-commit 强制触发条件"。

## 软观察（非阻断）

- 正则脆弱：建议放宽或改读 frontmatter 元数据
- MARKER 误匹配：建议改独特字面量注释
- drift 透传：建议 502 + `_send_json` 规范化
- 404 缩进：中文宽度导致纯 ASCII 客户端错位
- 过程纪律：建议写 ADR + pre-commit 评审加强制触发条件
- `versioned` 字段缺失：`START_HERE.md` 返回 null 时应额外标 `versioned: false`
- commit author：bac6e95 author = `Trae IDE`，责任链模糊
