# C 层 round2 复评材料包：MISSING→CRITICAL + 注入面消除

> 评审对象: 本地 commit `6bd4804`（未 push）
> 前置: round1 A=CONDITIONAL（2 阻断）/ B=CONDITIONAL（1 阻断）/ C=CONDITIONAL（0 真阻断）
> 本轮: 修 P0（MISSING 静默）+ P1（注入面）

## 一、P0 修复（A+B 共识阻断）：MISSING → CRITICAL

**原问题**：drift-check.sh ref 不存在时输出 `level="MISSING"`，但 drift-cron.sh:26 `alerts = [b for b in report['branches'] if b.get('level') in ('CRITICAL','WARN')]` —— MISSING 不进 hash，配置漂移永远不告警。

**修复**：drift-check.sh ref 不存在时改 `level="CRITICAL"`，保留 status_desc 区分：
```python
if verify.returncode != 0:
    # round1 评审 P0 修复: level=CRITICAL（不是 MISSING）
    # 原因: drift-cron.sh state hash 只过滤 CRITICAL/WARN, 用 MISSING 会被静默吞掉
    results.append({
        "branch": b, "ahead": -1, "behind": -1, "head": "",
        "level": "CRITICAL",
        "status_desc": f"⚠️ 配置漂移: drift-config.json 列了 {b} 但远端不存在",
        "conflicts": []
    })
    continue
```

**实测验证**（构造假分支 `agent/test-missing-blabla`）：
```
agent/zcode: EXISTS
agent/qoder: EXISTS
agent/kimi: EXISTS
agent/solo: EXISTS
agent/mira: EXISTS
agent/test-missing-blabla: CRITICAL  ← 不存在的分支现在标 CRITICAL
```

## 二、P1 修复（A 独有阻断，B/C 软观察）：注入面消除

**原问题**：`python3 <<PYEOF`（无引号）+ `branches = "$BRANCHES_STR".split()` —— bash 展开 `$BRANCHES_STR` 进 python 双引号字符串，构造分支名可触发任意代码执行（A 实测 `os.system("echo PWNED")` 执行）。

**修复**：合并两段 python 为单进程 + heredoc 引号 + argv 传值：
```bash
# heredoc 用 'PYEOF'（关闭 bash 变量展开, 消除注入面）
# CONFIG 路径用 argv[1] 传值（不插值进 python 代码）
python3 - "$CONFIG" <<'PYEOF'
import json, sys, subprocess, os
config_path = sys.argv[1]
...
PYEOF
```

**关键变更**：
- 消除 `BRANCHES_STR` 这个 bash↔python 中转变量（注入面根源）
- CONFIG 路径不再 `'$CONFIG'` 插值，改 `sys.argv[1]`
- heredoc 加引号 `<<'PYEOF'` 关闭 bash 展开
- 单 python 进程完成：读 config → fetch 分支 → 算漂移 → 输出 JSON

## 三、patch 脚本增强

`apply-c-layer-drift-check-20260727.py` 加 `--force` 参数：
- 首次应用：`python3 apply-c-layer-drift-check-20260727.py`
- round1 修复重写：`python3 apply-c-layer-drift-check-20260727.py --force`
- 备份后缀区分：`.bak-c-layer-{ts}`（首次）vs `.bak-c-layer-fix-{ts}`（force）

## 四、实测验证

**5 分支正常跑**（功能回归）：
```
分支数: 5
  agent/zcode OK | ✅ 完全同步
  agent/qoder CRITICAL | 🔴 双向分叉:22个新工作+落后278,需判断
  agent/kimi CRITICAL | 🔴 双向分叉:250个新工作+落后191,需判断
  agent/solo NOTICE | 🟡 有74个新工作未合入master,等集成窗口
  agent/mira CRITICAL | 🔴 双向分叉:365个新工作+落后578,需判断
```

**MISSING→CRITICAL 验证**（假分支测试）：见 §一。

**bash 语法检查**：`bash -n drift-check.sh` PASS。

## 五、未修的（软观察，独立任务）

按 round1 三方软观察，以下不阻断本轮，记入 backlog：
- lessons §8.4 第 6 项根因深化（git ls-remote 强制规则 + 配置裁定必须附一手命令输出）
- drift-cron.sh:17-18 半成品 cp 保护（drift-check exit 非 0 时仍 cp 部分输出）
- conflict-tracker.py CRITICAL→MISSING 假 RESOLVED（现 CRITICAL→CRITICAL 同级，仍可能误判，但 conflict-tracker 只看 conflicts 字段，MISSING/CRITICAL 都是 conflicts=[] 应该都不会误触发——待验证）
- gen-card.py 归档（飞书卡片渲染行为）
- 归档版本化子目录（archive/ecs-scripts/ 被多轮评审共用）
- python3 版本隐式假设（f-string 需 ≥3.6）

## 六、请评审判断

A：你 round1 的 2 阻断（B1 注入 + B2 MISSING）现在闭环了吗？

B：你 round1 的 B-1（MISSING 静默）闭环了吗？

C：你 round1 提的"lessons 根因偏浅"等软观察本轮未修（声明在 §五），你接受延后吗？

特别请 A 评估：注入面修复（合并 python + heredoc 引号 + argv）是否真正消除你实测的 `os.system` 执行路径？
