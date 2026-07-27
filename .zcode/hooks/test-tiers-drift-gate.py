#!/usr/bin/env python3
"""
单测：tiers-drift-gate-postuse.py (SO-11-v2-1 round2)
"""

import json
import os
import subprocess
import sys
import tempfile

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tiers-drift-gate-postuse.py")
REPO_ROOT = r"C:\Users\Admin\Documents\trae_projects\agent-collaboration-standard"

PASS_COUNT = 0
FAIL_COUNT = 0


def run_hook(tool_name, tool_input):
    hook_input = {"tool_name": tool_name, "tool_input": tool_input}
    proc = subprocess.run(
        ["python", HOOK],
        input=json.dumps(hook_input).encode("utf-8"),
        capture_output=True,
        timeout=20,
    )
    return proc.returncode, proc.stdout.decode("utf-8", errors="replace")


def _record(ok, name, detail=""):
    global PASS_COUNT, FAIL_COUNT
    if ok:
        PASS_COUNT += 1
        print(f"✅ PASS | {name}")
    else:
        FAIL_COUNT += 1
        print(f"❌ FAIL | {name}")
    if detail:
        print(f"        {detail}")
    print()


def main():
    print("=" * 60)
    print("单测 tiers-drift-gate-postuse.py (v2-1 round2)")
    print("=" * 60)
    print()

    # T1: 改 reviewer-tiers.yaml（真实 repo 当前一致）→ 放行
    ec, out = run_hook("Write", {
        "file_path": os.path.join(REPO_ROOT, "governance/specs/reviewer-tiers.yaml"),
        "content": "# test",
    })
    _record(ec == 0, "T1: 改 reviewer-tiers.yaml（一致）→ 放行", f"exit={ec}")

    # T2: 改 governance-review-process.md（一致）→ 放行
    ec, out = run_hook("Write", {
        "file_path": os.path.join(REPO_ROOT, "governance/specs/governance-review-process.md"),
        "content": "# test",
    })
    _record(ec == 0, "T2: 改 governance-review-process.md（一致）→ 放行", f"exit={ec}")

    # T3: 改无关文件 → 放行（不触发 lint）
    ec, out = run_hook("Write", {
        "file_path": "/tmp/foo.txt",
        "content": "x",
    })
    _record(ec == 0, "T3: 改无关文件 → 放行（不触发）", f"exit={ec}")

    # T4: 改 reviewer-tiers.yaml + drift（构造临时 repo 故意制造漂移）
    tmp_repo = tempfile.mkdtemp(prefix="drift-test-")
    specs = os.path.join(tmp_repo, "governance", "specs")
    scripts = os.path.join(tmp_repo, "scripts")
    os.makedirs(specs, exist_ok=True)
    os.makedirs(scripts, exist_ok=True)
    # 复制 lint 脚本 + 真实 reviewer-tiers.yaml
    import shutil
    shutil.copy(os.path.join(REPO_ROOT, "scripts/check-reviewer-tiers-drift.py"), scripts)
    shutil.copy(os.path.join(REPO_ROOT, "governance/specs/reviewer-tiers.yaml"), specs)
    # 故意写不一致的 spec §二（档位与 YAML 不同）
    with open(os.path.join(specs, "governance-review-process.md"), "w", encoding="utf-8") as f:
        f.write("## 二、评审方组合\n\n"
                "| **评审方 A** | Mira opus5.0 | ... | ... |\n"  # YAML 是 opus4.8p
                "| **评审方 B** | Mira gpt5.6sol | ... | ... |\n"
                "| **评审方 C** | Qoder cantus | ... | ... |\n\n"
                "## 三、\n")
    env = os.environ.copy()
    env["AGENT_COLLABORATION_REPO"] = tmp_repo
    hook_input = {
        "tool_name": "Write",
        "tool_input": {
            "file_path": os.path.join(tmp_repo, "governance/specs/governance-review-process.md"),
            "content": "# changed",
        },
    }
    proc = subprocess.run(
        ["python", HOOK],
        input=json.dumps(hook_input).encode("utf-8"),
        capture_output=True,
        timeout=20,
        env=env,
    )
    _record(proc.returncode == 2 and "漂移阻断" in proc.stdout.decode("utf-8", "replace"),
            "T4: 改 spec §二（drift：opus5.0 vs YAML opus4.8p）→ deny",
            f"exit={proc.returncode}")
    try:
        shutil.rmtree(tmp_repo)
    except Exception:
        pass

    # T5: Edit 工具也触发
    ec, out = run_hook("Edit", {
        "file_path": os.path.join(REPO_ROOT, "governance/specs/reviewer-tiers.yaml"),
        "old_string": "x", "new_string": "y",
    })
    _record(ec == 0, "T5: Edit reviewer-tiers.yaml（一致）→ 放行", f"exit={ec}")

    # T6: 非 Write/Edit 工具 → 放行（不触发）
    hook_input = {"tool_name": "Read", "tool_input": {"file_path": os.path.join(REPO_ROOT, "governance/specs/reviewer-tiers.yaml")}}
    proc = subprocess.run(["python", HOOK], input=json.dumps(hook_input).encode(),
                          capture_output=True, timeout=10)
    _record(proc.returncode == 0, "T6: Read 工具 → 放行（不触发）", f"exit={proc.returncode}")

    print("=" * 60)
    print(f"总结: {PASS_COUNT} PASS / {FAIL_COUNT} FAIL")
    print("=" * 60)
    if FAIL_COUNT > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
