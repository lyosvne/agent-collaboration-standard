# 评审材料包：SO-11 跳链检测 hook

> 评审对象：chain-gate-precommit.py + 单测 + config 挂载 + 文档
> 评审性质：§四.步骤0 强制触发（循环闭合：本机制自身变更属强制评审对象）
> 评审日期：2026-07-25
> 触发依据：meta-review-gate round1 opus4.8p→opus4.6 事故的直接解药

## 一、背景（事故复现）

2026-07-25 meta-review-gate round1：
- spec 真值层写 `A = opus4.8p`
- ZCode 调用 `mira -p "评审方 A..." --model opus4.6`（理由：mira --help 列表只有 opus4.6）
- 实测 opus4.8p 完全可调，mira --help 列表滞后
- round1 A 票作废，重走 round3

**根因**（lessons §8.6）：环境与真值层冲突时未验证就换档。spec §二.2.1 已约束但靠自觉。

**SO-11 解药**：PreToolUse hook 自动校验档位与真值层一致，不靠自觉。

## 二、方案

### 2.1 识别评审调度
- mira -p + 评审关键字（"评审方 A/B/C" / "review-package" / "评审材料" / 档位名）→ 评审调度
- qoder-bridge.py --tier cantus → C 评审调度
- 不拦：mira -p 无评审关键字 / qoder-bridge --tier general/frontend / 非 Bash

### 2.2 校验规则
**A/B（mira）**：
- 必须显式 `--model`（不写 = 用默认 = 跳链风险）→ 无则 deny
- 评审方识别**只用 "评审方 A/B" 关键字**（不用档位名，防循环识别——这是 D8/D10 测试发现的 bug 修复）
- --model 必须在 {真值层对应评审方档位}
- 也要在 mira-integration-status 档位表（防 spec §二 漏更新）

**C（qoder-bridge）**：
- --tier 必须 = cantus

### 2.3 真值层读取（hook 解析 spec markdown）
- governance-review-process.md §二表格 → {A: opus4.8p, B: gpt5.6sol, C: cantus}
- mira-integration-status.md 档位表 → 18 个可达档位
- 解析失败 fail-closed

### 2.4 override 机制
- ~/.zcode/hooks/.chain-gate-override.json（30 分钟窗口）
- 真值层过期/档位临时下架的紧急场景（需先问用户）

## 三、单测（19/19 PASS）

| Case | 场景 | 验证 |
|------|------|------|
| 真值层 §二 | spec 解析 | {A:opus4.8p, B:gpt5.6sol, C:cantus} ✅ |
| 真值层档位表 | mira 18 档 | 含 opus4.8p/gpt5.6sol ✅ |
| 识别 | mira 评审调度 | ✅ |
| 识别 | mira 非评审（生图） | 放行 ✅ |
| D1 | A + opus4.8p（一致） | 放行 ✅ |
| **D2【今天事故】** | **A + opus4.6（错档）** | **deny ✅** |
| D3 | A 无 --model | deny（必须显式） ✅ |
| D4 | 非评审 mira | 放行 ✅ |
| D5 | qoder cantus | 放行 ✅ |
| D7 | B + gpt5.6sol | 放行 ✅ |
| D8 | B + opus4.8p（错档） | deny ✅ |
| D9 | A + opus4.9p（假档） | deny ✅ |
| D10 | 评审材料无 A/B 标注 | fail-closed deny ✅ |
| D11 | 真 values层解析失败 | deny ✅ |
| D12 | override | 放行 ✅ |
| D13 | 非 Bash | 放行 ✅ |

## 四、要评审方回答的问题

### Q1：识别机制是否够？
- 评审关键字清单（"评审方 A/B/C" + "review-package" + 档位名）覆盖度够吗？
- agent 用新措辞（如"架构评审"不带"评审方 A"）会漏拦吗？
- 是否应改为白名单（必须显式标 `--reviewer A`）？

### Q2：评审方识别靠 prompt 关键字是否可靠？
- 当前：命令含"评审方 A"→ 识别为 A 评审
- 风险：agent 写"评审方 A 和 B 的汇总"→ 识别为 {A,B} 集合，--model 在 {opus4.8p, gpt5.6sol} 都放行
- D8/D10 测试发现：把档位名当评审方标识会循环识别（已修），现行方案是否还有类似陷阱？

### Q3：真值层双源（spec §二 + mira-integration-status）是否合理？
- spec §二 给评审方档位（A=opus4.8p）
- mira-integration-status 给可达档位全集（防 spec 漏更新）
- 风险：两份都改了才生效，单源更干净但损失一层校验

### Q4：威胁模型边界
- 防忘记（用默认档 / 凭 --help 换档）✅
- 不防恶意（改 prompt 措辞绕关键字）—— 与 review-gate 同边界
- mira proxy / 直接 HTTP 路径不覆盖（独立任务）
- 这个边界划对了吗？

### Q5：和 review-gate 的关系
- 两个 hook 并列挂 PreToolUse（review-gate 拦 ECS 部署，chain-gate 拦评审调度）
- 有无冲突或重复？
- 应该合并吗？

## 五、红线遵守

- 新增 hook 脚本（治理基础设施）→ §四.步骤0 强制触发（循环闭合）
- 改 .zcode/config.json（project 级，加 hook 挂载）→ 同上
- 不动 ECS / 不动 ~/.zcode/cli/config.json
- override 文件在 ~/.zcode/hooks/ 不进 repo

## 六、调度前校验（§二.2.1，本次执行）

1. 档位真值层一致：A=opus4.8p / B=gpt5.6sol / C=cantus ✅
2. 实测可达性：round3 已实测 22 档全可达（间隔短不复测）
3. 冲突上报：无
4. 材料内联：prompts 全部内联
