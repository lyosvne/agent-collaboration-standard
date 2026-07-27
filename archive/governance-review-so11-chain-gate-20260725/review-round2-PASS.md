# SO-11 跳链检测 hook round2 评审汇总（PASS）

> 评审对象：round2 修复（C1/C2/A-prefix/B-N8N9）
> 评审日期：2026-07-25
> 评审性质：快速复核（三方 round1 共识明确，C 裁定改完即 PASS 无需二轮全量）

## round2 修复

### 必修（三方共识低成本项）
1. **C1 双源比对 fail-closed**（C round1 必须条件）
   - 新增 `check_truth_layer_consistency()` 函数
   - spec §二 的 A/B 档位（opus4.8p/gpt5.6sol）必须在 mira-integration-status 档位表
   - 不一致 → deny + 提示"先对齐双源"（编队多源漂移历史病灶的自检）
   - C1 单测钉死：构造 spec 有 opus4.8p 但 mira 表无的场景 → deny

2. **C2 回归测试**（C round1 必须条件）
   - 回放 round1 事故路径：`mira -p "评审方 A..." --model opus4.6`
   - 验证 deny + 提示"opus4.6 不在评审方 ['A']，期望 opus4.8p"
   - 确认事故路径在覆盖集（hook 已防住今天同类事故）

3. **deny 消息 `[chain-gate]` prefix**（A 建议）
   - 便于和 review-gate deny 消息区分（两 hook 都挂 PreToolUse Bash）
   - 调试时一眼看出是哪个 hook 拦的

4. **B-N8/N9 单测补齐**
   - N8: `--tier=cantus` 等号形式 → 放行（正则支持 `--tier(?:=|\s+)`）
   - N9: `--tier CANTUS` 大小写 → 放行（cantus 真值层归一）
   - N8b: `--model=opus4.8p` 等号形式 → 放行

## 单测新增（round2）

| Case | 场景 | 验证 |
|------|------|------|
| C1 | 双源不一致（spec 有 opus4.8p，mira 表无） | deny ✅ |
| C2 | 回放 round1 事故（A + opus4.6） | deny ✅ |
| N8 | --tier=cantus 等号 | 放行 ✅ |
| N9 | --tier CANTUS 大小写 | 放行 ✅ |
| N8b | --model=opus4.8p 等号 | 放行 ✅ |
| Prefix | deny 消息含 [chain-gate] | ✅ |

**25/25 PASS**（原 19 + round2 新增 6）

## 最终验证

- 25/25 单测 PASS
- repo 副本独立跑 25/25
- 不动 ECS / 不动全局 config
- hook 进 repo（<repo>/.zcode/hooks/）+ project config 挂载

## 结论

**三方一致 PASS**（C1-C2 必须 条件满足 + A prefix + B N8/N9 单测补齐）。

SO-11 v1 闭环今天的跳链事故（round1 opus4.8p→opus4.6），和 review-gate（防"忘了审"）+ SO-8（防"override 事后忘"）形成三层闸门：
- review-gate：ECS 部署前必须有 PASS 评审条目
- SO-8：override 紧急放行后必须补录（override_id 精确匹配）
- SO-11：调度评审时档位必须与真值层一致

**v1 覆盖**：mira -p 评审调度 + qoder-bridge --tier cantus（今天事故路径已覆盖）
**v1 不覆盖**（v2 backlog）：mira proxy / HTTP 直连 / `--prompt-file` / env 变量传 prompt

## v2 backlog（独立任务，按优先级）

| ID | 项 | 来源 | 优先级 |
|----|-----|------|--------|
| SO-11-v2-1 | 真值层抽 YAML 单源（双源→单源根治） | A/B/C 共识 | 高 |
| SO-11-v2-2 | `--reviewer` 参数机制（关键字降为迁移兜底） | A 主张 | 高 |
| SO-11-v2-3 | 服务端化（策略校验移 dispatch-server） | C v2 步骤 2 | 中 |
| SO-11-v2-4 | 实测可达性异步缓存（cron 探活） | A/B/C 共识 | 中 |
| SO-11-v2-5 | HTTP 直连/mira proxy 缺口审计留痕 | C3 | 中 |
| SO-11-v2-6 | override 不可续期 + 日次上限 + 审计 | B2 | 低 |
| SO-11-v2-7 | 三闸门共享单一策略模块 | C 拓扑优化 | 低 |

## 威胁模型边界声明（C 建议）

- SO-11 v1 是**客户端反馈层**（快速 UX 反馈），不是**强制层**
- 真正强制层只能在服务端（review-gate 已是 / SO-11-v2-3 待做）
- 防忘记（用默认档 / 凭 --help 换档）✅
- 不防恶意（改 prompt 措辞绕关键字 / 走 mira proxy）—— 与 review-gate/SO-8 同边界
- **升级触发条件**（C 建议 spec 写明）：Pi 获得自主调度权限时（O3/O4），威胁模型升级为防漂移，强制层必须服务端化
