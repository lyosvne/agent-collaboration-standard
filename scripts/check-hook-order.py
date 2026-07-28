#!/usr/bin/env python3
"""
check-hook-order.py — PreToolUse hook 执行顺序契约 lint（SO-13 backlog #8）

A round2 新发现 2："AGENTS.md 写死顺序，但没有 CI/pre-commit 校验 config.json
实际顺序与声明一致。跳链教训里第 2 条（改到 home 级 hook）就是'文档说一套
代码做一套'的类型。"

本 lint 校验：
  1. config.json 的 PreToolUse 数组顺序
  2. bootstrap-gate 必须在第 1 位（AGENTS.md 锁定的硬契约，round2 M3 B BLOCKER）
  3. （软校验）打印完整顺序供人工核对

不一致 → exit 1 + 打印差异。
无 CI 场景，靠自觉 + AGENTS.md 约束（建议改 config.json 后跑此脚本）。

跑法：python scripts/check-hook-order.py
"""

import json
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_JSON = os.path.join(REPO_ROOT, ".zcode", "config.json")

# AGENTS.md 锁定的硬契约：bootstrap-gate 必须第 1 位
# 理由（round2 M3，B BLOCKER）：hook 链短路，bootstrap-gate 是下游 hook 的前置条件
HARD_CONTRACTS = [
    {"position": 0, "must_contain": "bootstrap-gate", "reason": "M3 round2: 前置条件必须先跑"},
]


def load_pretooluse_order():
    """读 config.json，返回 PreToolUse Bash matcher 的 hook 命令列表（按顺序）。"""
    if not os.path.exists(CONFIG_JSON):
        return None, f"config.json 不存在: {CONFIG_JSON}"
    try:
        with open(CONFIG_JSON, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        return None, f"config.json 解析失败: {e}"
    events = cfg.get("hooks", {}).get("events", {})
    pretooluse = events.get("PreToolUse", [])
    if not pretooluse:
        return [], "PreToolUse 无挂载"
    # 取第一个 matcher 组（假设 Bash matcher）
    hooks = []
    for entry in pretooluse:
        if entry.get("matcher") == "Bash":
            for h in entry.get("hooks", []):
                cmd = h.get("command", "")
                # 提取 hook 文件名
                m = re.search(r"([a-zA-Z_-]+\.py)", cmd)
                hooks.append(m.group(1) if m else cmd)
            break
    return hooks, "ok"


def main():
    print("=" * 60)
    print("check-hook-order（SO-13 #8: PreToolUse 顺序契约 lint）")
    print("=" * 60)

    errors = []
    warnings = []

    order, err = load_pretooluse_order()
    if err.startswith("config.json 不存在"):
        print(f"❌ FATAL: {err}")
        sys.exit(1)
    if not order:
        print(f"❌ FATAL: PreToolUse 无 Bash hook 挂载")
        sys.exit(1)

    print(f"✅ config.json PreToolUse Bash 顺序（共 {len(order)} 个）:")
    for i, h in enumerate(order):
        print(f"   {i+1}. {h}")
    print()

    # 硬契约校验
    for contract in HARD_CONTRACTS:
        pos = contract["position"]
        must = contract["must_contain"]
        if pos >= len(order):
            errors.append(f"位置 {pos+1} 不存在（只有 {len(order)} 个 hook），期望 {must}")
        elif must not in order[pos]:
            errors.append(
                f"位置 {pos+1} 是 '{order[pos]}'，硬契约要求含 '{must}'（{contract['reason']}）"
            )

    # 软校验：建议性的完整顺序（不强制，只 warn）
    # 理想顺序（来自 governance-infrastructure-status.md §一）：
    # bootstrap-gate → review-gate → chain-gate → session-gate
    expected = ["bootstrap-gate", "review-gate", "chain-gate", "session-gate"]
    actual_names = []
    for h in order:
        for e in expected:
            if e in h:
                actual_names.append(e)
                break
    if actual_names != expected[: len(actual_names)] or len(actual_names) != len(expected):
        if len(actual_names) == len(expected):
            warnings.append(
                f"顺序与建议不符：实际 {actual_names} vs 建议 {expected}（非硬契约，但建议对齐）"
            )

    print()
    if errors:
        print(f"❌ 硬契约违反 {len(errors)} 处:")
        for e in errors:
            print(f"  - {e}")
        print()
        print("修复: 改 .zcode/config.json 的 PreToolUse 数组顺序，bootstrap-gate 放第 1 位")
        print("      （见 governance/specs/governance-infrastructure-status.md §一 顺序契约）")
        sys.exit(1)
    else:
        print("✅ 硬契约通过（bootstrap-gate 在第 1 位）")
        if warnings:
            print(f"⚠️  软警告 {len(warnings)} 处:")
            for w in warnings:
                print(f"  - {w}")
        sys.exit(0)


if __name__ == "__main__":
    main()
