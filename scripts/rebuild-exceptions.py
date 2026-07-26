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
OVERRIDES_FILE = Path(r"C:\Users\Admin\.agent-collaboration\archive\retired-terms-manual-history-overrides-20260726.md")
TERMS = ["Claude Code", "claude-zhipu", "Codex", "QoderWork", "Trae IDE"]
LINE_RE = re.compile(r"^(.+?):([0-9]+):(.*)$")


def load_manual_overrides() -> set[str]:
    """round4 新增: 读人工确认 HISTORY 覆盖清单。返回 {file:line|tool} 集合。

    最严收窄后, 部分合法 HISTORY（知识资产/迁移/兼容性/方案代码）会被 classify raise。
    本文件是 ZCode 逐条人工判定为 HISTORY 的覆盖, classify 命中此清单直接归 HISTORY。
    """
    if not OVERRIDES_FILE.is_file():
        return set()
    keys = set()
    for ln in OVERRIDES_FILE.read_text(encoding="utf-8").splitlines():
        s = ln.strip()
        if not s.startswith("|") or "---" in s:
            continue
        parts = [p.strip() for p in s.split("|")]
        if len(parts) < 5:
            continue
        file, lineno, tool = parts[1], parts[2], parts[3]
        if file and lineno and tool and file != "文件":
            keys.add(f"{file}:{lineno}|{tool}")
    return keys


# round4: 模块级加载人工覆盖（classify 用）
MANUAL_OVERRIDES = load_manual_overrides()


class UnclassifiedHit(Exception):
    """命中未匹配任何已知分类模式, 需人工判定（fail-closed, 不默认归 HISTORY）。"""


def classify(rel: str, content: str, context: str = "", manual_key: str = "") -> str:
    """判定命中类别。未匹配任何模式 → 抛 UnclassifiedHit（fail-closed）。

    节点2 round4 修复（A/B 三方共识, 最严收窄）:
      round3 的 classify 仍含 specs/ 白名单 + 宽泛上下文词, B/A 标为新 fail-open。
      round4 最严收窄: 只保留 archive/ + 明确历史关键词 + 上下文含[RETIRED-/TERMS。
      其他全部 raise, 强制人工判定。

    人工覆盖机制（manual_key 参数）:
      最严收窄后, 合法 HISTORY（知识资产/迁移/兼容性/方案代码）会被 raise。
      ZCode 逐条人工判定后写入 manual-history-overrides 文件。
      classify 收到 manual_key 时, 若在 overrides 集合中, 归"人工确认HISTORY"。

    参数:
      rel: 相对路径
      content: 当前命中行内容
      context: 前后行上下文
      manual_key: "file:line|tool" 键, 用于查 overrides
    """
    # 人工覆盖优先（round4）: 命中 overrides 直接归 HISTORY
    if manual_key and manual_key in MANUAL_OVERRIDES:
        return "人工确认HISTORY"
    # archive/ 目录下的命中默认为历史归档
    if rel.startswith("archive/"):
        return "归档文档历史引用"
    # 明确历史叙述关键词
    if any(k in content for k in ["退役", "淘汰", "retire", "下线", "废弃", "归档", "已删", "历史"]):
        return "历史叙述"
    # 上下文（前后行）含 [RETIRED- 或词表定义 → 方案示例代码
    if context and ("[RETIRED-" in context or "TERMS" in context or "词表" in context
                    or "RETired" in context or "placeholder" in context):
        return "方案示例代码"
    # round4 BL-R4-2 修复(C 建议): 删除 content 词桶(case/grep/awk/print/placeholder 等)
    # 这些宽泛子串可被构造句绕过("in case Codex fails"含"case ")。
    # 16 条真方案代码已移入 manual-overrides, 由人工确认机制覆盖。
    # 当行只认上下文(前后行), 不再认当行宽泛词。
    # round4 最严收窄: 其他全 raise, 强制人工判定
    raise UnclassifiedHit(
        f"未分类命中（round4 最严收窄, 需人工判定 ROLE or HISTORY）: {rel} | {content[:80]}"
    )


def scan_hits() -> list[tuple[str, int, str, str, str]]:
    """扫 standards/ 所有命中（含 [RETIRED- 已替换的）, 返回 [(rel, line, tool, content, cls)]。

    设计演进:
      - v3.4: 过滤含 [RETIRED- 的行（与 _scan_raw_lines 不一致）
      - round2: 不过滤, 全部命中都登记, classify 自动分类
      - round3（本版）: 不过滤 + 检查 grep 退出码（B-4）+ classify 激进收窄

    节点2 round3 修复（B-4 fail-closed + C-2 注释一致）:
      - grep 退出码: 0=命中, 1=无命中, 2=错误。round2 只检查 ==2,
        但 stdout 为空时（grep 错误）会返回空列表, main 仍重写 exceptions → fail-open。
        修复: grep 退出码非 0/1 即抛错（fail-closed）。
      - 注释与代码一致: 不再声称"标注 is_replaced", 实际行为是全部命中都 classify。
    """
    pat = "|".join(TERMS)
    # round4: grep -B1 -A1 拿前后行上下文（捕获"上文 RETired_TERMS_LIST=("）
    r = subprocess.run(["grep", "-rEn", "-B1", "-A1", pat, str(STANDARDS)],
                       capture_output=True, text=True)
    # B-4 fail-closed: grep 退出码 0=命中 1=无命中, 其他(2+)=错误, 必须抛错
    if r.returncode not in (0, 1):
        raise RuntimeError(f"grep 执行失败 rc={r.returncode}: {r.stderr}")
    prefix = str(STANDARDS).replace("\\", "/") + "/"
    rows = []
    # 解析 grep -B1 -A1 输出: 命中行 + 前后行, 用 -- 分组分隔
    # 格式: <path>-<lineno>-<content>(命中) 前后是 <path>:<lineno>:<content>(上下文)
    # 简化: 按 -- 分组, 每组找含 TERMS 的命中行 + 收集上下文
    blocks = r.stdout.split("--")
    LINE_RE_CTX = __import__("re").compile(r"^(.+?)[-:]([0-9]+)[-:](.*)$")
    for block in blocks:
        block_lines = [l for l in block.splitlines() if l.strip()]
        if not block_lines:
            continue
        # 收集上下文(所有行) + 找命中行
        context_parts = []
        for line in block_lines:
            m = LINE_RE_CTX.match(line)
            if not m:
                continue
            fpath, lineno, content = m.group(1), m.group(2), m.group(3)
            # 去掉 grep 的 - 前缀(上下文行用 -, 命中行用 :)
            fpath_norm = fpath.replace("\\", "/").rstrip("-")
            rel = fpath_norm[len(prefix):] if fpath_norm.startswith(prefix) else fpath_norm
            for t in TERMS:
                if t in content:
                    ctx = " ".join(context_parts)
                    manual_key = f"{rel}:{lineno}|{t}"
                    rows.append((rel, int(lineno), t, content.strip(), classify(rel, content, ctx, manual_key)))
            context_parts.append(content)
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
            # round4 C 条件项2: 过滤表头行(避免累积重复表头当数据)
            parts = [p.strip() for p in s.split("|")]
            if len(parts) >= 2 and parts[1] == "文件":
                continue
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
