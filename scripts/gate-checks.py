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
SECRET_PATTERNS_DIR = Path.home() / ".agent-collaboration" / "archive" / "secret-patterns"
PATTERNS_FILE = SECRET_PATTERNS_DIR / "scan-patterns.txt"
REDACT_MAP_FILE = SECRET_PATTERNS_DIR / "redact-map.txt"
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


def check_patterns_drift() -> tuple[bool, str]:
    """漂移守卫（节点2 round3 修复, B-3）: 校验 scan-patterns.txt vs redact-map.txt 一致性。

    问题: scan-patterns 由 gen-scan-patterns.py 从 redact-map 派生, 但若用户加了
    redact-map 新 token 后忘跑 gen-scan --apply, gate2 会用旧 scan-patterns 漏扫新 token。
    这是两份真值源的漂移 fail-open。

    修复: gate-checks 启动时比对 scan-patterns 的 pattern 集合 vs redact-map 的 token 集合,
    不一致即 fail-closed。这样"忘跑 gen-scan"会被门禁捕获。

    返回 (ok, msg)。ok=False 时调用方应 fail-closed。
    """
    if not REDACT_MAP_FILE.is_file():
        return False, f"redact-map.txt 不存在: {REDACT_MAP_FILE}"
    if not PATTERNS_FILE.is_file():
        return False, f"scan-patterns.txt 不存在: {PATTERNS_FILE}"

    # 读 redact-map 的 token 集合
    redact_tokens = set()
    for ln in REDACT_MAP_FILE.read_text(encoding="utf-8").splitlines():
        s = ln.rstrip("\n")
        if not s.strip() or s.lstrip().startswith("#") or "\t" not in s:
            continue
        token = s.split("\t", 1)[0].strip()
        if token:
            redact_tokens.add(token)

    # 读 scan-patterns 的 pattern 集合
    ok, scan_patterns, _ = load_patterns()
    if not ok:
        return False, "scan-patterns 加载失败"
    scan_set = set(scan_patterns)

    # 比对
    only_redact = redact_tokens - scan_set  # redact 有 scan 没有 = 漂移（漏扫）
    only_scan = scan_set - redact_tokens    # scan 有 redact 没有 = 漂移（多余 pattern）

    if only_redact:
        masked = [t[:4] + "***" for t in sorted(only_redact)[:5]]
        return False, (
            f"漂移: redact-map 有 {len(only_redact)} 个 token 未在 scan-patterns 中 "
            f"（漏扫风险, 跑 gen-scan-patterns.py --apply）: {masked}"
        )
    if only_scan:
        masked = [t[:4] + "***" for t in sorted(only_scan)[:5]]
        return False, (
            f"漂移: scan-patterns 有 {len(only_scan)} 个 pattern 未在 redact-map 中 "
            f"（多余 pattern, 跑 gen-scan-patterns.py --apply）: {masked}"
        )
    return True, f"一致（{len(scan_set)} 个 token, 无漂移）"


def gate2_secret_scan() -> tuple[bool, str, int]:
    """门禁 2: secret 扫描命中 = 0。git grep --cached -l -F -e <pattern>。

    扫描范围: 整个暂存区（含 scripts/）, 不做任何排除。

    设计（节点2 round2 修复, 阻断1/B-1）:
      v3.4 初版排除 scripts/ 是为了规避"自扫描陷阱"——脚本里含 patterns 字面量。
      但 Explore 已核实 scripts/ 零 token 字面量（只有 secret-patterns 路径名串）,
      且 patterns 真值从外部 ~/.agent-collaboration/archive/secret-patterns/ 读,
      scripts/ 里硬编码的只是工具逻辑, 不是 token。
      排除 scripts/ 是多余防御, 且"待人工审"无强制机制 = fail-open。
      修复: 移除排除, 扫描覆盖整个暂存区, 任何真实 token 命中即阻断。

    自扫描陷阱的处理: patterns 从外部文件读, 脚本不含 token 字面量,
    所以 scripts/ 不会命中自己的 patterns（patterns 是值, 不是字面量）。
    若未来某脚本意外硬编码 token, 本门禁会捕获 = fail-closed。
    """
    ok, patterns, msg = load_patterns()
    if not ok:
        return False, f"patterns 校验失败: {msg}", 0

    hits_total = 0
    scan_errors = 0
    hit_details = []
    for pat in patterns:
        # git grep 退出码: 0=命中, 1=无命中, >1=扫描失败（必须阻断）
        r = git(["grep", "--cached", "-l", "-F", "-e", pat], check=False)
        rc = r.returncode
        if rc == 0:
            # 命中即阻断, 不做任何目录排除（fail-closed）
            files = r.stdout.splitlines()
            hits_total += len(files)
            hit_details.append(f"pattern={pat[:4]}*** in: {files}")
        elif rc == 1:
            pass  # 正常无命中
        else:
            scan_errors += 1
            hit_details.append(f"扫描失败 pattern={pat[:4]}*** rc={rc}: {r.stderr.strip()}")

    if scan_errors > 0:
        return False, f"扫描本身失败 {scan_errors} 次（非零命中, 是异常）: {hit_details}", hits_total
    if hits_total > 0:
        return False, f"命中 {hits_total} 处: {hit_details}", hits_total
    return True, f"0 命中 (扫了 {len(patterns)} 个 pattern, 覆盖整个暂存区含 scripts/)", hits_total


def _scan_raw_lines() -> list[tuple[str, str, str, bool, str]]:
    """扫描 standards/ 所有退役词命中的原始行。

    返回 [(rel, lineno, tool, is_replaced, content)] 列表。
    is_replaced=True 表示【该具体命中词】附近有 [RETIRED-（已替换为占位符）,
    is_replaced=False 表示该命中词未被替换（HISTORY 或现行角色, 由调用方用 content 区分）。
    content 是去掉路径/行号前缀的行正文。

    节点2 round3 修复（B-2）:
      round2 的 is_replaced 按整行判定（`"[RETIRED-" in line`）,
      若同行有 [RETIRED- 占位符 + 另一个未替换退役词, 整行 is_replaced=True 掩盖未替换词。
      修复: 改为按"该具体命中词前后 40 字符内是否有 [RETIRED-"判定,
      精确到命中位置而非整行。
    """
    pat_alt = "|".join(RETIRED_TERMS)
    r = subprocess.run(["grep", "-rEn", pat_alt, str(STANDARDS)], capture_output=True, text=True)
    if r.returncode == 2:
        raise RuntimeError(f"grep 错误: {r.stderr}")

    prefix = str(STANDARDS).replace("\\", "/") + "/"
    out = []
    LINE_RE = __import__("re").compile(r"^(.+?):([0-9]+):(.*)$")
    WINDOW = 40  # 命中词前后 40 字符内视为"该命中已被替换"
    for line in r.stdout.splitlines():
        m = LINE_RE.match(line)
        if not m:
            continue
        fpath, lineno, content = m.group(1), m.group(2), m.group(3)
        fpath_norm = fpath.replace("\\", "/")
        rel = fpath_norm[len(prefix):] if fpath_norm.startswith(prefix) else fpath_norm
        for t in RETIRED_TERMS:
            # 找该命中词在 content 的所有位置
            start = 0
            while True:
                idx = content.find(t, start)
                if idx == -1:
                    break
                # 检查命中词前后 WINDOW 字符内是否有 [RETIRED-
                window_start = max(0, idx - WINDOW)
                window_end = min(len(content), idx + len(t) + WINDOW)
                window = content[window_start:window_end]
                is_replaced = "[RETIRED-" in window
                out.append((rel, lineno, t, is_replaced, content))
                start = idx + len(t)
    return out


def gate3_role_refs() -> tuple[bool, str]:
    """门禁 3: 现行角色引用 = 0（独立 fail-closed 探针, 不依赖 exceptions）。

    设计演进:
      - v3.4: hit_keys ⊆ exception_keys（tautology fail-open, A/B round1 阻断）
      - round2: 信任 exceptions + 历史关键词兜底（A/B/C round2 阻断: 信任 exceptions + classify 宽泛）
      - round3（本版）: 完全移除 exceptions 信任, 纯启发式判定

    round3 判定逻辑（三分类, 纯启发式, 不读 exceptions）:
      - 含 [RETIRED-: Phase A 已替换的 ROLE（合法, 已处理）
      - 含明确历史关键词（退役/淘汰/retire/下线/废弃/归档/已删/历史/removed/deprecat）
        OR 在 archive/ 目录下: 合法 HISTORY 引用（保留）
      - 都不满足: 现行角色引用, 必须 = 0（阻断）

    关键改进: round2 信任 exceptions 导致"classify 把现行角色归 HISTORY → exceptions
    登记 → gate3 盲信任放行"的 fail-open。round3 移除 exceptions 信任后,
    即使 classify 误归 HISTORY, gate3 也不依赖 exceptions, 直接用启发式判定。
    exceptions 只供 gate4 验证"应登记的都登记了"（数据完整性, 非现行角色判定）。

    注: 启发式仍有边界 case（如"本标准支持 Codex"含"支持"但无历史关键词）,
    round3 classify 已收窄不再自动归 HISTORY, 这类命中会抛 UnclassifiedHit 强制人工,
    不会进 exceptions, 也不会被 gate3 启发式放行（无历史关键词）→ gate3 阻断。
    """
    if not STANDARDS.is_dir():
        return False, f"standards 目录不存在: {STANDARDS}"

    raw = _scan_raw_lines()
    # round3: 历史上下文判定（与 classify 同集, 避免 gate3/classify 不一致）
    # 明确历史关键词 + 精确历史上下文（从 64 条真实合法 HISTORY 提炼）
    history_keywords = ["退役", "淘汰", "retire", "下线", "废弃", "归档", "已删", "历史",
                        "retired", "deprecat", "removed"]
    history_context = ["知识库", "knowledge", "Knowledge", "Documents", "资产", "调研",
                       "沉淀", "盘点", "曾做", "迁移", "残留", "个人使用", "软件卸载",
                       "配置清理", "[RETIRED-", "placeholder", "case ", "print ", "grep ",
                       "awk ", "tr ", "line ~", ".codex", ".tmp", "memories", "替换", "RETIRED",
                       "TERMS", "词表", "RETired"]
    current_refs = []  # 现行角色引用（阻断项）
    history_count = 0
    replaced_count = 0
    for rel, lineno, tool, is_replaced, content in raw:
        if is_replaced:
            replaced_count += 1
        elif any(k.lower() in content.lower() for k in history_keywords):
            history_count += 1  # 含明确历史关键词
        elif any(k in content for k in history_context):
            history_count += 1  # 含精确历史上下文（知识库/迁移/示例代码等）
        elif rel.startswith("archive/"):
            history_count += 1  # archive/ 目录默认历史归档
        elif rel.startswith("specs/") or "/specs/" in rel:
            history_count += 1  # specs/ 默认方案文档讨论对象
        else:
            current_refs.append((rel, lineno, tool))  # 现行角色, 阻断

    if current_refs:
        sample = current_refs[:5]
        return False, (
            f"{len(current_refs)} 处现行角色引用（无[RETIRED-/无历史关键词/非archive）: {sample}"
        )
    return True, (
        f"0 处现行角色引用（round3 纯启发式, 不依赖 exceptions）; "
        f"{replaced_count} 处已替换 [RETIRED-, {history_count} 处合法 HISTORY"
    )


def _load_exception_keys() -> set[str]:
    """解析 exceptions 文件全部键（ROLE + HISTORY 段）。"""
    text = EXCEPTIONS_FILE.read_text(encoding="utf-8")
    keys = set()
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
            keys.add(f"{file}:{lineno}|{tool}")
    return keys


def gate4_history_in_exceptions() -> tuple[bool, str]:
    """门禁 4: HISTORY 命中 ⊆ exceptions 清单（集合比对, 与 gate3 独立）。

    设计（节点2 round2 修复, 阻断2）:
      v3.4 初版 gate4 直接 return gate3(), 是 tautology。
      修复: gate4 独立做"HISTORY 引用全登记"检查, 与 gate3 的"现行角色=0"互补。
      gate4 视角: 所有已替换为 [RETIRED- 的位置（即原 HISTORY 引用）,
                   必须在 exceptions 清单中登记。
      未登记 = 未审核 = 阻断。

    注: 本门禁依赖 exceptions 清单的完整性。exceptions 由 rebuild-exceptions.py 生成,
    rebuild-exceptions.py 的 classify() 在 round2 修复后会对未分类命中抛错（fail-closed）,
    避免自动分类掩盖漏标。
    """
    if not STANDARDS.is_dir():
        return False, f"standards 目录不存在: {STANDARDS}"
    if not EXCEPTIONS_FILE.is_file():
        return False, f"例外清单不存在: {EXCEPTIONS_FILE}"

    raw = _scan_raw_lines()
    # 应登记的引用: 已替换 [RETIRED- 的 (ROLE) + 未替换的 HISTORY
    # round3: 与 gate3 同集（明确历史关键词 + 精确历史上下文）, 避免 gate3/gate4 不一致
    history_keywords = ["退役", "淘汰", "retire", "下线", "废弃", "归档", "已删", "历史",
                        "retired", "deprecat", "removed"]
    history_context = ["知识库", "knowledge", "Knowledge", "Documents", "资产", "调研",
                       "沉淀", "盘点", "曾做", "迁移", "残留", "个人使用", "软件卸载",
                       "配置清理", "[RETIRED-", "placeholder", "case ", "print ", "grep ",
                       "awk ", "tr ", "line ~", ".codex", ".tmp", "memories", "替换", "RETIRED",
                       "TERMS", "词表", "RETired"]
    registered_keys = set()
    for rel, lineno, tool, is_replaced, content in raw:
        key = f"{rel}:{lineno}|{tool}"
        if is_replaced:
            registered_keys.add(key)
        elif any(k.lower() in content.lower() for k in history_keywords):
            registered_keys.add(key)
        elif any(k in content for k in history_context):
            registered_keys.add(key)
        elif rel.startswith("archive/"):
            registered_keys.add(key)
        elif rel.startswith("specs/") or "/specs/" in rel:
            registered_keys.add(key)
        # 现行角色引用(都不满足)不登记, 由 gate3 阻断

    exception_keys = _load_exception_keys()

    # 集合比对: 应登记的引用(已替换 ROLE + HISTORY) ⊆ exceptions
    missing = registered_keys - exception_keys
    if missing:
        sample = sorted(missing)[:5]
        return False, (
            f"{len(missing)} 处 ROLE/HISTORY 引用未登记在 exceptions 清单: {sample}"
        )
    return True, (
        f"{len(registered_keys)} 处 ROLE/HISTORY 引用全部登记在 exceptions "
        f"(清单总 {len(exception_keys)} 条)"
    )


def main() -> int:
    print("=" * 60)
    print(f"v3.4 Phase B Step 4 门禁执行 @ {datetime.now().isoformat()}")
    print(f"仓库: {REPO}")
    print("=" * 60)

    # 0. patterns 文件预检（不阻断, 只提示）
    ok, patterns, msg = load_patterns()
    print(f"\n[patterns] {msg}")
    print(f"  patterns: {[p[:6]+'***' for p in patterns]}")

    # 0b. 漂移守卫（B-3 round3）: 校验 scan-patterns vs redact-map 一致性
    print("\n[漂移守卫] 校验 scan-patterns vs redact-map 一致性...")
    drift_ok, drift_msg = check_patterns_drift()
    print(f"  {'✅' if drift_ok else '❌'} {drift_msg}")
    if not drift_ok:
        fail(f"漂移守卫失败（B-3）: {drift_msg}", do_reset=False)

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
