---
version: 1.0
status: active
type: principle
created: 2026-07-28
owner: ZCode
title: 跨边界状态传递元原则（编队级通用纪律）
scope: 所有跨边界状态传递场景的通用纪律，从 SO-11-v2-2 + SO-12 实践中抽象
related:
  - specs/governance-infrastructure-status.md
  - specs/governance-review-process.md
  - specs/reviewer-tiers.yaml
  - ../unified-agent-collaboration-standard.md
source_reviews:
  - so11-v2-2-session-continuity（A round2 Q5 抽象）
  - so12-bootstrap-gate（C round2 Q4 编队化主张）
supersedes: []
---

# 跨边界状态传递元原则

> **编队级通用纪律**。从 SO-11-v2-2（评审调度）+ SO-12（session bootstrap）实践中抽象出的高阶原则，
> 未来跨机器 / 跨仓库 / 跨用户的场景可直接套用，不必每次重新发明。

## 一、为什么需要这个原则（根因）

编队反复付学费的漂移模式，根因都是同一个：**状态跨边界传递时，用"记忆/推断"代替"显式查询"，导致接收方凭模糊印象编造或改错地方**。

实例（2026-07-25 ~ 28 真实事故）：
- **跨 agent 边界**：调 C 评审时忘了 qoder-bridge 调用方式（治理文档已固化，但 ZCode 凭记忆编了 `ssh ecs`）
- **跨 session 边界**：compact 续接后忘了 mira endpoint（真实 `mira.byteintl.net`，凭记忆编了 `api.mira.chat`）
- **跨文件边界**：改 hook 改到 home 级而非 project 级（凭印象以为 home 是生效路径）

三类事故表面不同，**底层同构**：状态（调用方式 / endpoint / 生效路径）从"产生方"传到"消费方"时跨了边界，消费方用叙事层记忆代替事实层查询。

## 二、原则（一句话）

**任何跨边界的状态传递，必须显式化 + fail-closed，不靠记忆/推断/兜底。**

拆解：
- **显式化**：状态以真值文件 / 环境变量 / 标记文件形式显式传递，不依赖接收方"记得"
- **fail-closed**：状态缺失或不可校验时，接收方拒绝执行（deny / 报错），不静默放行
- **不靠兜底**：禁止"时间窗口兜底 / mtime 扫描 / 默认值回退"等隐式路径——这些会把 fail-closed 悄悄变成 fail-open

## 三、已落地的实例（原则的两次应用）

### 实例 1：评审调度（跨 agent 边界）—— SO-11-v2-2

**传递的状态**：当前评审项目 + 当前 round + 上一轮 session_id

**显式化**：
- 环境变量 `CURRENT_REVIEW_PROJECT` + `CURRENT_REVIEW_ROUND`（ZCode 调评审前 export）
- session_id 在 `review-sessions-index.yaml`（git 真值层）

**fail-closed**（session-gate hook）：
- 未 export 环境变量 → deny（M1/M2）
- session_continuity 配置缺失 → deny（M3）
- 有上一轮 session_id 但未用 `-r` → deny

**反例（被消除的兜底）**：
- 兜底扫 archive 最近改动目录猜项目 → 删除（M1，最坏失败是续接错误会话的静默污染）
- regex 扫命令文本猜 round → 降级为交叉校验 warn（M2，控制平面/数据平面分离）

### 实例 2：session bootstrap（跨 session 边界）—— SO-12

**传递的状态**：真值三件套（reviewer-tiers.yaml / spec §二 / config.json）的内容 + session 身份

**显式化**：
- SessionStart hook 注入真值三件套到 additionalContext
- bootstrap 标记文件存 session_id + truth_hashes（sha256）

**fail-closed**（bootstrap-gate hook）：
- 标记缺失 / session_id 不匹配 / truth hash 漂移 → deny
- 动手类操作（mira 评审 / ECS patch / 改真值层）前强制校验

**反例（被消除的兜底）**：
- 8h 时间窗口兜底 → 删除（M1，C 指出"fail-closed 被悄悄变成 fail-open"，恰是 compact 跳链复现路径）

## 四、原则的抽象层次（A round2 Q5 的洞察）

> "SO-11-v2-2 挖出来的不是一个评审调度的局部原则，而是一个跨层的**元原则**：任何跨 session 边界的状态传递，都必须显式化 + fail-closed。评审调度是'跨 agent 边界'，bootstrap 是'跨 session 边界'，同构。"

```
跨边界状态传递（元原则）
├── 跨 agent 边界
│   ├── 评审调度（SO-11-v2-2：CURRENT_REVIEW_PROJECT/ROUND + session_id）
│   ├── 编队交接（handoff pack，待套用）
│   └── Pi 调度（dispatch-server，待套用）
├── 跨 session 边界
│   ├── compact 续接 bootstrap（SO-12：SessionStart 注入 + bootstrap-gate）
│   └── 跨 session 评审记忆（SO-11-v2-2：-r 续接 + expired_rounds）
├── 跨文件边界
│   ├── hook 生效路径（project 级 vs home 级，待治理 §5.1）
│   └── 真值层多源（reviewer-tiers.yaml 单源，SO-11-v2-1 已治）
├── 跨机器边界（未来）
│   ├── 本机 ↔ ECS（git commit 硬同步 + drift-check 兜底）
│   └── 本机 ↔ 云端 agent（Qoder/Kimi，handoff pack）
└── 跨用户边界（未来）
    └── 林于炜 ↔ 编队（不可委托清单 + 用户裁决）
```

**应用方法**：遇到新的跨边界场景，先问"传递的状态是什么？怎么显式化？怎么 fail-closed？"，按实例 1/2 的模式设计，不必重新发明。

## 五、威胁模型边界

本原则**防诚实健忘**（接收方忘了查真值），不防**主动规避**：
- agent 可以手动伪造标记 / 改 prompt 措辞绕关键字识别 / 变量拼接绕命令匹配
- 这些是**设计边界，不是 bug**——防恶意需 server 端闸门（SO-3 演进方向：ECS 部署入口校验 PASS token）
- 边界必须显式声明（见各 hook 的 AGENTS.md 威胁模型段），避免后续误当安全边界用

## 六、与现有治理文档的关系

| 文档 | 角色 |
|---|---|
| 本文件 | 元原则（抽象层，跨场景通用） |
| `governance-infrastructure-status.md` | 实现现状（5 个 hook 怎么落地本原则） |
| `governance-review-process.md` §二 | 评审调度细则（实例 1 的人读规范） |
| `reviewer-tiers.yaml` | 档位真值（实例 1/2 都读的机器源） |
| `unified-agent-collaboration-standard.md` | 编队协作标准（本原则应被引用，待 SO-13 补指针） |

## 七、未来应用（待套用本原则的场景）

1. **编队交接（handoff pack）**：跨 agent 交接时，上下文状态应显式化（交接包文件）+ fail-closed（接收方未确认收到完整包不开始工作）
2. **Pi 调度（dispatch-server）**：Pi 给云端 agent 派活时，任务状态应显式化（HTTP 端点）+ fail-closed（agent 未确认任务参数不执行）
3. **hook 生效路径治理（§5.1 双源）**：home/project 双源应消除（显式化为单一 project 级）+ drift-gate 加 lint（fail-closed：两处不一致 deny）

## 八、维护约定

- 本文件是**原则层**，不频繁改（除非抽象层次有新洞察）
- 新的跨边界场景应用本原则时，在本文件 §七 补一条 + 在对应实现文档引用本文件
- 改本文件不触发 drift-gate（不在 TRIGGER_PATTERNS），但改 §三 实例（hook 行为）必须同步 governance-infrastructure-status.md
