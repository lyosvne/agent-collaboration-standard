#!/usr/bin/env python3
"""
Bootstrap Inject -- SessionStart Hook (SO-12 compact 续接 bootstrap)
=====================================================================
治"compact 续接后忘全局信息"问题。

根因：compact summary 是有损摘要（保留"做了什么"，丢"事实在哪 + 为什么"）。
新 session 不主动 reload 项目真值，导致协作链路断裂（如 SO-11-v2-2 round1
调 C 时忘了调用方式、改 hook 改到 home 级而非 project 级）。

机制（SO-11-v2-2 M1/M2 思路在 session bootstrap 层的应用）：
  SessionStart（matcher: compact|resume|clear|startup）触发时：
  1. 读"真值三件套"关键段
     - reviewer-tiers.yaml（档位 + dispatchers + session_continuity，机器源）
     - governance-review-process.md §二.1/§二.2（A/B/C 调度 + C 完整 ssh 命令 + 续接准则）
     - .zcode/config.json（hook 实际生效路径）
  2. 摘要输出为 additionalContext JSON（注入对话上下文，确保"看见"）
  3. 写 bootstrap 标记文件（~/.zcode/hooks/.bootstrap-done.json）
     - 含 session_id + 时间戳 + 已读真值文件清单
     - bootstrap-gate-precommit.py 在"动手类"操作前检查此标记

设计原则：
  - 显式注入取代推断（M1/M2 思路）
  - fail-closed：三件套任一损坏 → 不写标记 → 后续动手被 bootstrap-gate 拦
  - 不依赖 compact summary 记忆，只信真值文件
  - 本地状态不进 repo（同 .review-gate-override-pending.json 模式）
"""

import json
import os
import re
import sys
import tempfile
import time
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# import 共享模块（M2：truth hash 计算）
try:
    sys.path.insert(0, SCRIPT_DIR)
    from _bootstrap_common import compute_truth_hash, get_session_id, TRUTH_FILES, REPO_ROOT
except Exception as e:
    # import 失败 → 退化到本地实现（hook 不能崩）
    sys.stderr.write(f"[bootstrap-inject] _bootstrap_common import 失败，退化本地实现: {e}\n")
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
        return os.environ.get("ZCODE_SESSION_ID") or os.environ.get("CLAUDE_SESSION_ID") or "unknown"
    def compute_truth_hash():
        import hashlib
        hashes = {}
        for key, path in TRUTH_FILES.items():
            with open(path, "rb") as f:
                hashes[key] = hashlib.sha256(f.read()).hexdigest()[:16]
        return hashes

# 真值三件套路径（从共享模块来）
REVIEWER_TIERS_YAML = TRUTH_FILES["reviewer_tiers_yaml"]
SPEC_REVIEW_PROCESS = TRUTH_FILES["spec_review_process"]
CONFIG_JSON = TRUTH_FILES["config_json"]

# bootstrap 标记文件（本地状态，不进 repo）
BOOTSTRAP_MARKER = os.path.join(SCRIPT_DIR, ".bootstrap-done.json")


def read_truth_files():
    """读真值三件套，返回 dict。任一失败 → 抛异常（fail-closed）。"""
    result = {}

    # 1. reviewer-tiers.yaml 全文（机器源，hook 读它）
    if not os.path.exists(REVIEWER_TIERS_YAML):
        raise FileNotFoundError(f"reviewer-tiers.yaml 不存在: {REVIEWER_TIERS_YAML}")
    with open(REVIEWER_TIERS_YAML, "r", encoding="utf-8") as f:
        result["reviewer_tiers_yaml"] = f.read()

    # 2. spec §二关键段（§二.1 调度前校验 + §二.2 会话续接）
    if not os.path.exists(SPEC_REVIEW_PROCESS):
        raise FileNotFoundError(f"governance-review-process.md 不存在: {SPEC_REVIEW_PROCESS}")
    with open(SPEC_REVIEW_PROCESS, "r", encoding="utf-8") as f:
        spec_full = f.read()
    # 摘 §二（从 "## 二、" 到 "## 三、" 之前）
    m = re.search(r"(## 二、.*?)(?=## 三、)", spec_full, re.DOTALL)
    result["spec_section_2"] = m.group(1).strip() if m else spec_full[:3000]

    # 3. config.json 全文（hook 实际生效路径）
    if not os.path.exists(CONFIG_JSON):
        raise FileNotFoundError(f".zcode/config.json 不存在: {CONFIG_JSON}")
    with open(CONFIG_JSON, "r", encoding="utf-8") as f:
        result["config_json"] = f.read()

    return result


def build_additional_context(truth):
    """构建 additionalContext 文本（注入对话上下文）"""
    lines = [
        "# 📌 SO-12 compact 续接 bootstrap 真值三件套（SessionStart hook 自动注入）",
        "",
        "> 本 session 已自动加载项目真值，不依赖 compact summary 记忆。",
        "> 动手前请以此为准（档位 / 调用方式 / hook 生效路径）。",
        "",
        "## 1. reviewer-tiers.yaml（档位真值源，hook 读它）",
        "```yaml",
        truth["reviewer_tiers_yaml"],
        "```",
        "",
        "## 2. spec §二（A/B/C 调度 + 会话续接准则）",
        "<!-- 含 C 完整 ssh 命令（spec §二.1 第 5 条 + C 调用固化段）-->",
        truth["spec_section_2"],
        "",
        "## 3. .zcode/config.json（hook 实际生效路径 = project 级 ${ZCODE_PROJECT_DIR}/.zcode/hooks/）",
        "```json",
        truth["config_json"],
        "```",
        "",
        "---",
        "✅ bootstrap 完成。动手类操作（mira 评审调度 / ECS patch / 改真值层）前 bootstrap-gate 会校验标记。",
    ]
    return "\n".join(lines)


def write_bootstrap_marker(truth_files_seen):
    """写 bootstrap 标记文件（原子写 + 0600 权限，Unix）。
    M2（round2）：标记存三件套 sha256，bootstrap-gate 校验时重算比对。"""
    session_id = get_session_id() or "unknown"
    now_iso = datetime.now(timezone.utc).isoformat()
    # M2: 算三件套 sha256（inject 时已读，这里复用 hash 函数）
    try:
        truth_hashes = compute_truth_hash()
    except Exception as e:
        # hash 计算失败 → 标记不写（fail-closed，让 bootstrap-gate 拦）
        sys.stderr.write(f"[bootstrap-inject] truth hash 计算失败，不写标记: {e}\n")
        raise
    marker = {
        "session_id": session_id,
        "bootstrapped_at": now_iso,
        "bootstrapped_at_epoch": time.time(),
        "truth_files_seen": truth_files_seen,
        "truth_hashes": truth_hashes,  # M2：三件套内容 sha256[:16]
        "mechanism": "SO-12-bootstrap-inject-sessionstart-v2",
    }
    # 原子写：tmp + rename
    tmp_fd, tmp_path = tempfile.mkstemp(prefix=".bootstrap-done-", dir=SCRIPT_DIR, suffix=".tmp")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(marker, f, indent=2, ensure_ascii=False)
        # Unix 权限 0600（Windows chmod 忽略，不报错）
        try:
            os.chmod(tmp_path, 0o600)
        except OSError:
            pass
        os.replace(tmp_path, BOOTSTRAP_MARKER)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
    return marker


def main():
    try:
        raw = sys.stdin.buffer.read()
        hook_input = json.loads(raw.decode("utf-8", errors="replace"))
    except Exception:
        return  # 解析失败不阻断 SessionStart

    # SessionStart 的 matcher 已在 config.json 配置，hook 进程被调起即说明匹配
    # 但兼容性检查：hook_input 可能含 session_id / match_value
    # （SKILL.md 说 SessionStart match value 是 startup/resume/clear/compact）

    # 读真值三件套（fail-closed：任一失败 → 不写标记，不注入，让 bootstrap-gate 拦）
    try:
        truth = read_truth_files()
    except Exception as e:
        # 读真值失败：输出 error additionalContext（让 agent 看见），不写标记
        err_ctx = (
            f"# ⚠️ SO-12 bootstrap 失败\n\n"
            f"读真值三件套失败: {e}\n\n"
            f"动手类操作会被 bootstrap-gate deny。请修复真值文件后重启 session。"
        )
        print(json.dumps({
            "SessionStart": {"additionalContext": err_ctx}
        }, ensure_ascii=False))
        return

    # 写标记
    truth_files_seen = [
        "governance/specs/reviewer-tiers.yaml",
        "governance/specs/governance-review-process.md§二",
        ".zcode/config.json",
    ]
    try:
        write_bootstrap_marker(truth_files_seen)
    except Exception as e:
        # 标记写入失败：输出 warn，不阻断（bootstrap-gate 会因标记缺失而拦）
        sys.stderr.write(f"[bootstrap-inject] 标记写入失败: {e}\n")

    # 注入 additionalContext
    ctx = build_additional_context(truth)
    print(json.dumps({
        "SessionStart": {"additionalContext": ctx}
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
