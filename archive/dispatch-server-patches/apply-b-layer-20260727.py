"""Pi 治理纳入 B 层 patch（2026-07-27）

对 /opt/pi-orchestrator/extensions/dispatch-server.py 做幂等改动：
1. 加常量 DRIFT_LATEST
2. 加 2 路由 /dispatch/truth/versions + /dispatch/drift
3. 加 2 handler 方法 _handle_truth_versions + _handle_drift
4. 更新 404 帮助字符串

幂等：检测标记字符串，已应用则跳过。先备份再改。
"""
import sys
import shutil
import time
from pathlib import Path

TARGET = Path("/opt/pi-orchestrator/extensions/dispatch-server.py")
MARKER = "DRIFT_LATEST = os.environ.get"  # 幂等标记


def main():
    if not TARGET.exists():
        print(f"❌ 目标文件不存在: {TARGET}", file=sys.stderr)
        return 1

    src = TARGET.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"⚠️  已应用过 B 层 patch（标记 {MARKER!r} 已存在），跳过。", file=sys.stderr)
        return 0

    # 备份
    ts = time.strftime("%Y%m%d-%H%M%S")
    bak = TARGET.with_suffix(TARGET.suffix + f".bak-b-layer-{ts}")
    shutil.copy2(TARGET, bak)
    print(f"✅ 备份: {bak}")

    # 1. 加常量 DRIFT_LATEST（在 GITHUB_RAW_BASE 块后插入）
    #    GITHUB_RAW_BASE 块以 'https://raw.githubusercontent.com/lyosvne/agent-collaboration-standard/master"\n)' 结束
    constant_anchor = '"https://raw.githubusercontent.com/lyosvne/agent-collaboration-standard/master"\n)'
    constant_new = constant_anchor + '''

# drift 治理（drift-cron.sh 每 30min 写入）
DRIFT_LATEST = os.environ.get("DRIFT_LATEST", "/opt/pi-orchestrator/logs/drift-latest.json")'''
    if src.count(constant_anchor) != 1:
        print(f"❌ 常量锚点匹配次数 != 1（{src.count(constant_anchor)}），中止", file=sys.stderr)
        return 1
    src = src.replace(constant_anchor, constant_new, 1)

    # 2. 加 2 路由（在 404 fallthrough 前）
    route_anchor = '        self._send_text(f"未知端点: {path}\\n可用:'
    route_new = '''        # /dispatch/truth/versions（治理文档版本清单, 时序版本自动化）
        if parts == ["dispatch", "truth", "versions"]:
            return self._handle_truth_versions()

        # /dispatch/drift（漂移体检最新报告）
        if parts == ["dispatch", "drift"]:
            return self._handle_drift()

        self._send_text(f"未知端点: {path}\\n可用:'''
    if src.count(route_anchor) != 1:
        print(f"❌ 路由锚点匹配次数 != 1（{src.count(route_anchor)}），中止", file=sys.stderr)
        return 1
    src = src.replace(route_anchor, route_new, 1)

    # 3. 更新 404 帮助字符串（加新端点到列表）
    help_old = '/dispatch/history/<agent>, /dispatch/models, /dispatch/health"'
    help_new = '/dispatch/history/<agent>, /dispatch/models, /dispatch/health,\\n                        /dispatch/truth/versions, /dispatch/drift"'
    if help_old not in src:
        print("❌ 404 帮助字符串锚点未找到，中止", file=sys.stderr)
        return 1
    src = src.replace(help_old, help_new, 1)

    # 4. 加 2 handler 方法（在 _handle_health 后插入）
    #    _handle_health 以 '        })' 结束（紧跟 _handle_models 或下一个 def）
    #    用 'def _handle_models' 作为后置锚点，在其前插入
    handler_anchor = '    def _handle_models(self):'
    handler_new = '''    def _handle_truth_versions(self):
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
        })

    def _handle_drift(self):
        """漂移体检最新报告（drift-cron.sh 每 30min 写入 drift-latest.json）。

        透传 JSON（与 /fleet /context 模式一致）。文件不存在时返回空对象。
        """
        data = read_file(DRIFT_LATEST, "{}")
        self._send_text(data, 200, "application/json; charset=utf-8")

    def _handle_models(self):'''
    if src.count(handler_anchor) != 1:
        print(f"❌ handler 锚点匹配次数 != 1（{src.count(handler_anchor)}），中止", file=sys.stderr)
        return 1
    src = src.replace(handler_anchor, handler_new, 1)

    # 语法检查
    try:
        compile(src, str(TARGET), "exec")
    except SyntaxError as e:
        print(f"❌ 语法检查失败: {e}，已保留备份 {bak}，未写入目标", file=sys.stderr)
        return 1

    TARGET.write_text(src, encoding="utf-8")
    print(f"✅ 已写入 {TARGET}")
    print(f"   备份: {bak}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
