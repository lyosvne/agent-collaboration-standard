#!/usr/bin/env python3
"""
Bootstrap Gate -- PreToolUse Hook (SO-12 compact 续接 bootstrap 强制)
=====================================================================
配合 bootstrap-inject-sessionstart.py，强制"动手前必先 bootstrap"。

机制：
  拦 Bash 命令，识别"动手类"操作：
    - mira 评审调度（mira -p + 评审关键字，复用 chain-gate 识别）
    - ECS 操作（scp/rsync/ssh 到 aetherisonline.xyz + apply-*.py，复用 review-gate 识别）
    - 改真值层（cat > reviewer-tiers.yaml/spec/config.json 等写入）
  命中"动手类"时检查 bootstrap 标记（~/.zcode/hooks/.bootstrap-done.json）：
    - 标记缺失 → deny + 提示"先重启 session 或手动 cat 三件套"
    - 标记存在但 session_id 不匹配 + 超过时间窗口 → deny（防旧标记复用）
    - 标记损坏（非合法 JSON）→ deny（fail-closed）
    - 标记存在且有效 → 放行

校验逻辑（双来源，防 ZCODE_SESSION_ID env 缺失）：
  - session_id 优先：标记.session_id == 当前 ZCODE_SESSION_ID → 通过
  - 时间窗口兜底：若无 ZCODE_SESSION_ID env，用 bootstrapped_at_epoch 判
    （默认 8 小时内有效——一个工作日内 bootstrap 过即放行）

幂等性：同 session 多次动手，标记一直在，不重复拦。
"""

import json
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BOOTSTRAP_MARKER = os.path.join(SCRIPT_DIR, ".bootstrap-done.json")

# import 共享模块（M2：truth hash 校验）
try:
    sys.path.insert(0, SCRIPT_DIR)
    from _bootstrap_common import compute_truth_hash, get_session_id, TRUTH_FILES, REPO_ROOT
except Exception as e:
    sys.stderr.write(f"[bootstrap-gate] _bootstrap_common import 失败，退化本地实现: {e}\n")
    _DEFAULT_REPO_FROM_SCRIPT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
    _FALLBACK_REPO = r"C:\Users\Admin\Documents\trae_projects\agent-collaboration-standard"
    _test_yaml = os.path.join(_DEFAULT_REPO_FROM_SCRIPT, "governance", "specs", "reviewer-tiers.yaml")
    REPO_ROOT = os.environ.get("AGENT_COLLABORATION_REPO") or (
        _DEFAULT_REPO_FROM_SCRIPT if os.path.exists(_test_yaml) else _FALLBACK_REPO
    )
    TRUTH_FILES = {
        "reviewer_tiers_yaml": os.path.join(REPO_ROOT, "governance", "specs", "reviewer-tiers.yaml"),
        "spec_review_process": os.path.join(REPO_ROOT, "governance", "specs", "governance-review-process.md"),
        "config_json": os.path.join(REPO_ROOT, ".zcode", "config.json"),
    }
    def get_session_id():
        return os.environ.get("ZCODE_SESSION_ID") or os.environ.get("CLAUDE_SESSION_ID")
    def compute_truth_hash():
        import hashlib
        hashes = {}
        for key, path in TRUTH_FILES.items():
            with open(path, "rb") as f:
                hashes[key] = hashlib.sha256(f.read()).hexdigest()[:16]
        return hashes

REVIEWER_TIERS_YAML = TRUTH_FILES["reviewer_tiers_yaml"]

# round2 M1: 删除 BOOTSTRAP_TTL_SECONDS（时间窗口兜底变 fail-open，三方共识删除）


def load_marker():
    """读 bootstrap 标记。返回 (marker_dict_or_None, reason)。
    - 标记存在且合法 → (dict, "ok")
    - 标记缺失 → (None, "missing")
    - 标记损坏 → (None, "corrupt")
    """
    if not os.path.exists(BOOTSTRAP_MARKER):
        return None, "missing"
    try:
        with open(BOOTSTRAP_MARKER, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return None, "corrupt"
        return data, "ok"
    except (json.JSONDecodeError, OSError):
        return None, "corrupt"


def is_marker_valid(marker):
    """标记是否有效（round2 M1+M2：纯 session_id 校验 + truth hash 比对）。
    返回 (bool, reason)。

    M1（round2 三方共识）：删除 8h 时间窗口兜底（变 fail-open，C 指出恰是 compact 跳链复现路径）。
    M2（round2 三方共识）：加 truth hash 校验（防"读过但读的是旧版"）。
    """
    if not marker:
        return False, "empty"
    # M1: session_id 校验（唯一来源，无时间窗口兜底）
    marker_sid = marker.get("session_id", "")
    current_sid = get_session_id()
    if not current_sid:
        # env 缺失 → deny + 提示重启（fail-closed，不留兜底）
        return False, "no_session_env（重启 session 触发 SessionStart hook 写正确标记）"
    if marker_sid != current_sid:
        return False, f"session_id_mismatch（标记={marker_sid}, 当前={current_sid}）"
    # M2: truth hash 校验（真值已变 → 标记失效）
    marker_hashes = marker.get("truth_hashes", {})
    if not marker_hashes:
        return False, "no_truth_hashes（旧标记 v1 或损坏，需重 bootstrap）"
    try:
        current_hashes = compute_truth_hash()
    except Exception as e:
        # 当前真值读不出来 → 真值损坏 → deny（fail-closed）
        return False, f"truth_read_fail（{e}）"
    for key, h in marker_hashes.items():
        if current_hashes.get(key) != h:
            return False, f"truth_drift（{key} 已变，需重 bootstrap）"
    return True, "session_id_match+truth_hash_match"


def load_reviewer_keywords():
    """从 reviewer-tiers.yaml 读评审关键字（复用 chain-gate 模式）"""
    if not os.path.exists(REVIEWER_TIERS_YAML):
        return []
    try:
        import yaml
        with open(REVIEWER_TIERS_YAML, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f.read()) or {}
        kws = []
        for info in (data.get("reviewers", {}) or {}).values():
            if isinstance(info, dict):
                kw = info.get("dispatch_keyword")
                if kw:
                    kws.append(kw)
        kws += data.get("review_dispatch_extra_keywords", []) or []
        return [k for k in kws if k]
    except Exception:
        return []


def is_action_command(command, keywords):
    """判命令是否"动手类"（需要 bootstrap 保护）。
    动手类 = 会改系统状态或调外部资源的操作：
    - mira 评审调度（mira -p + 评审关键字）
    - ECS 操作（ssh/scp/rsync 到 aetherisonline.xyz + apply-*.py）
    - 改真值层（写 reviewer-tiers.yaml / governance-review-process.md / config.json）
    不拦：只读（cat/git log/ls/grep）、mira 非评审调度、普通 shell

    M5（round2）：正则补全——含无空格重定向 + cp/mv/install/truncate/tee/sed -i/python open(w/a) + 编辑器。
    威胁模型边界：防诚实健忘，不防主动规避（变量拼接/eval/bash -c curl 漏判，是设计边界）。
    """
    cmd_lower = command.lower()
    # 1. mira 评审调度（复用 chain-gate 识别）
    if re.search(r"\bmira\s+(-p|--print)\b", command, re.IGNORECASE):
        if any(kw.lower() in cmd_lower for kw in keywords):
            return True, "mira 评审调度"
        return False, None  # mira 但非评审，不拦
    # 2. ECS 操作（ssh/scp/rsync 到 aetherisonline.xyz 或 apply-*.py）
    if "aetherisonline.xyz" in cmd_lower:
        return True, "ECS 操作（aetherisonline.xyz）"
    if re.search(r"\bapply-\S*\.py\b", command):
        return True, "ECS patch（apply-*.py）"
    # 3. 改真值层（M5: 正向列举写入动作，含无空格重定向）
    truth_patterns = [
        r"reviewer-tiers\.yaml",
        r"governance-review-process\.md",
        r"\.zcode[\\/]config\.json",
    ]
    # M5: 写入动作正则清单（round2 补全）
    write_action_patterns = [
        r">+\s*\S",                                    # 重定向 >file / > file / >> append
        r"\btee\b",                                    # tee
        r"\bcp\b",                                     # cp（覆盖）
        r"\bmv\b",                                     # mv（覆盖/重命名）
        r"\binstall\b\s+-m",                           # install -m
        r"\btruncate\b",                               # truncate
        r"\bsed\s+-i\b",                               # sed -i 原地改
        r"\bpython\d?\s+-c\b[^|]*open\s*\([^)]*['\"][wa]",  # python -c "...open(...,'w/a')"
        r"\bvim\b|\bnano\b|\bemacs\b|\bgedit\b|\bcode\s+-w\b",  # 编辑器
    ]
    for pat in truth_patterns:
        if re.search(pat, command):
            for wpat in write_action_patterns:
                if re.search(wpat, command, re.IGNORECASE):
                    return True, f"改真值层（{pat} + 写入动作）"
    return False, None


def build_deny_reason(detail):
    manual_marker_cmd = (
        f'python -c "import json,time; '
        f"json.dump({{'session_id':'manual','bootstrapped_at_epoch':time.time()}}, "
        f"open(r'{BOOTSTRAP_MARKER}','w'))\""
    )
    return (
        f"⚠️ **[bootstrap-gate] 动手前未完成 bootstrap（SO-12）**\n\n"
        f"{detail}\n\n"
        f"**为何阻断**: compact 续接后真值信息有损，必须先 bootstrap 再动手——"
        f"这是 SO-11-v2-2 M1/M2 思路（显式 + fail-closed）在 session bootstrap 层的应用。\n\n"
        f"**修复**: \n"
        f"  1. 重启 session（SessionStart hook 会自动注入真值三件套 + 写标记），或\n"
        f"  2. 手动 `cat governance/specs/reviewer-tiers.yaml` + `cat .zcode/config.json` "
        f"+ 读 spec §二 确认调用方式，然后写标记：\n"
        f"     `{manual_marker_cmd}`\n\n"
        f"**威胁模型**: 防忘记（compact 后忘真值），不防恶意（手动伪造标记可绕过）。"
    )


def main():
    try:
        raw = sys.stdin.buffer.read()
        hook_input = json.loads(raw.decode("utf-8", errors="replace"))
    except Exception:
        return

    if hook_input.get("tool_name", "") != "Bash":
        return
    command = hook_input.get("tool_input", {}).get("command", "")
    if not command:
        return

    keywords = load_reviewer_keywords()
    is_action, action_type = is_action_command(command, keywords)
    if not is_action:
        return  # 非动手类，放行（不拦只读）

    # 检查 bootstrap 标记
    marker, reason = load_marker()
    if reason == "corrupt":
        print(json.dumps({
            "decision": "block",
            "reason": build_deny_reason(
                f"bootstrap 标记文件损坏（{BOOTSTRAP_MARKER} 非合法 JSON）。"
                f"动手类型: {action_type}。请删除标记文件后重启 session。"
            ),
        }, ensure_ascii=False))
        sys.exit(2)
    if reason == "missing":
        print(json.dumps({
            "decision": "block",
            "reason": build_deny_reason(
                f"bootstrap 标记缺失（SessionStart hook 未跑或失败）。"
                f"动手类型: {action_type}。"
            ),
        }, ensure_ascii=False))
        sys.exit(2)

    # 标记存在，校验有效性
    valid, vreason = is_marker_valid(marker)
    if not valid:
        print(json.dumps({
            "decision": "block",
            "reason": build_deny_reason(
                f"bootstrap 标记无效（{vreason}）。"
                f"标记 session_id={marker.get('session_id','?')}, "
                f"当前 session_id={get_session_id()}。"
                f"动手类型: {action_type}。请重启 session 重新 bootstrap。"
            ),
        }, ensure_ascii=False))
        sys.exit(2)
    # 有效，放行


if __name__ == "__main__":
    main()
