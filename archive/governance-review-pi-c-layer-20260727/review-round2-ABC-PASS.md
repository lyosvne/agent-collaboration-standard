# Pi 治理纳入 C 层 round2 评审结果（三方全 PASS）

> 评审对象: commit 6bd4804（MISSING→CRITICAL + 注入面消除）
> 评审日期: 2026-07-27

## 结论：A PASS + B PASS + C PASS

C 层 round1→round2 完整闭环。

## 三方评审要点

### A（PASS）

- **B1 注入面真消除**：重新构造攻击向量（分支名 `agent/x";os.system("echo PWNED")#`），修复后的 heredoc `<<'PYEOF'` + argv + JSON 三重防线阻断注入路径。JS 模拟验证旧模式 os.system 执行 vs 新模式始终是字符串元素
- **B2 MISSING 闭环**：JS hash 模拟证明 CRITICAL 进 state hash，去重行为正确（首次漂移发卡/持续静默/漂移修复发恢复卡）。假分支测试可信
- **新发现**：conflict-tracker 假 RESOLVED 材料包§五措辞需修正（不阻断）—— conflict-tracker 不读 level 只看 conflicts，但若分支上次有冲突本次配置漂移会误触发 RESOLVED 卡（独立缺陷，非本轮引入）

### B（PASS）

- **B-1 闭环**：drift-cron.sh:26 filter 命中 CRITICAL，链路完整
- **conflict-tracker 验证**：完全不读 level 字段，round2 修复对它零影响。假 RESOLVED 路径在 MISSING 旧版即存在，与本次修复正交
- **过程纪律认可**：§8.4 第 4 类首次完整闭环（评审发现真阻断 → 修复 → 复评）

### C（PASS）

- **P0/P1 技术验证通过**
- **重要发现**：实测 git ref 规则——`"` `` ` `` `;` 实际是合法分支字符（rc=0），证明 A round1 注入面阻断技术上成立，C round1 的"unreachable"判断偏松
- **修复后实测**：三种恶意分支名（`agent/a"b` / `` agent/a`id` `` / `agent/a;touch /tmp/pwned;`）经修复路径全部安全传递，无命令执行 artifact
- 软观察延后可接受

## 三方共识

- P0（MISSING→CRITICAL）+ P1（注入面）2 阻断真闭环
- 软观察（conflict-tracker 假 RESOLVED / drift-cron 半成品 cp / lessons 根因 / gen-card 归档等）正确归入 backlog

## 下轮优先项（三方软观察 backlog）

1. conflict-tracker.py L76-87 加远端存活校验（修假 RESOLVED，fail-open 路径）
2. drift-cron.sh:17-18 半成品 cp 保护（fail-open 路径）
3. lessons §8.4 第 6 项根因深化（git ls-remote 强制规则 + 配置裁定必须附一手命令输出）
4. gen-card.py 归档（飞书卡片渲染行为可核验）
5. 归档版本化子目录（archive/ecs-scripts/ 多轮共用）

## 纪律闭环

- §8.4 第 4 类（drift-check.sh 改动）首次完整闭环
- round1 三方分级清晰（共识真阻断 vs 独有阻断 vs 软观察）
- round2 修复精准对应分级 + 实测验证
- pre-commit 流程：Plan Mode → 用户审 → 应用 → 验证 → round1 评审 → 修复 → round2 复评 → push
