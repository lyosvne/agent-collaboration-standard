#!/usr/bin/env python3
"""
Session Gate -- PreToolUse Hook (SO-11-v2-2 会话续接)
=======================================================
强制 spec §二.2.2：同一评审项目 roundN 调 mira A/B 必须用 -r 续接 roundN-1。

用户需求："本项目所有评审的 Mira 调用归类为一个项目，同一会话续接有上下文。"

机制（round2 修复后，A/B/C 三方共识 M1-M5）：
  拦 Bash 命令，识别 mira 评审调度（mira -p + 评审方关键字）。
  命中"评审方"字样后进入严格模式，要求调度元数据齐备：

  M1（项目识别 fail-closed）:
    CURRENT_REVIEW_PROJECT 环境变量未设 → deny（删兜底扫描，最坏失败是续接错误会话）

  M2（round 显式参数）:
    CURRENT_REVIEW_ROUND 环境变量未设 → deny（regex 抓首个 round 被 prompt 描述历史绕过）
    命令文本里的 round 号仅作交叉校验 warn，不作判据

  M3（配置缺失 fail-closed + 威胁模型分层）:
    session_continuity 节点缺失/损坏/enabled 非 bool → deny（配置删除即绕过机制）
    session_continuity.enabled: false 显式禁用 → 放行（保留紧急制动）
    命令完全无"评审方"字样 → 非评审调用，放行（真边界）

  M5（session 过期降级通道）:
    roundN-1 在 index 的 expired_rounds 列表 → 放行 fresh
    但 stderr 提示"prompt 必须内嵌上轮结论摘要"（补偿上下文）

  通过 M1/M2 后，查 archive/review-sessions-index.yaml 当前项目 reviewer 的 roundN-1 session_id：
  - 有 sid 且本次没用 -r → deny + 提示正确 id
  - 用了 -r 但 id 不匹配 → deny
  - 首轮/归档/无记录/过期 → 放行

实测 mira -r 跨进程续接可用（2026-07-25）。
"""

import json
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

_DEFAULT_REPO_FROM_SCRIPT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
_FALLBACK_REPO = r"C:\Users\Admin\Documents\trae_projects\agent-collaboration-standard"
_test_yaml = os.path.join(_DEFAULT_REPO_FROM_SCRIPT, "governance", "specs", "reviewer-tiers.yaml")
REPO_ROOT = os.environ.get("AGENT_COLLABORATION_REPO") or (
    _DEFAULT_REPO_FROM_SCRIPT if os.path.exists(_test_yaml) else _FALLBACK_REPO
)
REVIEWER_TIERS_YAML = os.path.join(REPO_ROOT, "governance", "specs", "reviewer-tiers.yaml")


def load_yaml(path):
    if not os.path.exists(path):
        return None, f"不存在: {path}"
    try:
        import yaml
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f.read()), "ok"
    except Exception as e:
        return None, f"解析失败: {e}"


def get_session_continuity_config():
    """从 reviewer-tiers.yaml 读 session_continuity 配置"""
    data, _ = load_yaml(REVIEWER_TIERS_YAML)
    if not data:
        return None
    return data.get("session_continuity")


def is_mira_review_dispatch(command, config_data):
    """复用 chain-gate 识别逻辑：mira -p + 评审关键字。
    invocation_pattern 用硬编码 fallback（chain-gate 已校验档位，本 hook 只关心续接）"""
    if not re.search(r"\bmira\s+(-p|--print)\b", command, re.IGNORECASE):
        return False
    reviewers = config_data.get("reviewers", {}) if config_data else {}
    keywords = [info.get("dispatch_keyword") for info in reviewers.values() if isinstance(info, dict)]
    keywords += config_data.get("review_dispatch_extra_keywords", []) or []
    keywords = [k for k in keywords if k]
    return any(kw.lower() in command.lower() for kw in keywords)


def identify_reviewer(command, config_data):
    """识别命令调的是 A 还是 B（用 dispatch_keyword）"""
    cmd_lower = command.lower()
    reviewers = config_data.get("reviewers", {}) if config_data else {}
    found = set()
    for r_id, info in reviewers.items():
        if not isinstance(info, dict):
            continue
        kw = info.get("dispatch_keyword", "")
        if kw and kw.lower() in cmd_lower:
            found.add(r_id)
    return found


def extract_resume_id(command, config):
    """从命令提取 -r <id> 值，无则 None"""
    resume_arg = config.get("resume_arg", "-r") if config else "-r"
    # 支持 -r X 和 -r=X 两种
    pat = re.compile(re.escape(resume_arg) + r'(?:=|\s+)(\S+)', re.IGNORECASE)
    m = pat.search(command)
    return m.group(1).strip().strip("'\"") if m else None


def identify_current_round_from_env(config):
    """M2: 从环境变量读当前 round（真值源）。
    返回 (round_int_or_None, reason_str)。
    - 环境变量已设且合法 → (int, "ok")
    - 环境变量未设 → (None, "env_missing")  ← 调用方应 deny
    - 环境变量设了但不是数字 → (None, "env_invalid")
    """
    env_key = config.get("current_round_env", "CURRENT_REVIEW_ROUND") if config else "CURRENT_REVIEW_ROUND"
    val = os.environ.get(env_key)
    if not val:
        return None, "env_missing"
    # 支持 "round2" / "2" 两种写法
    m = re.search(r'(\d+)', val)
    if not m:
        return None, f"env_invalid({val})"
    return int(m.group(1)), "ok"


def scan_round_in_command(command):
    """M2 交叉校验: 从命令文本抓 round 号（仅作 warn，不作判据）。
    返回首个匹配的 round int 或 None。控制平面（环境变量）才是真值。"""
    m = re.search(r'\bround[_\s]*(\d+)\b', command, re.IGNORECASE)
    return int(m.group(1)) if m else None


def find_current_project(config):
    """M1: 从环境变量读当前评审项目（唯一来源，不兜底扫描）。
    返回 (project_str_or_None, reason_str)。
    - 环境变量已设 → (str, "ok")
    - 未设 → (None, "env_missing")  ← 调用方应 deny
    """
    env_key = config.get("current_project_env", "CURRENT_REVIEW_PROJECT") if config else "CURRENT_REVIEW_PROJECT"
    project = os.environ.get(env_key)
    if project:
        return project, "ok"
    return None, "env_missing"


def find_prev_session_id(project, reviewer, current_round, config):
    """从 review-sessions-index.yaml 查当前项目 reviewer 的 roundN-1 session_id。
    返回 (sid_or_None, reason_str)：
    - (sid, "ok")               : 有 roundN-1 sid，需校验 -r
    - (None, "expired")         : roundN-1 在 expired_rounds 里，放行 fresh（M5）
    - (None, "archived")        : 项目已归档，放行
    - (None, "no_prev_sid")     : roundN-1 无记录（真首轮或记录缺失），放行
    - (None, "index_不可读")    : index 损坏
    - (None, "project_not_in_index"): 项目未登记
    """
    if not project or current_round is None or current_round <= 1:
        return None, "first_round"  # 首轮，无需续接
    prev_round = current_round - 1
    index_path = os.path.join(REPO_ROOT, config.get("record_index", "archive/review-sessions-index.yaml"))
    data, _ = load_yaml(index_path)
    if not data:
        return None, "index_不可读"
    projects = data.get("projects", []) or []
    for p in projects:
        if p.get("project") == project:
            status = p.get("status", "")
            if status == config.get("archived_status", "ARCHIVED"):
                return None, "archived"  # 归档项目放行
            # M5: 检查 roundN-1 是否在 expired_rounds 里（项目级字段，所有 reviewer 共享）
            expired_field = config.get("expired_rounds_field", "expired_rounds")
            expired_rounds = p.get(expired_field, []) or []
            if isinstance(expired_rounds, list) and prev_round in expired_rounds:
                return None, "expired"  # 上轮已过期，放行 fresh（M5）
            sessions = p.get("reviewer_sessions", {}) or {}
            reviewer_chain = sessions.get(reviewer, {}) or {}
            sid = reviewer_chain.get(f"round{prev_round}")
            if sid is None:
                return None, "no_prev_sid"
            return sid, "ok"
    return None, "project_not_in_index"


def build_deny_reason(detail):
    return (
        f"⚠️ **[session-gate] 会话续接阻断（SO-11-v2-2）**\n\n"
        f"{detail}\n\n"
        f"**为何阻断**: spec §二.2.2——同一评审项目 roundN 必须用 -r 续接 roundN-1 的 session_id，"
        f"让 A/B 有项目内记忆（不重复指出已修问题）。\n\n"
        f"**真值层**: archive/review-sessions-index.yaml\n"
        f"**记录**: 每轮 mira 调用完成后，把 json 输出的 session_id 回填到 index 对应 round 字段"
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

    # 读配置
    config_data, err = load_yaml(REVIEWER_TIERS_YAML)
    if config_data is None:
        return  # 真值层失败由 chain-gate 处理（本 hook 不重复 fail-closed）

    sc_config = config_data.get("session_continuity", {})
    # M3: session_continuity 节点缺失/损坏 → deny（配置删除即绕过机制）
    # 但 enabled: false 显式禁用 → 放行（保留紧急制动能力，C 修正版）
    if not isinstance(sc_config, dict) or not sc_config:
        print(json.dumps({
            "decision": "block",
            "reason": build_deny_reason(
                "reviewer-tiers.yaml 的 session_continuity 节点缺失或损坏（非 dict/空）。\n"
                "这是配置异常，不是显式禁用——防配置删除即绕过机制（M3，round2 三方共识）。\n"
                "若要紧急禁用，请显式设 `session_continuity.enabled: false`。"
            ),
        }, ensure_ascii=False))
        sys.exit(2)
    # enabled 字段必须是 bool（lint 也校验，但 hook 兜底）
    enabled = sc_config.get("enabled")
    if not isinstance(enabled, bool):
        print(json.dumps({
            "decision": "block",
            "reason": build_deny_reason(
                f"session_continuity.enabled 必须是 bool，当前: {type(enabled).__name__}={enabled!r}（M3）。\n"
                "若要禁用，请设 `enabled: false`（bool）。"
            ),
        }, ensure_ascii=False))
        sys.exit(2)
    if not enabled:
        return  # 显式禁用，放行（紧急制动）

    # 只拦 mira 评审调度
    if not is_mira_review_dispatch(command, config_data):
        return

    # 识别评审方（A/B/C）
    reviewers_in_cmd = identify_reviewer(command, config_data)
    if not reviewers_in_cmd:
        return  # 命令完全无"评审方"字样 → 非评审调用，放行（M3 真边界）

    # ===== M1/M2: 严格模式（命中"评审方"字样后，项目/round 元数据必须齐备）=====
    problems = []

    # M1: CURRENT_REVIEW_PROJECT 必填
    project, proj_reason = find_current_project(sc_config)
    if proj_reason == "env_missing":
        problems.append(
            f"未设环境变量 CURRENT_REVIEW_PROJECT（M1，round2 三方共识：删兜底扫描，最坏失败是续接错误会话）。\n"
            f"调评审前请内联注入：`CURRENT_REVIEW_PROJECT=<项目名> mira -p ...`"
        )

    # M2: CURRENT_REVIEW_ROUND 必填
    current_round, round_reason = identify_current_round_from_env(sc_config)
    if round_reason == "env_missing":
        problems.append(
            f"未设环境变量 CURRENT_REVIEW_ROUND（M2，round2 三方共识：regex 抓首个 round 被 prompt 描述历史绕过）。\n"
            f"调评审前请内联注入：`CURRENT_REVIEW_ROUND=<N> mira -p ...`（如 round2 则设 2）"
        )
    elif round_reason.startswith("env_invalid"):
        problems.append(
            f"CURRENT_REVIEW_ROUND 值非法（{round_reason}），必须是数字或 roundN 格式（M2）。"
        )

    # M2 交叉校验：环境变量与命令文本里的 round 不一致 → warn（写入 stderr，不 deny）
    # （prompt 可能描述历史 round，不一致不一定是错，只提示）
    if current_round is not None:
        cmd_round = scan_round_in_command(command)
        if cmd_round is not None and cmd_round != current_round:
            sys.stderr.write(
                f"[session-gate] M2 交叉校验 warn: CURRENT_REVIEW_ROUND={current_round} "
                f"但命令文本含 round{cmd_round}（可能是描述历史，请确认环境变量正确）\n"
            )

    # 项目/round 不齐 → 直接 deny（M1/M2 fail-closed），不进入 session 查询
    if problems:
        print(json.dumps({
            "decision": "block",
            "reason": build_deny_reason("\n".join(f"- {p}" for p in problems)),
        }, ensure_ascii=False))
        sys.exit(2)

    # ===== session 续接校验（项目/round 都齐备后）=====
    for r in reviewers_in_cmd:
        # 只对 mira 平台且在 platforms_with_continuity 内的评审方校验
        reviewer_info = config_data.get("reviewers", {}).get(r, {})
        if not isinstance(reviewer_info, dict):
            continue
        platform = reviewer_info.get("platform", "")
        continuity_platforms = sc_config.get("platforms_with_continuity", [])
        if not any(p in platform for p in continuity_platforms):
            continue  # C (qoder) 不校验续接

        prev_sid, reason = find_prev_session_id(project, r, current_round, sc_config)
        if reason in ("archived", "first_round", "no_prev_sid", "project_not_in_index"):
            continue  # 归档/首轮/无记录/未登记 → 放行
        if reason == "expired":
            # M5: 上轮 session 过期，放行 fresh，但提示 prompt 必须内嵌上轮结论
            sys.stderr.write(
                f"[session-gate] M5: 评审方 {r} round{current_round-1} session 已过期"
                f"（在 expired_rounds 里），本次放行 fresh。"
                f"**评审 prompt 必须内嵌 round{current_round-1} 结论摘要**"
                f"（补偿上下文，对齐北极星终局第 4 条）。\n"
            )
            continue
        if reason == "index_不可读":
            problems.append(
                f"评审方 {r}: review-sessions-index.yaml 不可读（M5 降级失败），需修复 index 或登记 expired_rounds"
            )
            continue
        # reason == "ok"，有 prev_sid，校验 -r
        used_sid = extract_resume_id(command, sc_config)
        if not used_sid:
            problems.append(
                f"评审方 {r} round{current_round} 未用 -r 续接。"
                f"应加 `-{sc_config.get('resume_arg', 'r').lstrip('-')} {prev_sid}` "
                f"（round{current_round-1} 的 session_id）。"
                f"若该 session 已过期，在 index 的 expired_rounds 加 {current_round-1} 后可 fresh。"
            )
        elif used_sid != prev_sid:
            problems.append(
                f"评审方 {r} round{current_round} 的 -r {used_sid} 与 round{current_round-1} "
                f"session_id ({prev_sid}) 不匹配"
            )

    if problems:
        print(json.dumps({
            "decision": "block",
            "reason": build_deny_reason("\n".join(f"- {p}" for p in problems)),
        }, ensure_ascii=False))
        sys.exit(2)


if __name__ == "__main__":
    main()
