---
version: 1.0
status: active
type: retrospective
created: 2026-07-26
owner: ZCode
title: 节点 2 评审 5 轮迭代复盘 + 编队传播缺失诊断
scope: 节点 2 评审(round1→round5)的经验沉淀 + 传播缺失诊断 + 路线缺口核查
related:
  - specs/review-process-lessons.md
  - specs/agent-collaboration-git-sync-plan.md
  - specs/o1-governance-plan.md
---

# 节点 2 评审 5 轮迭代复盘 + 编队传播缺失诊断

## 一、节点 2 评审 5 轮迭代数据

| 轮次 | A (opus4.8p) | B (gpt5.6sol) | C (cantus) | commit |
|---|---|---|---|---|
| round1 | 条件(1 阻断) | 不通过(5 阻断) | 超时(工具轨迹指向) | `0359227` |
| round2 | 条件(1 阻断) | 不通过(4 阻断) | 不通过(3 阻断) | `cc8c83a` |
| round3 | 条件(3 阻断) | 不通过(4 阻断) | 条件(2 阻断) | `d969cea` |
| round4 | **通过**(0) | 不通过(2 阻断) | 条件(2 阻断) | `3c48344` |
| round5 | — | **通过**(0) | **通过**(0) | `b2eb24e` |

**最终:三方一致通过,Phase C 合并 master 完成(commit b2eb24e)**。

## 二、核心教训(5 条)

### 2.1 fail-open 是治理评审的核心,不是"能跑过门禁"

5 轮迭代里,A/B/C 反复攻击的都是 fail-open:
- round1: `classify()` 永不返回 ROLE(所有分支归 HISTORY)+ gate4=gate3(tautology)
- round2: classify 宽泛词("支持/兼容/知识库")可吸收现行角色引用
- round3: gate3 盲信任 exceptions(同一集合比对)
- round4: specs/ 整目录白名单 + content 词桶(case/grep/awk)
- round5: per-occurrence 循环丢失(回归)+ content 词桶收窄不彻底

**根本教训**:治理门禁的目标是"现行角色引用 = 0",任何自动分类都是攻击面。最严的设计是:**自动分类面最小(只认 archive/+明确历史关键词),其他全 raise 强制人工,人工结果写入定点 overrides(只认 key 不认内容模式)**。

### 2.2 启发式判定不可能零 fail-open,人工 override 是必要补丁

5 轮迭代证明了:无论关键词列表收得多窄,总能构造绕过句("in case Codex fails"含 case)。最终方案是**四层防御**:
1. classify 最严收窄(自动判定面最小)
2. 人工 overrides(定点 key 精确匹配,不泛化,无 tautony)
3. gate3 独立启发式(不依赖自动 exceptions)
4. gate4 集合比对(数据完整性)

**关键洞察**(A/C 反驳 B 的 override 未绑内容):**override 是定点 key 不是模式**,新增的现行角色引用 key 不在清单 → 必阻断。攻击向量只对"修改已有 override 坐标的内容"有效,实战需要精确知道哪个坐标在 overrides,门槛高。

### 2.3 每轮评审都会引入新 fail-open,5 轮是必要的

| 轮 | 修的 fail-open | 引入的新 fail-open |
|---|---|---|
| round2 | gate3/4 tautology | classify 宽泛词 |
| round3 | classify 宽泛词 | specs/ 整目录白名单 + content 词桶 |
| round4 | specs/ 白名单 + 人工 overrides | per-occurrence 循环丢失(回归) |
| round5 | per-occurrence + content 词桶 | (无,真闭环) |

**根本教训**:修复 fail-open 时容易引入新 fail-open(回归)。必须用 diff 比对 + 实测复现验证。C 在 round4 用 diff 比对发现了 per-occurrence 回归,A/B 都没发现。

### 2.4 调度独立性 ≠ 调度方影响

round1 的另一会话担心"GLM-5.2 调度评审 = 选材/读结果/汇总的都是同一模型,独立性打折"。5 轮实证证明这个担心**部分成立但不致命**:
- A/B/C 是真不同模型独立产出(Mira 切模型 + Qoder cantus)
- 评审包(主评审包 + prompt)是节点 1 v3.4 三方一致通过的产物
- 汇总时 ZCode 如实呈现三方原文 + 交叉确认
- B/C 都独立 git clone 公开远程仓库复核(不依赖 ZCode 材料)

**真正的独立性风险**:cantus 顶层档深度思考特性导致单次 run_task 超时,容易"工具复核完成但没输出文字结论"。修法是 run_turn 多轮 + _wait_idle 组合,或限制工具调用次数。

### 2.5 三方评审必须用三个独立 run_in_background 并行

round1 首次用单 Bash `&` 起多评审,主 shell 退出子进程被杀,输出 0 字节。修复:三个独立 `run_in_background: true` Bash 调用,在同一条消息里发出。

## 三、编队传播缺失诊断(用户问"为什么其他会话/智能体不知道")

### 3.1 现状

| Agent | 能拿到全局上下文？ | 原因 |
|---|---|---|
| ZCode | ✅ | AGENTS.md 硬编码指向 standards/ |
| Trae(已退役) | ✅ | 同上 |
| **Qoder/Kimi/Mira** | ❌ | 调度无注入,靠主动 WebFetch 碰运气 |

### 3.2 三个根因

**根因 1:dispatch-server 只透出 1/4 治理文档**
- `_handle_all` 只拼了 CONTEXT.md + fleet-status + roadmap(v1.1) + history
- 漏了北极星 v1.2 / 架构真值 v1.0 / 编队分工 v1.1
- 没有 `/dispatch/north-star`、`/dispatch/architecture` 端点

**根因 2:云端 agent 调度时无任何上下文注入**
- `qoder-bridge.py` 的 `send_message` 直接发裸 prompt
- Kimi/Mira 同理(Mira 的 EXPAND_SYSTEM 纯生图)
- 只有 agent 主动 WebFetch `/dispatch/all` 才能拿到——靠自觉

**根因 3:本地 dispatch mirror 残缺**
- 本地 `dispatch/` 目录只有 CONTEXT/fleet-status/history
- ECS 上有 roadmap 但没北极星/架构/分工

### 3.3 修复方向(最小改动,优先级)

**P0:dispatch-server 补全治理文档端点**(改 1 文件,影响所有云端 agent)
- 新增 `/dispatch/north-star`、`/dispatch/architecture`、`/dispatch/fleet-division`
- `_handle_all` 追加这三段(section)

**P1:qoder-bridge 在 prompt 前注入"启动头"**(改 run_task 一处)
- 包装 prompt:"开工前先 WebFetch /dispatch/all 拿全局上下文"
- Kimi/Mira 桥接同理

**P2:本地 dispatch mirror 补齐**
- 把 ECS 治理文档拉到本地 dispatch 目录
- 或在 AGENTS.md 写明"dispatch 不含治理文档,治理文档读 standards/"

## 四、路线缺口核查(用户问"路线还有缺失吗")

### 4.1 O1 已完成项(13 项)
协作底座(CC→ZCode/Pi ECS/飞书桥/Qoder SSE/漂移治理设计/调度上下文)、Mira 主干接入、Kimi 本机调度、CC 密钥清除、Trae 收口、Phase A/B 安全同步、节点 2 三方评审通过、Phase C 合并 master。

### 4.2 O1 未完成项(P0 阻断真退出)

| # | 项 | 状态 |
|---|---|---|
| 1 | Phase C 合并 master | ✅ 本次完成(b2eb24e) |
| 2 | **Phase D:Y 落地**(废弃 ~/.agent-collaboration + 路径引用切换) | 未启动 |
| 3 | **5 域一致性真闭环**(ECS/Git/云端/本地/知识库 单一真值) | 仅 git 完成 |

### 4.3 节点 2 评审新暴露的 3 项(真空白,无任何章节承载)

| 缺口 | 严重度 | 说明 |
|---|---|---|
| **scripts/ 工具脚本长期维护归属** | 中 | 5 个 .py(gate-checks/mirror-sync/rebuild-exceptions/redact-tokens/gen-scan-patterns)无 spec 定义归属 |
| **manual-history-overrides 可持续性** | 中 | 53 条人工 override + 双解析函数会漂移(C round5 实证) |
| **dispatch-server 架构 spec 缺失** | **高** | 生产组件无架构文档、无职能归属、无 fleet-division 归属 |

### 4.4 架构层 3 项潜在缺口

- Kimi/Mira 无统一调度桥(只有 Qoder 有 qoder-bridge)
- 无 agent 级健康检查/心跳
- 无组件级故障降级策略

### 4.5 建议的下一步(P0/P1/P2)

**P0(本周,解锁 O1 收口)**:
1. ✅ Phase C 合并 master(已完成)
2. 启动 Phase D(Y 落地)
3. 更新 roadmap §当前位置 + O1 KR 增补"全域真值一致性"

**P1(O1 收口并行)**:
4. 远程分支清理第 1 批(29 条已合未删)
5. unified vs workspace-collaboration 去留裁定(节点 3 用户裁决)
6. ECS 基础设施治理(swap/时钟/孤儿进程)
7. **dispatch-server 架构 spec + 补全端点**(解决传播缺失 P0+P1)

**P2(O1 收尾 / 进 O2 前补齐)**:
8. scripts/ 工具脚本治理 spec
9. manual-overrides 共享解析函数改造
10. agent 级健康检查设计
11. 组件级降级策略
12. 知识库盘点收尾 + 本机 clone 清理

## 五、元反思

### 5.1 5 轮评审的成本与价值

5 轮迭代、6 个修复 commit、3 方独立 clone 复核——成本极高。但价值也高:
- 从 round1 的 tautology fail-open 到 round5 的四层防御链
- 每轮都发现真问题(不是吹毛求疵)
- 最终的 overrides 机制是"战略不可委托"原则的工程落地

**改进**:同类治理(退役词引用)未来应一次性设计到最严 + 人工 overrides,避免 5 轮迭代。

### 5.2 用户问"为什么其他智能体不知道"的深层启示

节点 2 评审聚焦 git 真值一致性,但**评审过程本身没有进入 dispatch 上下文**——A/B/C 每次都要 clone + 读评审包才知道在审什么。这跟用户问的"其他智能体不知道全局能力"是同一类问题:**治理真值在 git 仓库,但运行时真值(dispatch)不完整**。

Phase D 不仅要废弃 ~/.agent-collaboration,还要**让 dispatch 真正成为运行时单一真值**(北极星+架构+分工+路线图全透出)。否则下次评审/调度,其他智能体还是不知道全局。

## 六、当前状态

本文件作为节点 2 评审收尾的活文档。
下一步:Phase D + dispatch-server spec + 路线图 v1.2 更新(把节点 2 暴露的 3 项纳入)。
