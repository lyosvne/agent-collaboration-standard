#!/usr/bin/env python3
"""单测：session-gate-precommit.py (SO-11-v2-2 round2)

覆盖 round2 修复后的 M1-M5 全部行为：
  M1（项目识别 fail-closed）: S9
  M2（round 显式参数）: S10, S11
  M3（配置缺失 fail-closed + 威胁模型分层）: S12, S13
  M5（session 过期通道）: S14, S15
  既有行为回归: S1-S8（已加 CURRENT_REVIEW_ROUND，消除假阳性）
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "session-gate-precommit.py")

PASS_COUNT = 0
FAIL_COUNT = 0


def run_hook(command, env=None):
    hook_input = {"tool_name": "Bash", "tool_input": {"command": command}}
    e = os.environ.copy()
    # 默认清掉可能污染的环境变量
    for k in ("CURRENT_REVIEW_PROJECT", "CURRENT_REVIEW_ROUND"):
        e.pop(k, None)
    if env:
        e.update(env)
    proc = subprocess.run(["python", HOOK], input=json.dumps(hook_input).encode(),
                          capture_output=True, timeout=10, env=e)
    return proc.returncode, proc.stdout.decode("utf-8", "replace") + proc.stderr.decode("utf-8", "replace")


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


def make_temp_repo(index_yaml, reviewer_tiers_yaml=None):
    """构造临时 repo 含 reviewer-tiers.yaml + review-sessions-index.yaml"""
    tmp = tempfile.mkdtemp(prefix="session-test-")
    specs = os.path.join(tmp, "governance", "specs")
    archive = os.path.join(tmp, "archive")
    os.makedirs(specs, exist_ok=True)
    os.makedirs(archive, exist_ok=True)
    # reviewer-tiers.yaml（round2 版本，含 current_round_env + expired_rounds_field）
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
        "  current_round_env: 'CURRENT_REVIEW_ROUND'\n"
        "  archived_status: 'ARCHIVED'\n"
        "  expired_rounds_field: 'expired_rounds'\n"
    )
    with open(os.path.join(specs, "reviewer-tiers.yaml"), "w", encoding="utf-8") as f:
        f.write(rt)
    with open(os.path.join(archive, "review-sessions-index.yaml"), "w", encoding="utf-8") as f:
        f.write(index_yaml)
    return tmp


def main():
    print("=" * 60)
    print("单测 session-gate-precommit.py (v2-2 round2, M1-M5)")
    print("=" * 60)
    print()

    # ===== 回归：S1-S8（旧 case，加 CURRENT_REVIEW_ROUND 消除假阳性）=====

    # S1: round1 首轮（CURRENT_REVIEW_ROUND=1）放行
    tmp1 = make_temp_repo("""\
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
                 env={"AGENT_COLLABORATION_REPO": tmp1,
                      "CURRENT_REVIEW_PROJECT": "test-proj",
                      "CURRENT_REVIEW_ROUND": "1"})[0] == 0,
        "S1: round1 首轮（ROUND=1）→ 放行"
    )

    # S2: round2 无 -r → deny + 提示 session_id 111111
    ec, out = run_hook(
        'mira -p "评审方 A round2 复核" --model opus4.8p',
        env={"AGENT_COLLABORATION_REPO": tmp1,
             "CURRENT_REVIEW_PROJECT": "test-proj",
             "CURRENT_REVIEW_ROUND": "2"}
    )
    _record(ec == 2 and "111111" in out, "S2: round2 无 -r → deny + 提示 session_id 111111",
            f"exit={ec}")

    # S3: round2 用正确 -r 111111 → 放行
    _record(
        run_hook('mira -p "评审方 A round2 复核" --model opus4.8p -r 111111',
                 env={"AGENT_COLLABORATION_REPO": tmp1,
                      "CURRENT_REVIEW_PROJECT": "test-proj",
                      "CURRENT_REVIEW_ROUND": "2"})[0] == 0,
        "S3: round2 -r 正确 id → 放行"
    )

    # S4: round2 -r 错 id → deny
    ec, out = run_hook(
        'mira -p "评审方 A round2 复核" --model opus4.8p -r 999999',
        env={"AGENT_COLLABORATION_REPO": tmp1,
             "CURRENT_REVIEW_PROJECT": "test-proj",
             "CURRENT_REVIEW_ROUND": "2"}
    )
    _record(ec == 2 and "不匹配" in out, "S4: round2 -r 错 id → deny",
            f"exit={ec}")

    # S5: ARCHIVED 项目放行
    tmp2 = make_temp_repo("""\
projects:
  - project: archived-proj
    status: ARCHIVED
    reviewer_sessions:
      A: {round1: "222222"}
""")
    _record(
        run_hook('mira -p "评审方 A round2" --model opus4.8p',
                 env={"AGENT_COLLABORATION_REPO": tmp2,
                      "CURRENT_REVIEW_PROJECT": "archived-proj",
                      "CURRENT_REVIEW_ROUND": "2"})[0] == 0,
        "S5: ARCHIVED 项目 → 放行"
    )

    # S6: 非 mira 评审调度（普通 mira 调用，无"评审方"字样）放行
    _record(
        run_hook('mira -p "生成图片" --model opus4.6',
                 env={"AGENT_COLLABORATION_REPO": tmp1})[0] == 0,
        "S6: 非 评审 mira 调用 → 放行"
    )

    # S7: 评审方 C（qoder_cantus 平台，不在 continuity）→ 放行
    # 注：C 走 qoder-bridge 不走 mira，但这里测的是"若 mira 调度里标了评审方 C，
    # hook 识别出 C 但 C 不在 platforms_with_continuity，放行"
    _record(
        run_hook('mira -p "评审方 C round2" --model opus4.8p',
                 env={"AGENT_COLLABORATION_REPO": tmp1,
                      "CURRENT_REVIEW_PROJECT": "test-proj",
                      "CURRENT_REVIEW_ROUND": "2"})[0] == 0,
        "S7: 评审方 C（不在 continuity 平台）→ 放行"
    )

    # ===== M1: 项目识别 fail-closed =====

    # S9: 未 export CURRENT_REVIEW_PROJECT + 评审调度 → deny + 提示 export（M1）
    ec, out = run_hook(
        'mira -p "评审方 A round2 复核" --model opus4.8p',
        env={"AGENT_COLLABORATION_REPO": tmp1,
             "CURRENT_REVIEW_ROUND": "2"}  # 只设 ROUND，不设 PROJECT
    )
    _record(ec == 2 and "CURRENT_REVIEW_PROJECT" in out and "M1" in out,
            "S9【M1】: 未设 CURRENT_REVIEW_PROJECT → deny + 提示 M1",
            f"exit={ec}")

    # ===== M2: round 显式参数 =====

    # S10: 未 export CURRENT_REVIEW_ROUND + 评审调度 → deny + 提示 M2
    ec, out = run_hook(
        'mira -p "评审方 A round2 复核" --model opus4.8p',
        env={"AGENT_COLLABORATION_REPO": tmp1,
             "CURRENT_REVIEW_PROJECT": "test-proj"}  # 只设 PROJECT，不设 ROUND
    )
    _record(ec == 2 and "CURRENT_REVIEW_ROUND" in out and "M2" in out,
            "S10【M2】: 未设 CURRENT_REVIEW_ROUND → deny + 提示 M2",
            f"exit={ec}")

    # S11: CURRENT_REVIEW_ROUND=2 + prompt 含 "round1 已修" → 正确查 round1 sid（不抓 prompt 里的 round1）
    # 这是 B round1 BLOCKER 的回归测试：旧 regex 会抓首个 round1 → 误判首轮放行
    ec, out = run_hook(
        'mira -p "评审方 A，round1 已修 M1，本轮 round2 复核" --model opus4.8p',
        env={"AGENT_COLLABORATION_REPO": tmp1,
             "CURRENT_REVIEW_PROJECT": "test-proj",
             "CURRENT_REVIEW_ROUND": "2"}
    )
    _record(ec == 2 and "111111" in out,
            "S11【M2 回归】: ROUND=2 + prompt 含 round1 → 正确查 round1 sid 111111（不抓 prompt 首个 round1）",
            f"exit={ec}")

    # ===== M3: 配置缺失 fail-closed + 威胁模型分层 =====

    # S12: reviewer-tiers.yaml 缺 session_continuity 整节点 → deny（M3）
    tmp_no_sc = make_temp_repo(
        """\
projects:
  - project: test-proj
    status: REVIEWING
    reviewer_sessions: {A: {round1: "111111"}}
""",
        reviewer_tiers_yaml=(
            "reviewers:\n"
            "  A: {tier: opus4.8p, platform: mira, dispatch_keyword: 评审方 A}\n"
            "dispatchers:\n  mira: {invocation_pattern: '\\\\bmira\\\\s+(-p|--print)\\\\b'}\n"
            # 故意不写 session_continuity 节点
        )
    )
    ec, out = run_hook(
        'mira -p "评审方 A round2" --model opus4.8p',
        env={"AGENT_COLLABORATION_REPO": tmp_no_sc,
             "CURRENT_REVIEW_PROJECT": "test-proj",
             "CURRENT_REVIEW_ROUND": "2"}
    )
    _record(ec == 2 and "session_continuity" in out,
            "S12【M3】: session_continuity 节点缺失 → deny（配置删除即绕过机制）",
            f"exit={ec}")

    # S13: session_continuity.enabled: false 显式禁用 → 放行（紧急制动）
    tmp_disabled = make_temp_repo(
        """\
projects:
  - project: test-proj
    status: REVIEWING
    reviewer_sessions: {A: {round1: "111111"}}
""",
        reviewer_tiers_yaml=(
            "reviewers:\n"
            "  A: {tier: opus4.8p, platform: mira, dispatch_keyword: 评审方 A}\n"
            "dispatchers:\n  mira: {invocation_pattern: '\\\\bmira\\\\s+(-p|--print)\\\\b'}\n"
            "session_continuity:\n"
            "  enabled: false\n"  # 显式禁用
            "  strategy: round_n_resumes_round_n_minus_1\n"
            "  platforms_with_continuity: [mira]\n"
            "  resume_arg: '-r'\n"
            "  record_index: 'archive/review-sessions-index.yaml'\n"
            "  current_project_env: 'CURRENT_REVIEW_PROJECT'\n"
            "  current_round_env: 'CURRENT_REVIEW_ROUND'\n"
            "  archived_status: 'ARCHIVED'\n"
            "  expired_rounds_field: 'expired_rounds'\n"
        )
    )
    _record(
        run_hook('mira -p "评审方 A round2 无 -r" --model opus4.8p',
                 env={"AGENT_COLLABORATION_REPO": tmp_disabled,
                      "CURRENT_REVIEW_PROJECT": "test-proj",
                      "CURRENT_REVIEW_ROUND": "2"})[0] == 0,
        "S13【M3】: session_continuity.enabled: false 显式禁用 → 放行（紧急制动）"
    )

    # ===== M5: session 过期降级通道 =====

    # S14: round1 在 expired_rounds 里 → round2 放行 fresh（M5）
    tmp_expired = make_temp_repo("""\
projects:
  - project: expired-proj
    status: REVIEWING
    expired_rounds: [1]  # round1 session 已过期
    reviewer_sessions:
      A:
        round1: "OLD_EXPIRED_SID"  # 过期的 sid，不应被强制 -r
""")
    _record(
        run_hook('mira -p "评审方 A round2 fresh 调用" --model opus4.8p',
                 env={"AGENT_COLLABORATION_REPO": tmp_expired,
                      "CURRENT_REVIEW_PROJECT": "expired-proj",
                      "CURRENT_REVIEW_ROUND": "2"})[0] == 0,
        "S14【M5】: round1 在 expired_rounds → round2 放行 fresh（不强制 -r 过期 sid）"
    )

    # S15: round1 不在 expired_rounds 但有 sid → round2 仍要求 -r（未过期场景，回归）
    # 用 tmp1（test-proj，round1 sid=111111，无 expired_rounds）
    ec, out = run_hook(
        'mira -p "评审方 A round2" --model opus4.8p',
        env={"AGENT_COLLABORATION_REPO": tmp1,
             "CURRENT_REVIEW_PROJECT": "test-proj",
             "CURRENT_REVIEW_ROUND": "2"}
    )
    _record(ec == 2 and "111111" in out and "-r" in out,
            "S15【M5 回归】: round1 未过期（不在 expired_rounds）→ round2 仍要求 -r 111111",
            f"exit={ec}")

    # 清理
    for t in [tmp1, tmp2, tmp_no_sc, tmp_disabled, tmp_expired]:
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
