#!/usr/bin/env python3
"""
Pi 冲突追踪+升级机制
- 记录每个分支代码冲突的首次发现时间 + 持续次数
- 每次体检后更新追踪状态
- 持续未解决自动升级(NOTICE→WARN→CRITICAL)
- 升级时发飞书告警给用户
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

def update_track(current_conflicts):
    """
    current_conflicts: dict {branch_name: [conflict_files]}
    返回: 需要发告警的升级事件列表
    """
    track = load_track()
    now = time.time()
    branches = track["branches"]
    escalations = []

    # 更新已追踪的分支
    for name in list(branches.keys()):
        if name in current_conflicts:
            # 冲突还在,次数+1
            branches[name]["count"] += 1
            branches[name]["last_seen"] = now
            old_level = branches[name]["level"]
            new_level = get_level(branches[name]["count"])
            branches[name]["level"] = new_level
            
            # 级别升级了 → 告警
            if new_level != old_level:
                hours = branches[name]["count"] * 0.5  # 每次30分钟
                escalations.append({
                    "branch": name,
                    "level": new_level,
                    "hours": hours,
                    "files": current_conflicts[name],
                    "first_seen": branches[name]["first_seen"]
                })
        else:
            # 冲突解决了!
            branches[name]["resolved"] = True
            branches[name]["resolved_at"] = now
            escalations.append({
                "branch": name,
                "level": "RESOLVED",
                "hours": 0,
                "files": [],
                "first_seen": branches[name]["first_seen"]
            })
            # 保留记录但标记已解决(下次体检可以清理)

    # 新发现的冲突
    for name, files in current_conflicts.items():
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
        
        if level == "RESOLVED":
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
    
    # 提取有代码冲突的分支(排除已解决的 work-ledger)
    current = {}
    for b in report.get("branches", []):
        code_conflicts = [c for c in b.get("conflicts", []) if "work-ledger" not in c]
        if code_conflicts:
            name = b["branch"].replace("agent/", "")
            current[name] = code_conflicts
    
    escalations = update_track(current)
    if escalations:
        process_escalations(escalations)
        for esc in escalations:
            print(f"  {esc['branch']}: {esc['level']}")
    else:
        print("  无升级事件")
