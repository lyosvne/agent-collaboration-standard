#!/usr/bin/env bash
# drift-check.sh — Pi 漂移体检(含冲突检测)
set -euo pipefail
MIRROR="/opt/pi-orchestrator/drift-mirrors/aetheris"
cd "$MIRROR"
git fetch origin 2>/dev/null
for b in master agent/claude agent/kimi agent/qoder agent/trae agent/solo agent/zcode; do
  git fetch origin "$b:refs/remotes/origin/$b" 2>/dev/null || true
done

python3 <<'PYEOF'
import subprocess, json, os

branches = ["agent/claude", "agent/kimi", "agent/qoder", "agent/trae", "agent/solo", "agent/zcode"]
master = "refs/remotes/origin/master"
results = []

for b in branches:
    ref = f"refs/remotes/origin/{b}"
    ahead = int(subprocess.check_output(["git", "rev-list", "--count", f"{master}..{ref}"]).strip() or b"0")
    behind = int(subprocess.check_output(["git", "rev-list", "--count", f"{ref}..{master}"]).strip() or b"0")
    head = subprocess.check_output(["git", "rev-parse", "--short", ref]).strip().decode()

    if behind > 50: level = "CRITICAL"
    elif behind > 10: level = "WARN"
    elif behind > 3: level = "NOTICE"
    else: level = "OK"
    if ahead > 0 and level == "OK": level = "NOTICE"

    # 冲突检测(只有双向分叉才检测)
    conflicts = []
    status_desc = ""
    if ahead == 0 and behind == 0:
        status_desc = "✅ 完全同步"
    elif ahead == 0 and behind > 0:
        status_desc = f"🟢 落后master {behind}个commit,无新工作,Pi可安全同步"
    elif ahead > 0 and behind == 0:
        status_desc = f"🟡 有{ahead}个新工作未合入master,等集成窗口"
    elif ahead > 0 and behind > 0:
        status_desc = f"🔴 双向分叉:{ahead}个新工作+落后{behind},需判断"
        # 检测冲突(merge dry-run)
        try:
            os.makedirs("/tmp/_drift_conflict_check", exist_ok=True)
            os.system(f"rm -rf /tmp/_drift_conflict_check/*")
            subprocess.run(["git", "worktree", "add", "--detach", "/tmp/_drift_conflict_check", ref],
                         capture_output=True)
            subprocess.run(["git", "-C", "/tmp/_drift_conflict_check", "fetch", "origin", "master"],
                         capture_output=True)
            merge = subprocess.run(["git", "-C", "/tmp/_drift_conflict_check", "merge", "FETCH_HEAD", "--no-edit"],
                                  capture_output=True, text=True)
            if "CONFLICT" in merge.stdout or "CONFLICT" in merge.stderr:
                diff = subprocess.check_output(["git", "-C", "/tmp/_drift_conflict_check", "diff", "--name-only", "--diff-filter=U"], text=True)
                conflicts = [f for f in diff.strip().split("\n") if f]
            subprocess.run(["git", "worktree", "remove", "/tmp/_drift_conflict_check", "--force"], capture_output=True)
        except Exception:
            pass

    results.append({"branch": b, "ahead": ahead, "behind": behind, "head": head,
                    "level": level, "status_desc": status_desc, "conflicts": conflicts})

print(json.dumps({"timestamp": subprocess.check_output(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"]).strip().decode(),
                  "branches": results}, ensure_ascii=False, indent=2))
PYEOF
