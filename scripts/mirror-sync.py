#!/usr/bin/env python3
"""
mirror-sync.py — 对齐 rsync -a --delete --exclude 语义的 Python 实现

用途: v3.4 同步方案 Phase B.2 执行器（git 仓库不含 rsync 二进制时的替代）

策略对齐 (rsync -a --delete --exclude):
  - mirror:          递归复制源→目标, 覆盖已有, 删除目标独有（除非命中 exclude）
  - selective-mirror: mirror + 指定 exclude 列表
  - add-only:        递归复制源→目标, 不覆盖已有, 不删除（用 safe_copy 实现）

关键设计原则（来自 v3.4 评审约束）:
  1. 默认 dry-run, 显式 --apply 才真正改盘
  2. 每个映射输出 新增/修改/删除/排除 四清单（满足节点 2 门禁 5）
  3. 任一步骤失败 sys.exit(1)（显式报错, 约束 8: 不 echo 误报成功）
  4. exclude 模式用 fnmatch（对齐 rsync --exclude glob 语义）
  5. 仅复制普通文件, 跳过 .git（不碰仓库元数据）
  6. 不保留 mtime/权限（git 只关心内容）

退出码:
  0 = 全部成功
  1 = 任意失败（已 apply 的改动需手动回滚, 见回滚模型 §4.1）
"""
from __future__ import annotations

import argparse
import filecmp
import fnmatch
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

# ---------- 工具函数 ----------

def iter_files(root: Path) -> Iterable[Path]:
    """递归遍历 root 下所有普通文件, 跳过 .git 目录。"""
    for dirpath, dirnames, filenames in os.walk(root):
        # 原地修改 dirnames 即可跳过（os.walk 标准用法）
        if ".git" in dirnames:
            dirnames.remove(".git")
        for name in filenames:
            full = Path(dirpath) / name
            if full.is_file():
                yield full


def relpath_under(path: Path, root: Path) -> str:
    """返回 path 相对于 root 的 posix 相对路径（统一用 / 分隔，便于跨平台比对）。"""
    return path.relative_to(root).as_posix()


def matches_any(rel: str, patterns: list[str]) -> bool:
    """对齐 rsync --exclude: 支持目录前缀匹配和 glob。

    rsync exclude 'foo/' 匹配名为 foo 的目录及其下所有内容;
    rsync exclude '*.bak' 匹配任意深度的该 glob.
    这里实现等价语义:
      - 以 '/' 结尾的 pattern 视为目录排除（rel 路径以该目录名开头，或路径段含该目录）
      - 其余 pattern 用 fnmatch 匹配完整 rel 路径, 以及路径中任意一段
    """
    for pat in patterns:
        if pat.endswith("/"):
            dirpat = pat.rstrip("/")
            # rel 以 "dirpat/" 开头, 或路径段恰好等于 dirpat
            if rel == dirpat or rel.startswith(dirpat + "/") or f"/{dirpat}/" in f"/{rel}/":
                return True
            continue
        # glob 匹配: 完整路径或最后一段
        if fnmatch.fnmatch(rel, pat):
            return True
        last = rel.rsplit("/", 1)[-1]
        if fnmatch.fnmatch(last, pat):
            return True
    return False


# ---------- 同步策略 ----------

@dataclass
class SyncReport:
    """单个映射的同步报告。"""
    name: str
    strategy: str
    src: str
    dst: str
    added: list[str] = field(default_factory=list)
    modified: list[str] = field(default_factory=list)
    deleted: list[str] = field(default_factory=list)
    excluded_src: list[str] = field(default_factory=list)
    skipped_existing: list[str] = field(default_factory=list)  # add-only 不覆盖
    errors: list[str] = field(default_factory=list)

    def is_clean(self) -> bool:
        return not self.errors


def mirror(
    name: str, src: Path, dst: Path, excludes: list[str], apply: bool
) -> SyncReport:
    """mirror / selective-mirror: 覆盖 + 删除目标独有（排除项保留）。"""
    report = SyncReport(name=name, strategy="mirror", src=str(src), dst=str(dst))

    src_files: dict[str, Path] = {}
    for f in iter_files(src):
        rel = relpath_under(f, src)
        if matches_any(rel, excludes):
            report.excluded_src.append(rel)
            continue
        src_files[rel] = f

    dst_files: dict[str, Path] = {}
    if dst.exists():
        for f in iter_files(dst):
            rel = relpath_under(f, dst)
            if matches_any(rel, excludes):
                # 目标侧的排除项不动（与 rsync --delete 配合 --exclude 一致: 排除项不被删）
                report.excluded_src.append(f"(dst-keep){rel}")
                continue
            dst_files[rel] = f

    # 新增 + 修改
    for rel, sp in src_files.items():
        dp = dst / rel
        if rel not in dst_files:
            report.added.append(rel)
            if apply:
                dp.parent.mkdir(parents=True, exist_ok=True)
                try:
                    dp.write_bytes(sp.read_bytes())
                except OSError as e:
                    report.errors.append(f"add {rel}: {e}")
        else:
            existing = dst_files[rel]
            if not filecmp.cmp(sp, existing, shallow=False):
                report.modified.append(rel)
                if apply:
                    try:
                        existing.write_bytes(sp.read_bytes())
                    except OSError as e:
                        report.errors.append(f"mod {rel}: {e}")

    # 删除目标独有
    for rel, dp in dst_files.items():
        if rel not in src_files:
            report.deleted.append(rel)
            if apply:
                try:
                    dp.unlink()
                except OSError as e:
                    report.errors.append(f"del {rel}: {e}")

    return report


def add_only(name: str, src: Path, dst: Path, apply: bool) -> SyncReport:
    """add-only: 递归复制, 不覆盖已有, 不删除。"""
    report = SyncReport(name=name, strategy="add-only", src=str(src), dst=str(dst))
    for f in iter_files(src):
        rel = relpath_under(f, src)
        dp = dst / rel
        if dp.exists():
            report.skipped_existing.append(rel)
            continue
        report.added.append(rel)
        if apply:
            dp.parent.mkdir(parents=True, exist_ok=True)
            try:
                dp.write_bytes(f.read_bytes())
            except OSError as e:
                report.errors.append(f"add {rel}: {e}")
    return report


def add_only_single(name: str, src_file: Path, dst_file: Path, apply: bool) -> SyncReport:
    """add-only 单文件（README → LOCAL-USAGE.md, START_HERE → 根）。"""
    report = SyncReport(name=name, strategy="add-only(file)", src=str(src_file), dst=str(dst_file))
    if not src_file.is_file():
        report.errors.append(f"源文件不存在: {src_file}")
        return report
    if dst_file.exists():
        report.skipped_existing.append(dst_file.name)
        return report
    report.added.append(dst_file.name)
    if apply:
        try:
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            dst_file.write_bytes(src_file.read_bytes())
        except OSError as e:
            report.errors.append(f"add {dst_file}: {e}")
    return report


# ---------- 报告输出 ----------

def print_report(report: SyncReport) -> None:
    print(f"\n=== {report.name} [{report.strategy}] ===")
    print(f"  src: {report.src}")
    print(f"  dst: {report.dst}")
    if report.added:
        print(f"  + 新增 ({len(report.added)}):")
        for x in sorted(report.added):
            print(f"      {x}")
    if report.modified:
        print(f"  ~ 修改 ({len(report.modified)}):")
        for x in sorted(report.modified):
            print(f"      {x}")
    if report.deleted:
        print(f"  - 删除 ({len(report.deleted)}):")
        for x in sorted(report.deleted):
            print(f"      {x}")
    if report.skipped_existing:
        print(f"  = 跳过-已存在 ({len(report.skipped_existing)}):")
        for x in sorted(report.skipped_existing):
            print(f"      {x}")
    if report.excluded_src:
        print(f"  × 排除 ({len(report.excluded_src)}):")
        for x in sorted(report.excluded_src):
            print(f"      {x}")
    if report.errors:
        print(f"  ❌ 错误 ({len(report.errors)}):")
        for x in report.errors:
            print(f"      {x}")


# ---------- 主入口 ----------

# ⚠️ Phase D 后语义变化（2026-07-26 标注，逻辑未改）:
#   Phase D 前: SRC_ROOT(~/.agent-collaboration/) 是活跃真值, DST_ROOT(git仓库) 是镜像目标
#   Phase D 后: SRC_ROOT 降级为只读历史快照, DST_ROOT(git仓库 governance/) 升为真值
#   当前 "本机→git" 的 mirror 方向可能需反转，或本脚本整体废弃（真值已在 git，无需 mirror）
#   本轮不动 mirror 逻辑（留长期卫生阶段评审），但 DST_ROOT 改为 REPO 推导（round4 修复 A+B 共识）
SRC_ROOT = Path(os.environ.get(
    "LEGACY_SNAPSHOT_ROOT",
    os.path.expanduser("~/.agent-collaboration")))
DST_ROOT = Path(os.environ.get(
    "REPO_ROOT",
    str(Path(__file__).resolve().parents[1])))  # scripts/ 父目录 = 仓库根，避免跨 checkout 混读


def build_plan() -> list:
    """构造 v3.4 §二 同步计划。返回 (kind, *args) 元组列表。"""
    plan = []

    # mirror 类（含 --delete）
    mirror_pairs = [
        ("standards→governance", SRC_ROOT / "standards", DST_ROOT / "governance", []),
        ("audits",               SRC_ROOT / "audits",    DST_ROOT / "audits",    []),
        ("configs",              SRC_ROOT / "configs",   DST_ROOT / "configs",   []),
        ("registry",             SRC_ROOT / "registry",  DST_ROOT / "registry",  []),
        ("project-starter",      SRC_ROOT / "project-starter", DST_ROOT / "project-starter", []),
    ]
    for name, src, dst, exc in mirror_pairs:
        plan.append(("mirror", name, src, dst, exc))

    # selective-mirror: archive 排除密钥归档
    archive_excludes = [
        "cc-retirement-20260726/",
        "backups/",
        "*.pre-rotation-bak",
        "retired-terms.txt",
        "secret-patterns/",
    ]
    plan.append(("mirror", "archive(selective)", SRC_ROOT / "archive", DST_ROOT / "archive", archive_excludes))

    # add-only 类
    plan.append(("add-only", "templates", SRC_ROOT / "templates", DST_ROOT / "templates"))
    plan.append(("add-only", "docs",       SRC_ROOT / "docs",       DST_ROOT / "docs"))

    # 单文件 add-only
    plan.append(("add-only-file", "README→LOCAL-USAGE",
                 SRC_ROOT / "README.md", DST_ROOT / "governance" / "LOCAL-USAGE.md"))
    plan.append(("add-only-file", "START_HERE→根",
                 SRC_ROOT / "START_HERE.md", DST_ROOT / "START_HERE.md"))

    return plan


def main() -> int:
    ap = argparse.ArgumentParser(description="v3.4 Phase B.2 同步执行器（Phase D 后 legacy）")
    ap.add_argument("--apply", action="store_true",
                    help="（Phase D 后已禁用，传入会 exit 1；原方向会覆盖 git 真值）")
    ap.add_argument("--only", metavar="NAME", action="append", default=[],
                    help="只运行名称匹配的映射（可多次, 子串匹配）")
    args = ap.parse_args()

    # Phase D-B round2 修复（A/B round1 共识阻断3）:
    # mirror-sync 原方向是"本机快照 → git 仓库"，但 Phase D 后本机已降级为只读历史快照，
    # git 仓库升为真值。原方向 --apply 会用滞后快照覆盖 git 真值 + 删除 git 独有文件，是破坏路径。
    # 本轮禁用 --apply，只允许 dry-run 作审计用。反转同步方向需另立规格 + 独立评审。
    if args.apply:
        print("❌ Phase D 后 mirror-sync --apply 已禁用（原方向会覆盖 git 真值）", file=sys.stderr)
        print("   原方向：~/.agent-collaboration/（只读快照）→ git 仓库（真值），语义已反转", file=sys.stderr)
        print("   如需反转同步方向，另立规格 + 独立评审；当前 git 已是真值，无需 mirror", file=sys.stderr)
        return 1

    print(f"模式: DRY-RUN(只读, Phase D 后 --apply 已禁用)")
    print(f"源根: {SRC_ROOT}（Phase D 后已降级为只读历史快照）")
    print(f"目标根: {DST_ROOT}")

    if not SRC_ROOT.is_dir():
        print(f"❌ 源根不存在: {SRC_ROOT}", file=sys.stderr)
        return 1

    plan = build_plan()
    if args.only:
        plan = [p for p in plan if any(n in p[1] for n in args.only)]
        if not plan:
            print(f"❌ --only 没匹配到任何映射", file=sys.stderr)
            return 1

    reports = []
    for item in plan:
        kind = item[0]
        if kind == "mirror":
            _, name, src, dst, exc = item
            # fail-closed（节点2 round2 修复, 阻断3/B-3）:
            # v3.4 初版源缺失只 ⚠️ 跳过, 循环正常 return 0 = fail-open。
            # 修复: 源缺失即失败, 避免静默漏同步已批准的映射。
            if not src.is_dir():
                print(f"\n❌ 源目录不存在, 中止: {name} ({src})", file=sys.stderr)
                print("   fail-closed: 每个批准的映射的源必须存在。", file=sys.stderr)
                return 1
            r = mirror(name, src, dst, exc, apply=args.apply)
        elif kind == "add-only":
            _, name, src, dst = item
            if not src.is_dir():
                print(f"\n❌ 源目录不存在, 中止: {name} ({src})", file=sys.stderr)
                print("   fail-closed: 每个批准的映射的源必须存在。", file=sys.stderr)
                return 1
            r = add_only(name, src, dst, apply=args.apply)
        elif kind == "add-only-file":
            _, name, src, dst = item
            r = add_only_single(name, src, dst, apply=args.apply)
        else:
            print(f"❌ 未知 kind: {kind}", file=sys.stderr)
            return 1
        reports.append(r)
        print_report(r)

    # 汇总
    total_added = sum(len(r.added) for r in reports)
    total_mod = sum(len(r.modified) for r in reports)
    total_del = sum(len(r.deleted) for r in reports)
    total_skip = sum(len(r.skipped_existing) for r in reports)
    total_err = sum(len(r.errors) for r in reports)

    print("\n" + "=" * 60)
    print(f"汇总: +{total_added} ~{total_mod} -{total_del} ={total_skip} ❌{total_err}")
    if total_err > 0:
        print("❌ 有错误, 退出码 1（已 apply 的改动需手动回滚）")
        return 1
    if not args.apply:
        print("（dry-run, 未写盘。Phase D 后 --apply 已禁用，本脚本仅作 legacy 审计用）")
    else:
        print("✅ apply 完成, 请跑 git status / git diff 复核")  # 不可达（--apply 已在入口禁用）
    return 0


if __name__ == "__main__":
    sys.exit(main())
