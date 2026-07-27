#!/usr/bin/env python3
"""
Session Gate -- PreToolUse Hook (SO-11-v2-2 会话续接)
=======================================================
强制 spec §二.2.2：同一评审项目 roundN 调 mira A/B 必须用 -r 续接 roundN-1。

用户需求："本项目所有评审的 Mira 调用归类为一个项目，同一会话续接有上下文。"

机制：
  拦 Bash 命令，识别 mira 评审调度（复用 chain-gate 的 YAML 真值层读取），
  查 archive/review-sessions-index.yaml 当前项目的 roundN-1 session_id：
  - 有 session_id 且本次没用 -r → deny + 提示正确 id
  - 用了 -r 但 id 不匹配 → deny + 提示正确 id
  - 首轮（无 roundN-1）/ 项目 ARCHIVED → 放行

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


def identify_current_round(command):
    """从命令文本粗略识别当前是 round 几（prompt 里通常含 roundN 字样）"""
    m = re.search(r'\bround[_\s]*(\d+)\b', command, re.IGNORECASE)
    if m:
        return int(m.group(1))
    return None


def find_current_project(config):
    """识别当前评审项目名。优先环境变量，兜底扫最近改动的 archive 目录"""
    env_key = config.get("current_project_env", "CURRENT_REVIEW_PROJECT") if config else "CURRENT_REVIEW_PROJECT"
    project = os.environ.get(env_key)
    if project:
        return project
    # 兜底：扫 archive/governance-review-* 找最近改动的
    archive_dir = os.path.join(REPO_ROOT, "archive")
    if not os.path.isdir(archive_dir):
        return None
    candidates = []
    for d in os.listdir(archive_dir):
        full = os.path.join(archive_dir, d)
        if d.startswith("governance-review-") and os.path.isdir(full):
            try:
                mtime = os.path.getmtime(full)
                candidates.append((mtime, d.replace("governance-review-", "")))
            except OSError:
                pass
    if not candidates:
        return None
    candidates.sort(reverse=True)  # 最近改动优先
    return candidates[0][1]


def find_prev_session_id(project, reviewer, current_round, config):
    """从 review-sessions-index.yaml 查当前项目 reviewer 的 roundN-1 session_id"""
    if not project or current_round is None or current_round <= 1:
        return None, None  # 首轮，无需续接
    prev_round = current_round - 1
    index_path = os.path.join(REPO_ROOT, config.get("record_index", "archive/review-sessions-index.yaml"))
    data, _ = load_yaml(index_path)
    if not data:
        return None, "index 不可读"
    projects = data.get("projects", []) or []
    for p in projects:
        if p.get("project") == project:
            status = p.get("status", "")
            if status == config.get("archived_status", "ARCHIVED"):
                return None, "archived"  # 归档项目不强制续接
            sessions = p.get("reviewer_sessions", {}) or {}
            reviewer_chain = sessions.get(reviewer, {}) or {}
            sid = reviewer_chain.get(f"round{prev_round}")
            return sid, "ok"
    return None, "project 不在 index"


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
    if not sc_config or not sc_config.get("enabled"):
        return  # 未启用

    # 只拦 mira 评审调度
    if not is_mira_review_dispatch(command, config_data):
        return

    # 识别评审方（A/B）
    reviewers_in_cmd = identify_reviewer(command, config_data)
    if not reviewers_in_cmd:
        return  # 识别不出评审方，由 chain-gate 处理

    # 识别当前 round
    current_round = identify_current_round(command)
    if current_round is None:
        return  # 命令里没标 round，无法判定（放行，靠 ZCode 自觉标 round）

    # 查上一轮 session_id
    project = find_current_project(sc_config)
    problems = []
    for r in reviewers_in_cmd:
        # 只对 mira 平台且在 platforms_with_continuity 内的评审方校验
        reviewer_info = config_data.get("reviewers", {}).get(r, {})
        if not isinstance(reviewer_info, dict):
            continue
        platform = reviewer_info.get("platform", "")
        continuity_platforms = sc_config.get("platforms_with_continuity", [])
        if not any(p in platform for p in continuity_platforms):
            continue  # C (qoder) 不校验
        prev_sid, reason = find_prev_session_id(project, r, current_round, sc_config)
        if reason == "archived":
            continue  # 归档项目放行
        if prev_sid is None:
            continue  # 无 roundN-1 记录（可能是真首轮或记录缺失），放行
        # 有 prev_sid，校验本次命令是否用了正确的 -r
        used_sid = extract_resume_id(command, sc_config)
        if not used_sid:
            problems.append(
                f"评审方 {r} round{current_round} 未用 -r 续接。"
                f"应加 `-{sc_config.get('resume_arg', 'r').lstrip('-')} {prev_sid}` "
                f"（round{current_round-1} 的 session_id）"
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
