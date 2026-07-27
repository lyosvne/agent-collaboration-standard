# 复评材料包 round3：/dispatch/drift 加 AUTH_KEY

> 评审对象: 本地 commit c17fdcc（未 push）
> 前置: round2 复评 A=CONDITIONAL（1 阻断：公网 drift 无 auth）/ B=PASS / C=PASS
> 本轮目标: 闭环 A 的剩余阻断
> 评审日期: 2026-07-27

## 一、A round2 阻断回顾

A round2 说："Caddy 反代对 `/dispatch/drift` 的公网暴露证据缺。bind 127.0.0.1 只锁直连，Caddy 反代路径未锁。"

实测验证：`curl https://aetherisonline.xyz/dispatch/drift` 公网返回 HTTP 200 + 6 分支完整报告（分支名 + commit SHA + 冲突文件路径）—— **A 阻断确认成立**。

Caddyfile 实证（`/etc/caddy/Caddyfile`）：
```
aetherisonline.xyz {
    ...
    handle /dispatch/* {
        reverse_proxy 127.0.0.1:8765
    }
    ...
}
```
无 site 级 auth、无 IP allowlist、无 Basic Auth。

## 二、修复（用户裁定方案 A：dispatch-server 端加 AUTH_KEY）

**改动**：`_handle_drift` 方法开头加 4 行 auth check，复用 `_handle_append_history` 的 auth 模式（POST 端点已用）：

```python
def _handle_drift(self):
    """...docstring 加认证说明..."""
    # 认证（与 POST /dispatch/history 一致, query param ?key=）
    if AUTH_KEY:
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        provided = qs.get("key", [""])[0]
        if provided != AUTH_KEY:
            return self._send_text("认证失败", 403)
    raw = read_file(DRIFT_LATEST, None)
    # ...（fail-closed 逻辑不变）...
```

**关键点**：
- 复用 `AUTH_KEY`（来自 `DISPATCH_KEY` 环境变量，已设非空 32 字符 hex）—— 不引入新环境变量
- query param `?key=<DISPATCH_KEY>`（与 POST `/dispatch/history/<agent>` 完全一致）
- 失败 HTTP 403 "认证失败"（与 POST 一致）
- `/dispatch/truth/versions` **不加 auth**（A round2 评审说敏感度低，治理文档本就是公开真值）

## 三、patch 脚本

`archive/dispatch-server-patches/apply-b-layer-auth-20260727.py`：
- 幂等哨兵：`# PATCH-B-LAYER-AUTH-20260727-APPLIED`
- 前置检查：B 层 fix patch（`PATCH-B-LAYER-FIX-20260727-APPLIED`）已应用
- 备份：`.bak-b-layer-auth-20260727-113641`
- 语法检查：`compile()` 在 write 前
- **吸取 round2 教训**：应用前先验证 `urlparse`/`parse_qs` 在 dispatch-server.py L28 已 import（`from urllib.parse import urlparse, parse_qs`），不会重蹈 round2 的 `Path import` NameError

## 四、实测验证（5 项全过）

```
=== 1. 公网 drift 无 key（应 403）===
HTTP 403
认证失败

=== 2. 公网 drift 带 key（应 200）===
HTTP 200
带 key OK, branches: 6

=== 3. 公网 truth/versions 无 key（应 200 公开）===
HTTP 200
truth/versions OK, docs: ['north-star', 'architecture', 'fleet-division', 'roadmap', 'start-here']

=== 4. health（应 200）===
HTTP 200
health: ok
```

POST `/dispatch/history/<agent>?key=<key>` 回归：auth 模式未动，仍工作。

**安全说明**：DISPATCH_KEY 明文仅临时在 shell 变量用于验证测试，未写入任何文件/commit/log。验证后临时文件已清理。

## 五、客户端影响

- **ZCode PC curl**（未来读 drift）：加 `?key=$DISPATCH_KEY`
- **drift-cron.sh**（飞书卡片）：不经 dispatch-server，直接读 drift-latest.json，**不受影响**
- **Pi 内部**：不通过 HTTP 读 drift，**不受影响**

唯一受影响的是 ZCode 手动 curl，加 `?key=` 即可。

## 六、已知限制（不要求本轮处理）

- **timing attack**：用 `!=` 而非 `hmac.compare_digest`，理论 timing 漏洞。与 POST 现有一致，独立任务可改
- **AUTH_KEY 空 fallback**：`if AUTH_KEY:` 条件下才校验，若未来 DISPATCH_KEY 被清空，端点会开放。生产 DISPATCH_KEY 已设非空，且本依赖已在 docstring 注明
- **DISPATCH_KEY 在 .env**：ZCode 不读不写明文（除本次验证临时用），用户保管

## 七、纪律遵守（§8.4 首个正面案例）

按 review-process-lessons §8.4 第 1/3/5 类（改 dispatch-server.py / 改端点路由 / 改鉴权逻辑 = 强制 pre-commit 评审），本轮走完整流程：
1. ✅ Plan Mode 出方案（ExitPlanMode plan）
2. ✅ 用户审 + 批准
3. ✅ 应用 patch + 重启服务
4. ✅ 端到端验证（5 项）
5. ⏳ **本轮 round3 三方评审**（pre-commit，评审 PASS 后才 push）

不再犯"B 层先斩后审"错误。这是 §8.4 的首个正面案例。

## 八、请评审判断

A：你 round2 的阻断（Caddy 公网暴露证据）现在闭环了吗？端点级 AUTH_KEY 你接受吗？还是仍要求 Caddy 级 auth？

B/C：auth 模式复用 POST 一致性 + fail-closed 实测，你们有无新阻断？
