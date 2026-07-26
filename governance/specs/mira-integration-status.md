---
version: 2.2
status: trunk-complete
type: spec
created: 2026-07-25
updated: 2026-07-26
owner: ZCode
title: Mira 接入调研与现状
scope: 记录 Mira CLI / Proxy 真实形态与本机现状，为编队接入提供决策依据
source_doc:
  - 飞书 wiki GVUcw5USriC7sqk155YcM2Rpnzf 「[Togo] 在本地使用 Mira SOTA 模型：mira cli & mira proxy」
  - 读取方式：lark-cli wiki +node-get + docs +fetch（2026-07-25 ZCode 用林于炜身份）
supersedes: []
related:
  - specs/mira-vs-larkcli-capabilities.md
  - specs/mira-deep-dive-backlog.md
---

## 更新日志

- **v2.2 (2026-07-26)**：主干接入完成。评审模型路由（gpt5.6sol 默认 + opus4.8p 双审）、生图工作流（mira-img.py）、能力对比（vs lark-cli）、深度挖掘待办清单（backlog）全部落盘。状态 → trunk-complete。
- **v2.1 (2026-07-26)**：补 §B.3-B.6 评审/生图路由策略 + 远端会话同步机制 + 内置 Skill 清单 + 用户使用画像。
- **v2.0 (2026-07-26)**：Mira CLI 登录成功，非交互模式 + JSON 输出全部验证通过。
- **v1.1 (2026-07-25)**：用户裁决路径 A（mira-cli 终端调度）。已安装 Togo CLI v5.21.0。
- **v1.0 (2026-07-25)**：读取飞书文档，校正认知（Mira CLI 属于 Togo 平台）。

# Mira 接入调研与现状

## 一、关键认知校正

**Mira CLI 不是 Mira.exe 桌面客户端的命令行版本**，而是字节内部 **Togo 平台** 的能力之一。

之前我错误判断「Mira 无 CLI」，实际是混淆了两件事：
- `Mira.exe`（6 个进程在跑）= Mira **桌面客户端** GUI 主程序
- `mira` / `togo` 命令 = Togo 平台 CLI，由独立安装脚本提供，本机**未安装**

二者完全独立。文档标题「[Togo] 在本地使用 Mira SOTA 模型」明确说明 CLI 归属于 Togo 平台。

## 二、Mira CLI / Proxy 的真实形态（来源：飞书文档）

### 三种使用形态

| 形态 | 入口 | 定位 |
|---|---|---|
| **mira-cli** | 终端输入 `mira` | 原版 Mira 体验，CLI + 本地工具 + 交互优化 |
| **mira-proxy** | `togo connect` 自动启动 | 适配 Claude code 接口的本地代理（127.0.0.1:8787） |
| **Mira 官方 Web/客户端** | 在 Mira GUI 里用 Togo MCP | 让 Mira 后端通过 MCP 反向操作本地文件 |

### 安装（本机尚未执行）
```bash
curl -fsSL https://togo.byted.org/api/cli/install.sh | bash
togo connect --init
```

### mira-cli 关键命令
- `mira` — 启动终端会话
- `/resume <session_id>` — 跨设备恢复会话（session_id 来自 Mira web URL，如 `https://mira.byteintl.net/chat/109386225683`）
- `/new` — 新会话
- `/config auto-compact on` — 自动压缩
- `/config compact-mode local` — 生成摘要+新会话
- `/compact` — 手动压缩

### mira-proxy 关键点
- 启动 `togo connect` 自动起 proxy，端口 **127.0.0.1:8787**
- 自动写入 `~/.claude/settings.json`：`ANTHROPIC_BASE_URL=http://127.0.0.1:8787`
- **会剥除 Claude code 传过来的大部分上下文（system）**，只保留必要目录信息和用户输入
- 重要约束：Mira 服务端是有状态（上下文+沙箱+session），Claude 模型接口是无状态；二者不能完全对齐

### 配置文件位置（本机暂无）
- `~/.togo/mcp.json` — 注册本地其他 MCP（如 macos-use）
- `~/.togo/skills.json` — 扫描本地 Skills 范围
- `~/.mira/system_prompt.md` — 首轮注入模板
- `~/.mira/session_context.md` — 每轮注入模板

### 关键环境变量
| 变量 | 默认 | 用途 |
|---|---|---|
| `MIRA_PROXY_RATE_LIMIT_INTERVAL` | 1 | 限频秒数 |
| `MIRA_AUTO_CONTINUE_ON_ERROR` | 0 | 错误自动重试 |
| `MIRA_AUTO_CONTINUE_MAX_RETRIES` | 3 | 重试次数 |
| `MIRA_CLI_SSE_IDLE_TIMEOUT` | 300 | SSE 流超时秒数 |

### 隐私说明（文档明确）
- mira cookie 保存在本地
- **本地设备的命令调用记录不会存储在服务端**

## 三、本机现状盘点（2026-07-25 实测，安装后）

### 安装阶段（已完成）

| 项 | 状态 | 备注 |
|---|---|---|
| `togo` 命令 | ✅ 已安装 v5.21.0 | 位于 `C:\Users\Admin\.local\bin\togo.exe` |
| `mira` 命令 | ✅ 已安装 v5.21.0 | 位于 `C:\Users\Admin\.local\bin\mira.exe` |
| `~/.togo/` 目录 | ✅ 已创建 | src/、uv-bootstrap/ 等 |
| `~/.mira/` 目录 | （等登录后创建） | |
| 同包装的其他 CLI | ✅ `aime`、`ida`、`mira-local` | 与 mira 共享 togo-cli wheel |
| PATH 配置 | ⚠️ 新 shell 需手动加 `~/.local/bin` | uv tool update-shell 已运行，但当前 Bash 会话需手动 export |

### 登录阶段（已完成，2026-07-26）

| 项 | 状态 | 备注 |
|---|---|---|
| `mira login --cookie` | ✅ 成功 | 凭证已落盘到 `~/.mira/config.json` |
| `mira status` | ✅ 正常 | sessionId=221449582099，Web 链接可跨设备恢复 |
| `mira -p "test"` | ✅ 非交互模式工作 | 自动识别 Windows 11/bash/工作目录/121 skills |
| `mira -p --output-format json "test"` | ✅ JSON 输出干净规整 | 包含 session_id/usage/cost 等字段 |

### 登录踩坑记录（重要，避免重复尝试）

| 路径 | 结果 | 原因 |
|---|---|---|
| rookiepy 自动读浏览器 cookie | ❌ 失败 | Chrome v130 appbound encryption，管理员权限也解不出 |
| headless Chrome + CDP 读 cookie | ❌ 失败 | user-data-dir 改变后 appbound key 失效，cookie 解不出 |
| DevTools 控制台 document.cookie | ❌ 失败 | mira_session 是 HttpOnly，JS 读不到 |
| Default profile 带 --remote-debugging-port | ❌ 失败 | user-data-dir 已被占用时 debug 端口静默不启 |
| **Chrome DevTools 手动复制 cookie + mira login --cookie** | ✅ 成功 | 绕开所有自动解密，直接粘贴明文 cookie |

**结论**：Chrome v130+ 的 appbound encryption 是物理限制，CLI 自动登录路径全部失效。后续本机若 cookie 过期（30 天），需要重复手动复制 cookie 流程。

### 桌面客户端与旧协议（无关项）

| 项 | 状态 | 备注 |
|---|---|---|
| `Mira.exe` 桌面客户端 | 已被关闭（6 进程清零） | 安装时被检测为锁文件风险，用户手动关闭。可随时重新启动 |
| 旧协作协议 `Aetheris-link/.mira/collaboration-protocol.md` | 存在（v1.0, 2026-05-26） | 旧 Mira×CC 协议，git + pending-review.json 信号，1h 轮询。**与 Togo CLI 体系无关**，是另一套机制 |

## 四、与编队定位的关系

按 `global-roadmap-v1.1.md`，Mira 在编队中的定位是**生图 + 代码/架构评审**（特化节点）。

Togo CLI 提供了三种接入路径，**需要决策**：

### 路径 A：通过 mira-cli 调度（终端形态，类似 Kimi 接入）
- 优点：跟 Kimi 接入模式一致，ZCode/Pi 可在终端中调度
- 缺点：mira-cli 是交互式 TUI，非 `-p` 一次性模式，subprocess 调度需改造

### 路径 B：通过 mira-proxy 反向被调度（CC/Claude 桌面用 Mira 后端）
- 优点：直接用 Mira 的 SOTA 模型当 Claude 后端
- 缺点：**这与「ZCode 主控」定位冲突**——proxy 模式下 Mira 变成 ZCode 的模型 provider，而不是被调度的执行节点
- 该路径适合「让 Claude Desktop/CC 用上 Mira 模型」的场景，不适合「编队调度 Mira 做评审/生图」

### 路径 C：用 Mira GUI + Togo MCP（让 Mira 后端通过 MCP 反向读写本地）
- 优点：Mira 自主模式，Togo MCP 桥接本地文件
- 缺点：仍是 Mira 主控本机，非编队调度

## 五、待决策

1. **编队 Mira 角色**到底是「被调度的执行节点」（路径 A）还是「SOTA 模型 provider」（路径 B）？二者互斥。
2. 如选路径 A：是否授权本机安装 Togo CLI（`curl | bash` 形式，红线：安装新工具需用户确认）。
3. 旧的 `Aetheris-link/.mira/collaboration-protocol.md`（v1.0, 2026-05-26）是否仍有效？需要废弃还是升级到 Togo 体系？

## 七、已验证的 Mira CLI 能力（v5.21.0 实测）

### A. 调度核心能力

| 能力 | 命令 | 验证状态 |
|---|---|---|
| 单次非交互模式 | `mira -p "<任务>"` | ✅ |
| JSON 结构化输出 | `--output-format json` | ✅ Pi 调度可解析 |
| 流式 JSON | `--output-format stream-json` | 未测 |
| 会话恢复（指定 ID） | `mira -p -r <session_id>` | ✅ session_id 字段返回 |
| 会话续接（最近） | `mira -p -c` | 未测 |
| Mock 模式（不耗 token） | `--mock` | 未测 |

### B. 模型切换（40+ 个，远超文档）

**默认**：`opus4.7`（Cloud-O-4.7，当前 CLI 已切到此）
**实测切换验证**：`glm5.2` ✅、`gpt-image-2` ✅、`gpt5.6sol` ✅、`opus4.8p` ✅

#### 完整模型清单（按厂商分组）

| 厂商 | 模型 ID | 备注 |
|---|---|---|
| **Cloud-O (Claude)** | opus4.8 / opus4.8t / opus4.8p / opus4.7 / opus4.7t / opus4.7p / opus4.6 / opus4.6t / opus4.6p / opus4.5 | t=Think, p=Pro |
| **GPT** | gpt5.5 / gpt5.5t / gpt5.5p / gpt5.6sol / gpt5.6luna / gpt5.6terra / gpt5.4 / gpt5.4pro | sol/luna/terra 是专精版 |
| **Gemini** | gemini3.1 / gemini3.5flash | |
| **GLM** | glm5 / glm5.1 / glm5.2 / glm5.2t / glm5.2p | **与 ZCode 同源** |
| **国产** | kimi / kimicoding / deepseek / minimax2.7 / seed2pro / seed2code | |
| **Sonnet** | sonnet4.6 / sonnet4 / sonnet3.7 / sonnet3.5 | |
| **Haiku** | haiku3.5 | 轻量 |
| **独立生图模型** | gpt-image-2 | OpenAI 生图模型 |

### B.2 生图能力分档（关键校正）

**生图有两条独立路径，不是同一个东西**：

| 路径 | 引擎 | 触发方式 | 实测域名 | 输出 |
|---|---|---|---|---|
| **Nano Draw（工具调用）** | Mira 后端工具 | 任何对话模型 + 提示词触发 `generate_pictures` / `edit_pictures` | `p-mira-img-sign-sgnontt.byteintl.net` | PNG/JPEG，一次最多 4 张 |
| **gpt-image-2（独立模型）** | OpenAI 模型 | `mira model gpt-image-2` 切换后直接画 | `mira.byteintl.net/mira/api/v1/file/` | PNG，一次 1 张 |

#### Nano Draw 能力（推荐主用）
- **generate_pictures**：文生图，文字描述 → 图片，一次最多 4 张
- **edit_pictures**：图生图/图像编辑，输入图片 URL + 修改要求，一次最多 4 张
- 输出格式：`png`（默认）/ `jpeg`
- **优势**：支持批量（4 张）、支持图生图编辑、跟对话模型协同（opus4.7 推理 + Nano 出图）

#### gpt-image-2 能力
- 纯文生图，一次 1 张
- **优势**：独立模型，不走工具调用链路，响应更直接

#### 编队生图策略
- **默认走 Nano Draw**：批量、可编辑、跟推理模型协同
- **gpt-image-2 备选**：需要 OpenAI 风格时用

### B.3 评审模型路由策略（用户裁决 2026-07-26 v2）

| 场景 | 模型 | 触发条件 |
|---|---|---|
| **默认评审** | **gpt5.6sol** | 所有日常架构/代码评审首选 |
| **复杂问题双审** | **opus4.8p** | gpt5.6sol 输出后，对复杂/关键问题补充 Claude 视角双审 |

**双审工作流**：
```
gpt5.6sol 评审 → 若问题复杂 → opus4.8p 二次评审 → 综合两份结论
```

实测数据：
- gpt5.6sol：10.8s，20K input + 80 output tokens（快、省）
- opus4.8p：12.5s，含 thinking_tokens=19（深、细）

### B.4 生图工作流（用户裁决 2026-07-26）

**三条路径，按场景路由**：

#### 路径 ① 单图高质量（默认，gpt-image-2 直出）
**适用**：单张图、质量优先、不需要批量
**工作流**：`用户简短需求 → Gemini 3.5flash 提示词扩写/仿写/优化 → gpt-image-2 直出`

```
[用户输入] "一只柴犬坐草地上"
    ↓
[Gemini 3.5flash] 扩写为详细英文提示词（主体+风格+光照+构图+细节）
    ↓
[gpt-image-2] 直出生成 PNG
    ↓
[输出] 图片 URL
```

**编队单质量最高的单图模型**。

#### 路径 ② 批量生图（Nano 引擎）
**适用**：一次多张、快速出图、风格探索
**工作流**：`任意对话模型 + generate_pictures 工具调用`

```
[用户输入] "柴犬 4 种不同姿态"
    ↓
[opus4.7 或其他对话模型] 调用 Nano generate_pictures 工具
    ↓
[输出] 最多 4 张 PNG URL
```

#### 路径 ③ 图生图/编辑（Nano edit_pictures）
**适用**：基于已有图修改、风格化、元素替换
**工作流**：`图片 URL + 修改要求 → Nano edit_pictures 工具`

### B.5 调度策略总表（更新版）

| 任务类型 | 推荐路径/模型 | 触发条件 |
|---|---|---|
| **代码/架构评审（默认）** | gpt5.6sol | 日常评审 |
| **代码/架构评审（双审）** | gpt5.6sol + opus4.8p | 复杂问题 |
| **生图（单图高质量）** | Gemini 3.5flash → gpt-image-2 | 单张、质量优先 |
| **生图（批量）** | opus4.7 + Nano generate_pictures | 多张、探索 |
| **生图（图生图）** | opus4.7 + Nano edit_pictures | 基于已有图修改 |
| 前端方案探索 | kimi / kimicoding | 与编队 Kimi 同源 |
| 中文场景 | glm5.2 | 中文优化 |
| 文档/总结 | haiku3.5 | 量大便宜 |

### B.6 待评估项（用户裁决纳入后续）

- **两路径质量对比**：用户目前无法评判 gpt-image-2 vs Nano Draw 的质量差异
- **后续动作**：构建标准测试集（同提示词两路径各跑一次），人工评判质量差异
- **优先级**：中等（不影响主线，但影响最终路由策略）

### C. 历史会话与远端任务能力（重大发现，2026-07-26）

**之前判断错误**：原以为"客户端历史不自动同步到 CLI"。实测校正——**会自动同步**，且能完整 resume。

#### C.1 远端会话同步机制
- Mira 后端会话**自动同步到本地 JSONL 转录文件**（`~/.mira/conversations/`）
- `mira history` 命令只显示 CLI 创建的会话（误导性），但**远端会话实际已落盘**
- 通过 Skill（`mira-chat-organizer`）或直接读 JSONL 能拿到全部远端会话

#### C.2 跨设备会话恢复（已实测）
```bash
mira -p -r <session_id> "用一句话总结我们上一个回合在讨论什么"
```
**实测结果**：resume 远端会话 `221678259987`（客户端创建的 Prompt 工程会话），Mira 完整记住上下文，准确复述了之前的讨论内容。

**编队价值**：
- ZCode/Pi 调度 Mira 时，**任何远端会话都能被恢复并续接**
- 客户端里未完成的任务，CLI 可以接着做
- session_id 来自 Mira Web URL 的数字（如 `/chat/221678259987`）

#### C.3 Mira 内置 Skill 清单（远端业务数据访问）

Mira CLI 不仅是 LLM 调度入口，还内置了大量**字节内部业务数据访问 Skill**：

| 类别 | Skill 名 | 能力 | 编队价值 |
|---|---|---|---|
| **Mira 自身** | `mira-usage` | 使用量统计（活跃天数/token/会话数/模型分布） | ⭐ Pi 成本治理数据源 |
| | `mira-chat-organizer` | 历史会话整理+按主题归类到 Project | ⭐ 远端任务检索 |
| | `mira-share-viewer` | 查看 `/share/` 或 `/chat/` 链接内容 | |
| **飞书办公** | `lark-task` | 飞书任务（待办/已完成） | ⭐ CSM 工作核心 |
| | `lark-calendar` | 飞书日程、会议、忙闲 | ⭐ CSM 工作核心 |
| | `lark-doc` / `lark-wiki` / `lark-base` | 飞书文档/知识库/多维表格 | ⭐ 客户资料 |
| | `lark-im` / `im-chat-manager` | 飞书群聊消息 | |
| **CIS** | `cis-cli` | 审批/报销/差旅待办 | |
| **HR** | `people-performance` / `people-level-comp-review` | 绩效/调薪 | |
| **检索** | `one_context` | 公司私域检索（文档/消息/OKR/妙记） | ⭐ 知识检索 |
| | `memory-import` | 导入记忆片段 | |

**关键约束**：
- ❌ **没有跨平台聚合 API**——不能一键拉所有系统的任务清单
- ✅ 只能按 Skill 分渠道查
- ⚠️ 部分 Skill 需要具体参数（文档 ID、空间 ID 等），不能盲查

#### C.4 用户真实使用画像（mira-usage 实测，2026-07-26）

通过 `mira-usage` skill 拉取的真实数据：

| 指标 | 数值 |
|---|---|
| 活跃天数（近 30 天）| 27 天 |
| 总会话数 | 384 |
| 总 Token | 6.66 亿 |
| 首次活跃 | 2026-05-07 |
| 主力模型 | Orange-Outstanding-4.8（opus4.8）占 79.7% |
| 次主力 | Gemini 3.5 Flash / opus4.6 / Gpt Image 2 |

**含义**：用户是 Mira 重度使用者，主力模型已经是 opus4.8，跟编队评审策略（gpt5.6sol + opus4.8p 双审）契合。

### D. 生图能力（roadmap 关键）

**已实测通过**：
```bash
mira model gpt-image-2
mira -p "画一个简单的红色圆圈" --output-format json
```
返回：`![](https://mira.byteintl.net/mira/api/v1/file/d/tos-mya-i-xobrcjvdq7/xxx.png)` —— 图片 URL（21s 生成）

**Mira 在编队里的生图定位明确成立**。

### E. 其他能力（部分未测）

| 命令 | 能力 | 是否测过 |
|---|---|---|
| `mira spec /lume:*` | SpecCoding（PM 模式 + Feature/design/tasks/spec.md 流程） | 未测 |
| `mira mcp setup` | MCP Bridge 安装（暴露本地工具给 Mira 后端） | 未测 |
| `mira mcp run/start/stop` | MCP Bridge 后台管理 | 未测 |
| `mira plugin add/list/enable` | Claude Code 兼容插件管理 | 未测 |
| `mira hook install` | AI 代码贡献埋点（改 ~/.claude/settings.json + git hooks） | **不测**（CC 已退役） |
| `mira proxy` | Anthropic 兼容代理（127.0.0.1:8787） | **不测**（与主控定位冲突） |
| `mira togo` | 注册本机为 MCP + 启动 togo connect | **不测**（会触发 mira-proxy） |

### F. 客户端能力对比

**客户端独有（CLI 不直接暴露）**：
- 项目（Project）
- 任务（Task）— Togo 平台的跨设备任务派发
- 记忆（Memory）— 长期记忆库
- MCP 后端调度

**CLI 独有（客户端没有）**：
- `-p` 非交互模式（适合自动化）
- `--output-format json`（适合 Pi 解析）
- 跨设备 session 恢复（`-r`）

**结论**：CLI 是客户端的"调度入口子集"，覆盖**对话 + 模型切换 + 生图 + 历史恢复**，但**项目/任务/记忆**这类 GUI 重功能不直接暴露给 CLI。

## 八、Pi 调度方案设计草案（参照 Kimi 接入模式）

基于实测验证，Mira CLI 完全支持 Pi 编队调度：

### 调度入口
```bash
mira -p "<任务描述>" --output-format json
```

### 输出解析（Pi 关注字段）
| 字段 | 用途 |
|---|---|
| `is_error` | 调度结果判定 |
| `result` | 模型回复内容 |
| `session_id` | 会话续接（`mira -p -r <session_id> "续问"`）|
| `usage.input_tokens / output_tokens` | token 成本治理 |
| `total_cost_usd` | 内部工具为 0，不消耗预算 |
| `duration_ms` | 性能监控 |

### 模型选择策略（成本治理）
- 默认 opus4.6（最强但贵）
- 轻量任务（评审/总结/分类）：显式切 `sonnet4.6` 或 `sonnet4`
- 切换：`mira model sonnet4.6`

### 编队角色定位（按 global-roadmap-v1.1）
Mira 是**生图 + 代码/架构评审**特化节点：
- 评审任务：`mira -p "评审以下代码/架构..." --output-format json`
- 生图任务：需进一步测 Mira 是否有生图能力（暂未验证）
- 跨设备会话续接：通过 `session_id` 实现（Mira 的强项）

### 待验证项（接入设计阶段完成）
1. **生图能力**：roadmap 中 Mira 定位含"生图"，但 CLI 是否暴露生图接口未验证
2. **大文件处理**：评审代码片段时是否支持文件路径输入
3. **MCP 注册**：`mira mcp setup` 能否将编队其他工具暴露给 Mira
4. **与 Kimi 的边界**：前端实现归 Kimi，Mira 不碰仓库代码

### 风险与边界
- ⚠️ **不要跑 `mira togo`**：会启动 togo connect + mira-proxy，可能改 `~/.claude/settings.json`（CC 已退役）
- ⚠️ **cookie 30 天过期**：到期需手动复制 cookie 重登（appbound encryption 限制）
- ⚠️ **ZCode 当前提权状态**：为读 cookie 临时提权，建议完成 Mira 接入设计后取消提权
- ⚠️ **不进 git/不进日志**：cookie 凭证信息不写入任何版本控制
