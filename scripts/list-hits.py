#!/usr/bin/env python3
"""列出 38 条命中明细 + 分类，供人工过目。"""
import os
import re
import subprocess
from pathlib import Path
from collections import Counter

# 路径策略（Phase D-B，2026-07-26）：扫描 git 仓库 governance/ 真值，环境变量可覆盖
REPO = Path(os.path.expanduser("~/Documents/trae_projects/agent-collaboration-standard"))
STANDARDS = Path(os.environ.get("STANDARDS_SCAN_DIR", str(REPO / "governance")))
TERMS = ["Claude Code", "claude-zhipu", "Codex", "QoderWork", "Trae IDE"]
prefix = str(STANDARDS).replace("\\", "/") + "/"
pat = "|".join(TERMS)
r = subprocess.run(["grep", "-rEn", pat, str(STANDARDS)], capture_output=True, text=True)

# 用正则: 路径(含盘符冒号) : 行号 : 内容
# Windows 路径 C:\...\file.md:lineno:content
# 盘符冒号是第 2 个字符，行号冒号在路径之后
LINE_RE = re.compile(r"^(.+?):([0-9]+):(.*)$")

def classify(rel, content):
    c = content.lower()
    if any(k in content for k in ["知识库", "knowledge"]) or "documents" in c or "Documents" in content:
        return "知识库名/路径"
    if rel.startswith("specs/") or "/specs/" in rel:
        return "治理方案文档"
    if any(k in content for k in ["插件", "兼容", "支持", "生态"]):
        return "工具生态参考"
    if any(k in content for k in ["退役", "淘汰", "retire", "下线", "废弃"]):
        return "历史叙述"
    return "其他(默认HISTORY)"

rows = []
for line in r.stdout.splitlines():
    if "[RETIRED-" in line:
        continue
    m = LINE_RE.match(line)
    if not m:
        continue
    fpath, lineno, content = m.group(1), m.group(2), m.group(3)
    fpath_norm = fpath.replace("\\", "/")
    rel = fpath_norm[len(prefix):] if fpath_norm.startswith(prefix) else fpath_norm
    for t in TERMS:
        if t in content:
            rows.append((rel, int(lineno), t, content.strip()[:110], classify(rel, content)))

rows.sort(key=lambda x: (x[0], x[1], x[2]))
print(f"共 {len(rows)} 条 (file,line,tool) 组合\n")
cls_c = Counter(r[4] for r in rows)
print("分类统计:")
for k, v in cls_c.most_common():
    print(f"  {v:3d}  {k}")
print("\n" + "=" * 90)
for rel, ln, tool, content, cls in rows:
    print(f"\n{rel}:{ln} [{tool}] [{cls}]")
    print(f"  {content}")
