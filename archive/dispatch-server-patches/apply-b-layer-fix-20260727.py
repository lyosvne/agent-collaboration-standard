"""Pi 治理纳入 B 层修复 patch（2026-07-27，事后评审阻断修复）

修复三方评审共识阻断:
- 阻断1: /truth/versions 加 commit_sha + content_sha12 + mtime + versioned
- 阻断3: /dispatch/drift fail-closed（_send_json + 502 兜底）
- 软观察: 正则放宽 + MARKER 哨兵 + drift 消费者契约 docstring

前置: 已应用 apply-b-layer-20260727.py（检测哨兵注释）
幂等: 用新哨兵 PATCH-B-LAYER-FIX-20260727-APPLIED 检测
"""
import sys
import shutil
import time
import subprocess
import hashlib
import os
from pathlib import Path

TARGET = Path("/opt/pi-orchestrator/extensions/dispatch-server.py")
SENTINEL_PRECONDITION = "# drift 治理（drift-cron.sh 每 30min 写入）"  # B 层已应用的标记
SENTINEL_THIS = "# PATCH-B-LAYER-FIX-20260727-APPLIED"  # 本修复的幂等标记


def main():
    if not TARGET.exists():
        print(f"❌ 目标文件不存在: {TARGET}", file=sys.stderr)
        return 1

    src = TARGET.read_text(encoding="utf-8")

    # 前置检查: B 层 patch 必须已应用
    if SENTINEL_PRECONDITION not in src:
        print(f"❌ 前置 B 层 patch 未应用（找不到 {SENTINEL_PRECONDITION!r}），本修复依赖 B 层端点已存在", file=sys.stderr)
        return 1

    # 幂等检查
    if SENTINEL_THIS in src:
        print(f"⚠️  本修复 patch 已应用（哨兵 {SENTINEL_THIS!r} 已存在），跳过。", file=sys.stderr)
        return 0

    # 备份
    ts = time.strftime("%Y%m%d-%H%M%S")
    bak = TARGET.with_suffix(TARGET.suffix + f".bak-b-layer-fix-{ts}")
    shutil.copy2(TARGET, bak)
    print(f"✅ 备份: {bak}")

    # === 修复 1: 重写 _handle_truth_versions（加 commit_sha/content_sha12/mtime/versioned）===
    truth_old = '''    def _handle_truth_versions(self):
        """治理文档版本清单（时序版本自动化, 各域自校验对齐）。

        解析 -vX.Y.md 文件名后缀得 version; source = mirror/github/missing。
        对应 archive/governance-review-node1 §5.3 设计。
        """
        import re
        versions = {}
        for key, filename in GOVERNANCE_FILES.items():
            _, source = read_governance_file(filename)
            m = re.search(r"-v(\\d+\\.\\d+)\\.md$", filename)
            version = m.group(1) if m else None
            versions[key] = {
                "filename": filename,
                "version": version,
                "source": source,
            }
        self._send_json({
            "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "github_raw_base": GITHUB_RAW_BASE,
            "governance_dir": GOVERNANCE_DIR,
            "documents": versions,
        })'''

    truth_new = '''    def _handle_truth_versions(self):
        """治理文档版本清单（时序版本自动化, 各域自校验对齐）。

        消费者契约（2026-07-27 评审修复后）:
        - version: 文件名 -vX.Y[.Z] 解析, 用 split+int 比较（非字符串比较）
        - versioned: False 表示非时序版本文件（如 START_HERE.md）, 跳过版本校验
        - commit_sha: governance-mirror HEAD（全局, 所有文档同源）, mirror 落后 github 时消费者可能误判, 需结合 mtime 判断新鲜度
        - content_sha12: 文件内容 sha256 前 12 位, 同版本号下内容变化可检测
        - mtime: 文件最后修改时间 ISO, mirror 同步延迟时消费者可据此判断
        - source: mirror/github/missing, mirror=本地快照, github=raw 兜底, missing=双源失败

        对应 archive/governance-review-node1 §5.3 设计（version/updated/commit-hash）。
        """
        import re
        # mirror HEAD（所有文档同源一次调用）
        commit_sha = None
        try:
            result = subprocess.run(
                ["git", "-C", GOVERNANCE_ROOT, "rev-parse", "HEAD"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                commit_sha = result.stdout.strip() or None
        except Exception:
            pass

        versions = {}
        for key, filename in GOVERNANCE_FILES.items():
            content, source = read_governance_file(filename)
            # 正则放宽: 支持 1-3 段 semver（v1.2 / v1.2.3）
            m = re.search(r"-v(\\d+(?:\\.\\d+){0,2})\\.md$", filename)
            version = m.group(1) if m else None
            versioned = m is not None

            # 文件级指纹 + mtime（仅 mirror 源可取, github/missing 时为 None）
            content_sha12 = None
            mtime = None
            if source == "mirror":
                mirror_path = (os.path.join(GOVERNANCE_ROOT, filename)
                               if filename == "START_HERE.md"
                               else os.path.join(GOVERNANCE_DIR, filename))
                try:
                    with open(mirror_path, "rb") as f:
                        raw = f.read()
                    content_sha12 = hashlib.sha256(raw).hexdigest()[:12]
                    mtime = time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                          time.gmtime(os.path.getmtime(mirror_path)))
                except Exception:
                    pass

            versions[key] = {
                "filename": filename,
                "version": version,
                "versioned": versioned,
                "commit_sha": commit_sha,
                "content_sha12": content_sha12,
                "mtime": mtime,
                "source": source,
            }
        self._send_json({
            "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "github_raw_base": GITHUB_RAW_BASE,
            "governance_dir": GOVERNANCE_DIR,
            "mirror_root": GOVERNANCE_ROOT,
            "documents": versions,
        })'''

    if truth_old not in src:
        print("❌ _handle_truth_versions 原文锚点未找到（B 层 patch 可能已部分变），中止", file=sys.stderr)
        return 1
    src = src.replace(truth_old, truth_new, 1)

    # === 修复 3: 重写 _handle_drift（fail-closed + _send_json + 502 兜底）===
    drift_old = '''    def _handle_drift(self):
        """漂移体检最新报告（drift-cron.sh 每 30min 写入 drift-latest.json）。

        透传 JSON（与 /fleet /context 模式一致）。文件不存在时返回空对象。
        """
        data = read_file(DRIFT_LATEST, "{}")
        self._send_text(data, 200, "application/json; charset=utf-8")'''

    drift_new = '''    def _handle_drift(self):
        """漂移体检最新报告（drift-cron.sh 每 30min 写入 drift-latest.json）。

        消费者契约（2026-07-27 评审修复后, fail-closed）:
        - HTTP 200 + 合法 JSON: drift 报告正常, 含 timestamp + branches 数组
        - HTTP 502 + {"error": ...}: drift-latest.json 缺失 / 不可读 / JSON 损坏
          （消费者必须把 502 视为 drift 系统异常, 不是"无漂移"）
        - 正常的零漂移状态也会是 {"timestamp": "...", "branches": [...]}, 而非空 {}
          （空 {} 在修复前被当 200 返回是 fail-open, 已修）
        """
        raw = read_file(DRIFT_LATEST, None)
        if raw is None or raw == "（文件不存在）" or "（读取失败" in raw:
            self._send_json({
                "error": "drift report unavailable",
                "missing": True,
                "path": DRIFT_LATEST,
                "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }, 502)
            return
        try:
            data = json.loads(raw)
        except (ValueError, json.JSONDecodeError) as e:
            self._send_json({
                "error": "drift report malformed",
                "detail": str(e),
                "path": DRIFT_LATEST,
                "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }, 502)
            return
        self._send_json(data)'''

    if drift_old not in src:
        print("❌ _handle_drift 原文锚点未找到, 中止", file=sys.stderr)
        return 1
    src = src.replace(drift_old, drift_new, 1)

    # === 加哨兵注释（幂等标记 + import subprocess/hashlib 顶部已 import, 检查）===
    # subprocess/hashlib 已在本脚本顶部 import, 但 dispatch-server.py 顶部可能没有
    # 检查并按需补 import
    if "import subprocess" not in src:
        # 在第一个 import 行后加
        src = src.replace("import os", "import os\nimport subprocess\nimport hashlib", 1)
        print("✅ 顶部补 import subprocess + hashlib")
    elif "import hashlib" not in src:
        src = src.replace("import subprocess", "import subprocess\nimport hashlib", 1)
        print("✅ 顶部补 import hashlib")

    # 在 DRIFT_LATEST 常量后加哨兵注释
    src = src.replace(
        'DRIFT_LATEST = os.environ.get("DRIFT_LATEST", "/opt/pi-orchestrator/logs/drift-latest.json")',
        'DRIFT_LATEST = os.environ.get("DRIFT_LATEST", "/opt/pi-orchestrator/logs/drift-latest.json")\n'
        + SENTINEL_THIS,
        1,
    )

    # 语法检查
    try:
        compile(src, str(TARGET), "exec")
    except SyntaxError as e:
        print(f"❌ 语法检查失败: {e}, 已保留备份 {bak}, 未写入目标", file=sys.stderr)
        return 1

    TARGET.write_text(src, encoding="utf-8")
    print(f"✅ 已写入 {TARGET}")
    print(f"   备份: {bak}")
    print(f"   哨兵: {SENTINEL_THIS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
