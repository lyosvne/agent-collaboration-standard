# 复评材料包：Pi 治理纳入 B 层阻断修复（round2）

> 评审对象: 本地 commit（修复 4 阻断，未 push）
> 前置: round1 评审 A/B/C 全 CONDITIONAL，共识 4 阻断（详见同目录 review-A/B/C-*.md）
> 评审日期: 2026-07-27
> 评审方: A（opus4.8p via Mira）/ B（gpt5.6sol via Mira）/ C（cantus via Qoder）

---

## 一、4 阻断修复对照

### 阻断 1（A+B 阻断，C 软观察）：`/truth/versions` 缺 commit SHA

**原问题**：只返回 filename/version/source，同版本号下内容漂移检测不到。

**修复**：`/truth/versions` 每项加 4 字段 + 顶层加 mirror_root：
- `commit_sha`: governance-mirror HEAD（subprocess 调 `git rev-parse HEAD`，全局所有文档同源）
- `content_sha12`: 文件内容 sha256 前 12 位（每文件唯一，同版本号下内容变化可检测）
- `mtime`: 文件 mtime ISO（mirror 同步延迟时判断新鲜度）
- `versioned`: bool（区分"无版本文件"如 START_HERE.md 与"解析失败"）
- 顶层加 `mirror_root`: /opt/pi/governance-mirror/repo

**实测**（修复后 curl 输出）：
```json
{
  "time": "2026-07-27T03:05:10Z",
  "mirror_root": "/opt/pi/governance-mirror/repo",
  "documents": {
    "north-star": {
      "filename": "north-star-v1.2.md",
      "version": "1.2",
      "versioned": true,
      "commit_sha": "bac6e95b50cee0c2f135f5564ce0d5e5a02f6abb",
      "content_sha12": "e27a83542e80",
      "mtime": "2026-07-26T16:12:29Z",
      "source": "mirror"
    },
    ...
  }
}
```

### 阻断 3（A 阻断，C 强调 fail-open，B 软观察）：drift 透传 fail-open

**原问题**：`read_file(DRIFT_LATEST, "{}")` + `_send_text("{}", 200)`，文件缺失/malformed 都返回 200。

**修复**：`_handle_drift` 改为 fail-closed：
```python
raw = read_file(DRIFT_LATEST, None)
if raw is None or raw == "（文件不存在）" or "（读取失败" in raw:
    self._send_json({"error": "drift report unavailable", "missing": True, ...}, 502)
    return
try:
    data = json.loads(raw)
except (ValueError, json.JSONDecodeError) as e:
    self._send_json({"error": "drift report malformed", "detail": str(e), ...}, 502)
    return
self._send_json(data)
```

**单元测试**（Python 直接调逻辑）：
- 文件不存在 → `raw is None` → 502 ✅
- malformed JSON → JSONDecodeError 兜底 → 502 ✅
- 正常文件 → `_send_json(data)` 规范化输出，HTTP 200 ✅

**消费者契约写入 docstring**：HTTP 200 = 正常；HTTP 502 = drift 系统异常（消费者必须把 502 视为异常，不是"无漂移"）。

### 阻断 2（B+C 强烈要求，A 也提）：过程违规未落账

**修复**：
1. `governance/specs/review-process-lessons.md` 新增 §八（4 子节）：
   - §8.1 违规情形
   - §8.2 为何可接受（不强制回滚）
   - §8.3 真问题（"小改动"开脱是错的）
   - §8.4 防复发措施（4 类 ECS 改动强制 pre-commit 评审）
   - §8.5 教训
2. roadmap v1.9 版本历史补承认违规 + 修复 patch 链接

### 阻断 4（A 阻断，C 要求分项覆盖度）：C 层"90%"无实证

**修复**：
1. `archive/ecs-scripts/` 归档 5 个 ECS 生产脚本（脱敏飞书 chat_id）：
   - drift-cron.sh / drift-check.sh / conflict-tracker.py / governance-sync.sh / model-tracker.sh
2. `archive/ecs-scripts/README.md` 实证：
   - root crontab（3 个 cron 任务时间表）
   - pi-dispatch-server.service systemd unit 全文
   - **dispatch-server bind 127.0.0.1（仅 localhost，不暴露公网）** ← 闭环评审 B/C 安全疑虑
   - spec §3 覆盖矩阵（~95%，仅"写 Aetheris 真值层"未实现）
   - spec §5 覆盖度（§5.1 已固化 / §5.2/§5.3 未实现，承认真空）
3. spec §10 + roadmap 改为分项覆盖度说明，删除"90%"硬数字

### 软观察（顺手修）

- 版本正则放宽：`-v(\d+\.\d+)\.md$` → `-v(\d+(?:\.\d+){0,2})\.md$`（支持 semver 三段）
- MARKER 改哨兵注释：`# PATCH-B-LAYER-FIX-20260727-APPLIED`（不依赖变量名匹配）
- `_handle_truth_versions` + `_handle_drift` docstring 写消费者契约（version 用 split+int 比较；versioned=false 跳过版本校验；502 = 异常）

## 二、修复过程小插曲（自曝）

第一次 patch 用了 `Path(...)` 但没在 dispatch-server.py 顶部加 `from pathlib import Path`，导致服务重启后端点 Empty reply（NameError）。**这是我没本地测试就部署的错**。处理：
1. 回滚到 B 层工作版（`.bak-b-layer-fix-20260727-110009`）
2. 改 patch 脚本用 `os.path`（不依赖新 import）
3. 重新应用 + 重启 + 验证

教训：ECS 改动即使 patch 脚本语法过，也要先在隔离环境跑一次端到端再部署。

## 三、未修的（声明）

- **drift-check.sh 退役分支**：脚本仍扫 `agent/claude` `agent/trae`（C 层任务，本轮 B 层只暴露不改逻辑，评审已知情）
- **`/dispatch/drift` 加 AUTH_KEY**：A 标阻断要求加 auth。但发现 dispatch-server bind 127.0.0.1（仅 localhost），Caddy 反代受控，公网不直接可达——C 标 PASS（内网模型下 OK），B 标 CONDITIONAL（要 bind 证据）。本轮用 bind 证据闭环，未加端点级 AUTH_KEY。如评审仍要求加，下轮处理
- **commit author bac6e95 = Trae IDE**：git config 问题，非本次引入，不 amend 已 push commit

## 四、验证证据

- gate-checks 4 门禁全过（140 条 HISTORY 全登记）
- `/truth/versions` 实测 5 文档全有 commit_sha bac6e95 + content_sha12 + mtime
- `/drift` fail-closed 单元测试通过（文件缺失/malformed 都 502）
- `/health` 回归正常

## 五、请评审判断

针对 round1 你提的阻断/软观察，逐条判断修复是否到位：
- 已修 → PASS
- 修但不充分 → CONDITIONAL（说明缺什么）
- 未修或修错 → FAIL

特别请 A 评估：commit_sha/content_sha12 是否满足"时序版本自动化各域自校验"实质需求？还是仍不够？
