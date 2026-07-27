#!/usr/bin/env python3
# # PATCH-C-LAYER-FAILOPEN-FIX-20260727-APPLIED
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
CHAT_ID = os.environ.get("DRIFT_FEISHU_CHAT_ID", "[REDACTED-FEISHU-CHAT-ID]")

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

    # 更新已追踪的分支（fail-open 修复: 区分 RESOLVED vs DISAPPEARED + round2 去重防刷屏）
    for name in list(branches.keys()):
        state = current_state.get(name)
        # 分支本次不在 report 里（被 drift-config.json 移除）→ DISAPPEARED
        if state is None:
            # round2 去重: 已通知过 DISAPPEARED 且仍 resolved → 不重发（防 30min 刷屏）
            if branches[name].get("disappeared_notified"):
                continue
            branches[name]["resolved"] = True
            branches[name]["resolved_at"] = now
            branches[name]["disappeared_notified"] = True
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
            # round2 去重: 已通知过 DISAPPEARED → 不重发
            if branches[name].get("disappeared_notified"):
                continue
            branches[name]["resolved"] = True
            branches[name]["resolved_at"] = now
            branches[name]["disappeared_notified"] = True
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
            # round2: 分支复活（之前 disappeared_notified=True, 现在 exists=True 有冲突）→ 重置通知标记
            # round3 修 B round2 C-1: 同时重置 resolved=False（DISAPPEARED 时遗留 True 会让 L127 当新分支双发）
            branches[name]["disappeared_notified"] = False
            branches[name]["resolved"] = False
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
            branches[name]["disappeared_notified"] = False  # round2: 重置, 允许未来再漂移时告警
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
                f"⚠️ **{name} 分支消失**\n\n"
                f"Pi 上次记录 agent/{name} 有冲突, 本次体检找不到该分支。\n"
                f"可能: 分支被删/改名, 或 drift-config.json 配置漂移。\n"
                f"未发'冲突已解决'卡片（避免误报）。"
            )
        elif level == "RESOLVED":
            send_feishu(
                f"✅ **{name} 冲突已解决!**\n\n"
                f"Pi 体检验证:agent/{name} 的代码冲突已被解决,分支已恢复正常。\n"
                f"感谢对应 Agent 的及时处理。"
            )
        elif level == "NOTICE":
            # 首次发现,不单独发(体检卡片里已有)
            pass
        elif level == "WARN":
            send_feishu(
                f"🟠 **{name} 冲突持续 1 小时未解决**\n\n"
                f"冲突文件: {', '.join(files)}\n"
                f"对应 Agent 请尽快处理:fetch origin master, merge 解决冲突后 push。\n"
                f"Pi 将持续追踪。"
            )
        elif level == "CRITICAL":
            send_feishu(
                f"🔴 **{name} 冲突持续 2 小时未解决!**\n\n"
                f"冲突文件: {', '.join(files)}\n"
                f"⚠️ 对应 Agent 尚未处理。如果 Agent 不可用,请用户决定:\n"
                f"  • 手动处理冲突\n"
                f"  • 或授权 Pi 用确定性策略合并(保留两边代码)\n"
                f"  • 或暂时隔离该分支"
            )
        elif level == "ESCALATE":
            send_feishu(
                f"🚨 **{name} 冲突已持续 4 小时,升级给用户**\n\n"
                f"冲突文件: {', '.join(files)}\n\n"
                f"**需要你决策:**\n"
                f"Pi 已多次通知对应 Agent,但冲突仍未解决。\n"
                f"请决定下一步:\n"
                f"  1. 你亲自处理\n"
                f"  2. 授权 Pi 确定性合并(保留两边代码 + 构建验证)\n"
                f"  3. 暂时隔离 agent/{name}(不参与集成)\n"
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
