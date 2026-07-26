# Pi 飞书指令手册

> 群名：**AI协作大群**
> 机器人：**@Aetheris-息壤**
> 用法：在群里 @机器人 + 指令，或直接发指令关键词

## 指令一览

| 指令 | 作用 | 示例 |
|---|---|---|
| `体检` / `漂移` | 立即执行漂移体检，发交互卡片 | `@Aetheris-息壤 体检` |
| `状态` / `status` | 查看各分支同步状态（简洁版） | `@Aetheris-息壤 状态` |
| `同步 <分支>` | 把 master 同步到指定分支 | `@Aetheris-息壤 同步 kimi` |
| `qoder <任务>` | 转发给 Qoder 云智能体执行 | `@Aetheris-息壤 qoder 写一个快排` |
| `帮助` / `help` | 显示指令列表 | `@Aetheris-息壤 帮助` |

可用分支：`claude` / `kimi` / `qoder` / `trae` / `solo` / `zcode`

---

## Qoder 云智能体指令详解

Qoder 是部署在云端的代码智能体。通过飞书群可以直接给它派活，它执行完把结果发回群里。

### 基本用法

```
@Aetheris-息壤 qoder <你的任务描述>
```

或用等价前缀：

```
@Aetheris-息壤 @qoder <任务>
@Aetheris-息壤 任务 <任务>
```

### 适合的任务类型

✅ **适合交给 Qoder 的：**
- 写函数/组件/脚本（"写一个防抖函数"、"生成一个 React 按钮组件"）
- 代码分析（"这段代码有什么问题：..."）
- 格式转换（"把这段 JSON 转成 TypeScript 接口"）
- 解释概念（"解释一下 Promise.all"）

⚠️ **不适合交给 Qoder 的：**
- 操作你的仓库（Qoder 在云端，不碰你的本地 git）
- 需要看大量上下文的任务（单个会话上下文有限）
- 实时交互式调试（它是单轮任务模式）

### 执行流程

```
你发指令 → Pi 确认"已转发" → Qoder 云端执行 → 结果回流到群
           (立即)              (几秒到几分钟)      (代码块格式)
```

### 示例

```
@Aetheris-息壤 qoder 用 Python 写一个函数：输入一个列表，返回其中所有重复元素

→ Pi 回复：
   📤 任务已转发给 Qoder
   📝 用 Python 写一个函数：输入一个列表...
   ⏳ 云端执行中,结果稍后回流...

→ Qoder 完成后 Pi 回复：
   ✅ Qoder 完成 (3.2s)
   🆔 sess_xxx
   
   def find_duplicates(lst):
       seen, dups = set(), set()
       for x in lst:
           if x in seen: dups.add(x)
           seen.add(x)
       return list(dups)
```

---

## ZCode 本地直接调用 Qoder

除了飞书群，你也可以在本地命令行直接调 Qoder（不走飞书）：

```bash
# 单次任务
python qoder-bridge.py "你的任务描述"

# 列出所有会话
python qoder-bridge.py --list

# 查某个会话状态
python qoder-bridge.py --status <session_id>

# 查某个会话的完整对话
python qoder-bridge.py --result <session_id>
```

**前提**：需要 `export QODER_PAT=你的PAT`（PAT 已存在 ECS 的 `.env`，本地用需要单独配置）。

---

## 自动化：漂移体检

不用手动操作。Pi 每 30 分钟自动执行一次漂移体检：

- **正常**：不发消息（不打扰）
- **发现分叉/冲突**：自动发交互卡片到群里，带"通知智能体"/"自动同步"按钮
- **冲突升级**：按 NOTICE → WARN(1h) → CRITICAL(2h) → ESCALATE(4h) 逐级提醒

手动触发：群里发 `体检` 或 `漂移`。

---

## 架构说明

```
  你（飞书群）              ZCode 本地           Pi 自动化(cron)
     │                        │                      │
     │ @bot qoder ...         │ python qoder-        │ drift-cron.sh
     │                        │   bridge.py "..."    │
     ▼                        ▼                      ▼
  ┌──────────────────────────────────────────────────────┐
  │     feishu-message-handler.py（飞书桥接）              │
  │              ↓ 导入                                    │
  │     qoder_bridge.py（统一 Qoder 客户端）               │
  │     · create_session() · send_message()              │
  │     · stream_response() · run_task()                 │
  └──────────────────────────┬───────────────────────────┘
                             ▼
               Qoder Cloud Agents API
               POST /sessions/{id}/events
               GET  /sessions/{id}/events/stream (SSE)
```

三个入口共用同一个 `qoder_bridge.py` 模块，API 调用逻辑只写一次。
