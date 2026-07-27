"""Pi 治理纳入 B 层 round3: /dispatch/drift 加 AUTH_KEY（修 A round2 阻断）

背景: 公网 https://aetherisonline.xyz/dispatch/drift 经 Caddy 反代无 auth 可达
修复: 复用 _handle_append_history 的 auth 模式（query param ?key=AUTH_KEY, 403 失败）

前置: B 层 patch + B 层 fix patch 已应用
幂等: 用哨兵 PATCH-B-LAYER-AUTH-20260727-APPLIED
"""
import sys
import shutil
import time
from pathlib import Path

TARGET = Path("/opt/pi-orchestrator/extensions/dispatch-server.py")
SENTINEL_FIX = "# PATCH-B-LAYER-FIX-20260727-APPLIED"  # B 层 fix 已应用标记
SENTINEL_THIS = "# PATCH-B-LAYER-AUTH-20260727-APPLIED"


def main():
    if not TARGET.exists():
        print(f"❌ 目标文件不存在: {TARGET}", file=sys.stderr)
        return 1

    src = TARGET.read_text(encoding="utf-8")

    # 前置: B 层 fix 必须已应用
    if SENTINEL_FIX not in src:
        print(f"❌ 前置 B 层 fix patch 未应用（找不到 {SENTINEL_FIX!r}）", file=sys.stderr)
        return 1

    # 幂等
    if SENTINEL_THIS in src:
        print(f"⚠️  本 patch 已应用（哨兵已存在），跳过。", file=sys.stderr)
        return 0

    # 备份
    ts = time.strftime("%Y%m%d-%H%M%S")
    bak = TARGET.with_suffix(TARGET.suffix + f".bak-b-layer-auth-{ts}")
    shutil.copy2(TARGET, bak)
    print(f"✅ 备份: {bak}")

    # === 在 _handle_drift 方法体开头加 auth check ===
    # 当前 _handle_drift 起手是 docstring 后接 raw = read_file(DRIFT_LATEST, None)
    drift_anchor = '''    def _handle_drift(self):
        """漂移体检最新报告（drift-cron.sh 每 30min 写入 drift-latest.json）。

        消费者契约（2026-07-27 评审修复后, fail-closed）:
        - HTTP 200 + 合法 JSON: drift 报告正常, 含 timestamp + branches 数组
        - HTTP 502 + {"error": ...}: drift-latest.json 缺失 / 不可读 / JSON 损坏
          （消费者必须把 502 视为 drift 系统异常, 不是"无漂移"）
        - 正常的零漂移状态也会是 {"timestamp": "...", "branches": [...]}, 而非空 {}
          （空 {} 在修复前被当 200 返回是 fail-open, 已修）
        """
        raw = read_file(DRIFT_LATEST, None)'''

    drift_new = '''    def _handle_drift(self):
        """漂移体检最新报告（drift-cron.sh 每 30min 写入 drift-latest.json）。

        认证（2026-07-27 round3 修复 A 评审阻断 2）:
        - 公网经 Caddy https://aetherisonline.xyz/dispatch/drift 可达, 必须带 ?key=AUTH_KEY
        - 复用 _handle_append_history 的 auth 模式（query param, 403 失败）
        - 依赖 DISPATCH_KEY 环境变量已设非空（否则 AUTH_KEY 空, fallback 开放）

        消费者契约（2026-07-27 评审修复后, fail-closed）:
        - HTTP 200 + 合法 JSON: drift 报告正常, 含 timestamp + branches 数组
        - HTTP 403 "认证失败": ?key 缺失或不匹配（公网未授权访问）
        - HTTP 502 + {"error": ...}: drift-latest.json 缺失 / 不可读 / JSON 损坏
          （消费者必须把 502 视为 drift 系统异常, 不是"无漂移"）
        - 正常的零漂移状态也会是 {"timestamp": "...", "branches": [...]}, 而非空 {}
          （空 {} 在修复前被当 200 返回是 fail-open, 已修）
        """
        # 认证（与 POST /dispatch/history 一致, query param ?key=）
        if AUTH_KEY:
            parsed = urlparse(self.path)
            qs = parse_qs(parsed.query)
            provided = qs.get("key", [""])[0]
            if provided != AUTH_KEY:
                return self._send_text("认证失败", 403)
        raw = read_file(DRIFT_LATEST, None)'''

    if drift_anchor not in src:
        print("❌ _handle_drift 锚点未找到（B 层 fix patch 可能已部分变），中止", file=sys.stderr)
        return 1
    src = src.replace(drift_anchor, drift_new, 1)

    # 加哨兵注释（在 SENTINEL_FIX 后）
    src = src.replace(
        SENTINEL_FIX,
        SENTINEL_FIX + "\n" + SENTINEL_THIS,
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
