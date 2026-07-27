# ECS 漂移治理脚本归档（2026-07-27）

> 来源: SSH 拉取 ECS `/opt/pi-orchestrator/extensions/` 5 个生产脚本
> 用途: Pi 治理纳入 B 层评审阻断 4 实证（C 层"shell cron 已覆盖 90%"依据）
> 脱敏: 飞书 chat_id `oc_4ee87700172d277a6479d234bb42b1b3` → `[REDACTED-FEISHU-CHAT-ID]`

## 脚本清单

| 脚本 | 大小 | 功能 | 触发 |
|---|---|---|---|
| `drift-cron.sh` | 2.3KB | 入口: 调 drift-check.sh + conflict-tracker.py + MD5 指纹防刷屏 + 飞书卡片 | root crontab `*/30 * * * *` |
| `drift-check.sh` | 3.1KB | fetch + 算 ahead/behind/dirty + 分级 OK/NOTICE/WARN/CRITICAL + 合并冲突 dry-run | drift-cron.sh 调 |
| `conflict-tracker.py` | 6.6KB | 持久化冲突状态 + 自动升级 NOTICE→WARN→CRITICAL→ESCALATE | drift-cron.sh 调 |
| `governance-sync.sh` | 1.0KB | git pull governance-mirror + 失败告警 | root crontab `0 * * * *` |
| `model-tracker.sh` | 3.2KB | Qoder Cloud 模型清单轮询 | root crontab `0 10 * * *` |

## ECS 实证（2026-07-27）

### root crontab
```
0 */6 * * * /root/.hermes/skills/lark_cli/token_refresh.sh
DRIFT_FEISHU_CHAT_ID=[REDACTED-FEISHU-CHAT-ID]
*/30 * * * * bash /opt/pi-orchestrator/extensions/drift-cron.sh >> /opt/pi-orchestrator/logs/drift-cron.log 2>&1
0 10 * * * bash /opt/pi-orchestrator/extensions/model-tracker.sh >> /opt/pi-orchestrator/logs/model-tracker.log 2>&1
0 * * * * bash /opt/pi-orchestrator/extensions/governance-sync.sh >> /opt/pi-orchestrator/logs/governance-sync.log 2>&1
```

### pi-dispatch-server.service（systemd unit）
```
[Unit]
Description=Pi Dispatch Context Server (fleet shared context HTTP endpoint)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/pi-orchestrator/extensions
EnvironmentFile=/opt/pi-orchestrator/.env
Environment=DISPATCH_DIR=/opt/pi/dispatch
Environment=DISPATCH_PORT=8765
ExecStart=/usr/bin/python3 /opt/pi-orchestrator/extensions/dispatch-server.py
Restart=always
RestartSec=5
StandardOutput=append:/opt/pi-orchestrator/logs/dispatch-server.log
StandardError=append:/opt/pi-orchestrator/logs/dispatch-server.log

[Install]
WantedBy=multi-user.target
```

### 网络绑定（安全闭环）
```
LISTEN 0  5  127.0.0.1:8765  0.0.0.0:*  users:(("python3",pid=1912402,fd=3))
```
**dispatch-server 仅 bind `127.0.0.1`（localhost），不暴露公网**。Caddy 反代 `/dispatch/*` 对外，公网访问受 Caddy 配置控制。这闭环了评审 B/C 的安全疑虑（评审包 §五.6）。

## spec §3 覆盖矩阵（实证漂移体检功能覆盖度）

| spec §3 要求 | shell cron 覆盖 | 实证脚本 |
|---|---|---|
| §3.1 fetch（不改工作区）| ✅ 100% | drift-check.sh |
| §3.1 ahead/behind/dirty 计数 | ✅ 100% | drift-check.sh |
| §3.1 branch_vs_master 对比 | ✅ 100% | drift-check.sh |
| §3.2 分级 OK/NOTICE/WARN/CRITICAL | ✅ 100% | drift-check.sh |
| §3.3 只读保证（绝不 pull/merge/checkout/reset）| ✅ 100% | drift-check.sh（仅 fetch + rev-list + status）|
| DriftReport 写真值层 | ⚠️ 部分 | drift-latest.json 落 logs/，未直接写 Aetheris（仅飞书卡片透出）|
| 飞书卡片 | ✅ 100% | drift-cron.sh 经 pi-feishu |

**结论**：spec §3 体检功能 ~95% 由 shell cron 覆盖（漂移检测/分级/告警全闭环，仅"写 Aetheris 真值层"未实现，但飞书卡片 + dispatch-server `/drift` 端点已暴露）。

## spec §5（源头预防）覆盖度

| spec §5 要求 | 覆盖状态 |
|---|---|
| §5.1 铁律: agent 只在 agent/<name> 分支工作 | ✅ workspace-collaboration-v2.1 §4 已固化 |
| §5.2 pre-commit hook | ❌ 各 clone 未安装（待 C 层或独立任务）|
| §5.3 集成窗口周报提案卡 | ❌ 未实现（待 C 层或 Pi 增强任务）|

**真空**：§5.2/§5.3 未实现，但这两项是"源头预防"增强，不阻断漂移治理核心闭环（§3 体检 + §4.1 通知已工作）。

## 与评审的对应

- 评审 A 阻断 3（C 层收窄依据非实证）→ 本归档闭环
- 评审 B1 §七（C 层 §5 真空）→ 本 README §"spec §5 覆盖度"显式承认真空
- 评审 C §七（90% 无实证）→ 本 README 改为分项覆盖矩阵（§3 ~95%，§5 部分）
