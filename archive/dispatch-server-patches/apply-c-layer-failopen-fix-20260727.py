"""Pi 漂移治理 fail-open 修复 patch（2026-07-27）

修复 2 个 fail-open 路径（三方评审软观察 backlog）:
1. drift-cron.sh: drift-check 失败时静默 abort 无告警 → 改为发飞书系统异常卡片
2. conflict-tracker.py: 分支消失误判 RESOLVED → 区分 DISAPPEARED vs RESOLVED（整体重写）

前置: drift-check.sh round1 修复已应用（哨兵 PATCH-C-LAYER-DRIFT-CHECK-20260727-APPLIED）
幂等: PATCH-C-LAYER-FAILOPEN-FIX-20260727-APPLIED
"""
import sys
import shutil
import time
import subprocess
from pathlib import Path

DRIFT_CRON = Path("/opt/pi-orchestrator/extensions/drift-cron.sh")
CONFLICT_TRACKER = Path("/opt/pi-orchestrator/extensions/conflict-tracker.py")
DRIFT_CHECK_PATH = Path("/opt/pi-orchestrator/extensions/drift-check.sh")

SENTINEL_PRECONDITION = "# PATCH-C-LAYER-DRIFT-CHECK-20260727-APPLIED"
SENTINEL_THIS = "# PATCH-C-LAYER-FAILOPEN-FIX-20260727-APPLIED"


def patch_drift_cron():
    """drift-cron.sh: drift-check 失败时发系统异常卡片（不再静默 abort）"""
    if not DRIFT_CRON.exists():
        print(f"❌ drift-cron.sh 不存在", file=sys.stderr)
        return 1
    src = DRIFT_CRON.read_text(encoding="utf-8")

    if SENTINEL_THIS in src:
        print(f"⚠️  drift-cron.sh 已应用本 patch，跳过", file=sys.stderr)
        return 0

    ts = time.strftime("%Y%m%d-%H%M%S")
    bak = DRIFT_CRON.with_suffix(DRIFT_CRON.suffix + f".bak-failopen-{ts}")
    shutil.copy2(DRIFT_CRON, bak)
    print(f"✅ drift-cron.sh 备份: {bak}")

    old_block = """# ① 体检
bash "$DRIFT_CHECK" > "$REPORT_FILE" 2>/dev/null
cp "$REPORT_FILE" /opt/pi-orchestrator/logs/drift-latest.json
python3 /opt/pi-orchestrator/extensions/conflict-tracker.py 2>/dev/null >> /opt/pi-orchestrator/logs/conflict-track.log || true"""

    new_block = f"""# ① 体检（fail-open 修复 2026-07-27: drift-check 失败发系统异常卡片, 不再静默 abort）
{SENTINEL_THIS}
set +e
bash "$DRIFT_CHECK" > "$REPORT_FILE" 2>/dev/null
DRIFT_CHECK_RC=$?
set -e

if [ "$DRIFT_CHECK_RC" -ne 0 ]; then
  # drift-check 失败: 不 cp（保留旧 drift-latest.json）, 发系统异常卡片
  echo "[$TIMESTAMP] drift-check 失败(exit=$DRIFT_CHECK_RC), 发系统异常卡片"
  lark-cli im +messages-send --as bot --chat-id "$CHAT_ID" \\
      --markdown "🚨 **Pi 漂移体检失败** (exit=$DRIFT_CHECK_RC)

drift-check.sh 异常退出, 可能原因:
- drift-config.json 不存在/语法坏/Aetheris 条目缺失
- drift-mirrors/aetheris 目录被删
- python3 / git 不可用

排查: ssh root@aetherisonline.xyz 'bash /opt/pi-orchestrator/extensions/drift-check.sh'
保留: 旧 drift-latest.json 未被覆盖, /dispatch/drift 端点仍返回上次成功报告" 2>/dev/null >> /dev/null || true
  rm -f "$REPORT_FILE" 2>/dev/null || true
  exit 1
fi

cp "$REPORT_FILE" /opt/pi-orchestrator/logs/drift-latest.json
python3 /opt/pi-orchestrator/extensions/conflict-tracker.py 2>/dev/null >> /opt/pi-orchestrator/logs/conflict-track.log || true"""

    if old_block not in src:
        print(f"❌ drift-cron.sh 锚点未找到, 中止", file=sys.stderr)
        return 1
    src = src.replace(old_block, new_block, 1)

    tmp = DRIFT_CRON.with_suffix(".tmp")
    tmp.write_text(src, encoding="utf-8")
    result = subprocess.run(["bash", "-n", str(tmp)], capture_output=True, text=True)
    if result.returncode != 0:
        tmp.unlink()
        print(f"❌ drift-cron.sh bash 语法检查失败: {result.stderr}, 未应用", file=sys.stderr)
        return 1
    tmp.unlink()

    DRIFT_CRON.write_text(src, encoding="utf-8")
    DRIFT_CRON.chmod(0o755)
    print(f"✅ drift-cron.sh 已写入 + bash -n PASS")
    return 0


def patch_conflict_tracker():
    """conflict-tracker.py: 区分 RESOLVED vs DISAPPEARED（整体重写, 避免锚点脆弱）"""
    if not CONFLICT_TRACKER.exists():
        print(f"❌ conflict-tracker.py 不存在", file=sys.stderr)
        return 1
    src = CONFLICT_TRACKER.read_text(encoding="utf-8")

    if SENTINEL_THIS in src:
        print(f"⚠️  conflict-tracker.py 已应用本 patch，跳过", file=sys.stderr)
        return 0

    ts = time.strftime("%Y%m%d-%H%M%S")
    bak = CONFLICT_TRACKER.with_suffix(CONFLICT_TRACKER.suffix + f".bak-failopen-{ts}")
    shutil.copy2(CONFLICT_TRACKER, bak)
    print(f"✅ conflict-tracker.py 备份: {bak}")

    # 保留原 CHAT_ID（从原文件读, 不硬编码真实值）
    chat_id_line = None
    for line in src.split('\n'):
        if 'CHAT_ID = os.environ.get' in line:
            chat_id_line = line.strip()
            break
    if chat_id_line is None:
        print(f"❌ 找不到 CHAT_ID 定义, 中止", file=sys.stderr)
        return 1

    new_src = '''#!/usr/bin/env python3
# ''' + SENTINEL_THIS + '''
"""
Pi 冲突追踪+升级机制（fail-open 修复 2026-07-27: 区分 RESOLVED vs DISAPPEARED）
- 记录每个分支代码冲突的首次发现时间 + 持续次数
- 每次体检后更新追踪状态
- 持续未解决自动升级(NOTICE→WARN→CRITICAL)
- 升级时发飞书告警给用户
- 分支消失/配置漂移标 DISAPPEARED, 不误判 RESOLVED
"""
import json, os, time, subprocess

TRACK_FILE = "/opt/pi-orchestrator/logs/conflict-track.json"
''' + chat_id_line + '''

# 升级阈值(体检次数,每30分钟一次)
LEVELS = [
    (0, "NOTICE"),    # 首次发现
    (2, "WARN"),      # 1小时未解决(2次体检)
    (4, "CRITICAL"),  # 2小时未解决(4次体检)
    (8, "ESCALATE"),  # 4小时未解决 → 升级给用户
]

def load_track():
    if os.path.exists(TRACK_FILE):
        with open(TRACK_FILE) as f:
            return json.load(f)
    return {"branches": {}}

def save_track(track):
    with open(TRACK_FILE, "w") as f:
        json.dump(track, f, indent=2, ensure_ascii=False)

def send_feishu(markdown):
    subprocess.run([
        "lark-cli", "im", "+messages-send", "--as", "bot",
        "--chat-id", CHAT_ID, "--markdown", markdown
    ], capture_output=True)

def get_level(count):
    """根据持续次数返回当前级别"""
    level = "NOTICE"
    for threshold, lvl in LEVELS:
        if count >= threshold:
            level = lvl
    return level

def update_track(current_state):
    """
    current_state: dict {branch_name: {"conflicts": [...], "exists": bool}}
    exists=False 表示分支在 report 但标记为配置漂移（drift-check ref 不存在）
    返回: 需要发告警的升级事件列表（含 RESOLVED / DISAPPEARED 区分, 2026-07-27）
    """
    track = load_track()
    now = time.time()
    branches = track["branches"]
    escalations = []

    # 更新已追踪的分支（fail-open 修复: 区分 RESOLVED vs DISAPPEARED）
    for name in list(branches.keys()):
        state = current_state.get(name)
        # 分支本次不在 report 里（被 drift-config.json 移除）→ DISAPPEARED
        if state is None:
            branches[name]["resolved"] = True
            branches[name]["resolved_at"] = now
            escalations.append({
                "branch": name,
                "level": "DISAPPEARED",
                "hours": 0,
                "files": [],
                "first_seen": branches[name]["first_seen"]
            })
            continue
        # 分支在 report 但标记为配置漂移（exists=False）→ DISAPPEARED（不误判 RESOLVED）
        if not state.get("exists", True):
            branches[name]["resolved"] = True
            branches[name]["resolved_at"] = now
            escalations.append({
                "branch": name,
                "level": "DISAPPEARED",
                "hours": 0,
                "files": [],
                "first_seen": branches[name]["first_seen"]
            })
            continue
        # 分支存在且 conflicts 非空 → 原 count+1 逻辑
        if state["conflicts"]:
            branches[name]["count"] += 1
            branches[name]["last_seen"] = now
            old_level = branches[name]["level"]
            new_level = get_level(branches[name]["count"])
            branches[name]["level"] = new_level

            if new_level != old_level:
                hours = branches[name]["count"] * 0.5
                escalations.append({
                    "branch": name,
                    "level": new_level,
                    "hours": hours,
                    "files": state["conflicts"],
                    "first_seen": branches[name]["first_seen"]
                })
        else:
            # 分支存在且 conflicts=[] → 真解决了
            branches[name]["resolved"] = True
            branches[name]["resolved_at"] = now
            escalations.append({
                "branch": name,
                "level": "RESOLVED",
                "hours": 0,
                "files": [],
                "first_seen": branches[name]["first_seen"]
            })

    # 新发现的冲突（只看 exists=True 且 conflicts 非空）
    for name, state in current_state.items():
        if not state.get("exists", True):
            continue
        files = state["conflicts"]
        if not files:
            continue
        if name not in branches or branches[name].get("resolved"):
            branches[name] = {
                "first_seen": now,
                "last_seen": now,
                "count": 1,
                "level": "NOTICE",
                "files": files,
                "resolved": False
            }
            escalations.append({
                "branch": name,
                "level": "NOTICE",
                "hours": 0,
                "files": files,
                "first_seen": now
            })

    # 清理已解决超过1天的记录
    for name in list(branches.keys()):
        if branches[name].get("resolved") and now - branches[name].get("resolved_at", 0) > 86400:
            del branches[name]

    save_track(track)
    return escalations

def process_escalations(escalations):
    """处理升级事件,发飞书告警"""
    for esc in escalations:
        name = esc["branch"]
        level = esc["level"]
        files = esc["files"]

        if level == "DISAPPEARED":
            send_feishu(
                f"⚠️ **{name} 分支消失**\\n\\n"
                f"Pi 上次记录 agent/{name} 有冲突, 本次体检找不到该分支。\\n"
                f"可能: 分支被删/改名, 或 drift-config.json 配置漂移。\\n"
                f"未发'冲突已解决'卡片（避免误报）。"
            )
        elif level == "RESOLVED":
            send_feishu(
                f"✅ **{name} 冲突已解决!**\\n\\n"
                f"Pi 体检验证:agent/{name} 的代码冲突已被解决,分支已恢复正常。\\n"
                f"感谢对应 Agent 的及时处理。"
            )
        elif level == "NOTICE":
            # 首次发现,不单独发(体检卡片里已有)
            pass
        elif level == "WARN":
            send_feishu(
                f"🟠 **{name} 冲突持续 1 小时未解决**\\n\\n"
                f"冲突文件: {', '.join(files)}\\n"
                f"对应 Agent 请尽快处理:fetch origin master, merge 解决冲突后 push。\\n"
                f"Pi 将持续追踪。"
            )
        elif level == "CRITICAL":
            send_feishu(
                f"🔴 **{name} 冲突持续 2 小时未解决!**\\n\\n"
                f"冲突文件: {', '.join(files)}\\n"
                f"⚠️ 对应 Agent 尚未处理。如果 Agent 不可用,请用户决定:\\n"
                f"  • 手动处理冲突\\n"
                f"  • 或授权 Pi 用确定性策略合并(保留两边代码)\\n"
                f"  • 或暂时隔离该分支"
            )
        elif level == "ESCALATE":
            send_feishu(
                f"🚨 **{name} 冲突已持续 4 小时,升级给用户**\\n\\n"
                f"冲突文件: {', '.join(files)}\\n\\n"
                f"**需要你决策:**\\n"
                f"Pi 已多次通知对应 Agent,但冲突仍未解决。\\n"
                f"请决定下一步:\\n"
                f"  1. 你亲自处理\\n"
                f"  2. 授权 Pi 确定性合并(保留两边代码 + 构建验证)\\n"
                f"  3. 暂时隔离 agent/{name}(不参与集成)\\n"
                f"  4. 延长等待(Agent 可能稍后处理)"
            )

if __name__ == "__main__":
    # 从最新体检报告读取当前冲突
    report_path = "/opt/pi-orchestrator/logs/drift-latest.json"
    if not os.path.exists(report_path):
        print("无体检报告,跳过")
        exit(0)

    with open(report_path) as f:
        report = json.load(f)

    # 提取分支状态（fail-open 修复: 区分 RESOLVED vs DISAPPEARED）
    # exists=False 表示配置漂移（drift-check ref 不存在, level=CRITICAL + ahead=-1）
    current = {}
    for b in report.get("branches", []):
        code_conflicts = [c for c in b.get("conflicts", []) if "work-ledger" not in c]
        name = b["branch"].replace("agent/", "")
        is_drift_marker = (b.get("level") == "CRITICAL" and b.get("ahead", 0) == -1)
        current[name] = {
            "conflicts": code_conflicts,
            "exists": not is_drift_marker
        }

    escalations = update_track(current)
    if escalations:
        process_escalations(escalations)
        for esc in escalations:
            print(f"  {esc['branch']}: {esc['level']}")
    else:
        print("  无升级事件")
'''

    try:
        compile(new_src, str(CONFLICT_TRACKER), "exec")
    except SyntaxError as e:
        print(f"❌ conflict-tracker.py 语法检查失败: {e}, 未应用（备份保留 {bak}）", file=sys.stderr)
        return 1

    CONFLICT_TRACKER.write_text(new_src, encoding="utf-8")
    CONFLICT_TRACKER.chmod(0o755)
    print(f"✅ conflict-tracker.py 已写入（整体重写）+ py_compile PASS")
    return 0


def main():
    drift_check_src = DRIFT_CHECK_PATH.read_text(encoding="utf-8")
    if SENTINEL_PRECONDITION not in drift_check_src:
        print(f"❌ 前置 drift-check.sh round1 修复未应用（找不到 {SENTINEL_PRECONDITION!r}）", file=sys.stderr)
        return 1

    rc1 = patch_drift_cron()
    if rc1 != 0:
        return rc1
    rc2 = patch_conflict_tracker()
    if rc2 != 0:
        return rc2

    print(f"\n✅ fail-open 修复全部应用完成")
    print(f"   哨兵: {SENTINEL_THIS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
