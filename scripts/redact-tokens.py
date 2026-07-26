#!/usr/bin/env python3
"""
redact-tokens.py — 脱敏 archive 评审归档 + specs 里的 token 片段

设计原则（来自 v3.4 + review-process-lessons 教训 1）:
  执行计划/脚本本身不能成为泄露源。本脚本【不硬编码任何 token】，
  脱敏映射从外部文件 ~/.agent-collaboration/archive/secret-patterns/redact-map.txt 读。

外部映射格式（TAB 分隔）:
  <token-string>\t<replacement>

替换策略:
  - 长串先替（按 token 长度降序）, 避免短串吃掉长串前缀
  - 默认 dry-run, --apply 才写盘

扫描范围: archive/ + governance/specs/
不扫 scripts/（脚本逻辑区, 本脚本不含 token, 其他脚本若含需单独审查）
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path.home() / "Documents" / "trae_projects" / "agent-collaboration-standard"
SRC = Path.home() / ".agent-collaboration"
REDACT_MAP = SRC / "archive" / "secret-patterns" / "redact-map.txt"

# 扫描范围: 工作树 + 源端（两处都要脱敏, 否则 mirror 会把脏版本拉回工作树）
SCAN_DIRS = [
    REPO / "archive",
    REPO / "governance" / "specs",
    SRC / "archive",
    SRC / "standards" / "archive",
    SRC / "standards" / "specs",
]


def load_redactions() -> list[tuple[str, str]]:
    """从外部 redact-map.txt 读脱敏映射。按 token 长度降序排（长串先替）。"""
    if not REDACT_MAP.is_file():
        sys.exit(f"❌ 脱敏映射文件不存在: {REDACT_MAP}")
    pairs = []
    for ln in REDACT_MAP.read_text(encoding="utf-8").splitlines():
        s = ln.rstrip("\n")
        if not s.strip() or s.lstrip().startswith("#"):
            continue
        if "\t" not in s:
            print(f"⚠️ 跳过格式错误行（无 TAB）: {s[:20]}...", file=sys.stderr)
            continue
        token, replacement = s.split("\t", 1)
        token = token.strip()
        if token:
            pairs.append((token, replacement.strip()))
    # 长串在前
    pairs.sort(key=lambda x: len(x[0]), reverse=True)
    return pairs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="真正写盘（默认 dry-run）")
    args = ap.parse_args()

    print(f"模式: {'APPLY' if args.apply else 'DRY-RUN'}")
    print(f"脱敏映射: {REDACT_MAP}（外部文件, 本脚本不含 token）")

    redactions = load_redactions()
    print(f"加载 {len(redactions)} 条脱敏映射")
    # 不打印 token 内容（避免再次进入日志/终端历史）

    total_hits = 0
    file_changes: dict[str, list] = {}

    for scan_dir in SCAN_DIRS:
        if not scan_dir.is_dir():
            print(f"⚠️ 跳过不存在的目录: {scan_dir}")
            continue
        for p in scan_dir.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix not in (".md", ".txt", ".json", ".jsonl"):
                continue
            # 排除 secret-patterns/ 目录（patterns/redact-map 文件本身的 token 字面量是工具逻辑, 不脱敏）
            if "secret-patterns" in p.parts:
                continue
            try:
                text = p.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue

            hits_in_file = []
            new_text = text
            for token, replacement in redactions:
                count = new_text.count(token)
                if count > 0:
                    hits_in_file.append((token, replacement, count))
                    new_text = new_text.replace(token, replacement)

            if hits_in_file:
                # 显示相对 home 的路径, 便于区分工作树 vs 源端
                try:
                    rel = p.relative_to(Path.home()).as_posix()
                except ValueError:
                    rel = str(p)
                file_changes[rel] = hits_in_file
                total_hits += sum(c for _, _, c in hits_in_file)
                print(f"\n📄 {rel}")
                for token, repl, count in hits_in_file:
                    masked = token[:2] + "***" if len(token) > 4 else "***"
                    print(f"   {masked} → {repl}  ({count} 处)")
                if args.apply:
                    p.write_text(new_text, encoding="utf-8")

    print("\n" + "=" * 60)
    print(f"汇总: {total_hits} 处 token, 涉及 {len(file_changes)} 个文件")
    if args.apply:
        print("✅ 已写盘, 请 grep 复核零残留")
    else:
        print("（dry-run, 未写盘。确认请加 --apply）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
