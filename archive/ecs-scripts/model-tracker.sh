#!/bin/bash
# model-tracker.sh — 模型版本追踪
# cron 每天跑一次，对比三档目标 model id 是否变化，发现变化发飞书通知
#
# 追踪的三档：
#   general  → qmodel_preview (Qwen3.8-Max-Preview)
#   frontend → kmodel_latest  (Kimi-K3)
#   cantus   → cmodel         (Cantus)
#
# 发现以下情况时发飞书通知：
#   1. 模型 id 从可用列表中消失（下线）
#   2. 有同系列新版本出现（Qwen/Kimi/Cantus 升级）

set -euo pipefail

source /opt/pi-orchestrator/.env

API="https://api.qoder.com/api/v1/cloud"
TRACK_FILE="/opt/pi/dispatch/model-tracking.json"
CHAT_ID="${DRIFT_FEISHU_CHAT_ID:-[REDACTED-FEISHU-CHAT-ID]}"

# 上次已知的三档配置
LAST_GENERAL="${LAST_GENERAL:-qmodel_preview}"
LAST_FRONTEND="${LAST_FRONTEND:-kmodel_latest}"
LAST_CANTUS="${LAST_CANTUS:-cmodel}"

# 拉最新模型列表
MODELS=$(curl -s -m 15 "$API/models" -H "Authorization: Bearer $QODER_PAT")
ALL_IDS=$(echo "$MODELS" | python3 -c "
import sys, json
d = json.load(sys.stdin)
ids = [m['id'] for m in d.get('data', [])]
print(' '.join(ids))
")

CHANGES=""

# 检查每档是否还在
for TIER_INFO in "general:$LAST_GENERAL:Qwen3.8-Max" "frontend:$LAST_FRONTEND:Kimi-K3" "cantus:$LAST_CANTUS:Cantus"; do
    TIER=$(echo "$TIER_INFO" | cut -d: -f1)
    MODEL_ID=$(echo "$TIER_INFO" | cut -d: -f2)
    LABEL=$(echo "$TIER_INFO" | cut -d: -f3)

    if echo "$ALL_IDS" | grep -qw "$MODEL_ID"; then
        : # 还在，正常
    else
        CHANGES="${CHANGES}\n🔴 **${LABEL}** (${MODEL_ID}) 已从可用模型列表中消失！"
        # 找同系列替代
        SERIES=$(echo "$MODEL_ID" | cut -d_ -f1)
        REPLACEMENT=$(echo "$ALL_IDS" | tr ' ' '\n' | grep "^${SERIES}" | head -1)
        if [ -n "$REPLACEMENT" ]; then
            CHANGES="${CHANGES}\n   可能的替代: ${REPLACEMENT}"
        fi
    fi
done

# 检查同系列是否有新版本（qmodel/kmodel/cmodel 前缀）
for PREFIX in "qmodel:Qwen系列" "kmodel:Kimi系列" "cmodel:Cantus系列"; do
    P=$(echo "$PREFIX" | cut -d: -f1)
    LBL=$(echo "$PREFIX" | cut -d: -f2)
    COUNT=$(echo "$ALL_IDS" | tr ' ' '\n' | grep -c "^${P}" || true)
    if [ "$COUNT" -gt 1 ]; then
        NEW_ONES=$(echo "$ALL_IDS" | tr ' ' '\n' | grep "^${P}")
        CHANGES="${CHANGES}\n🆕 ${LBL} 有多个版本可用: ${NEW_ONES}"
    fi
done

# 保存追踪状态
python3 -c "
import json, time
data = {
    'checked_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
    'tiers': {
        'general': '$LAST_GENERAL',
        'frontend': '$LAST_FRONTEND',
        'cantus': '$LAST_CANTUS'
    },
    'all_model_ids': '$ALL_IDS'.split(),
    'changes': '''${CHANGES}'''.strip()
}
with open('$TRACK_FILE', 'w') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
"

# 有变化时发飞书通知
if [ -n "$CHANGES" ]; then
    MSG="🔔 **模型版本追踪报告**\n\n检测到以下变化：\n${CHANGES}\n\n请确认是否需要更新 agent 配置。"
    lark-cli im +messages-send --as bot --chat-id "$CHAT_ID" --markdown "$MSG" 2>/dev/null || true
    echo -e "检测到变化:\n$CHANGES"
else
    echo "[$(date -u +%Y%m%dT%H%M%SZ)] 三档模型均正常，无变化"
fi
