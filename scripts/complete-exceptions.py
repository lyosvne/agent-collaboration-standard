#!/usr/bin/env python3
"""
complete-exceptions.py — 补全例外清单的 HISTORY 部分

问题: 上个 session 的 exceptions 文件 HISTORY 部分用概括描述（"在 archive/ 下所有引用"）,
      没逐条列出 file:line|tool, 导致门禁 4 集合比对无法工作。

本脚本:
  1. 扫 standards/ 下所有退役词命中（排除已 [RETIRED- 替换的）
  2. 解析现有 exceptions 文件, 提取已登记的 ROLE + HISTORY 键
  3. 找出未登记的命中, 按文件分类
  4. 把未登记的命中追加到 exceptions 文件的 HISTORY 部分（逐条 file:line|tool|分类理由）

分类理由（自动判定）:
  - 含 '知识库' / 'knowledge' / 'Documents' / '路径' → 知识库名/路径引用
  - 在 specs/ 下 → 治理方案文档讨论对象
  - 含 '插件' / '兼容' / '支持' → 工具生态参考
  - 含 '退役' / '淘汰' / 'retire' → 历史叙述
  - 其他 → 默认 HISTORY（需人工复核）

输出: 更新后的 exceptions 文件（逐条 HISTORY）
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

STANDARDS = Path(r"C:\Users\Admin\.agent-collaboration\standards")
EXC_FILE = Path(r"C:\Users\Admin\.agent-collaboration\archive\retired-terms-exceptions-20260726.md")
TERMS = ["Claude Code", "claude-zhipu", "Codex", "QoderWork", "Trae IDE"]

# 分类规则（按优先级）
def classify(rel_path: str, content: str) -> str:
    c = content.lower()
    if any(k in content for k in ["知识库", "knowledge"]) or "documents" in c or "路径" in content:
        return "知识库名/路径"
    if "/specs/" in rel_path or rel_path.startswith("specs/"):
        return "治理方案文档讨论对象"
    if any(k in content for k in ["插件", "兼容", "支持", "生态"]):
        return "工具生态参考"
    if any(k in content for k in ["退役", "淘汰", "retire", "下线", "废弃"]):
        return "历史叙述"
    return "其他(默认HISTORY)"


def scan_hits() -> dict[str, list[tuple[str, str]]]:
    """扫 standards/ 所有命中（排除 [RETIRED-），返回 {key: [(rel, tool, content)]}。"""
    pat = "|".join(TERMS)
    r = subprocess.run(["grep", "-rEn", pat, str(STANDARDS)], capture_output=True, text=True)
    prefix = str(STANDARDS).replace("\\", "/") + "/"
    hits = {}  # key "rel:line|tool" -> (rel, line, tool, content)
    for line in r.stdout.splitlines():
        if "[RETIRED-" in line:
            continue
        m = line.split(":", 2)
        if len(m) < 3:
            continue
        fpath, lineno, content = m
        fpath_norm = fpath.replace("\\", "/")
        if fpath_norm.startswith(prefix):
            rel = fpath_norm[len(prefix):]
        else:
            rel = fpath_norm
        # 该行命中哪些工具
        for t in TERMS:
            if t in content:
                key = f"{rel}:{lineno}|{t}"
                hits[key] = (rel, lineno, t, content.strip())
    return hits


def parse_existing_exceptions() -> tuple[set[str], set[str]]:
    """解析现有 exceptions 文件, 返回 (role_keys, history_keys)。"""
    text = EXC_FILE.read_text(encoding="utf-8")
    role_keys = set()
    history_keys = set()
    current_section = None
    for ln in text.splitlines():
        s = ln.strip()
        if s.startswith("## "):
            upper = s.upper()
            if "ROLE" in upper:
                current_section = "ROLE"
            elif "HISTORY" in upper:
                current_section = "HISTORY"
            else:
                current_section = None
            continue
        if not s.startswith("|") or "---" in s:
            continue
        parts = [p.strip() for p in s.split("|")]
        # 表格行: | file | line | tool | content | reason |
        if len(parts) < 5:
            continue
        file, lineno, tool = parts[1], parts[2], parts[3]
        key = f"{file}:{lineno}|{tool}"
        if current_section == "ROLE":
            role_keys.add(key)
        elif current_section == "HISTORY":
            history_keys.add(key)
    return role_keys, history_keys


def main() -> int:
    hits = scan_hits()
    role_keys, history_keys = parse_existing_exceptions()
    print(f"扫描命中（去重）: {len(hits)} 条")
    print(f"现有 ROLE 登记数: {len(role_keys)}")
    print(f"现有 HISTORY 登记数: {len(history_keys)}")

    # 找未登记的
    all_registered = role_keys | history_keys
    unregistered = []
    for key, (rel, ln, tool, content) in hits.items():
        if key in all_registered:
            continue
        unregistered.append((rel, ln, tool, content))
    print(f"未登记命中: {len(unregistered)} 条")

    # 按文件分组统计
    from collections import Counter
    file_counter = Counter(u[0] for u in unregistered)
    print("\n未登记命中按文件分布:")
    for f, c in file_counter.most_common():
        print(f"  {c:3d}  {f}")

    # 分类
    print("\n未登记命中按分类:")
    cls_counter = Counter(classify(u[0], u[3]) for u in unregistered)
    for cls, c in cls_counter.most_common():
        print(f"  {c:3d}  {cls}")

    # 生成追加内容
    if not unregistered:
        print("\n✅ 所有命中已登记, 无需补全")
        return 0

    print(f"\n将追加 {len(unregistered)} 条到 exceptions 文件的 HISTORY 部分")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
