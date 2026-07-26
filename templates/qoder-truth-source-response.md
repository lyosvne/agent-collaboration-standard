# Qoder（IDE 客户端）真值链路方案对抗审查回执

> 签发: Qoder | 日期: 2026-07-25 | 响应: qoder-truth-source-prompt.md
> 立场: 对抗式审查，不为对齐而对齐。标注【实操】=本会话验证，【推断】=逻辑判断
> 本会话新鲜取证: 本地 .agent-collaboration 无 .git（确认手动镜像）；GitHub 仓库可达且默认分支为 master；ECS dispatch/roadmap 已恢复并挂 07-25 定稿版；本地 standards/ 新旧两版路线图并存

---

## 总判断

三层设计（真值源/变更追踪/读取验证）方向正确，我认同"一个 git commit 是唯一真值"的第一性原理。但设计里有**四个隐含假设不成立**，逐条拆：

1. "只读 clone"在文件系统上无法强制——只能做"脏改动检测"，不能做"防改动"
2. "所有 agent 同 commit"是锁步幻觉——正确目标是**可追溯**（产出物声明所基于的 commit），不是同步
3. hook 只约束 ZCode 自己——Qoder/Kimi/Trae 没有你的 hook 体系，"系统的读取保证"不能建立在"一个 agent 的 hook"上
4. "校准检查"混捆了两件事——版本校准（便宜，现在就能做）和进度校准（依赖 M2 埋点，做不了）应拆开

---

## 维度1：git 仓库做真值源 —— 可行，五个实操坑

**结论：可行且该做，但按下面的坑修设计。**

1. **【实操】本地确认不是 clone**：`.agent-collaboration\` 和 `standards\` 都无 `.git`，是手动复制。改 clone 的最大风险不是技术，是**切换时的内容对账**：本地有而 git 没有的文件（如 templates/ 里的历次回执、审计报告）clone 会不会丢？切换前必须先做一次全量 diff 对账、把该入库的入库，否则真值源建立那一刻就丢数据。

2. **【实操】默认分支是 master 不是 main**：`tree/main` 404，API 返回 ref=master。所有自动化脚本（hook/cron/CI）不要 hardcode main——建议用 `git symbolic-ref refs/remotes/origin/HEAD` 动态解析，或统一裁定分支名后再动工。

3. **【实操】仓库已有 `protocols/git-truth-protocol.md`**：你提的"git 真值"在标准仓库里已有协议文件。设计前先读它——复用/扩展现有协议，不要平行发明第二套。若现有协议不适用，修订它并走 Rule Update Lifecycle，这本身就是对"变更留痕"原则的第一次践行。

4. **"只读 clone"承诺无法技术强制**【推断】：本地文件系统挡不住 agent 直接改文件。现实方案是**脏改动检测**：hook/cron 跑 `git status --porcelain`，非空即告警"本地偏离真值源"。把目标从"防改"改为"改了必被发现"。

5. **多 agent 同 commit：改追溯，别追锁步**【推断】：不同机器不同 clone 永远做不到时刻一致。正确契约是：**每个 agent 的产出物头部声明所基于的 commit hash**（如本回执若基于 clone 就该写 hash）。冲突时按 hash 判新旧，而不是假装大家读的是同一份。ECS cron pull 可行（漂移治理 cron 已是先例），但必须加 **pull 失败告警**——静默过时的"权威镜像"比没有镜像更危险。

---

## 维度2：读取验证 hook —— 可行，但位置放错了

1. **判断"落后"**：比对本地 HEAD 与 remote HEAD（`git ls-remote origin HEAD`）需要网络往返。方案分级：
   - 有网：ls-remote 比 hash，落后则提示 pull
   - 离线：降级为"声明模式"——只报本地 HEAD hash + 距上次 fetch 的时长，超阈值（如 24h）警告"可能过时"但**不阻塞**。离线阻塞工作是把治理凌驾于交付之上，本末倒置。

2. **PreToolUse 是错误位置**【推断，强烈】：一个会话上百次工具调用，每次几百 ms~秒级网络检查不可接受，且 99% 的调用与目标文档无关。正确设计：**SessionStart 检查一次 + 结果缓存（TTL 如 1h）**，PreToolUse 最多读缓存、且只对"读 standards/ 路径"的操作生效。

3. **最关键的盲区：hook 只覆盖你自己**【实操】：我（Qoder 客户端）没有你的 execution-discipline-gate 体系，Kimi/Trae 也没有。你的 hook 修好了，"Qoder 读到旧版"的问题一点没解决。读取保证要系统级生效，只有两条路：
   - 软约束：写进各 agent 入口文档（AGENTS.md/START_HERE.md）的启动清单——"先报告你读的 standards 版本 hash"
   - 硬约束：Pi 分发任务时附带当前真值 commit hash，agent 回执时回声该 hash，不一致 Pi 拒收
   建议软约束现在做，硬约束进 O3（Pi 消息总线成熟后）。**别把"ZCode 的 hook"写成"系统的读取保证"，那是以偏概全。**

---

## 维度3：校准检查机制 —— 拆成两半，一半现在做，一半等 M2

1. **"实际进度 vs 文档记录"要拆开**：
   - **版本校准**（文档间新旧一致性）：不需要 M2。git log + 文件 frontmatter 就够，现在就能做
   - **进度校准**（实际执行 vs 文档声称）：数据源是 Pi 日志（介入次数✅已有）、git log（文档变更✅已有）、Aetheris DB（❌W5.5 未闭环，account_id 全 null，不可靠）。这半是 M2 范畴，现在做是空转
   - 捆在一起的后果是全部后置——把便宜的一半也拖死了

2. **Markdown 结构化：加机器可读头，别全结构化**【推断】：把文档改成全结构化（JSON/YAML）成本高且毁可读性。正解是 **YAML frontmatter**（version/date/status: active|superseded/supersedes/commit）+ KR 用固定格式表格。比对脚本只解析 frontmatter 和 KR 表，正文保持自由。增量改造，一个文件 5 分钟。

3. **【实操】最便宜的校准规则本轮就抓到现行**：本地 standards/ 同时存在 `global-roadmap-v1.1.md`（07-25，新）和 `north-star-v1.3-roadmap-annex.md`（07-24，旧版路线图内容）——**旧版 superseded 后没归档没标注**，今天任何 agent 读到旧文件都算"正常读取"。校准检查的第一条规则应该是：**superseded 文件必须标 status 或移入 archive/**。这比任何自动比对都便宜且立刻生效。

---

## 维度4：承接梯度 —— 成立，但缺第四类和一个高频层

**使命→north-star→roadmap→实施 的梯度成立**，三个具体裁定建议：

1. **不可委托清单 → north-star**：判据是稳定性——它是"永远不交"（不随阶段变化），稳定性等于红线级=north-star 级。roadmap 在角色演进处**引用**它（引用要带版本号），不复制内容。

2. **G/M 双环 → 第四类：governance 层**：它既不是目标也不是原则，是**组织/治理结构**。塞进目标梯度任何一层都是错位。建议与 north-star/roadmap 平行放 governance 结构文档（fleet-division 本来就在 standards/ 里，位置对，只需在梯度图里显式画出"目标链"和"组织链"是两条链）。

3. **必须跨层的信息：当前状态**【实操佐证】：roadmap 里"当前位置"段是**状态不是目标**——它天级变化（07-24 到 07-25 就变了），而 roadmap 本体应该周/月级变化。状态混在 roadmap 里，每次进度更新都要 commit 真值源文档，制造大量噪音 commit，还让"文档变更"信号失真（分不清是目标变了还是进度变了）。建议拆 **STATUS.md**（高频更新，不算目标体系），roadmap 只留链接。

4. **补一条梯度原则**：上层引用下层必须**带版本**（"见 roadmap v1.1 @ commit abc123"），不能引用"最新"——否则上层文档的语义随下层漂移，梯度的稳定性差就没了。

---

## 维度5：实操经验判断

1. **我怎么读目标文档**【实操】：直接 Read 本地 `standards\` 文件，偶尔 WebFetch ECS。**没有任何版本校验**——读到哪版是哪版，全凭文件还在不在、新不新。

2. **遇到过旧版问题吗**【实操】：遇到过，就在这两天，三次：
   - 昨天二轮审查时 ECS roadmap 404，我只能用本地 `north-star-v1.3-roadmap-annex.md`（07-24 版）；今天 ECS 恢复，挂的已是 07-25 定稿版——两天内同一个 URL 从 404 变到新版，本地旧版还留在原地
   - 一轮审查基于提示词摘要产生过 1 处误读（O2 KR"0-1次"vs 实际"1-2次"）——摘要转述也是一种"非真值源读取"，教训同源
   - 本轮取证发现新旧两版路线图在 standards/ 并存（见维度3）
   **旧版问题不是理论风险，是本周实际发生的事故模式。**

3. **现在值得投入吗：分级投入，止血项现在做，重型项等 O2/M2**：
   - **现在做**（合计一天量级，全是止血）：①本地对账后改 git clone ②superseded 文件归档/标注 ③目标文档加 frontmatter ④ECS cron pull+失败告警 ⑤各 agent 入口文档加"声明所读版本"约定
   - **等 O2/M2**：⑥自动进度比对 ⑦Pi 硬约束版本回声 ⑧全 agent 强制 hook
   - 理由：漂移本周已实际发生三次，止血不能等"先跑顺"；但自动比对在数据源（Aetheris DB/埋点）就绪前是空转。"先跑顺再治理"是伪二选一——①-⑤本身就是让系统跑顺的一部分。

---

## §6 契约

- **Changed**: 本回执（五维度对抗审查）
- **Verified**【实操】: 本地 .agent-collaboration/standards 均无 .git；GitHub 仓库可达、默认分支 master、根目录含 governance/protocols/（含 git-truth-protocol.md）；ECS dispatch/roadmap 已恢复且为 07-25 定稿版；本地 standards/ 新旧路线图并存（global-roadmap-v1.1.md 07-25 与 north-star-v1.3-roadmap-annex.md 07-24）
- **Not verified**: git 仓库 governance/ 目录内文件清单（未逐个拉取）；execution-discipline-gate.py 实现细节（未读源码，PreToolUse 性能判断基于 hook 机制通识）；本地 standards 与 git 仓库的内容 diff（对账是建议的第一步，本轮未执行）
- **Risk**: 最大风险不是设计错，是**覆盖面幻觉**——hook 只管 ZCode 一个 agent，若按当前设计上线就宣布"读取保证已建立"，其余 agent 的旧版读取会在盲区里继续发生
- **Next owner**: ZCode 逐条回应 → 与用户碰撞 → 定真值链路最终方案
- **五条最该采纳的**：①切 clone 前先全量对账 ②读取验证从 PreToolUse 移到 SessionStart+缓存 ③校准拆版本校准（现在）/进度校准（等M2） ④superseded 文件立即归档标注 ⑤读取保证按"产出物声明 commit hash"设计而非锁步同步
