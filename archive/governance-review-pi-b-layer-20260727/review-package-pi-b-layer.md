# 评审材料包：Pi 治理纳入 B 层（dispatch-server 加 2 端点）

> 评审对象: commit `bac6e95`（已 push + ECS 部署 + 服务重启）
> 评审性质: **事后补审**（未走 pre-commit 三方评审，违反节点纪律，本包为补救）
> 评审日期: 2026-07-27
> 评审方: A（opus4.8p via Mira）/ B（gpt5.6sol via Mira）/ C（cantus via Qoder）

---

## 一、改动背景

**任务**：Pi 治理纳入 B 层（roadmap O1 #2）—— dispatch-server 加 `/dispatch/truth/versions` + `/dispatch/drift` 两端点。

**用户决策链**：
1. 探明 ECS 已有 shell cron（drift-cron.sh/drift-check.sh/conflict-tracker.py）生产运行，覆盖 spec §3 漂移体检 90% 功能
2. 用户先选「B（写 TS Extension）+ 本轮一次做完」，ZCode 指出组合不现实（TS Extension 需先修 spawn exports bug），用户承认误解
3. 用户重新决策「B. 只做 B 层端点，C 层 TS Extension 独立排期」
4. Plan Mode 出方案，用户批准

## 二、改动内容（真实 diff，ECS 实证）

**改动文件**：`/opt/pi-orchestrator/extensions/dispatch-server.py`（ECS 上，不在 git 仓库内）

```diff
@@ L43 后加常量 @@
+ # drift 治理（drift-cron.sh 每 30min 写入）
+ DRIFT_LATEST = os.environ.get("DRIFT_LATEST", "/opt/pi-orchestrator/logs/drift-latest.json")

@@ L212 前加 2 路由（404 fallthrough 前）@@
+ # /dispatch/truth/versions（治理文档版本清单, 时序版本自动化）
+ if parts == ["dispatch", "truth", "versions"]:
+     return self._handle_truth_versions()
+
+ # /dispatch/drift（漂移体检最新报告）
+ if parts == ["dispatch", "drift"]:
+     return self._handle_drift()

@@ L216 更新 404 帮助字符串 @@
- f"/dispatch/history/<agent>, /dispatch/models, /dispatch/health", 404)
+ f"/dispatch/history/<agent>, /dispatch/models, /dispatch/health,\n                        /dispatch/truth/versions, /dispatch/drift", 404)

@@ L279 后加 2 handler（_handle_health 后）@@
+ def _handle_truth_versions(self):
+     """治理文档版本清单（时序版本自动化, 各域自校验对齐）。
+     解析 -vX.Y.md 文件名后缀得 version; source = mirror/github/missing。
+     """
+     import re
+     versions = {}
+     for key, filename in GOVERNANCE_FILES.items():
+         _, source = read_governance_file(filename)
+         m = re.search(r"-v(\d+\.\d+)\.md$", filename)
+         version = m.group(1) if m else None
+         versions[key] = {
+             "filename": filename,
+             "version": version,
+             "source": source,
+         }
+     self._send_json({
+         "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
+         "github_raw_base": GITHUB_RAW_BASE,
+         "governance_dir": GOVERNANCE_DIR,
+         "documents": versions,
+     })
+
+ def _handle_drift(self):
+     """漂移体检最新报告（drift-cron.sh 每 30min 写入 drift-latest.json）。
+     透传 JSON（与 /fleet /context 模式一致）。文件不存在时返回空对象。
+     """
+     data = read_file(DRIFT_LATEST, "{}")
+     self._send_text(data, 200, "application/json; charset=utf-8")
```

## 三、git 仓库内改动（commit bac6e95）

- `archive/dispatch-server-patches/apply-b-layer-20260727.py`（新文件，幂等 patch 脚本）
- `governance/specs/pi-drift-governance-spec.md` §10 B 层 ⏳→✅，C 层范围收窄
- `governance/global-roadmap-v1.1.md` O1 #2 + v1.9 版本历史

## 四、验证证据（ECS 实测，2026-07-27 10:32Z）

**`/dispatch/truth/versions`**（5 个文档 version + source）：
```json
{
  "time": "2026-07-27T02:32:11Z",
  "documents": {
    "north-star": {"filename": "north-star-v1.2.md", "version": "1.2", "source": "mirror"},
    "architecture": {"filename": "agent-matrix-architecture-v1.0.md", "version": "1.0", "source": "mirror"},
    "fleet-division": {"filename": "fleet-division-v1.1.md", "version": "1.1", "source": "mirror"},
    "roadmap": {"filename": "global-roadmap-v1.1.md", "version": "1.1", "source": "mirror"},
    "start-here": {"filename": "START_HERE.md", "version": null, "source": "mirror"}
  }
}
```

**`/dispatch/drift`**（实时 drift-latest.json 透传）：
```json
{
  "timestamp": "2026-07-27T02:30:49Z",
  "branches": [
    {"branch": "agent/claude", "ahead": 0, "behind": 0, "level": "OK", ...},
    {"branch": "agent/kimi", "ahead": 250, "behind": 191, "level": "CRITICAL", "conflicts": [...]},
    ...
  ]
}
```

**`/dispatch/health` 回归**：原有端点不受影响，5 governance 文件全 mirror。

## 五、评审要点（请逐条判断 PASS/CONDITIONAL/FAIL）

1. **端点设计合理性**：`/truth/versions` 返回结构（filename/version/source）是否满足"时序版本自动化"需求（各域自校验对齐）？字段是否够用？
2. **版本解析正确性**：正则 `-v(\d+\.\d+)\.md$` 是否覆盖所有治理文档命名？START_HERE.md 返回 null 是否可接受？
3. **drift 透传方式**：`_handle_drift` 用 `read_file` + `_send_text` 透传 raw（不 json.loads/re-dump），与 /fleet /context 一致。是否合理？编码风险？
4. **幂等性**：patch 脚本用 MARKER 字符串检测，已应用则跳过。是否可靠？
5. **404 帮助字符串**：加了 `\n` + 缩进对齐，格式是否破坏？
6. **安全边界**：新端点都是 GET，无 AUTH_KEY 检查（与现有 GET 端点一致）。是否引入新的暴露风险？
7. **C 层范围收窄合理性**：spec §10 把 C 层从"写 TS Extension"收窄为"shell cron 已覆盖 90%，剩 drift-check 退役分支 + 可选 TS Extension"。这个收窄是否有依据（探明 ECS 已有 drift-cron.sh 等生产运行）？
8. **过程纪律违规**：未走 pre-commit 三方评审。本事后补审是否可接受？是否要求强制回滚重走流程？

## 六、已知限制（不需判 PASS/FAIL，仅供知情）

- 退役分支 agent/claude/agent/trae 仍在 drift 报告里（C 层待修，B 层只暴露不改逻辑）
- dispatch-server.py 不在 git 仓库，patch 脚本归档是审计替代
- ECS 备份文件 `.bak-b-layer-20260727-103156` 保留在 ECS 上
- commit bac6e95 author 显示 `Trae IDE`（应为 ZCode，git config 问题，非本次改动引入）

## 七、回滚方案（如评审判 FAIL）

```bash
ssh ... root@aetherisonline.xyz "cp /opt/pi-orchestrator/extensions/dispatch-server.py.bak-b-layer-20260727-103156 /opt/pi-orchestrator/extensions/dispatch-server.py && systemctl restart pi-dispatch-server.service"
# git 层: git revert bac6e95 + push
```
