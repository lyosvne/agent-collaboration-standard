# Round5 评审材料包 — Pi 独立部署方案（ECS 自闭环）

> 评审日期：2026-07-29
> 项目：pi-self-evolution-constitution round5
> 触发：governance-review-process §四步骤0 第2项（新建 ECS systemd 服务文件）

## 一、背景
宪法 v0.3 + 工具集方案 v0.3 已过四轮评审（宪法 round2 + 工具集 round4 三方 PASS）。L1 代码层 + 工具集 + 观测全部本机实施完成（build + 20/20 测试过，已 commit + push）。现在进 ECS 部署。

用户裁定：**Pi 自闭环独立运行，不碰旧系统**（旧系统是待替代范式，Pi 跑顺后替代）。

## 二、ECS 全景（调研事实）
| 组件 | 位置 | 端口 | 状态 | 与 Pi 关系 |
|---|---|---|---|---|
| aetheris-backend（旧范式） | /opt/aetheris-controlplane-backend | 18080 | active running | **不碰** |
| pi-orchestrator | /opt/pi-orchestrator | - | active running | **复用** qoder-bridge.py |
| openclaw | /opt/aetheris-runtime | 19089 | active running | **不碰** |
| hermes-sidecar | python venv | 8642 | active running | **已退役**，Pi 不依赖 |
| 前端 | /var/www/aetheris-frontend | caddy 80/443 | 托管 | **不碰** |

关键：aetheris backend 和 pi-orchestrator 零代码依赖。aetheris-backend 用 master（b212cca），我的代码在 refactor/backend-startup-lifecycle（落后 master 233 commit，但那是旧范式演进 Pi 不需要）。

## 三、部署方案
**架构**：`/opt/pi-self-growth/` 新建独立目录，git clone refactor 分支 + build，独立 DB（/opt/pi-self-growth/data/aetheris.db），端口 18090。

**凭证复用**（EnvironmentFile 指向现有文件，不复制值）：
- 飞书 ← /opt/.local/secure/feishu/feishu-app.env
- 模型网关 ← /opt/.local/secure/provider-control-plane/provider-keys.env

**独立隔离配置**（pi.env）：PORT=18090 + 独立 storage root + HERMES_RUNTIME_MODE=skip（sidecar 退役跳过）

**systemd unit**（⚠️触发评审）：pi-self-growth.service（ExecStart npx tsx src/index.ts，Restart=always）+ pi-kill-watcher.service（独立 timer 检查 .kill-flag）

## 四、用户裁定
- 飞书/模型网关：复用现有（同一凭证，EnvironmentFile 只读复用）
- hermes-sidecar：已退役，Pi 不依赖（HERMES_RUNTIME_MODE=skip）
- Pi 与旧系统：完全隔离（独立 DB/端口/进程）

## 五、给评审方的问题

### A（架构级）：
1. Pi 独立 backend 复用飞书凭证/模型网关，会和旧 aetheris-backend 冲突吗？（同一飞书应用两实例？同一网关并发？）
2. refactor 分支（落后 master 233 commit）部署会不会缺关键基础设施级依赖？
3. kill-watcher 独立 systemd service 检查 .kill-flag，守得住 M2（进程外强制）吗？

### B（逻辑/配置）：
1. PORT=18090 + 独立 storage root，和现有 aetheris-backend 完全隔离了吗？有无共享全局状态（lark-cli credentials/npm 缓存）？
2. HERMES_RUNTIME_MODE=skip 代码里有没有？没有的话 sidecar 调用是阻断还是降级？
3. EnvironmentFile 复用，两 backend 同时读同一 .env 会冲突吗？

### C（架构契合）：
1. Pi 部署 /opt/pi-self-growth 独立目录 + 复用 pi-orchestrator qoder-bridge.py，对齐预期吗？
2. 双系统并存到 Pi 成熟后替代，路径合理吗？
3. 有无更贴合现有 ECS 架构的部署方式？
