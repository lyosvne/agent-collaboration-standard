# Pi 治理纳入 B 层 round3 评审结果（三方全 PASS）

> 评审日期: 2026-07-27
> 评审对象: commit c17fdcc（/dispatch/drift 加 AUTH_KEY）
> 评审方: A（opus4.8p）/ B（gpt5.6sol）/ C（cantus）

## 结论：A PASS + B PASS + C PASS

B 层 round1→round3 完整闭环：
- round1: A/B/C 全 CONDITIONAL，共识 4 阻断
- round2: 修 3 阻断（commit_sha/content_sha12/mtime + drift fail-closed + ECS 脚本实证），A 剩 1 阻断（drift 公网 auth）
- round3: 修最后阻断（drift AUTH_KEY），A/B/C 全 PASS

## 三方评审要点

### A（PASS）

- **阻断闭环**：round2 的"Caddy 公网暴露"阻断由端点级 AUTH_KEY 闭环。round1 阻断 6 本来就接受 AUTH_KEY 作为闭环路径之一
- **auth 模式**：query param `?key=` / `!=` / `if AUTH_KEY:` 三项软观察全部"与 POST 一致"，不应在 drift 单独提高门槛。记 backlog 统一加固
- **/truth/versions 公开**：所有字段（commit_sha/content_sha12/mtime）都来自公开 GitHub 仓库，零字段私有信息公开化。OK
- **纪律亮点**：§8.4 首个正面案例，patch 哨兵 + import 前置验证是真学习

### B（PASS）

- **auth 一致性**：复用 `_handle_append_history` 模式完全对齐（同 AUTH_KEY / 同 query param / 同 403 / 同报错）
- **过程纪律**：round1 B2 诉求"防复发证据"实际落地
- **客户端影响**：blast radius 清晰，唯一受影响 ZCode curl
- 软观察：建议后续补"端点 auth 矩阵"小表（非阻断）

### C（PASS）

- **实现细节 vs 真阻断**：query param 日志面 / 空 fallback / timing 全为实现细节级软观察，非真阻断
- **patch import 前置检查**：强烈认可，是 round2 Path import NameError 教训的内化
- **客户端契约**：docstring + 材料包 §五 双层清晰

## 三方软观察 backlog（不阻断，统一加固）

1. dispatch-server 所有 auth 端点（POST history + GET drift）从 `?key=` query param 迁到 `Authorization: Bearer` header（消除 Caddy access log key 泄露）
2. `!=` → `hmac.compare_digest`（消除 timing attack）
3. `if AUTH_KEY:` fail-open → fail-closed（启动期强制校验）
4. 端点 auth 矩阵文档化（避免未来加端点策略迷航）

## 纪律闭环

- round1 过程违规 → review-process-lessons §八落账 + §8.4 强制触发清单
- round3 首次按 §8.4 走完整 pre-commit 流程：Plan Mode → 用户审 → 应用 → 验证 → 评审
- push 发生在评审 PASS 后（c17fdcc 本地等评审）
