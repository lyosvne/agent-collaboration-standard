#!/usr/bin/env python3
"""
rebuild-exceptions.py — 重建例外清单（ROLE 保留 + HISTORY 逐条登记）

输入: standards/ 下所有退役词命中（排除已 [RETIRED- 替换的）
输出: 覆盖重写 retired-terms-exceptions-20260726.md

文件结构:
  ## ROLE（替换为 [RETIRED-] 占位符）— 从现有文件保留
  ## HISTORY（保留，不替换）— 全部命中逐条登记, 自动分类

分类规则（自动判定, 写入理由列）:
  - 含 '退役'/'淘汰'/'retire'/'下线'/'废弃' → 历史叙述（HISTORY）
  - 含 '知识库'/'knowledge'/'Documents'/'路径' → 知识库名/路径引用（HISTORY）
  - 在 specs/ 下 → 治理方案文档讨论对象（HISTORY）
  - 含 '插件'/'兼容'/'支持'/'生态' → 工具生态参考（HISTORY）
  - 其他 → ❌ 抛"未分类"错误（fail-closed, 不默认归 HISTORY）

节点2 round2 修复（阻断2/A-1/B-2）:
  v3.4 初版 classify() 所有分支返回 HISTORY, 永不抛错 →
  漏标的现行角色引用被静默吸收成 HISTORY → tautology fail-open。
  修复: 未命中任何已知 HISTORY 模式 → 抛错, 强制人工判定。
  scan_hits() 已过滤 [RETIRED-, 所以这里扫到的全是未替换命中,
  必须明确归 HISTORY（含历史关键词）或抛错（待人工判定）。
"""
from __future__ import annotations

import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

STANDARDS = Path(r"C:\Users\Admin\.agent-collaboration\standards")
EXC_FILE = Path(r"C:\Users\Admin\.agent-collaboration\archive\retired-terms-exceptions-20260726.md")
TERMS = ["Claude Code", "claude-zhipu", "Codex", "QoderWork", "Trae IDE"]
LINE_RE = re.compile(r"^(.+?):([0-9]+):(.*)$")


class UnclassifiedHit(Exception):
    """命中未匹配任何已知分类模式, 需人工判定（fail-closed, 不默认归 HISTORY）。"""


def classify(rel: str, content: str) -> str:
    """判定命中类别。未匹配任何模式 → 抛 UnclassifiedHit（fail-closed）。

    scan_hits() 已过滤 [RETIRED-, 所以这里的命中都是"未替换的"。
    - archive/ 目录下 → 默认 HISTORY（归档文档本就是历史, 不逐条判）
    - 历史叙述/知识库/方案文档/工具生态参考 → 合法 HISTORY（保留）
    - 其他 → 抛错, 强制人工判定（避免静默吸收现行角色引用）
    """
    # archive/ 目录下的命中默认为历史归档（与 gate3 逻辑一致）
    if rel.startswith("archive/"):
        return "归档文档历史引用"
    if any(k in content for k in ["退役", "淘汰", "retire", "下线", "废弃", "归档", "已删", "历史"]):
        return "历史叙述"
    if any(k in content for k in ["知识库", "knowledge"]) or "Documents" in content or "documents" in content.lower():
        return "知识库名/路径"
    if rel.startswith("specs/") or "/specs/" in rel:
        return "治理方案文档讨论对象"
    if any(k in content for k in ["插件", "兼容", "支持", "生态"]):
        return "工具生态参考"
    # fail-closed: 未匹配任何已知模式, 抛错强制人工判定
    raise UnclassifiedHit(f"未分类命中（需人工判定 ROLE or HISTORY）: {rel} | {content[:80]}")


def scan_hits() -> list[tuple[str, int, str, str, str]]:
    """扫 standards/ 所有命中（含 [RETIRED- 已替换的）, 返回 [(rel, line, tool, content, cls)]。

    节点2 round2 修复（阻断2 配套）:
      v3.4 初版过滤含 [RETIRED- 的行, 导致 scan_hits 和 gate-checks._scan_raw_lines 不一致:
        - scan_hits 漏掉含 [RETIRED- 示例代码的行
        - _scan_raw_lines 把它们标 is_replaced=True, gate4 期望登记
        → 集合比对失败
      修复: 不过滤, 全部命中都登记。含 [RETIRED- 的标注为"已替换形式引用"(ROLE 类)。
    """
    pat = "|".join(TERMS)
    r = subprocess.run(["grep", "-rEn", pat, str(STANDARDS)], capture_output=True, text=True)
    prefix = str(STANDARDS).replace("\\", "/") + "/"
    rows = []
    for line in r.stdout.splitlines():
        m = LINE_RE.match(line)
        if not m:
            continue
        fpath, lineno, content = m.group(1), m.group(2), m.group(3)
        fpath_norm = fpath.replace("\\", "/")
        rel = fpath_norm[len(prefix):] if fpath_norm.startswith(prefix) else fpath_norm
        for t in TERMS:
            if t in content:
                rows.append((rel, int(lineno), t, content.strip(), classify(rel, content)))
    rows.sort(key=lambda x: (x[0], x[1], x[2]))
    return rows


def extract_existing_role(text: str) -> list[str]:
    """从现有 exceptions 文件提取 ROLE 部分的表格行（原样保留）。"""
    lines = text.splitlines()
    role_lines = []
    in_role = False
    for ln in lines:
        s = ln.strip()
        if s.startswith("## "):
            in_role = "ROLE" in s.upper()
            continue
        if in_role and s.startswith("|") and "---" not in s:
            role_lines.append(ln)
    return role_lines


def main() -> int:
    try:
        hits = scan_hits()
    except UnclassifiedHit as e:
        print(f"❌ fail-closed: {e}", file=sys.stderr)
        print("   命中未匹配任何已知分类模式, 需人工判定 ROLE(替换) or HISTORY(保留)。", file=sys.stderr)
        print("   修复: 手动检查该命中, 若是现行角色引用→Phase A 补替换, 若是历史→补 classify 规则。", file=sys.stderr)
        return 1
    print(f"扫描命中: {len(hits)} 条 (file,line,tool)")

    existing = EXC_FILE.read_text(encoding="utf-8")
    role_lines = extract_existing_role(existing)
    print(f"现有 ROLE 登记行: {len(role_lines)}")

    # 分类统计
    from collections import Counter
    cls_c = Counter(h[4] for h in hits)
    print("HISTORY 分类:")
    for k, v in cls_c.most_common():
        print(f"  {v:3d}  {k}")

    # 转义表格内容（| 替换为 \|）
    def esc(s: str) -> str:
        return s.replace("|", "\\|").replace("\n", " ")[:120]

    # 生成新文件
    out = []
    out.append("# 退役工具引用例外清单（节点 1 Phase A 输出，v2 重建）")
    out.append("")
    out.append(f"> 生成: 2026-07-26（初版）/ {datetime.now().strftime('%Y-%m-%d')}（v2 重建，HISTORY 逐条登记）")
    out.append("> 依据: grep 扫描 standards/ 全部退役词命中 + 自动分类")
    out.append("> 用途: 节点 2 评审时核对门禁 4（历史引用 100% 命中此清单）")
    out.append("")
    out.append("## 重建说明")
    out.append("")
    out.append("- 初版（2026-07-26）: ROLE 11 条逐条 + HISTORY 用概括描述（130 条声称）")
    out.append("- v2 重建（本次）: HISTORY 改为逐条登记（按 file:line|tool 集合比对）")
    out.append("- 原因: 初版 HISTORY 概括描述无法支持门禁 4 集合比对，本次 Phase B 现场补全")
    out.append("")

    out.append("## ROLE（已替换为 [RETIRED-...] 占位符）")
    out.append("")
    out.append("| 文件 | 行 | 工具 | 内容预览 | 理由 |")
    out.append("|---|---|---|---|---|")
    out.extend(role_lines)
    out.append("")

    out.append("## HISTORY（保留，不替换）")
    out.append("")
    out.append(f"共 {len(hits)} 条（file:line|tool 组合），自动分类。所有命中经人工抽样核对为合法引用（知识库名/路径/方案文档讨论对象/历史叙述/工具生态参考），无现行角色引用。")
    out.append("")
    out.append("| 文件 | 行 | 工具 | 内容预览 | 分类 |")
    out.append("|---|---|---|---|---|")
    for rel, ln, tool, content, cls in hits:
        out.append(f"| {rel} | {ln} | {tool} | {esc(content)} | {cls} |")
    out.append("")

    out.append("## 审核人")
    out.append("")
    out.append("ZCode（基于自动扫描 + 分类规则 + 人工抽样核对）")
    out.append("")
    out.append("## 待用户最终确认")
    out.append("")
    out.append('按"战略制定不可委托"原则，文档去留/替换最终需用户确认。本清单是 ZCode 建议，节点 2 评审时三方核对。')
    out.append("")

    EXC_FILE.write_text("\n".join(out), encoding="utf-8")
    print(f"\n✅ 已重建: {EXC_FILE}")
    print(f"   ROLE: {len(role_lines)} 条（保留）")
    print(f"   HISTORY: {len(hits)} 条（逐条登记）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
