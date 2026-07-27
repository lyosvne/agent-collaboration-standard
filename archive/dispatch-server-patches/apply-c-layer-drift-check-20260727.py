"""Pi 治理纳入 C 层: drift-check.sh 去硬编码 + 退役分支修复（2026-07-27）

修复:
- 分支列表从 drift-config.json repos[Aetheris].agent_branches 读（去硬编码）
- 加 ref 存在性检查（防御配置含远端不存在的分支，如未来漂移）
- 加配置读失败 fail-closed（drift-config.json 不存在/语法坏 → exit 1）
- 移除退役分支 agent/claude agent/agent/trae（由 drift-config.json 驱动，不再硬编码）

前置: 无（独立脚本，幂等重写）
幂等: 哨兵 PATCH-C-LAYER-DRIFT-CHECK-20260727-APPLIED
"""
import sys
import shutil
import time
from pathlib import Path

TARGET = Path("/opt/pi-orchestrator/extensions/drift-check.sh")
SENTINEL_THIS = "# PATCH-C-LAYER-DRIFT-CHECK-20260727-APPLIED"

# 新版 drift-check.sh 全文（去硬编码 + ref 检查 + fail-closed + round1 评审修复）
# round1 评审修复（2026-07-27）:
#   - P0 MISSING→CRITICAL（A+B 共识阻断: drift-cron state hash 只过滤 CRITICAL/WARN, MISSING 静默漏报）
#   - P1 注入面（A 阻断: 合并两段 python 为一个进程, CONFIG 用 argv 传值, 消除 BRANCHES_STR 中转）
NEW_SCRIPT = '''#!/usr/bin/env bash
# drift-check.sh — Pi 漂移体检(含冲突检测)
# 分支列表来源: drift-config.json repos[Aetheris].agent_branches (去硬编码, 2026-07-27)
''' + SENTINEL_THIS + '''
set -euo pipefail
MIRROR="/opt/pi-orchestrator/drift-mirrors/aetheris"
CONFIG="/opt/pi/governance-mirror/repo/governance/configs/drift-config.json"

cd "$MIRROR"
git fetch origin 2>/dev/null

# fail-closed: 配置不存在 → exit 1
if [ ! -f "$CONFIG" ]; then
  echo "ERROR: drift-config.json 不存在: $CONFIG" >&2
  exit 1
fi

# 单 python 进程完成: 读 config → fetch 分支 → 算漂移 → 输出 JSON
# CONFIG 路径用 argv[1] 传值（不插值进 python 代码, 防注入面, round1 评审 P1 修复）
# heredoc 用 'PYEOF'（关闭 bash 变量展开, 消除注入面）
python3 - "$CONFIG" <<'PYEOF'
import json, sys, subprocess, os

config_path = sys.argv[1]

# 1. 读 drift-config.json 拿 Aetheris active 分支（fail-closed: 4 种失败模式 exit 1）
try:
    with open(config_path) as f:
        cfg = json.load(f)
except Exception as e:
    sys.stderr.write(f"ERROR: drift-config.json 读取失败: {e}\\n")
    sys.exit(1)

aetheris = next((r for r in cfg.get("repos", []) if r.get("name") == "Aetheris"), None)
if not aetheris:
    sys.stderr.write("ERROR: Aetheris not in drift-config.json repos\\n")
    sys.exit(1)
branches = aetheris.get("agent_branches", [])
if not branches:
    sys.stderr.write("ERROR: Aetheris agent_branches 为空\\n")
    sys.exit(1)

# 2. fetch 每个分支（|| true 容忍 ref 不存在, 不阻断）
for b in branches:
    subprocess.run(["git", "fetch", "origin", f"{b}:refs/remotes/origin/{b}"],
                   capture_output=True)

# 3. 算漂移
master = "refs/remotes/origin/master"
results = []

for b in branches:
    ref = f"refs/remotes/origin/{b}"

    # ref 存在性检查（防御配置含远端不存在的分支）
    verify = subprocess.run(["git", "rev-parse", "--verify", "--quiet", ref],
                            capture_output=True)
    if verify.returncode != 0:
        # round1 评审 P0 修复: level=CRITICAL（不是 MISSING）
        # 原因: drift-cron.sh state hash 只过滤 CRITICAL/WARN, 用 MISSING 会被静默吞掉, 配置漂移永远不告警
        results.append({
            "branch": b, "ahead": -1, "behind": -1, "head": "",
            "level": "CRITICAL",
            "status_desc": f"⚠️ 配置漂移: drift-config.json 列了 {b} 但远端不存在",
            "conflicts": []
        })
        continue

    ahead = int(subprocess.check_output(["git", "rev-list", "--count", f"{master}..{ref}"]).strip() or b"0")
    behind = int(subprocess.check_output(["git", "rev-list", "--count", f"{ref}..{master}"]).strip() or b"0")
    head = subprocess.check_output(["git", "rev-parse", "--short", ref]).strip().decode()

    if behind > 50: level = "CRITICAL"
    elif behind > 10: level = "WARN"
    elif behind > 3: level = "NOTICE"
    else: level = "OK"
    if ahead > 0 and level == "OK": level = "NOTICE"

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
        try:
            os.makedirs("/tmp/_drift_conflict_check", exist_ok=True)
            os.system("rm -rf /tmp/_drift_conflict_check/*")
            subprocess.run(["git", "worktree", "add", "--detach", "/tmp/_drift_conflict_check", ref],
                         capture_output=True)
            subprocess.run(["git", "-C", "/tmp/_drift_conflict_check", "fetch", "origin", "master"],
                         capture_output=True)
            merge = subprocess.run(["git", "-C", "/tmp/_drift_conflict_check", "merge", "FETCH_HEAD", "--no-edit"],
                                  capture_output=True, text=True)
            if "CONFLICT" in merge.stdout or "CONFLICT" in merge.stderr:
                diff = subprocess.check_output(["git", "-C", "/tmp/_drift_conflict_check", "diff", "--name-only", "--diff-filter=U"], text=True)
                conflicts = [f for f in diff.strip().split("\\n") if f]
            subprocess.run(["git", "worktree", "remove", "/tmp/_drift_conflict_check", "--force"], capture_output=True)
        except Exception:
            pass

    results.append({"branch": b, "ahead": ahead, "behind": behind, "head": head,
                    "level": level, "status_desc": status_desc, "conflicts": conflicts})

print(json.dumps({"timestamp": subprocess.check_output(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"]).strip().decode(),
                  "branches": results}, ensure_ascii=False, indent=2))
PYEOF
'''


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true",
                        help="强制覆盖已应用的 patch（用于 round1 评审修复重写）")
    args = parser.parse_args()

    if not TARGET.exists():
        print(f"❌ 目标文件不存在: {TARGET}", file=sys.stderr)
        return 1

    src = TARGET.read_text(encoding="utf-8")

    # 幂等检查
    if SENTINEL_THIS in src and not args.force:
        print(f"⚠️  本 patch 已应用（哨兵已存在），跳过。用 --force 强制覆盖（round1 修复）。", file=sys.stderr)
        return 0

    if SENTINEL_THIS in src and args.force:
        print(f"⚠️  --force 模式: 覆盖已应用版本（round1 评审修复）", file=sys.stderr)

    # 备份
    ts = time.strftime("%Y%m%d-%H%M%S")
    suffix = f".bak-c-layer-fix-{ts}" if args.force else f".bak-c-layer-{ts}"
    bak = TARGET.with_suffix(TARGET.suffix + suffix)
    shutil.copy2(TARGET, bak)
    print(f"✅ 备份: {bak}")

    # 写入新脚本（整体替换, 不做局部锚点替换, 因为改动较大）
    TARGET.write_text(NEW_SCRIPT, encoding="utf-8")
    # 保持可执行权限
    TARGET.chmod(0o755)

    # 语法检查（bash 语法）
    import subprocess
    result = subprocess.run(["bash", "-n", str(TARGET)], capture_output=True, text=True)
    if result.returncode != 0:
        # 回滚
        shutil.copy2(bak, TARGET)
        TARGET.chmod(0o755)
        print(f"❌ bash 语法检查失败: {result.stderr}, 已回滚, 备份保留: {bak}", file=sys.stderr)
        return 1

    print(f"✅ 已写入 {TARGET}")
    print(f"   备份: {bak}")
    print(f"   哨兵: {SENTINEL_THIS}")
    print(f"   bash -n 语法检查: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
