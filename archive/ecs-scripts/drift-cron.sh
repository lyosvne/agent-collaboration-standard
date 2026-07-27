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

# ① 体检（fail-open 修复 2026-07-27: drift-check 失败发系统异常卡片, 不再静默 abort）
# PATCH-C-LAYER-FAILOPEN-FIX-20260727-APPLIED
set +e
bash "$DRIFT_CHECK" > "$REPORT_FILE" 2>/dev/null
DRIFT_CHECK_RC=$?
set -e

if [ "$DRIFT_CHECK_RC" -ne 0 ]; then
  # drift-check 失败: 不 cp（保留旧 drift-latest.json）, 发系统异常卡片
  echo "[$TIMESTAMP] drift-check 失败(exit=$DRIFT_CHECK_RC), 发系统异常卡片"
  lark-cli im +messages-send --as bot --chat-id "$CHAT_ID" \
      --markdown "🚨 **Pi 漂移体检失败** (exit=$DRIFT_CHECK_RC)

drift-check.sh 异常退出, 可能原因:
- drift-config.json 不存在/语法坏/Aetheris 条目缺失
- drift-mirrors/aetheris 目录被删
- python3 / git 不可用

排查: ssh root@aetherisonline.xyz 'bash /opt/pi-orchestrator/extensions/drift-check.sh'
保留: 旧 drift-latest.json 未被覆盖, /dispatch/drift 端点仍返回上次成功报告" 2>/dev/null >> /dev/null || true
  # 清理失败的报告文件（部分输出无价值）
  rm -f "$REPORT_FILE" 2>/dev/null || true
  exit 1
fi

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
