#!/usr/bin/env python3
"""单测：session-gate-precommit.py (SO-11-v2-2)"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "session-gate-precommit.py")
REPO_ROOT = r"C:\Users\Admin\Documents\trae_projects\agent-collaboration-standard"

PASS_COUNT = 0
FAIL_COUNT = 0


def run_hook(command, env=None):
    hook_input = {"tool_name": "Bash", "tool_input": {"command": command}}
    e = os.environ.copy()
    if env:
        e.update(env)
    proc = subprocess.run(["python", HOOK], input=json.dumps(hook_input).encode(),
                          capture_output=True, timeout=10, env=e)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


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


def make_temp_repo_with_index(index_yaml, reviewer_tiers_yaml=None):
    """构造临时 repo 含 reviewer-tiers.yaml + review-sessions-index.yaml"""
    tmp = tempfile.mkdtemp(prefix="session-test-")
    specs = os.path.join(tmp, "governance", "specs")
    archive = os.path.join(tmp, "archive")
    os.makedirs(specs, exist_ok=True)
    os.makedirs(archive, exist_ok=True)
    # reviewer-tiers.yaml（最小可用）
    rt = reviewer_tiers_yaml or (
        "reviewers:\n"
        "  A: {tier: opus4.8p, platform: mira, dispatch_keyword: 评审方 A}\n"
        "  B: {tier: gpt5.6sol, platform: mira, dispatch_keyword: 评审方 B}\n"
        "  C: {tier: cantus, platform: qoder_cantus, dispatch_keyword: 评审方 C}\n"
        "dispatchers:\n  mira: {invocation_pattern: '\\\\bmira\\\\s+(-p|--print)\\\\b'}\n"
        "session_continuity:\n"
        "  enabled: true\n"
        "  strategy: round_n_resumes_round_n_minus_1\n"
        "  platforms_with_continuity: [mira]\n"
        "  resume_arg: '-r'\n"
        "  record_index: 'archive/review-sessions-index.yaml'\n"
        "  current_project_env: 'CURRENT_REVIEW_PROJECT'\n"
        "  archived_status: 'ARCHIVED'\n"
    )
    with open(os.path.join(specs, "reviewer-tiers.yaml"), "w", encoding="utf-8") as f:
        f.write(rt)
    with open(os.path.join(archive, "review-sessions-index.yaml"), "w", encoding="utf-8") as f:
        f.write(index_yaml)
    return tmp


def main():
    print("=" * 60)
    print("单测 session-gate-precommit.py (v2-2)")
    print("=" * 60)
    print()

    # S1: 首轮（round1）放行（无 round0 session）
    tmp1 = make_temp_repo_with_index("""\
projects:
  - project: test-proj
    review_dir: archive/governance-review-test/
    status: REVIEWING
    reviewer_sessions:
      A:
        round1: "111111"
""")
    _record(
        run_hook('mira -p "评审方 A round1 你好" --model opus4.8p',
                 env={"AGENT_COLLABORATION_REPO": tmp1, "CURRENT_REVIEW_PROJECT": "test-proj"})[0] == 0,
        "S1: round1 首轮 → 放行"
    )

    # S2: round2 无 -r → deny（应续接 round1 session）
    ec, out = run_hook(
        'mira -p "评审方 A round2 复核" --model opus4.8p',
        env={"AGENT_COLLABERATION_REPO": tmp1, "CURRENT_REVIEW_PROJECT": "test-proj"}
    )
    # 注：上面环境变量名打错了 AGENT_COLLABERATION，但 hook 读的是 AGENT_COLLABORATION_REPO，所以会用 fallback repo
    # 改对：
    ec, out = run_hook(
        'mira -p "评审方 A round2 复核" --model opus4.8p',
        env={"AGENT_COLLABORATION_REPO": tmp1, "CURRENT_REVIEW_PROJECT": "test-proj"}
    )
    _record(ec == 2 and "111111" in out, "S2: round2 无 -r → deny + 提示 session_id 111111",
            f"exit={ec}")

    # S3: round2 用正确 -r 111111 → 放行
    _record(
        run_hook('mira -p "评审方 A round2 复核" --model opus4.8p -r 111111',
                 env={"AGENT_COLLABORATION_REPO": tmp1, "CURRENT_REVIEW_PROJECT": "test-proj"})[0] == 0,
        "S3: round2 -r 正确 id → 放行"
    )

    # S4: round2 -r 错 id → deny
    ec, out = run_hook(
        'mira -p "评审方 A round2 复核" --model opus4.8p -r 999999',
        env={"AGENT_COLLABORATION_REPO": tmp1, "CURRENT_REVIEW_PROJECT": "test-proj"}
    )
    _record(ec == 2 and "不匹配" in out, "S4: round2 -r 错 id → deny",
            f"exit={ec}")

    # S5: ARCHIVED 项目放行（不强制续接）
    tmp2 = make_temp_repo_with_index("""\
projects:
  - project: archived-proj
    status: ARCHIVED
    reviewer_sessions:
      A: {round1: "222222"}
""")
    _record(
        run_hook('mira -p "评审方 A round2" --model opus4.8p',
                 env={"AGENT_COLLABORATION_REPO": tmp2, "CURRENT_REVIEW_PROJECT": "archived-proj"})[0] == 0,
        "S5: ARCHIVED 项目 → 放行"
    )

    # S6: 非 mira 评审调度（普通 mira 调用）放行
    _record(
        run_hook('mira -p "生成图片" --model opus4.6',
                 env={"AGENT_COLLABORATION_REPO": tmp1})[0] == 0,
        "S6: 非 评审 mira 调用 → 放行"
    )

    # S7: C (qoder) 调度不校验续接（platforms_with_continuity 只含 mira）
    _record(
        run_hook('mira -p "评审方 C round2" --model opus4.8p',
                 env={"AGENT_COLLABORATION_REPO": tmp1, "CURRENT_REVIEW_PROJECT": "test-proj"})[0] == 0,
        "S7: 评审方 C（不在 continuity 平台）→ 放行"
    )

    # S8: 命令没标 round → 放行（无法判定）
    _record(
        run_hook('mira -p "评审方 A 复核" --model opus4.8p',
                 env={"AGENT_COLLABORATION_REPO": tmp1, "CURRENT_REVIEW_PROJECT": "test-proj"})[0] == 0,
        "S8: 命令无 round 标识 → 放行（靠 ZCode 自觉）"
    )

    # 清理
    for t in [tmp1, tmp2]:
        try:
            shutil.rmtree(t)
        except Exception:
            pass

    print("=" * 60)
    print(f"总结: {PASS_COUNT} PASS / {FAIL_COUNT} FAIL")
    print("=" * 60)
    if FAIL_COUNT > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
