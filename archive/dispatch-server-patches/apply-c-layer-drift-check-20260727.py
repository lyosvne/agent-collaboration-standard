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

# 新版 drift-check.sh 全文（去硬编码 + ref 检查 + fail-closed）
NEW_SCRIPT = '''#!/usr/bin/env bash
# drift-check.sh — Pi 漂移体检(含冲突检测)
# 分支列表来源: drift-config.json repos[Aetheris].agent_branches (去硬编码, 2026-07-27)
''' + SENTINEL_THIS + '''
set -euo pipefail
MIRROR="/opt/pi-orchestrator/drift-mirrors/aetheris"
CONFIG="/opt/pi/governance-mirror/repo/governance/configs/drift-config.json"

cd "$MIRROR"
git fetch origin 2>/dev/null

# 从 drift-config.json 读 Aetheris active 分支列表
# fail-closed: 配置不存在/语法坏/Aetheris 条目缺失 → exit 1（drift-cron.sh 会记日志但不写 drift-latest.json）
if [ ! -f "$CONFIG" ]; then
  echo "ERROR: drift-config.json 不存在: $CONFIG" >&2
  exit 1
fi

BRANCHES_STR=$(python3 -c "
import json, sys
try:
    with open('$CONFIG') as f:
        cfg = json.load(f)
except Exception as e:
    sys.stderr.write(f'ERROR: drift-config.json 读取失败: {e}\\n')
    sys.exit(1)
aetheris = next((r for r in cfg.get('repos', []) if r.get('name') == 'Aetheris'), None)
if not aetheris:
    sys.stderr.write('ERROR: Aetheris not in drift-config.json repos\\n')
    sys.exit(1)
branches = aetheris.get('agent_branches', [])
if not branches:
    sys.stderr.write('ERROR: Aetheris agent_branches 为空\\n')
    sys.exit(1)
print(' '.join(branches))
") || exit 1

# bash fetch 循环（与原版一致, || true 容忍 ref 不存在）
for b in $BRANCHES_STR; do
  git fetch origin "$b:refs/remotes/origin/$b" 2>/dev/null || true
done

python3 <<PYEOF
import subprocess, json, os
branches = "$BRANCHES_STR".split()
master = "refs/remotes/origin/master"
results = []

for b in branches:
    ref = f"refs/remotes/origin/{b}"

    # ref 存在性检查（防御配置含远端不存在的分支）
    verify = subprocess.run(["git", "rev-parse", "--verify", "--quiet", ref],
                            capture_output=True)
    if verify.returncode != 0:
        results.append({
            "branch": b, "ahead": -1, "behind": -1, "head": "",
            "level": "MISSING",
            "status_desc": f"\\u26a0\\ufe0f \\u5206\\u652f {b} \\u5728\\u8fdc\\u7aef\\u4e0d\\u5b58\\u5728\\uff08\\u914d\\u7f6e\\u6f02\\u79fb\\uff1f\\uff09",
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

    # 冲突检测(只有双向分叉才检测)
    conflicts = []
    status_desc = ""
    if ahead == 0 and behind == 0:
        status_desc = "\\u2705 \\u5b8c\\u5168\\u540c\\u6b65"
    elif ahead == 0 and behind > 0:
        status_desc = f"\\U0001f7e2 \\u843d\\u540emaster {behind}\\u4e2acommit,\\u65e0\\u65b0\\u5de5\\u4f5c,Pi\\u53ef\\u5b89\\u5168\\u540c\\u6b65"
    elif ahead > 0 and behind == 0:
        status_desc = f"\\U0001f7e1 \\u6709{ahead}\\u4e2a\\u65b0\\u5de5\\u4f5c\\u672a\\u5408\\u5165master,\\u7b49\\u96c6\\u6210\\u7a97\\u53e3"
    elif ahead > 0 and behind > 0:
        status_desc = f"\\U0001f534 \\u53cc\\u5411\\u5206\\u53c9:{ahead}\\u4e2a\\u65b0\\u5de5\\u4f5c+\\u843d\\u540e{behind},\\u9700\\u5224\\u65ad"
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
    if not TARGET.exists():
        print(f"❌ 目标文件不存在: {TARGET}", file=sys.stderr)
        return 1

    src = TARGET.read_text(encoding="utf-8")

    # 幂等检查
    if SENTINEL_THIS in src:
        print(f"⚠️  本 patch 已应用（哨兵已存在），跳过。", file=sys.stderr)
        return 0

    # 备份
    ts = time.strftime("%Y%m%d-%H%M%S")
    bak = TARGET.with_suffix(TARGET.suffix + f".bak-c-layer-{ts}")
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
