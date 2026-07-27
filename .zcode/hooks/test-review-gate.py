#!/usr/bin/env python3
"""
单测：review-gate-precommit.py（round2）
覆盖：
  - 基础 4 类（deny PASS / deny 无条目 / deny 事后补审 / 放行只读）
  - round2 新增：
    - Q3 子串误匹配证伪（c-layer-drift-check 不放行 c-layer-failopen-fix）
    - Q1 rsync + IP 直连
    - override 放行
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "review-gate-precommit.py")
REPO_ROOT = r"C:\Users\Admin\Documents\trae_projects\agent-collaboration-standard"


def run_hook(command_text, repo_root=None):
    """模拟 PreToolUse 调用，返回 (exit_code, stdout)"""
    hook_input = {
        "tool_name": "Bash",
        "tool_input": {"command": command_text},
    }
    env = os.environ.copy()
    if repo_root:
        env["AGENT_COLLABORATION_REPO"] = repo_root
    proc = subprocess.run(
        ["python", HOOK],
        input=json.dumps(hook_input).encode("utf-8"),
        capture_output=True,
        timeout=10,
        env=env,
    )
    return proc.returncode, proc.stdout.decode("utf-8", errors="replace")


def ensure_no_override():
    override = os.path.join(os.path.dirname(HOOK), ".review-gate-override.json")
    if os.path.exists(override):
        os.remove(override)


PASS_COUNT = 0
FAIL_COUNT = 0


def case(name, command, expected_exit, expected_contains=None, repo_root=None):
    global PASS_COUNT, FAIL_COUNT
    ensure_no_override()
    exit_code, stdout = run_hook(command, repo_root)
    ok = exit_code == expected_exit
    if ok and expected_contains:
        for s in expected_contains:
            if s not in stdout:
                ok = False
                break
    status = "✅ PASS" if ok else "❌ FAIL"
    if ok:
        PASS_COUNT += 1
    else:
        FAIL_COUNT += 1
    print(f"{status} | {name}")
    print(f"        cmd: {command[:95]}")
    print(f"        期望 exit={expected_exit}, 实际 exit={exit_code}")
    if expected_contains:
        print(f"        期望 stdout 含: {expected_contains}")
    if not ok and stdout:
        print(f"        实际 stdout: {stdout[:250]}")
    print()


def make_temp_repo(entries_yaml):
    """构造临时 repo + YAML 闸门表"""
    tmp_repo = tempfile.mkdtemp(prefix="review-gate-test-")
    specs_dir = os.path.join(tmp_repo, "governance", "specs")
    os.makedirs(specs_dir, exist_ok=True)
    target = os.path.join(specs_dir, "pre-commit-review-gate-log.yaml")
    with open(target, "w", encoding="utf-8") as f:
        f.write(entries_yaml)
    return tmp_repo


def main():
    print("=" * 70)
    print("单测 review-gate-precommit.py (round2)")
    print(f"HOOK: {HOOK}")
    print(f"REPO: {REPO_ROOT}")
    print("=" * 70)
    print()

    # 临时 repo：含 PASS / 事后补审 / REVIEWING 三种状态
    yaml_content = """\
- gate_id: pi-b-layer
  verdict: PASS
  files: [apply-b-layer-20260727.py]
- gate_id: pi-c-layer-drift-check
  verdict: 事后补审
  files: [apply-c-layer-drift-check-20260727.py]
- gate_id: pi-c-layer-failopen-fix
  verdict: REVIEWING
  files: [apply-c-layer-failopen-fix-20260727.py]
- gate_id: meta-review-gate
  verdict: REVIEWING
  files: []
"""
    tmp_repo = make_temp_repo(yaml_content)

    # ===== 基础 case =====
    case(
        "1A: scp apply-pi-b-layer + verdict=PASS → 放行",
        'scp apply-b-layer-20260727.py root@aetherisonline.xyz:/opt/pi-orchestrator/',
        expected_exit=0,
        repo_root=tmp_repo,
    )

    case(
        "1B: scp apply-pi-c-layer-drift-check + verdict=事后补审 → deny",
        'scp apply-c-layer-drift-check-20260727.py root@aetherisonline.xyz:/opt/pi-orchestrator/',
        expected_exit=2,
        expected_contains=["事后补审", "pi-c-layer-drift-check"],
        repo_root=tmp_repo,
    )

    case(
        "2: scp apply-unknown + 无条目 → deny + 列 open gate_id",
        'scp apply-unknown-new-20260727.py root@aetherisonline.xyz:/opt/pi-orchestrator/',
        expected_exit=2,
        expected_contains=["NO_ENTRY", "open"],
        repo_root=tmp_repo,
    )

    case(
        "3: ssh 只读 git log → 放行",
        "ssh root@aetherisonline.xyz 'cd /opt/pi-orchestrator && git log --oneline -5'",
        expected_exit=0,
        repo_root=tmp_repo,
    )

    case(
        "4: ssh systemctl status → 放行",
        "ssh root@aetherisonline.xyz 'systemctl status pi-dispatch-server'",
        expected_exit=0,
        repo_root=tmp_repo,
    )

    case(
        "5: ssh systemctl restart + 无 PASS → deny",
        "ssh root@aetherisonline.xyz 'systemctl restart pi-dispatch-server'",
        expected_exit=2,
        expected_contains=["dispatch-server"],
        repo_root=tmp_repo,
    )

    case(
        "6: ssh 直接改 /opt/pi-orchestrator 文件 → deny",
        "ssh root@aetherisonline.xyz 'echo xxx > /opt/pi-orchestrator/extensions/dispatch-server.py'",
        expected_exit=2,
        expected_contains=["dispatch-server"],
        repo_root=tmp_repo,
    )

    case(
        "7: scp 到非 ECS 主机 → 放行",
        "scp apply-foo-20260727.py root@other-host.example.com:/tmp/",
        expected_exit=0,
        repo_root=tmp_repo,
    )

    # ===== round2 重点：Q3 子串误匹配证伪 =====
    case(
        "8A【Q3核心】: pi-b-layer PASS 不放行 pi-b-layer-v2（精确等值）",
        'scp apply-b-layer-v2-20260727.py root@aetherisonline.xyz:/opt/pi-orchestrator/',
        expected_exit=2,
        expected_contains=["NO_ENTRY", "b-layer-v2"],
        repo_root=tmp_repo,
    )

    case(
        "8B【Q3核心】: pi-c-layer-drift-check 事后补审 不误放 pi-c-layer-failopen-fix",
        'scp apply-c-layer-failopen-fix-20260727.py root@aetherisonline.xyz:/opt/pi-orchestrator/',
        expected_exit=2,
        expected_contains=["REVIEWING", "failopen-fix"],
        repo_root=tmp_repo,
    )

    case(
        "8C【Q3核心】: 子串 'layer' 不是任何 gate_id → deny",
        'scp apply-layer-20260727.py root@aetherisonline.xyz:/opt/pi-orchestrator/',
        expected_exit=2,
        expected_contains=["NO_ENTRY"],
        repo_root=tmp_repo,
    )

    # ===== round2：Q1 rsync + IP 直连 =====
    case(
        "9A【Q1补充】: rsync apply-*.py 到 ECS → deny（无 PASS）",
        'rsync -avz apply-foo-20260727.py root@aetherisonline.xyz:/opt/pi-orchestrator/',
        expected_exit=2,
        expected_contains=["Pre-commit 评审闸门阻断"],
        repo_root=tmp_repo,
    )

    case(
        "9B【Q1补充】: scp apply-*.py 到 ECS IP 直连 → deny",
        'scp apply-foo-20260727.py root@1.2.3.4:/opt/pi-orchestrator/',
        expected_exit=2,
        expected_contains=["Pre-commit 评审闸门阻断"],
        repo_root=tmp_repo,
    )

    case(
        "9C【Q1补充】: rsync apply-b-layer（PASS）→ 放行",
        'rsync -avz apply-b-layer-20260727.py root@aetherisonline.xyz:/opt/pi-orchestrator/',
        expected_exit=0,
        repo_root=tmp_repo,
    )

    # ===== round2：override =====
    case_override(tmp_repo)

    # ===== round3：C 自动降级条款（fail-closed 必须有单测钉死）=====

    # Case F1: YAML 文件不存在 → deny（fail-closed）
    case(
        "F1【C降级条款】: YAML 不存在 → deny（fail-closed）",
        'scp apply-b-layer-20260727.py root@aetherisonline.xyz:/opt/pi-orchestrator/',
        expected_exit=2,
        repo_root=tempfile.mkdtemp(prefix="empty-repo-"),  # 空 repo 无 YAML
    )

    # Case F2: YAML 语法坏 → deny
    tmp_bad_yaml = tempfile.mkdtemp(prefix="bad-yaml-repo-")
    os.makedirs(os.path.join(tmp_bad_yaml, "governance", "specs"), exist_ok=True)
    with open(os.path.join(tmp_bad_yaml, "governance", "specs", "pre-commit-review-gate-log.yaml"), "w") as f:
        f.write("this is: [invalid: yaml: content\n  - broken\n   bad indent\n")  # 故意坏
    case(
        "F2【C降级条款】: YAML 语法坏 → deny（fail-closed）",
        'scp apply-b-layer-20260727.py root@aetherisonline.xyz:/opt/pi-orchestrator/',
        expected_exit=2,
        repo_root=tmp_bad_yaml,
    )

    # Case F3: 条目无 files 字段 → deny（不误放）
    tmp_no_files = make_temp_repo("""\
- gate_id: foo
  verdict: PASS
""")
    case(
        "F3【C降级条款】: 条目无 files 字段 → deny（不因 verdict=PASS 误放）",
        'scp apply-foo-20260727.py root@aetherisonline.xyz:/opt/pi-orchestrator/',
        expected_exit=2,
        repo_root=tmp_no_files,
    )

    # Case F4: 大小写归一化（B-Q3）—— Apply-B-LAYER 大写应仍匹配小写条目
    case(
        "F4【B-Q3归一化】: 命令里 Apply-B-LAYER.py 大写仍匹配小写 files 条目 → 放行",
        'scp Apply-B-LAYER-20260727.py root@aetherisonline.xyz:/opt/pi-orchestrator/',
        expected_exit=0,
        repo_root=tmp_repo,
    )

    # 清理临时 bad yaml repo
    try:
        shutil.rmtree(tmp_bad_yaml)
    except Exception:
        pass

    # ===== 非 Bash 工具 =====
    case_non_bash()

    # ===== 临时 repo 真实表（验证回填的历史） =====
    case(
        "10【真实表】: pi-failopen 事后补审 → deny",
        'scp apply-c-layer-failopen-fix-20260727.py root@aetherisonline.xyz:/opt/pi-orchestrator/',
        expected_exit=2,
        repo_root=REPO_ROOT,
    )

    # 清理
    try:
        shutil.rmtree(tmp_repo)
    except Exception:
        pass

    print("=" * 70)
    print(f"总结: {PASS_COUNT} PASS / {FAIL_COUNT} FAIL")
    print("=" * 70)
    if FAIL_COUNT > 0:
        sys.exit(1)


def case_override(repo_root):
    global PASS_COUNT, FAIL_COUNT
    print("▶ Case override 生效 → 放行")
    override = os.path.join(os.path.dirname(HOOK), ".review-gate-override.json")
    with open(override, "w") as f:
        json.dump({"until": time.time() + 600, "reason": "test"}, f)
    try:
        hook_input = {
            "tool_name": "Bash",
            "tool_input": {
                "command": "scp apply-no-entry-20260727.py root@aetherisonline.xyz:/opt/pi-orchestrator/"
            },
        }
        env = os.environ.copy()
        env["AGENT_COLLABORATION_REPO"] = repo_root
        proc = subprocess.run(
            ["python", HOOK],
            input=json.dumps(hook_input).encode("utf-8"),
            capture_output=True,
            timeout=10,
            env=env,
        )
        ok = proc.returncode == 0
        status = "✅ PASS" if ok else "❌ FAIL"
        if ok:
            PASS_COUNT += 1
        else:
            FAIL_COUNT += 1
        print(f"  {status} | 期望 exit=0（override 放行）, 实际 exit={proc.returncode}")
        print()
    finally:
        if os.path.exists(override):
            os.remove(override)


def case_non_bash():
    global PASS_COUNT, FAIL_COUNT
    print("▶ Case 非 Bash 工具（Write） → 放行")
    hook_input = {
        "tool_name": "Write",
        "tool_input": {"file_path": "foo.py", "content": "..."},
    }
    proc = subprocess.run(
        ["python", HOOK],
        input=json.dumps(hook_input).encode("utf-8"),
        capture_output=True,
        timeout=10,
    )
    ok = proc.returncode == 0
    status = "✅ PASS" if ok else "❌ FAIL"
    if ok:
        PASS_COUNT += 1
    else:
        FAIL_COUNT += 1
    print(f"  {status} | 期望 exit=0, 实际 exit={proc.returncode}")
    print()


if __name__ == "__main__":
    main()
