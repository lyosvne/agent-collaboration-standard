#!/usr/bin/env python3
"""临时分析脚本：分析门禁 3 命中分布，决定关键词补齐方案。用完可删。"""
import subprocess
from pathlib import Path
from collections import Counter

STANDARDS = Path(r"C:\Users\Admin\.agent-collaboration\standards")
TERMS = ["Claude Code", "claude-zhipu", "Codex", "QoderWork", "Trae IDE"]
# 扩展历史关键词
HISTORY_KW = ["退役", "retire", "历史", "归档", "已删", "淘汰", "废弃",
              "deprecated", "was ", "had been", "previous", "原承接", "已换"]

pat = "|".join(TERMS)
r = subprocess.run(["grep", "-rEn", pat, str(STANDARDS)], capture_output=True, text=True)
lines = r.stdout.splitlines()
print(f"总命中行数: {len(lines)}")
print()

dir_counter = Counter()
remaining = []
for line in lines:
    if "[RETIRED-" in line:
        continue
    m = line.split(":", 2)
    if len(m) < 3:
        continue
    fpath, lineno, content = m
    fpath_norm = fpath.replace("\\", "/")
    prefix = "C:/Users/Admin/.agent-collaboration/standards/"
    if fpath_norm.startswith(prefix):
        fpath_norm = fpath_norm[len(prefix):]
    parent = "/".join(fpath_norm.split("/")[:-1]) or "(root)"
    dir_counter[parent] += 1
    if any(kw.lower() in content.lower() for kw in HISTORY_KW):
        continue
    remaining.append((fpath_norm, lineno, content[:140]))

print("=== 按目录分布（总命中, 含历史）===")
for d, c in dir_counter.most_common():
    print(f"  {c:3d}  {d}")
print()
print(f"=== 扩展关键词后剩余（疑似现行角色引用）: {len(remaining)} 处 ===")
for rel, ln, c in remaining:
    print(f"  {rel}:{ln}")
    print(f"    {c}")
