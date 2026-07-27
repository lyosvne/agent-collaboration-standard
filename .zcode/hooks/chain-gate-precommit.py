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
# 检查 SCRIPT_DIR 推断的 repo 是否真有 spec 文件，无则用 fallback
_test_spec = os.path.join(_DEFAULT_REPO_FROM_SCRIPT, "governance", "specs", "governance-review-process.md")
REPO_ROOT = os.environ.get("AGENT_COLLABORATION_REPO") or (
    _DEFAULT_REPO_FROM_SCRIPT if os.path.exists(_test_spec) else _FALLBACK_REPO
)
SPEC_REVIEW_PROCESS = os.path.join(REPO_ROOT, "governance", "specs", "governance-review-process.md")
SPEC_MIRA_STATUS = os.path.join(REPO_ROOT, "governance", "specs", "mira-integration-status.md")

# ===== 评审调度识别 =====

# mira -p / mira --print 调度
MIRA_DISPATCH_PATTERN = re.compile(r"\bmira\s+(-p|--print)\b", re.IGNORECASE)

# 评审关键字（命令含任一即判为评审调度，与 mira -p 同现）
REVIEW_KEYWORDS = [
    "评审方 A", "评审方 B", "评审方 C",
    "review-package", "评审材料", "评审任务",
    "opus4.8p", "gpt5.6sol", "cantus",  # 档位名出现也算评审信号
    "review-round", "评审汇总",
]

# qoder-bridge --tier cantus（C 评审调度）
QODER_CANTUS_PATTERN = re.compile(
    r"qoder-bridge(?:\.py)?\s+--tier\s+cantus\b", re.IGNORECASE
)

# 提取 --model 参数值（支持 --model X 和 --model=X 两种形式）
MIRA_MODEL_PATTERN = re.compile(r"--model(?:=|\s+)(\S+)", re.IGNORECASE)

# 提取 qoder-bridge --tier 值（支持 --tier X 和 --tier=X 两种形式，B-N8）
QODER_TIER_PATTERN = re.compile(r"--tier(?:=|\s+)(\S+)", re.IGNORECASE)


def is_mira_review_dispatch(command):
    """判命令是否为 mira 评审调度（mira -p + 含评审关键字）"""
    if not MIRA_DISPATCH_PATTERN.search(command):
        return False
    return any(kw.lower() in command.lower() for kw in REVIEW_KEYWORDS)


def is_qoder_review_dispatch(command):
    """判命令是否为 qoder C 评审调度（qoder-bridge --tier cantus）"""
    return bool(QODER_CANTUS_PATTERN.search(command))


def extract_mira_model(command):
    """提取 --model 值，无则返回 None"""
    m = MIRA_MODEL_PATTERN.search(command)
    return m.group(1).strip().strip("'\"") if m else None


def extract_qoder_tier(command):
    """提取 --tier 值，无则返回 None"""
    m = QODER_TIER_PATTERN.search(command)
    return m.group(1).strip().strip("'\"") if m else None


# ===== 真值层读取（解析 spec markdown）=====

# spec §二表格行格式：| **评审方 A** | Mira opus4.8p（...）| ... | `mira -p` + opus4.8p 档 |
# 解析：评审方 + 档位
SPEC_REVIEWER_ROW_PATTERN = re.compile(
    r"\*\*评审方\s+([ABC])\*\*\s*\|\s*([^|]+)\|[^|]+\|[^|]+", re.IGNORECASE
)

# mira-integration-status 档位表行：| **Cloud-O (Claude)** | opus4.8 / opus4.8t / ... |
MIRA_TIERS_ROW_PATTERN = re.compile(
    r"\|\s*\*\*Cloud-O\s*\(Claude\)\s*\*\*\s*\|\s*([^|]+)\|", re.IGNORECASE
)
GPT_TIERS_ROW_PATTERN = re.compile(
    r"\|\s*\*\*GPT\s*\*\*\s*\|\s*([^|]+)\|", re.IGNORECASE
)


def load_reviewer_tiers_from_spec():
    """从 governance-review-process.md §二表格解析评审方档位。

    返回: (tiers: dict, error: str)
      tiers = {"A": "opus4.8p", "B": "gpt5.6sol", "C": "cantus"}
    """
    if not os.path.exists(SPEC_REVIEW_PROCESS):
        return None, f"spec 不存在: {SPEC_REVIEW_PROCESS}"
    try:
        with open(SPEC_REVIEW_PROCESS, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        return None, f"读 spec 失败: {e}"

    # 截取 §二 评审方组合 到 §三之间
    m = re.search(r"## 二、评审方组合.*?(?=## 三、)", content, re.DOTALL)
    if not m:
        return None, "找不到 §二 评审方组合"
    section = m.group(0)

    tiers = {}
    for row in SPEC_REVIEWER_ROW_PATTERN.finditer(section):
        reviewer = row.group(1).upper()
        # 第二列格式 "Mira opus4.8p（Claude Opus 4.8 Pro）" 或 "Qoder cantus（...）"
        col2 = row.group(2).strip()
        # 提取档位名（第一个 token，去 "Mira "/"Qoder " 前缀）
        # 例：Mira opus4.8p（... → opus4.8p
        #     Qoder cantus（... → cantus
        tier_match = re.search(r"(?:Mira|Qoder)\s+([a-zA-Z0-9.]+)", col2, re.IGNORECASE)
        if tier_match:
            tiers[reviewer] = tier_match.group(1)

    if not all(k in tiers for k in ("A", "B", "C")):
        return None, f"解析不全，缺: {set('ABC') - set(tiers.keys())}，得到: {tiers}"

    return tiers, "ok"


def load_mira_known_tiers():
    """从 mira-integration-status.md 解析 A/B 档位的可达列表（防 spec §二 漏更新）。

    返回: (tiers_set: set, error: str)
      tiers_set 含所有 Cloud-O 和 GPT 档位名
    """
    if not os.path.exists(SPEC_MIRA_STATUS):
        return None, f"mira-integration-status 不存在: {SPEC_MIRA_STATUS}"
    try:
        with open(SPEC_MIRA_STATUS, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        return None, f"读 mira-integration-status 失败: {e}"

    all_tiers = set()
    # Cloud-O 行（opus 系列）
    for m in MIRA_TIERS_ROW_PATTERN.finditer(content):
        for t in re.split(r"[/,]", m.group(1)):
            t = t.strip().strip("*` ")
            if re.match(r"^opus[\d.]+[a-z]?$", t, re.IGNORECASE):
                all_tiers.add(t.lower())
    # GPT 行（gpt 系列）
    for m in GPT_TIERS_ROW_PATTERN.finditer(content):
        for t in re.split(r"[/,]", m.group(1)):
            t = t.strip().strip("*` ")
            if re.match(r"^gpt[\d.]+[a-z]*$", t, re.IGNORECASE):
                all_tiers.add(t.lower())

    return all_tiers, "ok"


# ===== 校验 =====

def check_truth_layer_consistency(reviewer_tiers, known_tiers):
    """C round1 C1：双源一致性校验。

    spec §二 解析出的 A/B 档位必须在 mira-integration-status 档位表里。
    不一致 → fail-closed（编队被多源漂移坑过 3 次，治理工具自己必须自检）。

    返回: (consistent: bool, reason: str)
    """
    if not reviewer_tiers:
        return False, "spec §二 真值层为空"
    if not known_tiers:
        return False, "mira-integration-status 档位表为空或不可读"

    inconsistent = []
    for reviewer, tier in reviewer_tiers.items():
        if reviewer in ("A", "B"):  # C 走 qoder，不在 mira 表
            if tier.lower() not in known_tiers:
                inconsistent.append(f"{reviewer}={tier}（spec §二 有但 mira-integration-status 无）")
    if inconsistent:
        return False, (
            f"真值层双源不一致: {'; '.join(inconsistent)}。"
            f"先对齐 spec §二 与 mira-integration-status.md 再调度（编队历史病灶：多源漂移）。"
        )
    return True, "ok"


def check_mira_alignment(command, reviewer_tiers, known_tiers):
    """校验 mira 评审调度的 --model 是否与真值层一致。

    返回: (ok: bool, reason: str)
    """
    # 判定评审方：只用"评审方 A/B"明确标识（不用档位名，防循环识别）
    cmd_lower = command.lower()
    reviewers_in_cmd = set()
    if "评审方 a" in cmd_lower:
        reviewers_in_cmd.add("A")
    if "评审方 b" in cmd_lower:
        reviewers_in_cmd.add("B")
    # mira 不调 C（C 走 qoder）

    if not reviewers_in_cmd:
        # 是评审调度但识别不出具体评审方（可能是新措辞）→ fail-closed
        return False, (
            "命令含评审信号但无法识别具体评审方（'评审方 A'/'评审方 B' 关键字均未命中）。"
            "必须在 prompt 里显式标注评审方（如'你是评审方 A'），不能只写档位名。"
        )

    # 必须显式 --model
    model = extract_mira_model(command)
    if not model:
        expected = " 或 ".join(reviewer_tiers[r] for r in sorted(reviewers_in_cmd))
        return False, (
            f"评审调度（{sorted(reviewers_in_cmd)}）必须显式 --model，"
            f"不能用默认档（防 mira --help 列表滞后导致跳链）。"
            f"期望 --model {expected}（spec §二真值层）。"
        )

    # --model 必须在期望集合
    expected_models = {reviewer_tiers[r].lower() for r in reviewers_in_cmd}
    if model.lower() not in expected_models:
        expected_str = " 或 ".join(sorted(expected_models))
        return False, (
            f"--model {model} 不在评审方 {sorted(reviewers_in_cmd)} 的真值层档位（{expected_str}）。"
            f"若真值层过期，请改 spec §二 + mira-integration-status.md，不要自行换档。"
            f"紧急场景写 override 文件：{OVERRIDE_FILE}"
        )

    # 也要在 mira-integration-status 已知档位表（防 spec §二 漏更新）
    if known_tiers and model.lower() not in known_tiers:
        return False, (
            f"--model {model} 在 spec §二 但不在 mira-integration-status 档位表（{len(known_tiers)} 档）。"
            f"可能档位已下架或 spec 漏更新，请实测 `mira -p OK --model {model}` 确认可达。"
        )

    return True, "ok"


def check_qoder_alignment(command, reviewer_tiers):
    """校验 qoder C 调度的 --tier 是否为 cantus。

    返回: (ok: bool, reason: str)
    """
    tier = extract_qoder_tier(command)
    expected = reviewer_tiers.get("C", "cantus").lower()
    if not tier:
        return False, "qoder-bridge 评审调度必须显式 --tier cantus"
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
        f"**真值层**: governance/specs/governance-review-process.md §二 + mira-integration-status.md\n"
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

    is_mira = is_mira_review_dispatch(command)
    is_qoder = is_qoder_review_dispatch(command)

    if not (is_mira or is_qoder):
        return  # 非评审调度，放行

    # 读真值层
    reviewer_tiers, err = load_reviewer_tiers_from_spec()
    if reviewer_tiers is None:
        # fail-closed
        print(json.dumps({
            "decision": "block",
            "reason": build_deny_reason(f"**[chain-gate] 真值层解析失败**: {err}\n\n请检查 spec §二表格格式。"),
        }, ensure_ascii=False))
        sys.exit(2)

    known_tiers, known_err = load_mira_known_tiers()

    # C round1 C1：双源一致性校验（spec §二 的 A/B 档位必须在 mira 档位表）
    consistent, consistency_reason = check_truth_layer_consistency(reviewer_tiers, known_tiers)
    if not consistent:
        print(json.dumps({
            "decision": "block",
            "reason": build_deny_reason(f"**[chain-gate] 真值层双源不一致**: {consistency_reason}"),
        }, ensure_ascii=False))
        sys.exit(2)

    if is_mira:
        ok, reason = check_mira_alignment(command, reviewer_tiers, known_tiers)
        if not ok:
            print(json.dumps({
                "decision": "block",
                "reason": build_deny_reason(reason),
            }, ensure_ascii=False))
            sys.exit(2)

    if is_qoder:
        ok, reason = check_qoder_alignment(command, reviewer_tiers)
        if not ok:
            print(json.dumps({
                "decision": "block",
                "reason": build_deny_reason(reason),
            }, ensure_ascii=False))
            sys.exit(2)


if __name__ == "__main__":
    main()
