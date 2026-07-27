#!/usr/bin/env bash
# drift-cron.sh — Pi 漂移治理 cron(智能去重版)
# 核心改进:只在状态变化时才发卡片,不重复打扰
set -euo pipefail

REPORT_DIR="/opt/pi-orchestrator/logs/drift-reports"
DRIFT_CHECK="/opt/pi-orchestrator/extensions/drift-check.sh"
GEN_CARD="/opt/pi-orchestrator/extensions/gen-card.py"
TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)
REPORT_FILE="$REPORT_DIR/drift-$TIMESTAMP.json"
CHAT_ID="${DRIFT_FEISHU_CHAT_ID:-[REDACTED-FEISHU-CHAT-ID]}"
LAST_HASH_FILE="/opt/pi-orchestrator/logs/drift-last-state.hash"

mkdir -p "$REPORT_DIR"

# ① 体检
bash "$DRIFT_CHECK" > "$REPORT_FILE" 2>/dev/null
cp "$REPORT_FILE" /opt/pi-orchestrator/logs/drift-latest.json
python3 /opt/pi-orchestrator/extensions/conflict-tracker.py 2>/dev/null >> /opt/pi-orchestrator/logs/conflict-track.log || true

# ② 生成状态指纹(只看告警分支的 ahead/behind/冲突文件,不看时间戳)
CURRENT_HASH=$(python3 -c "
import json,hashlib
with open('$REPORT_FILE') as f:
    report = json.load(f)
alerts = [b for b in report.get('branches',[]) if b.get('level') in ('CRITICAL','WARN')]
# 指纹 = 哪些分支告警 + 每个的 ahead/behind/冲突文件
state = '|'.join(f\"{b['branch']}:{b['ahead']}:{b['behind']}:{','.join(sorted(b.get('conflicts',[])))}\" for b in sorted(alerts, key=lambda x: x['branch']))
print(hashlib.md5(state.encode()).hexdigest())
" 2>/dev/null)

# ③ 对比上一次的状态指纹
LAST_HASH=$(cat "$LAST_HASH_FILE" 2>/dev/null || echo "none")

if [ "$CURRENT_HASH" = "$LAST_HASH" ]; then
  # 状态没变化,不发卡片(不打扰)
  echo "[$TIMESTAMP] 状态未变化(hash=$CURRENT_HASH),不发卡片"
  find "$REPORT_DIR" -name "drift-*.json" -mtime +7 -delete 2>/dev/null || true
  exit 0
fi

# ④ 状态变化了(或首次运行),生成并发卡片
CARD_JSON=$(python3 "$GEN_CARD" "$REPORT_FILE" 2>/dev/null || echo "")

if [ -n "$CARD_JSON" ]; then
  lark-cli im +messages-send --as bot --chat-id "$CHAT_ID" \
      --msg-type interactive --content "$CARD_JSON" 2>/dev/null >> /dev/null || true
  echo "[$TIMESTAMP] 状态变化,卡片已发送"
else
  # 无告警(gen-card 返回空)
  echo "[$TIMESTAMP] 无告警,不发卡片"
fi

# ⑤ 更新状态指纹
echo "$CURRENT_HASH" > "$LAST_HASH_FILE"

# ⑥ 清理旧报告
find "$REPORT_DIR" -name "drift-*.json" -mtime +7 -delete 2>/dev/null || true
