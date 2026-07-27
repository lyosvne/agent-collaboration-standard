#!/usr/bin/env python3
"""
Chain Gate -- PreToolUse Hook (SO-11)
======================================
强制执行 governance-review-process.md §二.2.1：调度评审方时档位必须与真值层一致。

背景：meta-review-gate round1 误把 opus4.8p 换成 opus4.6（mira --help 列表滞后），
spec §二.2.1 已约束靠自觉，本 hook 机制化（不靠自觉）。

机制：
  拦 Bash 命令，识别"评审调度"（mira -p + 评审关键字 / qoder-bridge --tier cantus），
  校验 --model / --tier 与真值层（spec §二表格）一致。不一致 → exit 2 deny。

威胁模型：防忘记（agent 用默认档 / 凭 --help 列表换档），不防恶意（agent 改措辞绕关键字识别）。
"""

import json
import os
import re
import sys
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OVERRIDE_FILE = os.path.join(SCRIPT_DIR, ".chain-gate-override.json")

# repo root 推断：
# 1. 环境变量优先（测试用）
# 2. hook 在 <repo>/.zcode/hooks/ 时，向上两级是 repo root
# 3. fallback 到默认 repo 路径（hook 在 ~/.zcode/hooks/ 全局副本时，SCRIPT_DIR 推断会指向 ~）
_DEFAULT_REPO_FROM_SCRIPT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
_FALLBACK_REPO = r"C:\Users\Admin\Documents\trae_projects\agent-collaboration-standard"
# v2-1: 检查 SCRIPT_DIR 推断的 repo 是否真有 reviewer-tiers.yaml（机器源），无则用 fallback
_test_yaml = os.path.join(_DEFAULT_REPO_FROM_SCRIPT, "governance", "specs", "reviewer-tiers.yaml")
REPO_ROOT = os.environ.get("AGENT_COLLABORATION_REPO") or (
    _DEFAULT_REPO_FROM_SCRIPT if os.path.exists(_test_yaml) else _FALLBACK_REPO
)
# v2-1: 真值层从 YAML 单源读（取代 spec markdown 解析）
REVIEWER_TIERS_YAML = os.path.join(REPO_ROOT, "governance", "specs", "reviewer-tiers.yaml")
SPEC_MIRA_STATUS = os.path.join(REPO_ROOT, "governance", "specs", "mira-integration-status.md")

# mira -p / mira --print 调度（v2-1 round2: 仍保留模块级正则，但实际值从 YAML dispatchers 读）
# 这些是 fallback 默认值，YAML dispatchers 节点优先
_DEFAULT_MIRA_INVOCATION = r"\bmira\s+(-p|--print)\b"
_DEFAULT_MIRA_MODEL = r"--model(?:=|\s+)(\S+)"
_DEFAULT_QODER_TIER = r"--tier(?:=|\s+)(\S+)"

# mira-integration-status 档位表行（旁路健康检查用，不数据化，属 hook 协议）
MIRA_TIERS_ROW_PATTERN = re.compile(
    r"\|\s*\*\*Cloud-O\s*\(Claude\)\s*\*\*\s*\|\s*([^|]+)\|", re.IGNORECASE
)
GPT_TIERS_ROW_PATTERN = re.compile(
    r"\|\s*\*\*GPT\s*\*\*\s*\|\s*([^|]+)\|", re.IGNORECASE
)


# ===== 真值层读取（v2-1: YAML 单源）=====

# 模块级缓存（hook 每次调用重启进程，缓存是为单次调用内多次访问）
_CACHED_YAML = None
_CACHED_YAML_ERR = None


def load_truth_layer():
    """v2-1: 从 reviewer-tiers.yaml 读真值层（取代 spec markdown 解析）。

    返回: (data: dict, error: str)
      data = {
        "reviewers": {"A": {"tier":..., "platform":..., "dispatch_keyword":...}, ...},
        "review_keywords": [...],  # 所有 dispatch_keyword + extra
        "qoder_patterns": [...],   # C 的 dispatch_command_pattern
      }
    """
    global _CACHED_YAML, _CACHED_YAML_ERR
    if _CACHED_YAML is not None or _CACHED_YAML_ERR is not None:
        return _CACHED_YAML, _CACHED_YAML_ERR

    if not os.path.exists(REVIEWER_TIERS_YAML):
        _CACHED_YAML_ERR = f"真值层 YAML 不存在: {REVIEWER_TIERS_YAML}"
        return None, _CACHED_YAML_ERR
    try:
        with open(REVIEWER_TIERS_YAML, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        _CACHED_YAML_ERR = f"读真值层 YAML 失败: {e}"
        return None, _CACHED_YAML_ERR

    try:
        import yaml
        raw = yaml.safe_load(content)
    except ImportError:
        _CACHED_YAML_ERR = "pyyaml 未安装"
        return None, _CACHED_YAML_ERR
    except Exception as e:
        _CACHED_YAML_ERR = f"YAML 解析失败: {e}"
        return None, _CACHED_YAML_ERR

    if not isinstance(raw, dict) or "reviewers" not in raw:
        _CACHED_YAML_ERR = "YAML 缺 reviewers 字段"
        return None, _CACHED_YAML_ERR

    reviewers = raw["reviewers"]
    # 收集所有 dispatch_keyword（评审方标识）+ extra keywords（评审信号）
    review_keywords = []
    for r_id, info in reviewers.items():
        if not isinstance(info, dict):
            continue
        kw = info.get("dispatch_keyword")
        if kw:
            review_keywords.append(kw)
    # C 的 qoder pattern 现在在 dispatchers.qoder_cantus（v2-1 round2 schema 重构）
    qoder_patterns = []
    dispatchers = raw.get("dispatchers", {}) or {}
    qoder_cantus = dispatchers.get("qoder_cantus", {})
    if isinstance(qoder_cantus, dict):
        inv_pat = qoder_cantus.get("invocation_pattern")
        if inv_pat:
            qoder_patterns.append(inv_pat)
    # 额外关键字（评审信号但非评审方标识，不参与 reviewer 识别）
    for extra in raw.get("review_dispatch_extra_keywords", []) or []:
        review_keywords.append(extra)

    _CACHED_YAML = {
        "reviewers": reviewers,
        "review_keywords": review_keywords,
        "qoder_patterns": qoder_patterns,
        "dispatchers": raw.get("dispatchers", {}) or {},
    }
    return _CACHED_YAML, "ok"


def load_mira_known_tiers():
    """从 mira-integration-status.md 解析 A/B 档位的可达列表（旁路健康检查）。

    v2-1: 仍读 markdown（平台能力清单，更新频率低，hook 仅作"档位是否存在"检查）
    """
    if not os.path.exists(SPEC_MIRA_STATUS):
        return None, f"mira-integration-status 不存在: {SPEC_MIRA_STATUS}"
    try:
        with open(SPEC_MIRA_STATUS, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        return None, f"读 mira-integration-status 失败: {e}"

    all_tiers = set()
    for m in MIRA_TIERS_ROW_PATTERN.finditer(content):
        for t in re.split(r"[/,]", m.group(1)):
            t = t.strip().strip("*` ")
            if re.match(r"^opus[\d.]+[a-z]?$", t, re.IGNORECASE):
                all_tiers.add(t.lower())
    for m in GPT_TIERS_ROW_PATTERN.finditer(content):
        for t in re.split(r"[/,]", m.group(1)):
            t = t.strip().strip("*` ")
            if re.match(r"^gpt[\d.]+[a-z]*$", t, re.IGNORECASE):
                all_tiers.add(t.lower())
    return all_tiers, "ok"


# ===== 评审调度识别（v2-1: 从 YAML 动态读关键字）=====


def _get_dispatcher_pattern(platform_key, field, default):
    """从 YAML dispatchers 读 pattern，失败用默认值"""
    data, _ = load_truth_layer()
    if data is None:
        return default
    pat = data.get("dispatchers", {}).get(platform_key, {}).get(field)
    return pat if pat else default


def is_mira_review_dispatch(command):
    """判命令是否为 mira 评审调度（mira -p + 含评审关键字）"""
    # invocation_pattern 从 YAML dispatchers.mira 读（v2-1 round2）
    pat = _get_dispatcher_pattern("mira", "invocation_pattern", _DEFAULT_MIRA_INVOCATION)
    if not re.search(pat, command, re.IGNORECASE):
        return False
    data, err = load_truth_layer()
    if data is None:
        return False
    keywords = data["review_keywords"]
    return any(kw.lower() in command.lower() for kw in keywords)


def is_qoder_review_dispatch(command):
    """判命令是否为 qoder C 评审调度（从 YAML 读 dispatch_command_pattern）"""
    data, err = load_truth_layer()
    if data is None:
        return False
    for pat in data["qoder_patterns"]:
        if re.search(pat, command, re.IGNORECASE):
            return True
    return False


def extract_mira_model(command):
    pat = _get_dispatcher_pattern("mira", "model_arg_pattern", _DEFAULT_MIRA_MODEL)
    m = re.search(pat, command, re.IGNORECASE)
    return m.group(1).strip().strip("'\"") if m else None


def extract_qoder_tier(command):
    pat = _get_dispatcher_pattern("qoder_cantus", "tier_arg_pattern", _DEFAULT_QODER_TIER)
    m = re.search(pat, command, re.IGNORECASE)
    return m.group(1).strip().strip("'\"") if m else None


# ===== 校验 =====

def check_truth_layer_consistency(reviewers, known_tiers):
    """C round1 C1：YAML 的 A/B 档位必须在 mira-integration-status 档位表里。

    v2-1: 真值层从 YAML 读，但仍用 mira markdown 做旁路健康检查。
    不一致 → fail-closed（编队被多源漂移坑过 3 次，治理工具自己必须自检）。
    """
    if not reviewers:
        return False, "YAML reviewers 为空"
    if not known_tiers:
        return False, "mira-integration-status 档位表为空或不可读"

    inconsistent = []
    for r_id, info in reviewers.items():
        if not isinstance(info, dict):
            continue
        if info.get("platform") == "mira":  # 只校验 mira 平台档位（A/B）
            tier = info.get("tier", "")
            if tier.lower() not in known_tiers:
                inconsistent.append(f"{r_id}={tier}（YAML 有但 mira-integration-status 无）")
    if inconsistent:
        return False, (
            f"真值层双源不一致: {'; '.join(inconsistent)}。"
            f"先对齐 reviewer-tiers.yaml 与 mira-integration-status.md 再调度（编队历史病灶：多源漂移）。"
        )
    return True, "ok"


def check_mira_alignment(command, reviewers):
    """校验 mira 评审调度的 --model 是否与 YAML 真值层一致。"""
    cmd_lower = command.lower()
    reviewers_in_cmd = set()
    for r_id, info in reviewers.items():
        if not isinstance(info, dict):
            continue
        if info.get("platform") != "mira":
            continue
        kw = info.get("dispatch_keyword", "")
        if kw and kw.lower() in cmd_lower:
            reviewers_in_cmd.add(r_id)

    if not reviewers_in_cmd:
        return False, (
            "命令含评审信号但无法识别具体评审方（dispatch_keyword 均未命中）。"
            "必须在 prompt 里显式标注评审方（如'你是评审方 A'），不能只写档位名。"
        )

    model = extract_mira_model(command)
    if not model:
        expected = " 或 ".join(reviewers[r]["tier"] for r in sorted(reviewers_in_cmd))
        return False, (
            f"评审调度（{sorted(reviewers_in_cmd)}）必须显式 --model，"
            f"不能用默认档（防 mira --help 列表滞后导致跳链）。"
            f"期望 --model {expected}（reviewer-tiers.yaml 真值层）。"
        )

    expected_models = {reviewers[r]["tier"].lower() for r in reviewers_in_cmd if "tier" in reviewers[r]}
    if model.lower() not in expected_models:
        expected_str = " 或 ".join(sorted(expected_models))
        return False, (
            f"--model {model} 不在评审方 {sorted(reviewers_in_cmd)} 的真值层档位（{expected_str}）。"
            f"若真值层过期，请改 reviewer-tiers.yaml（+ spec §二 + mira-integration-status.md，跑 lint），"
            f"不要自行换档。紧急场景写 override 文件：{OVERRIDE_FILE}"
        )
    return True, "ok"


def check_qoder_alignment(command, reviewers):
    """校验 qoder C 调度的 --tier 是否为 YAML 真值层的 cantus。"""
    tier = extract_qoder_tier(command)
    c_info = reviewers.get("C", {})
    expected = c_info.get("tier", "cantus").lower() if isinstance(c_info, dict) else "cantus"
    if not tier:
        return False, f"qoder-bridge 评审调度必须显式 --tier {expected}"
    if tier.lower() != expected:
        return False, (
            f"--tier {tier} 不是评审方 C 真值层档位（应为 {expected}）。"
            f"general/frontend 是非评审用途。"
        )
    return True, "ok"


def build_deny_reason(detail):
    return (
        f"⚠️ **[chain-gate] 协作链路闸门阻断（SO-11 跳链检测）**\n\n"
        f"{detail}\n\n"
        f"**为何阻断**: 2026-07-25 meta-review-gate round1 事故——agent 凭 mira --help 滞后列表"
        f"把 opus4.8p 换成 opus4.6，未验证就跳链（lessons §8.6）。\n\n"
        f"**真值层**: governance/specs/reviewer-tiers.yaml（机器源）+ mira-integration-status.md（旁路健康检查）\n"
        f"**spec §二.2.1**: 调度前必须档位真值层一致 + 实测可达 + 冲突上报用户\n\n"
        f"**紧急 override**（真值层过期场景，需问用户后用）:\n"
        f"  写 `{OVERRIDE_FILE}` 内容 `{{\"until\": <unix_ts_30min后>}}`"
    )


def get_override():
    try:
        with open(OVERRIDE_FILE, "r") as f:
            d = json.load(f)
        if time.time() < d.get("until", 0):
            return True
    except Exception:
        pass
    return False


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

    if get_override():
        return

    # v2-1: 先读 YAML 真值层（失败 fail-closed）
    data, err = load_truth_layer()
    if data is None:
        print(json.dumps({
            "decision": "block",
            "reason": build_deny_reason(f"**[chain-gate] 真值层 YAML 解析失败**: {err}\n\n请检查 reviewer-tiers.yaml。"),
        }, ensure_ascii=False))
        sys.exit(2)

    is_mira = is_mira_review_dispatch(command)
    is_qoder = is_qoder_review_dispatch(command)

    if not (is_mira or is_qoder):
        return  # 非评审调度，放行

    reviewers = data["reviewers"]
    known_tiers, _ = load_mira_known_tiers()

    # C round1 C1：YAML A/B 档位必须在 mira 档位表（旁路健康检查）
    consistent, consistency_reason = check_truth_layer_consistency(reviewers, known_tiers)
    if not consistent:
        print(json.dumps({
            "decision": "block",
            "reason": build_deny_reason(f"**[chain-gate] 真值层双源不一致**: {consistency_reason}"),
        }, ensure_ascii=False))
        sys.exit(2)

    if is_mira:
        ok, reason = check_mira_alignment(command, reviewers)
        if not ok:
            print(json.dumps({
                "decision": "block",
                "reason": build_deny_reason(reason),
            }, ensure_ascii=False))
            sys.exit(2)

    if is_qoder:
        ok, reason = check_qoder_alignment(command, reviewers)
        if not ok:
            print(json.dumps({
                "decision": "block",
                "reason": build_deny_reason(reason),
            }, ensure_ascii=False))
            sys.exit(2)


if __name__ == "__main__":
    main()
