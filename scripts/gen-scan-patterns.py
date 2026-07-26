#!/usr/bin/env python3
"""
gen-scan-patterns.py — 从 redact-map.txt 自动派生 scan-patterns.txt

节点2 round2 修复（阻断4/B-4）:
  v3.4 初版 scan-patterns.txt 只有 1 个 pattern（22a5***）, 不覆盖退役 token。
  B 评审要求覆盖已知退役凭证（4d0b/bcVs/JaZK）。
  本脚本从 redact-map.txt（单一真值源）取所有 token 键, 去重, 写入 scan-patterns.txt。

设计原则:
  - 单一真值源: redact-map.txt 是所有 token 的真值, scan-patterns.txt 自动派生
  - 不重复维护: 加新 token 只改 redact-map.txt, 跑本脚本即可
  - fail-closed: redact-map 不存在/格式错误 → exit 1
  - 本脚本不含 token 字面量（从外部读）

输入: ~/.agent-collaboration/archive/secret-patterns/redact-map.txt
输出: ~/.agent-collaboration/archive/secret-patterns/scan-patterns.txt

用法:
  python scripts/gen-scan-patterns.py            # dry-run, 打印将写入的 patterns
  python scripts/gen-scan-patterns.py --apply    # 实际写入 scan-patterns.txt
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SRC = Path.home() / ".agent-collaboration" / "archive" / "secret-patterns"
REDACT_MAP = SRC / "redact-map.txt"
SCAN_PATTERNS = SRC / "scan-patterns.txt"


def load_tokens() -> list[str]:
    """从 redact-map.txt 读所有 token 键, 去重, 按长度降序。"""
    if not REDACT_MAP.is_file():
        sys.exit(f"❌ redact-map.txt 不存在: {REDACT_MAP}")
    tokens = set()
    bad_lines = []
    for ln in REDACT_MAP.read_text(encoding="utf-8").splitlines():
        s = ln.rstrip("\n")
        if not s.strip() or s.lstrip().startswith("#"):
            continue
        if "\t" not in s:
            bad_lines.append(s)
            continue
        token = s.split("\t", 1)[0].strip()
        if token:
            tokens.add(token)
    if bad_lines:
        sys.exit(
            f"❌ redact-map.txt 含 {len(bad_lines)} 行格式错误（无 TAB）, 中止: "
            f"{[b[:20] for b in bad_lines[:3]]}"
        )
    if not tokens:
        sys.exit("❌ redact-map.txt 无有效 token, 中止")
    # 按长度降序（长串先扫, 避免短前缀吃掉长串）
    return sorted(tokens, key=len, reverse=True)


def render(tokens: list[str]) -> str:
    """渲染 scan-patterns.txt 内容。"""
    out = []
    out.append("# secret 扫描 patterns（v3.4 Phase B Step 4 用）")
    out.append("# 每行一个固定字符串（git grep -F 字面匹配，不解析为正则）")
    out.append("# 此文件在 ~/.agent-collaboration/archive/secret-patterns/，已被 mirror-sync exclude + .gitignore 双层防御")
    out.append("#")
    out.append(f"# 自动派生自 redact-map.txt（{len(tokens)} 个 token，按长度降序）")
    out.append(f"# 生成命令: python scripts/gen-scan-patterns.py --apply")
    out.append("# 注: 退役 token 本机已物理删除零残留，扫描会空转(exit 1)，属防御性扫描")
    out.append("")
    for t in tokens:
        out.append(t)
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="从 redact-map.txt 派生 scan-patterns.txt")
    ap.add_argument("--apply", action="store_true", help="实际写入（默认 dry-run）")
    args = ap.parse_args()

    tokens = load_tokens()
    print(f"从 redact-map.txt 加载 {len(tokens)} 个 token（去重后）")
    print(f"按长度降序: {[t[:4]+'***' for t in tokens]}")
    print()

    content = render(tokens)
    if args.apply:
        SCAN_PATTERNS.write_text(content, encoding="utf-8")
        print(f"✅ 已写入: {SCAN_PATTERNS}")
        print(f"   {len(tokens)} 个 pattern, 总 {len(content)} 字节")
    else:
        print("（dry-run, 未写盘。确认请加 --apply）")
        print("---将写入的内容---")
        # 脱敏显示（不打印 token 字面量到终端）
        masked = "\n".join(
            (line if line.startswith("#") or not line else f"{line[:4]}*** (len={len(line)})")
            for line in content.splitlines()
        )
        print(masked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
