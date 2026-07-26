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

REPO = Path(__import__("os").environ.get(
    "REPO_ROOT",
    str(Path(__file__).resolve().parents[1]))  # scripts/ 父目录 = 仓库根，避免跨 checkout 混读
SRC = Path.home() / ".agent-collaboration"
# 路径策略（Phase D-B，2026-07-26）：
#   REDACT_MAP 从 ~/.config/agent-collaboration/secret-patterns/ 读（环境变量可覆盖）
#   旧位置 ~/.agent-collaboration/archive/secret-patterns/ 已废弃（本机降级为只读历史快照）
SECRET_PATTERNS_DIR = Path(__import__("os").environ.get(
    "SECRET_PATTERNS_DIR",
    str(Path.home() / ".config" / "agent-collaboration" / "secret-patterns")))
REDACT_MAP = SECRET_PATTERNS_DIR / "redact-map.txt"

# 扫描范围: git 真值（archive + governance/specs）+ 本机历史快照（仍可能含旧脏版本，过渡期保留双源清理）
SCAN_DIRS = [
    REPO / "archive",
    REPO / "governance" / "specs",
    SRC / "archive",
    SRC / "standards" / "archive",
    SRC / "standards" / "specs",
]


def load_redactions() -> list[tuple[str, str]]:
    """从外部 redact-map.txt 读脱敏映射。按 token 长度降序排（长串先替）。

    fail-closed（节点2 round2 修复, 阻断5/B-5）:
      v3.4 初版格式错误行只 ⚠️ 跳过, 不阻断 → 映射文件损坏时静默放过。
      修复: 格式错误行 sys.exit(1), 强制修复映射文件再重跑。
    """
    if not REDACT_MAP.is_file():
        sys.exit(f"❌ 脱敏映射文件不存在: {REDACT_MAP}")
    pairs = []
    bad_lines = []
    for ln in REDACT_MAP.read_text(encoding="utf-8").splitlines():
        s = ln.rstrip("\n")
        if not s.strip() or s.lstrip().startswith("#"):
            continue
        if "\t" not in s:
            bad_lines.append(s)
            continue
        token, replacement = s.split("\t", 1)
        token = token.strip()
        if token:
            pairs.append((token, replacement.strip()))
    if bad_lines:
        # fail-closed: 格式错误即失败, 不静默跳过
        sys.exit(
            f"❌ redact-map.txt 含 {len(bad_lines)} 行格式错误（无 TAB 分隔）, 中止: "
            f"{[b[:20] for b in bad_lines[:3]]}。修复映射文件后重跑。"
        )
    if not pairs:
        sys.exit("❌ redact-map.txt 无有效映射行（全注释/空）, 中止")
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
    # fail-closed（节点2 round2 修复, 阻断5/B-5）:
    # v3.4 初版目录不存在/读失败都 continue 吞掉, 末尾 return 0 = fail-open。
    # 修复: 累计错误数, 末尾 return 1 if errors。
    missing_dirs = []
    read_errors = []

    for scan_dir in SCAN_DIRS:
        if not scan_dir.is_dir():
            # fail-closed: 配置的扫描目录必须存在, 缺失即错误
            missing_dirs.append(str(scan_dir))
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
            except (OSError, UnicodeDecodeError) as e:
                # fail-closed: 读失败即错误, 不静默跳过
                read_errors.append(f"{p}: {type(e).__name__}: {e}")
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
    # fail-closed（阻断5/B-5）: 报告所有错误, 有错则 return 1
    if missing_dirs:
        print(f"❌ {len(missing_dirs)} 个配置的扫描目录不存在:", file=sys.stderr)
        for d in missing_dirs:
            print(f"   - {d}", file=sys.stderr)
    if read_errors:
        print(f"❌ {len(read_errors)} 个文件读取失败:", file=sys.stderr)
        for e in read_errors[:5]:
            print(f"   - {e}", file=sys.stderr)
    if missing_dirs or read_errors:
        print("❌ fail-closed: 存在缺失目录/读失败, 脱敏闭环不可证明, 退出码 1", file=sys.stderr)
        return 1
    if args.apply:
        print("✅ 已写盘, 请 grep 复核零残留")
    else:
        print("（dry-run, 未写盘。确认请加 --apply）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
