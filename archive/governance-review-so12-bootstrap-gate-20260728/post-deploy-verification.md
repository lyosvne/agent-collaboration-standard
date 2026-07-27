# SO-12 上线后实测验证清单

> 状态：SO-12 已 commit + push（ed5b17a），但以下两项**未实测**，是上线前阻断点。
> 本 session 无法自测（hook 触发点在 Bash 工具调用之前，无法从内部观测；且 config.json 改动需 ZCode reload）。
> 用户重启 ZCode 后第一件事走本清单。

## 一、为什么本 session 测不了

1. **hook 触发点在 Bash 工具调用之前**：如果 hook deny 了，我的 Bash 根本不会被调起来，我无法从内部观测"我被拦了"
2. **config.json 改动需 reload**：ZCode 启动时读一次 config.json 注册 hook，改配置后要重启 ZCode 才生效（SKILL.md §1 "Configuration-file hooks"）
3. **ZCode 日志不记录 hook 执行**：INFO 级别只到 RPC，看不到 hook fired/timed out/blocked（SKILL.md §3 说"execution recorded in log"，但实测 2026-07-28.log 里 grep 不到 chain-gate/session-gate，可能日志级别或路径不同）

## 二、重启 ZCode 后必做的 3 项验证

### 验证 1：SessionStart hook 是否触发 + additionalContext 是否注入

**步骤**：
1. 完全退出 ZCode（托盘右键退出，不只是关窗口）
2. 重新启动 ZCode，打开 agent-collaboration-standard 项目
3. 新 session 第一条消息问："你看到了 SO-12 bootstrap 真值三件套吗？reviewer-tiers.yaml 的档位是什么？"

**期望**：
- session 启动时 SessionStart hook（matcher: startup）被触发
- additionalContext 注入到对话上下文（你能看到 reviewer-tiers.yaml 内容 + spec §二 + config.json）
- ZCode 回答 "看到了，A=opus4.8p, B=gpt5.6sol, C=cantus"（从注入的 additionalContext 读，不是凭记忆）

**如果失败**（ZCode 说没看到 / 凭记忆答）：
- SessionStart hook 没触发，或 additionalContext 没注入
- 排查：config.json 的 SessionStart matcher 是否正确、bootstrap-inject-sessionstart.py 是否有语法错误（`python .zcode/hooks/bootstrap-inject-sessionstart.py < /dev/null` 看是否崩）

### 验证 2：ZCODE_SESSION_ID 环境变量是否注入到 hook 进程

**步骤**（重启后在新 session 里）：
1. 让 ZCode 跑一条 Bash 命令：`python -c "import os; print('SESSION_ID =', os.environ.get('ZCODE_SESSION_ID') or os.environ.get('CLAUDE_SESSION_ID') or '(none)')"`
2. 看输出

**期望**：
- 输出 `SESSION_ID = sess_xxx`（ZCode 注入了 session_id）
- 这是 bootstrap-gate M1（纯 session_id 校验）能工作的前提

**如果输出 (none)**（关键阻断）：
- ZCode 没把 session_id 注入到 Bash 工具子进程的 env
- **注意**：Bash 工具子进程 ≠ hook 进程，hook 进程可能有 session_id 即使 Bash 子进程没有
- 真正验证 hook 进程的 env：临时改 bootstrap-inject-sessionstart.py，在 main 开头加一行 `open(r'C:\Users\Admin\.zcode\hooks\.env-dump.txt','w').write(str(dict(os.environ)))`，重启 ZCode 触发 SessionStart，看 .env-dump.txt 里有没有 ZCODE_SESSION_ID
- 如果 hook 进程也没有 session_id → bootstrap-gate 的 M1 会**永久 deny 所有动手类**（因为 env 永远缺失）→ 必须回退 M1 或改设计（如改用时间窗口兜底，或用进程 PID + 启动时间作为 session 标识）

### 验证 3：bootstrap-gate 是否真在第 1 位 + 真拦得住

**步骤**（验证 2 通过后）：
1. 新 session 启动后（SessionStart 应已写 bootstrap 标记）
2. 让 ZCode 跑一条动手类命令，但故意不 bootstrap：先 `rm C:/Users/Admin/.zcode/hooks/.bootstrap-done.json` 删标记
3. 再跑 `mira -p "评审方 A" --model opus4.8p`（不 export CURRENT_REVIEW_PROJECT）

**期望**：
- bootstrap-gate deny + 提示"未完成 bootstrap（SO-12）"
- 且 deny 发生在 chain-gate/session-gate 之前（因为是第 1 位）

**如果没拦**：
- config.json 顺序没生效，或 bootstrap-gate 脚本崩了
- 排查：`python .zcode/hooks/bootstrap-gate-precommit.py < /dev/null` 看是否崩

## 三、如果验证 2 失败的应急方案

C 新发现 2 警告的"fail-closed 退化为永久锁死"场景：如果 ZCode 不注入 ZCODE_SESSION_ID 到 hook 进程，bootstrap-gate 的 M1（env 缺失 → deny）会让所有动手类操作永远被拦，用户被迫手动伪造标记绕过——"纪律被架构逼出违规"。

**应急方案**（如果验证 2 失败）：
- **方案 A（回退时间窗口）**：恢复 8h 时间窗口兜底（放弃 M1 的纯 session_id 校验）。缺点：C round1 指出的 fail-open 风险回来。
- **方案 B（改 session 标识）**：bootstrap 标记不依赖 ZCODE_SESSION_ID，改用"进程启动时间 + PID"或"标记文件 mtime 在 ZCode 进程启动之后"作为 session 身份。
- **方案 C（标记 + 显式激活）**：bootstrap-gate 检查标记的 bootstrapped_at_epoch 在"最近一次 ZCode 进程启动时间"之后。ZCode 启动时间从日志或进程列表推。

**推荐**：先做验证 2，据结果选方案。不要现在就改设计——可能 ZCode 真的注入了，只是我测不到。

## 四、实测前的临时保护

在验证 1-3 完成前，bootstrap-gate 已经挂上但行为未知。为防止"永久锁死"或"不生效"两种极端：
- 如果重启后发现动手类全被拦（验证 2 失败场景）：临时 `rm .zcode/hooks/.bootstrap-done.json` + 改 config.json 把 bootstrap-gate 注释掉，恢复工作能力，再走应急方案
- 如果重启后发现 hook 完全没生效（验证 1/3 失败场景）：说明 ZCode 没加载 hook，检查 config.json schema 和 ZCode 版本兼容性

## 五、登记到 SO-13 backlog

以下问题本 session 暴露但未解决，登记 SO-13：
- SessionStart hook 触发的实测验证方法（需要一个能留下痕迹的诊断 hook）
- hook 执行日志的可观测性（ZCode 日志不记录 hook 执行，排查困难）
- ZCODE_SESSION_ID 注入范围确认（Bash 工具子进程 vs hook 进程）
