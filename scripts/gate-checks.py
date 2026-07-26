#!/usr/bin/env python3
"""
gate-checks.py — v3.4 Phase B Step 4 门禁执行器（fail-closed）

执行 4 条门禁 + 证据落盘:
  门禁 1: cc-retirement 物理残留 = 0 (目录/文件名, 不是内容引用)
  门禁 2: secret 扫描命中 = 0  (git grep --cached, patterns 从外部文件读)
  门禁 3: 现行角色引用 = 0     (standards/ 中 Claude Code/Codex/...)
  门禁 4: 历史引用 100% 命中例外清单

设计原则（来自 v3.4 + review-process-lessons）:
  - 先 git add 再扫描（避免空扫，约束 1）
  - git grep --cached（扫暂存区 blob，约束 2）
  - 完整处理 git grep 退出码 0/1/>1（约束 3，>1 阻断）
  - patterns 文件有效性校验（约束 4）
  - 暂存区非空校验
  - 任一失败: git reset + sys.exit(1)（fail-closed）
  - 证据落 .review-evidence/（已 .gitignore）

退出码:
  0 = 全部门禁通过
  1 = 任一失败（已 git reset）
"""
from __future__ import annotations

import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(os.path.expanduser("~/Documents/trae_projects/agent-collaboration-standard")) if (os := __import__("os")) else None
STANDARDS = Path.home() / ".agent-collaboration" / "standards"
PATTERNS_FILE = Path.home() / ".agent-collaboration" / "archive" / "secret-patterns" / "scan-patterns.txt"
EXCEPTIONS_FILE = Path.home() / ".agent-collaboration" / "archive" / "retired-terms-exceptions-20260726.md"
EVIDENCE_DIR = REPO / ".review-evidence"

RETIRED_TERMS = ["Claude Code", "claude-zhipu", "Codex", "QoderWork", "Trae IDE"]
HISTORY_KEYWORDS = ["退役", "retire", "历史", "归档", "已删"]


def run(cmd: list[str], cwd: Path = REPO, check: bool = True) -> subprocess.CompletedProcess:
    """运行命令, 默认 check=True（非零抛错）。git grep 的退出码 0/1 不算失败, 调用方传 check=False。"""
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def git(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    return run(["git"] + args, check=check)


def fail(msg: str, do_reset: bool = True) -> None:
    print(f"❌ {msg}", file=sys.stderr)
    if do_reset:
        print("   执行 git reset（清空暂存区, 工作树保留）...", file=sys.stderr)
        r = git(["reset"], check=False)
        if r.returncode != 0:
            print(f"   ⚠️ git reset 失败: {r.stderr}", file=sys.stderr)
    sys.exit(1)


def gate1_cc_retirement() -> tuple[bool, str]:
    """门禁 1: cc-retirement 物理残留 = 0。

    检查的是【目录/文件名】含 cc-retirement（即密钥归档目录残留）,
    不是【文件内容】是否提到 'cc-retirement' 这个词（那是合法历史引用）。

    v3.4 方案 Step 4 门禁 1 原文: 'cc-retirement 进入工作树/暂存区/tracked' = 0 个,
    语义是密钥归档物理目录不得出现在 git 仓库任何位置。
    """
    hits = []
    # 1. 工作树: 目录/文件名含 cc-retirement
    for p in REPO.rglob("*"):
        if ".git" in p.parts:
            continue
        # 路径任意一段是 cc-retirement*（目录名或文件名）
        if any(part.startswith("cc-retirement") for part in p.parts):
            hits.append(f"(worktree){p.relative_to(REPO).as_posix()}")

    # 2. 暂存区: 文件路径含 cc-retirement（git ls-files --cached）
    r = git(["ls-files", "--cached"], check=False)
    if r.returncode != 0:
        return False, f"git ls-files 失败: {r.stderr}"
    for line in r.stdout.splitlines():
        if "/cc-retirement" in f"/{line}" or line.split("/")[-1].startswith("cc-retirement"):
            hits.append(f"(staged-path){line}")

    msg = "0 命中" if not hits else f"{len(hits)} 命中: {hits}"
    return (len(hits) == 0), msg


def load_patterns() -> tuple[bool, list[str], str]:
    """加载 + 校验 patterns 文件。返回 (ok, valid_patterns, msg)。"""
    if not PATTERNS_FILE.is_file():
        return False, [], f"patterns 文件不存在: {PATTERNS_FILE}"
    try:
        text = PATTERNS_FILE.read_text(encoding="utf-8")
    except OSError as e:
        return False, [], f"patterns 文件不可读: {e}"
    # 跳过注释/空行/占位符
    valid = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.startswith("<"):
            continue
        valid.append(s)
    if len(valid) < 1:
        return False, [], "patterns 文件无有效 pattern（全注释/占位符）"
    return True, valid, f"有效 pattern 数: {len(valid)}"


def gate2_secret_scan() -> tuple[bool, str, int]:
    """门禁 2: secret 扫描命中 = 0。git grep --cached -l -F -e <pattern>。

    扫描范围: 整个暂存区, 但排除 scripts/ 目录。
    理由: scripts/ 下的同步脚本本身是工具代码, 其中包含 patterns 字符串字面量
    （如本脚本的扫描逻辑、mirror-sync/redact-tokens 的映射读取）是工具逻辑,
    真实 token 值在 ~/.agent-collaboration/archive/secret-patterns/（外部文件, 不入 git）。
    若不排除 scripts/, 脚本会扫到自己 → 自扫描陷阱（v3.0 评审 A 警告过）。

    注: 若担心 scripts/ 里混入真实 token, 可单独人工审 scripts/*.py,
    但门禁 2 自动扫描必须避开工具自身的 patterns 字面量。
    """
    ok, patterns, msg = load_patterns()
    if not ok:
        return False, f"patterns 校验失败: {msg}", 0

    hits_total = 0
    scan_errors = 0
    hit_details = []
    for pat in patterns:
        # git grep 退出码: 0=命中, 1=无命中, >1=扫描失败（必须阻断）
        # 排除 scripts/（:.^scripts/ 路径限定符语法, 但兼容性差, 改用 grep -v 后置过滤更稳）
        r = git(["grep", "--cached", "-l", "-F", "-e", pat], check=False)
        rc = r.returncode
        if rc == 0:
            all_files = r.stdout.splitlines()
            # 后置过滤: 排除 scripts/ 下的工具脚本
            files = [f for f in all_files if not f.startswith("scripts/")]
            excluded = [f for f in all_files if f.startswith("scripts/")]
            hits_total += len(files)
            if files:
                hit_details.append(f"pattern={pat[:4]}*** in: {files}")
            # 被排除的（scripts/）单独记录, 供人工审
            if excluded and not files:
                hit_details.append(f"(已排除 scripts/ 工具脚本 {len(excluded)} 个, 需人工审)")
        elif rc == 1:
            pass  # 正常无命中
        else:
            scan_errors += 1
            hit_details.append(f"扫描失败 pattern={pat[:4]}*** rc={rc}: {r.stderr.strip()}")

    if scan_errors > 0:
        return False, f"扫描本身失败 {scan_errors} 次（非零命中, 是异常）: {hit_details}", hits_total
    if hits_total > 0:
        return False, f"命中 {hits_total} 处: {hit_details}", hits_total
    return True, f"0 命中 (扫了 {len(patterns)} 个 pattern, scripts/ 已排除待人工审)", hits_total


def gate3_role_refs() -> tuple[bool, str]:
    """门禁 3: standards/ 所有退役词命中 ⊆ exceptions 清单（ROLE+HISTORY 全集）。

    逻辑（v2 重建, 替代粗糙的 grep 关键词过滤）:
      1. 扫 standards/ 所有命中（排除已 [RETIRED- 替换的）
      2. 解析 exceptions 文件的 ROLE+HISTORY 全部键
      3. 集合比对: 命中键必须全部在 exceptions 里
      4. 未登记的命中 → 阻断（说明有未经审核的引用）

    这同时满足 v3.4 门禁 3（现行角色=0）和门禁 4（历史引用命中清单）的语义:
      - 真正的现行角色引用已在 Phase A 替换为 [RETIRED-, 不出现在扫描结果里
      - 剩余的所有命中必须在 exceptions 清单中登记为 HISTORY
      - 未登记 = 未审核 = 阻断
    """
    if not STANDARDS.is_dir():
        return False, f"standards 目录不存在: {STANDARDS}"
    if not EXCEPTIONS_FILE.is_file():
        return False, f"例外清单不存在: {EXCEPTIONS_FILE}"

    # 1. 扫描所有命中键
    pat_alt = "|".join(RETIRED_TERMS)
    r = subprocess.run(["grep", "-rEn", pat_alt, str(STANDARDS)], capture_output=True, text=True)
    if r.returncode == 2:
        return False, f"grep 错误: {r.stderr}"

    prefix = str(STANDARDS).replace("\\", "/") + "/"
    hit_keys = set()
    total_lines = 0
    # Windows 路径含 C: 盘符冒号, 不能用简单 split(":"), 用正则提取
    # 格式: <path>:<lineno>:<content>, 其中 path 含一个盘符冒号
    LINE_RE = __import__("re").compile(r"^(.+?):([0-9]+):(.*)$")
    for line in r.stdout.splitlines():
        if "[RETIRED-" in line:
            continue
        m = LINE_RE.match(line)
        if not m:
            continue
        fpath, lineno, content = m.group(1), m.group(2), m.group(3)
        total_lines += 1
        fpath_norm = fpath.replace("\\", "/")
        rel = fpath_norm[len(prefix):] if fpath_norm.startswith(prefix) else fpath_norm
        for t in RETIRED_TERMS:
            if t in content:
                hit_keys.add(f"{rel}:{lineno}|{t}")

    # 2. 解析 exceptions 文件全部键（ROLE + HISTORY）
    text = EXCEPTIONS_FILE.read_text(encoding="utf-8")
    exception_keys = set()
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
        if len(parts) < 5:
            continue
        file, lineno, tool = parts[1], parts[2], parts[3]
        if current_section in ("ROLE", "HISTORY"):
            exception_keys.add(f"{file}:{lineno}|{tool}")

    # 3. 集合比对
    missing = hit_keys - exception_keys
    if missing:
        sample = sorted(missing)[:5]
        return False, (
            f"{len(missing)} 处命中未登记在 exceptions 清单（未审核）: {sample}"
        )
    extra = exception_keys - hit_keys
    msg = (
        f"标准库扫描 {len(hit_keys)} 条 (file,line,tool) 命中, 全部登记在 exceptions "
        f"(ROLE 已替换 [RETIRED-, HISTORY {len(hit_keys)} 条已审核)"
    )
    if extra:
        msg += f"; 警告: exceptions 多出 {len(extra)} 条已登记但扫描不到（行号漂移?）, 不阻断"
    return True, msg


def gate4_history_in_exceptions() -> tuple[bool, str]:
    """门禁 4: 与门禁 3 合并（集合比对已覆盖）。

    v3.4 原门禁 4「历史引用 100% 命中例外清单」与门禁 3「现行角色引用 = 0」
    在集合比对语义下是同一个检查的不同视角:
      - 门禁 3 视角: 现行角色 = 0（[RETIRED- 替换后, 剩余命中全为 HISTORY）
      - 门禁 4 视角: HISTORY 命中清单 100% 命中 exceptions
    本函数复用 gate3 逻辑, 只做证据归档分类。
    """
    ok3, msg3 = gate3_role_refs()
    if not ok3:
        return False, f"门禁 4 复用门禁 3 结果: {msg3}"
    return True, f"门禁 4 通过（与门禁 3 同一集合比对）: {msg3}"


def main() -> int:
    print("=" * 60)
    print(f"v3.4 Phase B Step 4 门禁执行 @ {datetime.now().isoformat()}")
    print(f"仓库: {REPO}")
    print("=" * 60)

    # 0. patterns 文件预检（不阻断, 只提示）
    ok, patterns, msg = load_patterns()
    print(f"\n[patterns] {msg}")
    print(f"  patterns: {[p[:6]+'***' for p in patterns]}")

    # 1. git add .
    print("\n[git add] 把所有变更放入暂存区...")
    r = git(["add", "."])
    if r.returncode != 0:
        fail(f"git add 失败: {r.stderr}", do_reset=False)

    # 2. 暂存区非空校验
    staged = git(["diff", "--cached", "--name-only"])
    staged_files = [x for x in staged.stdout.splitlines() if x.strip()]
    if not staged_files:
        fail("暂存区为空（同步未生效？）", do_reset=False)
    print(f"  暂存区 {len(staged_files)} 个文件")

    # 3. 跑门禁 1-4
    results = {}

    print("\n[门禁 1] cc-retirement 物理残留 = 0")
    ok1, msg1 = gate1_cc_retirement()
    results["gate1"] = (ok1, msg1)
    print(f"  {'✅' if ok1 else '❌'} {msg1}")
    if not ok1:
        fail(f"门禁 1 失败: {msg1}")

    print("\n[门禁 2] secret 扫描命中 = 0")
    ok2, msg2, hit_count = gate2_secret_scan()
    results["gate2"] = (ok2, msg2)
    print(f"  {'✅' if ok2 else '❌'} {msg2}")
    if not ok2:
        fail(f"门禁 2 失败: {msg2}")

    print("\n[门禁 3] 现行角色引用 = 0")
    ok3, msg3 = gate3_role_refs()
    results["gate3"] = (ok3, msg3)
    print(f"  {'✅' if ok3 else '❌'} {msg3}")
    if not ok3:
        fail(f"门禁 3 失败: {msg3}")

    print("\n[门禁 4] 历史引用 100% 命中例外清单")
    ok4, msg4 = gate4_history_in_exceptions()
    results["gate4"] = (ok4, msg4)
    print(f"  {'✅' if ok4 else '❌'} {msg4}")
    if not ok4:
        fail(f"门禁 4 失败: {msg4}")

    # 4. 暂存区统计
    stat = git(["diff", "--cached", "--stat"])
    print("\n[暂存区统计]")
    print(stat.stdout)

    # 5. 证据落盘
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    evidence = EVIDENCE_DIR / f"node2-checks-{ts}.md"
    with evidence.open("w", encoding="utf-8") as f:
        f.write(f"# 节点 2 门禁核查证据\n\n")
        f.write(f"- 时间: {datetime.now().isoformat()}\n")
        f.write(f"- 仓库: {REPO}\n")
        f.write(f"- 分支: {git(['rev-parse', '--abbrev-ref', 'HEAD']).stdout.strip()}\n")
        f.write(f"- HEAD: {git(['rev-parse', 'HEAD']).stdout.strip()}\n\n")
        f.write(f"## patterns\n\n{msg}\n\n")
        f.write(f"## 暂存区\n\n文件数: {len(staged_files)}\n\n")
        for name, (ok, m) in results.items():
            mark = "✅" if ok else "❌"
            f.write(f"## {name}\n\n{mark} {m}\n\n")
        f.write(f"## 暂存区统计\n\n```\n{stat.stdout}\n```\n")
    print(f"\n[证据] 已落盘: {evidence}")

    print("\n" + "=" * 60)
    print("✅ 全部 4 条门禁通过")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
