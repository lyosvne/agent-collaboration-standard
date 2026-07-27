#!/usr/bin/env python3
"""单测：bootstrap-gate-precommit.py (SO-12 round2 M1-M5)

覆盖 round2 修复：
  M1（删时间窗）: B3 改 / B9 改
  M2（truth hash 校验）: B10 / B11
  M5（正则补全）: B12（>file 无空格）/ B13（cp）/ B14（python open）/ B15（cat 只读放行）
  既有回归: B1/B2/B4/B5/B6/B7/B8
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bootstrap-gate-precommit.py")
COMMON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_bootstrap_common.py")
REPO_ROOT = r"C:\Users\Admin\Documents\trae_projects\agent-collaboration-standard"

PASS_COUNT = 0
FAIL_COUNT = 0


def compute_current_hash():
    """用共享模块算当前真值 hash（测试辅助）"""
    import importlib.util
    spec = importlib.util.spec_from_file_location("_bc", COMMON)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.compute_truth_hash()


def run_hook(command, env=None, marker=None):
    """跑 hook。marker: dict 写标记 / '__DELETE__' 删 / '__CORRUPT__' 损坏。"""
    marker_path = os.path.join(os.path.dirname(HOOK), ".bootstrap-done.json")
    if marker == "__DELETE__":
        if os.path.exists(marker_path):
            os.remove(marker_path)
    elif marker == "__CORRUPT__":
        with open(marker_path, "w", encoding="utf-8") as f:
            f.write("{not valid json}")
    elif isinstance(marker, dict):
        with open(marker_path, "w", encoding="utf-8") as f:
            json.dump(marker, f)
    e = os.environ.copy()
    for k in ("ZCODE_SESSION_ID", "CLAUDE_SESSION_ID"):
        e.pop(k, None)
    e["AGENT_COLLABORATION_REPO"] = REPO_ROOT
    if env:
        e.update(env)
    hook_input = {"tool_name": "Bash", "tool_input": {"command": command}}
    proc = subprocess.run(["python", HOOK], input=json.dumps(hook_input).encode(),
                          capture_output=True, timeout=10, env=e)
    out = proc.stdout.decode("utf-8", "replace") + proc.stderr.decode("utf-8", "replace")
    return proc.returncode, out


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


def cleanup_marker():
    marker_path = os.path.join(os.path.dirname(HOOK), ".bootstrap-done.json")
    if os.path.exists(marker_path):
        os.remove(marker_path)


def valid_marker(session_id="sess_test_123"):
    """构造有效标记（session_id 匹配 + truth_hashes 匹配当前真值）"""
    return {
        "session_id": session_id,
        "truth_hashes": compute_current_hash(),
        "mechanism": "SO-12-v2-test",
    }


def main():
    print("=" * 60)
    print("单测 bootstrap-gate-precommit.py (SO-12 round2 M1-M5)")
    print("=" * 60)
    print()

    current_hash = compute_current_hash()

    # B1: 标记缺失 + 动手类 → deny
    ec, out = run_hook(
        'mira -p "评审方 A round1" --model opus4.8p',
        env={"CURRENT_REVIEW_PROJECT": "t", "CURRENT_REVIEW_ROUND": "1"},
        marker="__DELETE__"
    )
    _record(ec == 2 and "bootstrap" in out.lower() and "SO-12" in out,
            "B1: 标记缺失 + mira 评审调度 → deny",
            f"exit={ec}")

    # B2: 标记存在 + session_id 匹配 + hash 匹配 + 动手类 → 放行
    ec, out = run_hook(
        'mira -p "评审方 A round1" --model opus4.8p',
        env={"ZCODE_SESSION_ID": "sess_test_123"},
        marker=valid_marker("sess_test_123")
    )
    _record(ec == 0, "B2: 标记 session_id+hash 双匹配 → 放行",
            f"exit={ec}")

    # B3（M1 改）: session_id 不匹配 → deny（无超时概念，纯 session_id 校验）
    ec, out = run_hook(
        'mira -p "评审方 A round1" --model opus4.8p',
        env={"ZCODE_SESSION_ID": "sess_new_456", "CURRENT_REVIEW_PROJECT": "t", "CURRENT_REVIEW_ROUND": "1"},
        marker=valid_marker("sess_old_999")
    )
    _record(ec == 2 and "session_id_mismatch" in out,
            "B3【M1】: session_id 不匹配 → deny（无时间窗口兜底）",
            f"exit={ec}")

    # B4: 非动手类（git log）+ 无标记 → 放行
    ec, out = run_hook('git log --oneline -5', marker="__DELETE__")
    _record(ec == 0, "B4: 非动手类（git log）+ 无标记 → 放行", f"exit={ec}")

    # B5: 标记缺失 + 改真值层 → deny
    ec, out = run_hook(
        'echo "x" > governance/specs/reviewer-tiers.yaml',
        marker="__DELETE__"
    )
    _record(ec == 2 and "bootstrap" in out.lower(),
            "B5: 标记缺失 + 改真值层 → deny", f"exit={ec}")

    # B6: 标记缺失 + mira 非评审调度 → 放行
    ec, out = run_hook('mira -p "生成猫图" --model opus4.6', marker="__DELETE__")
    _record(ec == 0, "B6: mira 非评审调度 + 无标记 → 放行", f"exit={ec}")

    # B7: 标记损坏 → deny（fail-closed）
    ec, out = run_hook(
        'mira -p "评审方 A round1" --model opus4.8p',
        env={"CURRENT_REVIEW_PROJECT": "t", "CURRENT_REVIEW_ROUND": "1"},
        marker="__CORRUPT__"
    )
    _record(ec == 2 and ("corrupt" in out.lower() or "损坏" in out),
            "B7: 标记损坏 → deny（fail-closed）", f"exit={ec}")

    # B8: ECS 操作 + 无标记 → deny
    ec, out = run_hook('ssh root@aetherisonline.xyz "ls /opt"', marker="__DELETE__")
    _record(ec == 2 and "ECS" in out, "B8: ECS 操作 + 无标记 → deny", f"exit={ec}")

    # B9（M1 改）: 无 ZCODE_SESSION_ID env → deny（M1 fail-closed，无时间窗兜底）
    ec, out = run_hook(
        'mira -p "评审方 A round1" --model opus4.8p',
        env={"CURRENT_REVIEW_PROJECT": "t", "CURRENT_REVIEW_ROUND": "1"},  # 不设 ZCODE_SESSION_ID
        marker=valid_marker("any_old_session")  # 即使有标记，无 env 也 deny
    )
    _record(ec == 2 and "no_session_env" in out,
            "B9【M1】: 无 ZCODE_SESSION_ID env → deny（删时间窗口兜底）",
            f"exit={ec}")

    # ===== M2: truth hash 校验 =====

    # B10（M2）: 标记 hash 与当前不一致 → deny（真值已变）
    tampered_hash = dict(current_hash)
    tampered_hash["reviewer_tiers_yaml"] = "deadbeefdeadbeef"  # 篡改
    ec, out = run_hook(
        'mira -p "评审方 A round1" --model opus4.8p',
        env={"ZCODE_SESSION_ID": "sess_test_123", "CURRENT_REVIEW_PROJECT": "t", "CURRENT_REVIEW_ROUND": "1"},
        marker={"session_id": "sess_test_123", "truth_hashes": tampered_hash}
    )
    _record(ec == 2 and "truth_drift" in out,
            "B10【M2】: 标记 hash 与当前真值不一致 → deny（真值已变）",
            f"exit={ec}")

    # B11（M2）: 标记 hash 完全匹配 → 放行（同 B2，明示 M2 通过路径）
    ec, out = run_hook(
        'mira -p "评审方 A round1" --model opus4.8p',
        env={"ZCODE_SESSION_ID": "sess_match"},
        marker=valid_marker("sess_match")
    )
    _record(ec == 0, "B11【M2】: 标记 session_id+truth_hash 双匹配 → 放行", f"exit={ec}")

    # ===== M5: 正则补全 =====

    # B12（M5）: echo x >reviewer-tiers.yaml（无空格重定向）→ deny
    ec, out = run_hook(
        'echo x >governance/specs/reviewer-tiers.yaml',  # 无空格
        env={"ZCODE_SESSION_ID": "sess_test"},
        marker="__DELETE__"
    )
    _record(ec == 2 and "bootstrap" in out.lower(),
            "B12【M5】: 无空格重定向 >reviewer-tiers.yaml → deny", f"exit={ec}")

    # B13（M5）: cp /tmp/x reviewer-tiers.yaml → deny
    ec, out = run_hook(
        'cp /tmp/fake reviewer-tiers.yaml',
        env={"ZCODE_SESSION_ID": "sess_test"},
        marker="__DELETE__"
    )
    _record(ec == 2 and "bootstrap" in out.lower(),
            "B13【M5】: cp 覆盖真值层 → deny", f"exit={ec}")

    # B14（M5）: python -c "open('reviewer-tiers.yaml','w')" → deny
    ec, out = run_hook(
        'python -c "open(\'governance/specs/reviewer-tiers.yaml\',\'w\').write(\'x\')"',
        env={"ZCODE_SESSION_ID": "sess_test"},
        marker="__DELETE__"
    )
    _record(ec == 2 and "bootstrap" in out.lower(),
            "B14【M5】: python -c open(w) 写真值层 → deny", f"exit={ec}")

    # B15（M5）: cat reviewer-tiers.yaml（只读）+ 无标记 → 放行（不拦只读）
    ec, out = run_hook(
        'cat governance/specs/reviewer-tiers.yaml',
        marker="__DELETE__"
    )
    _record(ec == 0, "B15【M5】: cat 真值层（只读）+ 无标记 → 放行（不拦只读）", f"exit={ec}")

    cleanup_marker()

    print("=" * 60)
    print(f"总结: {PASS_COUNT} PASS / {FAIL_COUNT} FAIL")
    print("=" * 60)
    if FAIL_COUNT > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
