# 评审材料包：Pi 治理纳入 C 层 drift-check.sh 去硬编码

> 评审对象: 本地 commit `1c5e18d`（未 push）
> 评审性质: pre-commit 三方评审（§8.4 第 4 类首次触发）
> 评审日期: 2026-07-27
> 评审方: A（opus4.8p via Mira）/ B（gpt5.6sol via Mira）/ C（cantus via Qoder）

## 一、背景

C 层 drift-check.sh 退役分支修复：原脚本硬编码 6 分支（含退役的 claude/trae），与 drift-config.json 真值不一致（A round1 阻断 3 + C 软观察）。

## 二、改动（3 处）

### 2.1 git 仓库 `governance/configs/drift-config.json` 真值校准

```diff
- "version": "1.0", "updated": "2026-07-26"
+ "version": "1.1", "updated": "2026-07-27"

  repos[0] agent-collaboration-standard:
-   agent_branches: ["agent/zcode", "agent/qoder", "agent/kimi", "agent/solo", "agent/mira"]
-   monitor_level: "full"
+   agent_branches: []
+   monitor_level: "none"
+   note: 治理仓库，不用 agent/* 分支模型（直接 commit master，2026-07-27 校准）。drift-check.sh 不扫此仓库；版本真值经 /truth/versions 端点暴露

  repos[1] Aetheris:
-   agent_branches: ["agent/zcode", "agent/qoder", "agent/kimi", "agent/solo", "agent/mira"]  (原配置)
+   agent_branches: ["agent/zcode", "agent/qoder", "agent/kimi", "agent/solo", "agent/mira"]  (保留 5 分支，实测确认)
```

### 2.2 ECS `/opt/pi-orchestrator/extensions/drift-check.sh` 去硬编码

**核心改动**（patch 脚本 `apply-c-layer-drift-check-20260727.py` 整体重写）：

1. **bash 顶部加 CONFIG 路径**：
```bash
CONFIG="/opt/pi/governance-mirror/repo/governance/configs/drift-config.json"
```

2. **从 drift-config.json 读 Aetheris agent_branches**（替换原硬编码 `for b in master agent/claude ...`）：
```bash
BRANCHES_STR=$(python3 -c "
import json, sys
try:
    with open('$CONFIG') as f:
        cfg = json.load(f)
except Exception as e:
    sys.stderr.write(f'ERROR: drift-config.json 读取失败: {e}\\n')
    sys.exit(1)
aetheris = next((r for r in cfg.get('repos', []) if r.get('name') == 'Aetheris'), None)
if not aetheris:
    sys.stderr.write('ERROR: Aetheris not in drift-config.json repos\\n')
    sys.exit(1)
branches = aetheris.get('agent_branches', [])
if not branches:
    sys.stderr.write('ERROR: Aetheris agent_branches 为空\\n')
    sys.exit(1)
print(' '.join(branches))
") || exit 1
```

3. **fail-closed**：配置不存在/语法坏/Aetheris 条目缺/agent_branches 空 → `exit 1`（drift-cron.sh 会记日志但不写 drift-latest.json，旧报告保留）

4. **python heredoc 加 ref 存在性检查**（防御配置含远端不存在的分支）：
```python
for b in branches:
    ref = f"refs/remotes/origin/{b}"
    verify = subprocess.run(["git", "rev-parse", "--verify", "--quiet", ref], capture_output=True)
    if verify.returncode != 0:
        results.append({"branch": b, "level": "MISSING",
                        "status_desc": f"⚠️ 分支 {b} 在远端不存在（配置漂移？）",
                        "ahead": -1, "behind": -1, "head": "", "conflicts": []})
        continue
    # ... 原有 ahead/behind/分级逻辑 ...
```

5. **哨兵注释** `# PATCH-C-LAYER-DRIFT-CHECK-20260727-APPLIED`

### 2.3 archive/ecs-scripts/drift-check.sh 归档版同步

之前归档的是旧版（含硬编码 + 退役分支），已同步为新版（去硬编码 + 含哨兵）。

## 三、实测验证（手动跑 drift-check.sh）

```
分支数: 5
  agent/zcode OK
  agent/qoder CRITICAL
  agent/kimi CRITICAL
  agent/solo NOTICE
  agent/mira CRITICAL
```

**claude/trae 已移除**（退役分支不再扫）。5 active 分支全扫到。

## 四、过程教训（已写入 review-process-lessons §8.4.6）

**错误链**：
1. 派 Explore agent 探明 Aetheris 分支，报告"agent/mira 不存在"
2. 基于此让用户决策"修配置去 mira"（用户选 A）
3. 改 drift-config.json 去掉 mira
4. 应用 patch 后实测跑 drift-check.sh，**发现 agent/mira 真实存在**（head=c51a93a7，CRITICAL）
5. 反向加回 mira，恢复正确

**根因**：探明与实际部署之间有时间窗，且 `git branch -r` 依赖本地 fetch 时机（drift-check.sh 自己先 `git fetch origin` 才看到最新）。

**改进**（写入 §8.4.6）：涉及"远端有什么"的事实，应**先跑实际命令**（drift-check.sh / git ls-remote）再让用户决策，不要基于二手探明报告让用户做配置裁定。

## 五、评审要点

1. **去硬编码正确性**：bash 用 `mapfile` + python 读 config，python heredoc 用 `$BRANCHES_STR` 注入（无 `'PYEOF'` 引号让变量展开）。这个 bash/python 交互模式有无问题？引用风险？

2. **fail-closed 完整性**：配置缺失/语法坏/Aetheris 缺/agent_branches 空 4 种失败都 exit 1。够吗？有无漏的失败模式（如 CONFIG 路径错、python3 不可用）？

3. **ref 存在性检查**：`git rev-parse --verify --quiet` 后 MISSING 级别。这个新级别 conflict-tracker.py / drift-cron.sh / 飞书卡片能否正确处理？会不会让 state hash 异常？

4. **drift-config.json 校准合理性**：
   - repos[0] agent-collaboration-standard 标 monitor_level none + agent_branches=[]（这仓库确实无 agent/* 模型，WebFetch 确认只有 master）
   - repos[1] Aetheris 保留 5 分支含 mira（实测存在）
   - 这个校准方向对吗？

5. **过程纪律**：本轮走完整 pre-commit 流程（Plan Mode → 用户审 → 应用 → 验证 → 现在评审），是 §8.4 第 4 类（drift-check.sh）首次触发正面案例。但中途有"探明误导 → 用户决策 → 实测推翻"的插曲，过程认可吗？

6. **归档同步**：archive/ecs-scripts/drift-check.sh 已同步新版（之前是旧版含硬编码）。归档版与 ECS 实际版一致性 OK 吗？

## 六、回滚

```bash
ssh ... root@aetherisonline.xyz "cp /opt/pi-orchestrator/extensions/drift-check.sh.bak-c-layer-20260727-120333 /opt/pi-orchestrator/extensions/drift-check.sh && chmod +x /opt/pi-orchestrator/extensions/drift-check.sh"
# git: git revert 1c5e18d
```

## 七、不做（边界）

- drift-config.json schema 大改（只校准值，不动结构）
- TS Extension / systemd 托管 / spawn exports 修复（C 层其他项）
- drift-cron.sh / conflict-tracker.py / Caddy（不动）
- agent-collaboration-standard 是否应该用 agent/* 模型（架构问题，不在本轮范围）
