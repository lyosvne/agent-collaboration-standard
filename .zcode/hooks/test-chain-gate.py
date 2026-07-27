#!/usr/bin/env python3
"""
单测：chain-gate-precommit.py (SO-11)
覆盖 D1-D8 + 真值层解析 + 识别逻辑
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chain-gate-precommit.py")
REPO_ROOT = r"C:\Users\Admin\Documents\trae_projects\agent-collaboration-standard"


def run_hook(command_text, repo_root=None):
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
    override = os.path.join(os.path.dirname(HOOK), ".chain-gate-override.json")
    if os.path.exists(override):
        os.remove(override)


PASS_COUNT = 0
FAIL_COUNT = 0


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


def case(name, command, expected_exit, expected_contains=None, repo_root=None):
    ensure_no_override()
    ec, out = run_hook(command, repo_root)
    ok = ec == expected_exit
    if ok and expected_contains:
        for s in expected_contains:
            if s not in out:
                ok = False
                break
    _record(ok, name, f"cmd: {command[:90]}\n        exit={ec} (期望 {expected_exit})" +
            (f"\n        期望含: {expected_contains}" if expected_contains else "") +
            (f"\n        实际 stdout: {out[:200]}" if not ok and out else ""))


def main():
    print("=" * 70)
    print("单测 chain-gate-precommit.py (SO-11)")
    print(f"HOOK: {HOOK}")
    print(f"REPO: {REPO_ROOT}")
    print("=" * 70)
    print()

    # ===== 真值层解析（v2-1: 从 YAML 读）=====
    import importlib.util
    spec_mod = importlib.util.spec_from_file_location("cg", HOOK)
    m = importlib.util.module_from_spec(spec_mod)
    spec_mod.loader.exec_module(m)

    data, err = m.load_truth_layer()
    reviewers = data["reviewers"] if data else {}
    expected_tiers = {"A": "opus4.8p", "B": "gpt5.6sol", "C": "cantus"}
    actual_tiers = {r: info.get("tier") for r, info in reviewers.items() if isinstance(info, dict)}
    _record(actual_tiers == expected_tiers,
            "真值层 YAML 解析（v2-1 单源）",
            f"tiers={actual_tiers} err={err}")

    # v2-1: 验证关键字从 YAML 动态读（非硬编码）
    keywords = data["review_keywords"] if data else []
    _record("评审方 A" in keywords and "评审方 B" in keywords and "review-package" in keywords,
            "YAML 数据驱动：dispatch_keyword + extra keywords 都读出",
            f"keywords={keywords}")

    # v2-1: 验证 qoder pattern 从 YAML 读
    qoder_patterns = data["qoder_patterns"] if data else []
    _record(len(qoder_patterns) >= 1 and "cantus" in qoder_patterns[0],
            "YAML 数据驱动：qoder dispatch_command_pattern 读出",
            f"patterns={qoder_patterns}")

    known, err2 = m.load_mira_known_tiers()
    _record("opus4.8p" in known and "gpt5.6sol" in known and len(known) >= 15,
            "真值层 mira 档位表解析（旁路健康检查）",
            f"{len(known)} 档 err={err2}")

    # ===== 识别逻辑 =====
    _record(m.is_mira_review_dispatch('mira -p "评审方 A 你好" --model opus4.8p'),
            "识别: mira -p + 评审方 A → 评审调度")
    _record(not m.is_mira_review_dispatch('mira -p "生成图片" --model opus4.6'),
            "识别: mira -p 无评审关键字 → 非评审（放行）")
    _record(m.is_qoder_review_dispatch("ssh ecs 'python3 qoder-bridge.py --tier cantus \"x\"'"),
            "识别: qoder-bridge --tier cantus → C 评审调度")
    _record(not m.is_qoder_review_dispatch("ssh ecs 'python3 qoder-bridge.py --tier general \"x\"'"),
            "识别: qoder-bridge --tier general → 非评审")

    # ===== D 系列：调度校验 =====

    # D1: 评审方 A + opus4.8p（真值层一致）→ 放行
    case(
        "D1: mira 评审方 A + --model opus4.8p → 放行",
        'mira -p "你是评审方 A（架构师视角）..." --model opus4.8p',
        expected_exit=0,
    )

    # D2【今天事故】: 评审方 A + opus4.6（不一致）→ deny
    case(
        "D2【今天事故】: mira 评审方 A + --model opus4.6 → deny",
        'mira -p "你是评审方 A（架构师视角）..." --model opus4.6',
        expected_exit=2,
        expected_contains=["opus4.6 不在评审方", "opus4.8p"],
    )

    # D3: 评审方 A 无 --model → deny（必须显式档位）
    case(
        "D3: mira 评审方 A 无 --model → deny（必须显式档位）",
        'mira -p "你是评审方 A（架构师视角）..."',
        expected_exit=2,
        expected_contains=["必须显式 --model"],
    )

    # D4: 非评审用途 mira -p → 放行（不拦）
    case(
        "D4: mira -p 非评审用途 → 放行（不拦）",
        'mira -p "生成一张猫咪图" --model opus4.6',
        expected_exit=0,
    )

    # D5: qoder-bridge --tier cantus → 放行
    case(
        "D5: qoder-bridge --tier cantus → 放行",
        "ssh root@aetherisonline.xyz 'cd /opt/pi/feishu-bridge && python3 qoder-bridge.py --tier cantus \"评审方 C\"'",
        expected_exit=0,
    )

    # D6: qoder-bridge --tier general（非评审，识别不出）→ 放行
    case(
        "D6: qoder-bridge --tier general → 放行（不拦非评审）",
        "ssh root@aetherisonline.xyz 'python3 qoder-bridge.py --tier general \"普通任务\"'",
        expected_exit=0,
    )

    # D7: 评审方 B + gpt5.6sol → 放行
    case(
        "D7: mira 评审方 B + --model gpt5.6sol → 放行",
        'mira -p "你是评审方 B（严格结构化审查）..." --model gpt5.6sol',
        expected_exit=0,
    )

    # D8: 评审方 B + opus4.8p（错档）→ deny
    case(
        "D8: mira 评审方 B + --model opus4.8p（错档）→ deny",
        'mira -p "你是评审方 B（严格结构化审查）..." --model opus4.8p',
        expected_exit=2,
        expected_contains=["不在评审方 ['B']", "gpt5.6sol"],
    )

    # D9: 评审方 A + opus4.9p（不在档位表）→ deny
    case(
        "D9: mira 评审方 A + --model opus4.9p（假档）→ deny",
        'mira -p "你是评审方 A..." --model opus4.9p',
        expected_exit=2,
    )

    # D10: 评审调度用新措辞（识别不出评审方）→ fail-closed deny
    case(
        "D10: mira -p + 评审材料（无 A/B 关键字）→ fail-closed deny",
        'mira -p "请评审这个方案 review-package" --model opus4.8p',
        expected_exit=2,
        expected_contains=["无法识别具体评审方"],
    )

    # ===== 真值层解析失败 fail-closed（v2-1: YAML 不存在）=====
    case(
        "D11【fail-closed】: 空 repo（YAML 不存在）+ 评审调度 → deny",
        'mira -p "你是评审方 A..." --model opus4.8p',
        expected_exit=2,
        expected_contains=["真值层 YAML 解析失败"],
        repo_root=tempfile.mkdtemp(prefix="empty-chain-"),
    )

    # ===== override =====
    ensure_no_override()
    override = os.path.join(os.path.dirname(HOOK), ".chain-gate-override.json")
    with open(override, "w") as f:
        json.dump({"until": time.time() + 600}, f)
    try:
        ec, out = run_hook('mira -p "评审方 A" --model opus4.6', repo_root=REPO_ROOT)
        _record(ec == 0, "D12【override】: override 生效 → 放行",
                f"exit={ec} (期望 0)")
    finally:
        if os.path.exists(override):
            os.remove(override)

    # ===== 非 Bash 工具 =====
    hook_input = {"tool_name": "Write", "tool_input": {"file_path": "x", "content": "..."}}
    proc = subprocess.run(["python", HOOK], input=json.dumps(hook_input).encode(),
                          capture_output=True, timeout=10)
    _record(proc.returncode == 0, "D13: 非 Bash 工具 → 放行",
            f"exit={proc.returncode}")

    # ===== round2：C1 双源比对 + C2 回归测试 + B-N8/N9 =====

    # Case C1【C round1 C1】: 双源不一致 → fail-closed deny
    # v2-1: 构造临时 repo：reviewer-tiers.yaml 写 opus4.8p，但 mira-integration-status 没有 opus4.8p
    tmp_repo_c1 = tempfile.mkdtemp(prefix="chain-c1-")
    specs_dir_c1 = os.path.join(tmp_repo_c1, "governance", "specs")
    os.makedirs(specs_dir_c1, exist_ok=True)
    with open(os.path.join(specs_dir_c1, "reviewer-tiers.yaml"), "w", encoding="utf-8") as f:
        f.write(
            "reviewers:\n"
            "  A:\n    tier: opus4.8p\n    platform: mira\n    dispatch_keyword: 评审方 A\n"
            "  B:\n    tier: gpt5.6sol\n    platform: mira\n    dispatch_keyword: 评审方 B\n"
            "  C:\n    tier: cantus\n    platform: qoder\n    dispatch_keyword: 评审方 C\n"
            "    dispatch_command_pattern: 'qoder-bridge(?:\\\\.py)?\\\\s+--tier\\\\s+cantus\\\\b'\n"
        )
    # mira-integration-status 故意只列旧档（无 opus4.8p）→ YAML 与平台表双源漂移
    with open(os.path.join(specs_dir_c1, "mira-integration-status.md"), "w", encoding="utf-8") as f:
        f.write("| **Cloud-O (Claude)** | opus4.6 / opus4.5 | t=Think |\n"
                "| **GPT** | gpt5.5 / gpt5.4 | sol/luna |\n")
    case(
        "C1【C round1 C1】: 双源不一致（YAML 有 opus4.8p，mira 表无）→ deny",
        'mira -p "评审方 A..." --model opus4.8p',
        expected_exit=2,
        expected_contains=["双源不一致", "opus4.8p"],
        repo_root=tmp_repo_c1,
    )
    try:
        shutil.rmtree(tmp_repo_c1)
    except Exception:
        pass

    # Case C2【C round1 C2 回归测试】: 回放 round1 事故路径（mira -p + 评审方 A + opus4.6）
    # 用真实 repo（spec §二 = opus4.8p，opus4.6 也在 mira 表但不是 A 的档位）
    case(
        "C2【C round1 C2 回归】: 回放 round1 事故路径 → deny",
        'mira -p "你是评审方 A（架构师视角），评审 XXX 方案" --model opus4.6',
        expected_exit=2,
        expected_contains=["opus4.6 不在评审方", "opus4.8p"],
    )

    # Case N8【B round2】: --tier=cantus 等号形式 → 放行
    case(
        "N8【B】: --tier=cantus 等号形式 → 放行",
        "ssh root@aetherisonline.xyz 'python3 qoder-bridge.py --tier=cantus \"评审方 C\"'",
        expected_exit=0,
    )

    # Case N9【B round2】: --tier CANTUS 大小写 → 放行（cantus 是真值层，大小写归一）
    case(
        "N9【B】: --tier CANTUS 大小写 → 放行",
        "ssh root@aetherisonline.xyz 'python3 qoder-bridge.py --tier CANTUS \"评审方 C\"'",
        expected_exit=0,
    )

    # Case N8b【B】: --model=opus4.8p 等号形式 → 放行
    case(
        "N8b【B】: --model=opus4.8p 等号形式（评审方 A）→ 放行",
        'mira -p "评审方 A..." --model=opus4.8p',
        expected_exit=0,
    )

    # Case Prefix: deny 消息含 [chain-gate] prefix（A 建议，便于和 review-gate 区分）
    ensure_no_override()
    ec, out = run_hook('mira -p "评审方 A" --model opus4.6', repo_root=REPO_ROOT)
    _record(ec == 2 and "[chain-gate]" in out,
            "Prefix【A】: deny 消息含 [chain-gate] 前缀",
            f"exit={ec} 含prefix={'[chain-gate]' in out}")

    # ===== v2-1: YAML 单源相关 case =====

    # Case V1: 真值层 YAML 缺 reviewers 字段 → fail-closed deny
    tmp_repo_v1 = tempfile.mkdtemp(prefix="chain-v1-")
    specs_v1 = os.path.join(tmp_repo_v1, "governance", "specs")
    os.makedirs(specs_v1, exist_ok=True)
    with open(os.path.join(specs_v1, "reviewer-tiers.yaml"), "w") as f:
        f.write("# 空 YAML\nfoo: bar\n")  # 缺 reviewers 字段
    case(
        "V1【v2-1】: YAML 缺 reviewers 字段 → fail-closed deny",
        'mira -p "评审方 A..." --model opus4.8p',
        expected_exit=2,
        expected_contains=["缺 reviewers 字段"],
        repo_root=tmp_repo_v1,
    )
    try:
        shutil.rmtree(tmp_repo_v1)
    except Exception:
        pass

    # Case L1: lint 脚本检测漂移（spec §二 与 YAML 不一致 → exit 1）
    LINT = os.path.join(REPO_ROOT, "scripts", "check-reviewer-tiers-drift.py")
    if os.path.exists(LINT):
        proc = subprocess.run(["python", LINT], capture_output=True, timeout=15)
        _record(proc.returncode == 0,
                "L1【v2-1 lint】: 真实 repo 一致 → exit 0",
                f"exit={proc.returncode}")
    else:
        _record(False, "L1【v2-1 lint】: 脚本不存在", LINT)

    print("=" * 70)
    print(f"总结: {PASS_COUNT} PASS / {FAIL_COUNT} FAIL")
    print("=" * 70)
    if FAIL_COUNT > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
