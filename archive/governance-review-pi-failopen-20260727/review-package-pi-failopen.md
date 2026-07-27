# 评审材料包：Pi 漂移治理 fail-open 修复

> 评审对象: 本地 commit `4535842`（未 push）
> 评审性质: pre-commit 三方评审（§8.4 第 4 类继续闭环）
> 评审日期: 2026-07-27

## 一、背景

C 层 round2 评审三方共识软观察 backlog 5 项，本轮处理 2 个 fail-open 真问题：
1. drift-cron.sh: drift-check 失败时静默 abort 无告警
2. conflict-tracker.py: 分支消失误判 RESOLVED

另顺带：gen-card.py 归档（B 层评审提的归档缺口）。

## 二、改动（3 处）

### 2.1 drift-cron.sh：drift-check 失败发系统异常卡片

**B/C 评审说的"半成品 cp"实测证伪**：
- `set -euo pipefail` L4 + L17 `bash "$DRIFT_CHECK"` 无 `|| true`
- drift-check exit 非 0 → set -e 触发 → drift-cron 立即 exit
- L18 cp 不执行 → **drift-latest.json 保留旧版（fail-safe）**

实测验证（构造坏 drift-config.json 让 drift-check exit 1）：
```
旧 drift-latest.json hash: c0fc22f2d1102c3557a6e8c1456aeec8
[20260727T054614Z] drift-check 失败(exit=1), 发系统异常卡片
新 drift-latest.json hash: c0fc22f2d1102c3557a6e8c1456aeec8  ← 一致
```

**但真正的 fail-open 是"静默 abort 无告警"**——配置漂移/mirror 删除/python3 故障时用户完全无感知。

**修复**（drift-cron.sh L16-19）：
```bash
set +e
bash "$DRIFT_CHECK" > "$REPORT_FILE" 2>/dev/null
DRIFT_CHECK_RC=$?
set -e

if [ "$DRIFT_CHECK_RC" -ne 0 ]; then
  echo "[$TIMESTAMP] drift-check 失败(exit=$DRIFT_CHECK_RC), 发系统异常卡片"
  lark-cli im +messages-send --as bot --chat-id "$CHAT_ID" \
      --markdown "🚨 **Pi 漂移体检失败** (exit=$DRIFT_CHECK_RC) ..." 2>/dev/null >> /dev/null || true
  rm -f "$REPORT_FILE" 2>/dev/null || true
  exit 1
fi
cp "$REPORT_FILE" /opt/pi-orchestrator/logs/drift-latest.json
python3 conflict-tracker.py 2>/dev/null >> conflict-track.log || true
```

### 2.2 conflict-tracker.py：区分 RESOLVED vs DISAPPEARED（整体重写）

**原 L76-86**：分支不在 current_conflicts 即标 RESOLVED + 发卡片（误报配置漂移）。

**修复**（整体重写，签名 `update_track(current_state)`）：
```python
def update_track(current_state):
    # current_state: {name: {"conflicts": [...], "exists": bool}}
    for name in list(branches.keys()):
        state = current_state.get(name)
        if state is None:  # 不在 report → DISAPPEARED
            escalations.append({"branch": name, "level": "DISAPPEARED", ...})
            continue
        if not state.get("exists", True):  # 配置漂移标记 → DISAPPEARED
            escalations.append({"branch": name, "level": "DISAPPEARED", ...})
            continue
        if state["conflicts"]:  # 冲突还在 → count+1
            ...
        else:  # exists=True + conflicts=[] → 真解决 RESOLVED
            escalations.append({"branch": name, "level": "RESOLVED", ...})
```

**main 块构造 current_state**：
```python
for b in report.get("branches", []):
    code_conflicts = [c for c in b.get("conflicts", []) if "work-ledger" not in c]
    name = b["branch"].replace("agent/", "")
    is_drift_marker = (b.get("level") == "CRITICAL" and b.get("ahead", 0) == -1)
    current[name] = {"conflicts": code_conflicts, "exists": not is_drift_marker}
```

`is_drift_marker` 检测：drift-check.sh 配置漂移时输出 `level=CRITICAL + ahead=-1`（round1 修复时 MISSING→CRITICAL 的标记）。

**process_escalations 加 DISAPPEARED 分支**（发"⚠️ 分支消失"卡片，不发"冲突已解决"）。

### 2.3 gen-card.py 归档

`archive/ecs-scripts/gen-card.py`（107 行，0 密钥命中——chat_id 在 drift-cron.sh 不在 gen-card.py）。

## 三、实测验证

### drift-cron fail-open 修复
```
模拟坏 config → drift-check exit 1
→ drift-cron 输出 "drift-check 失败(exit=1), 发系统异常卡片"
→ drift-latest.json hash 前后一致（旧版保留）
→ config 恢复后正常
```

### conflict-tracker 3 场景
```
场景1 配置漂移（kimi CRITICAL + ahead=-1 + conflicts=[]）→ DISAPPEARED ✅
场景2 真解决（kimi exists=True + conflicts=[]）→ RESOLVED ✅
场景3 冲突还在（kimi exists=True + conflicts=['App.tsx']）→ 无 escalation（count+1 未升级）✅
```

## 四、patch 脚本设计教训

conflict-tracker.py 第一版用"AST 风格结构化替换"（行级锚点）失败 3 次：
1. 尾随空格导致纯空白行锚点不匹配
2. 切片范围 `[start:for_loop+1]` 重复保留 for 循环首行
3. 多处替换混用 `lines` 和 `src` 状态不一致

最终改为**整体重写**（保留原 CHAT_ID 从原文件读，不硬编码），避免锚点匹配脆弱。教训：复杂多段替换优先整体重写。

## 五、评审要点

1. **drift-cron fail-open 修复正确性**：`set +e` 捕获 exit code 后立即 `set -e` 恢复。这个切换有无副作用？失败路径的 `rm -f "$REPORT_FILE"` + `exit 1` 合理吗？

2. **drift-cron "半成品 cp" 证伪**：B/C round2 评审说"半成品 cp 覆盖 latest"。我实测证伪（set -e 在 L17 触发，L18 不执行）。你认可这个证伪吗？还是仍认为有 fail-open 路径？

3. **conflict-tracker 3 场景验证可信度**：实测在隔离环境（临时 TRACK_FILE）跑，未污染真实 conflict-track.json。`is_drift_marker = (level == "CRITICAL" and ahead == -1)` 这个检测条件对吗？有无漏的 drift 标记场景？

4. **DISAPPEARED 卡片频率**：分支消失是低频事件，但配置漂移持续时会每次 cron 都触发 DISAPPEARED 吗？还是 drift-cron state hash 会去重？

5. **整体重写 vs 锚点替换**：conflict-tracker.py 整体重写保留原 CHAT_ID（从原文件读，不硬编码）。这个方式可接受吗？还是应该用更精细的锚点？

6. **gen-card.py 归档**：107 行无密钥。归档完整性 OK 吗？

## 六、回滚

```bash
ssh ... "cp drift-cron.sh.bak-failopen-{ts} drift-cron.sh && chmod +x"
ssh ... "cp conflict-tracker.py.bak-failopen-{ts} conflict-tracker.py && chmod +x"
git revert 4535842
```

## 七、不做（边界）

- lessons §8.4 第 6 项根因深化（文档独立任务）
- 归档版本化子目录（结构重构独立任务）
- python3 版本假设（边角）
