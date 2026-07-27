#!/usr/bin/env python3
"""
_bootstrap_common.py -- SO-12 共享模块（round2 M2）
====================================================
被 bootstrap-inject-sessionstart.py 和 bootstrap-gate-precommit.py 共同 import。
提供真值三件套路径推算 + sha256 计算，确保两 hook 用同一份 hash 逻辑。

M2 核心原理：bootstrap 时算三件套 sha256 写进标记；动手前重算当前 sha256 比对。
不一致 → 真值已变 → 标记失效 → 强制重 bootstrap。这是 fail-closed 的完整语义。
"""

import hashlib
import os

# repo root 推算（同其他 hook 模式）
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_REPO_FROM_SCRIPT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
_FALLBACK_REPO = r"C:\Users\Admin\Documents\trae_projects\agent-collaboration-standard"
_test_yaml = os.path.join(_DEFAULT_REPO_FROM_SCRIPT, "governance", "specs", "reviewer-tiers.yaml")
REPO_ROOT = os.environ.get("AGENT_COLLABORATION_REPO") or (
    _DEFAULT_REPO_FROM_SCRIPT if os.path.exists(_test_yaml) else _FALLBACK_REPO
)

# 真值三件套路径（hook 注入 + hash 校验都用这个）
TRUTH_FILES = {
    "reviewer_tiers_yaml": os.path.join(REPO_ROOT, "governance", "specs", "reviewer-tiers.yaml"),
    "spec_review_process": os.path.join(REPO_ROOT, "governance", "specs", "governance-review-process.md"),
    "config_json": os.path.join(REPO_ROOT, ".zcode", "config.json"),
}


def compute_truth_hash():
    """算三件套内容 sha256，返回 {key: sha256[:16]}。
    任一文件不存在/不可读 → 抛异常（让调用方 fail-closed）。
    """
    hashes = {}
    for key, path in TRUTH_FILES.items():
        if not os.path.exists(path):
            raise FileNotFoundError(f"真值文件不存在: {path}")
        with open(path, "rb") as f:
            content = f.read()
        hashes[key] = hashlib.sha256(content).hexdigest()[:16]  # 16 位够防碰撞
    return hashes


def get_session_id():
    """当前 session id（env 变量优先，没有则 None）。
    M1 改：返回 None 而非 'unknown'（让调用方明确区分"有 env"vs"无 env"）。
    """
    return os.environ.get("ZCODE_SESSION_ID") or os.environ.get("CLAUDE_SESSION_ID")
