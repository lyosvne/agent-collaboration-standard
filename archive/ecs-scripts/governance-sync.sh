#!/bin/bash
# governance-sync.sh — 定期从git仓库pull governance/到ECS镜像
# 失败时发飞书告警（漂移治理cron是先例）

set -euo pipefail

REPO="/opt/pi/governance-mirror/repo"
CHAT_ID="${DRIFT_FEISHU_CHAT_ID:-[REDACTED-FEISHU-CHAT-ID]}"
LOG="/opt/pi-orchestrator/logs/governance-sync.log"
TS=$(date -u +%Y%m%dT%H%M%SZ)

cd "$REPO"

# 记录pull前HEAD
BEFORE=$(git rev-parse HEAD 2>/dev/null || echo "unknown")

# pull
if git pull origin master --quiet 2>&1; then
    AFTER=$(git rev-parse HEAD)
    if [ "$BEFORE" != "$AFTER" ]; then
        echo "[$TS] 更新: $BEFORE → $AFTER" >> "$LOG"
    else
        echo "[$TS] 无更新" >> "$LOG"
    fi
else
    # pull失败，发飞书告警
    echo "[$TS] PULL失败" >> "$LOG"
    lark-cli im +messages-send --as bot --chat-id "$CHAT_ID" \
        --markdown "⚠️ **governance真值源同步失败**

ECS无法从GitHub pull agent-collaboration-standard。
ECS上的目标文档可能过时。

请检查：①GitHub网络 ②git仓库状态 ③ECS网络" 2>/dev/null || true
    exit 1
fi
