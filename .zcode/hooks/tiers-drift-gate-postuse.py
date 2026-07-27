#!/usr/bin/env python3
"""
Tiers Drift Gate -- PostToolUse Hook (SO-11-v2-1 round2)
==========================================================
强制 reviewer-tiers.yaml / spec §二 / mira-integration-status.md 三处一致。

B + C round1 共识硬阻断：手动 lint 靠自觉等于没约束（架构真值 §五"依赖 agent 主动同步
的设计本身有缺陷"）。本 hook 在 Write/Edit 改任一真值层文件后自动跑 lint，drift 则 deny。

机制：
  PostToolUse matcher=Write|Edit
  文件路径命中 reviewer-tiers.yaml / governance-review-process.md / mira-integration-status.md
  → 跑 scripts/check-reviewer-tiers-drift.py
  → exit 非 0 → deny（block）+ 提示 drift 详情
  → exit 0 → 放行

不覆盖 git pull / git checkout 等非 Write/Edit 路径（独立任务，C 建议 drift cron 兜底）。
"""

import json
import os
import re
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

_DEFAULT_REPO_FROM_SCRIPT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
_FALLBACK_REPO = r"C:\Users\Admin\Documents\trae_projects\agent-collaboration-standard"
_test_yaml = os.path.join(_DEFAULT_REPO_FROM_SCRIPT, "governance", "specs", "reviewer-tiers.yaml")
REPO_ROOT = os.environ.get("AGENT_COLLABORATION_REPO") or (
    _DEFAULT_REPO_FROM_SCRIPT if os.path.exists(_test_yaml) else _FALLBACK_REPO
)

LINT_SCRIPT = os.path.join(REPO_ROOT, "scripts", "check-reviewer-tiers-drift.py")

# 命中以下文件路径之一就触发 lint
TRIGGER_PATTERNS = [
    re.compile(r"reviewer-tiers\.yaml$", re.IGNORECASE),
    re.compile(r"governance-review-process\.md$", re.IGNORECASE),
    re.compile(r"mira-integration-status\.md$", re.IGNORECASE),
]


def should_trigger(file_path):
    if not file_path:
        return False
    # 归一化路径分隔符
    norm = file_path.replace("\\", "/")
    return any(p.search(norm) for p in TRIGGER_PATTERNS)


def run_lint():
    """跑 lint 脚本，返回 (ok, output)"""
    if not os.path.exists(LINT_SCRIPT):
        return False, f"lint 脚本不存在: {LINT_SCRIPT}"
    try:
        proc = subprocess.run(
            ["python", LINT_SCRIPT],
            capture_output=True,
            timeout=15,
            cwd=REPO_ROOT,
        )
        output = (proc.stdout.decode("utf-8", errors="replace") +
                  proc.stderr.decode("utf-8", errors="replace"))
        return proc.returncode == 0, output
    except subprocess.TimeoutExpired:
        return False, "lint 超时（15s）"
    except Exception as e:
        return False, f"lint 执行失败: {e}"


def main():
    try:
        raw = sys.stdin.buffer.read()
        hook_input = json.loads(raw.decode("utf-8", errors="replace"))
    except Exception:
        return  # 解析失败不阻断

    if hook_input.get("tool_name", "") not in ("Write", "Edit"):
        return

    tool_input = hook_input.get("tool_input", {})
    file_path = tool_input.get("file_path", "")
    if not should_trigger(file_path):
        return

    ok, output = run_lint()
    if ok:
        return  # 一致，放行

    # drift deny
    reason = (
        f"⚠️ **[tiers-drift-gate] 真值层漂移阻断（SO-11-v2-1 round2）**\n\n"
        f"检测到 `{os.path.basename(file_path)}` 改动后 reviewer-tiers.yaml / spec §二 / "
        f"mira-integration-status.md 三处不一致。\n\n"
        f"**lint 输出**:\n```\n{output[:1500]}\n```\n\n"
        f"**为何阻断**: B/C round1 共识——手动 lint 靠自觉等于没约束（架构真值 §五）。\n"
        f"**修复**: 对齐三处（YAML 是机器源，spec §二 + mira 跟随），跑 "
        f"`python scripts/check-reviewer-tiers-drift.py` 直到 exit 0，再重试本写操作。\n\n"
        f"**例外**: 紧急修复场景可临时跳过（写完后立即对齐三处 + commit 全部）"
    )
    print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))
    sys.exit(2)


if __name__ == "__main__":
    main()
