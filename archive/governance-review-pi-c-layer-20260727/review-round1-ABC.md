# Pi 治理纳入 C 层 round1 评审汇总

> 评审对象: commit 1c5e18d（drift-check.sh 去硬编码）
> 评审日期: 2026-07-27

## 三方结论

- A（opus4.8p）: CONDITIONAL（2 阻断）
- B（gpt5.6sol）: CONDITIONAL（1 阻断）
- C（cantus）: CONDITIONAL（0 真阻断，软观察为主）

## 共识真阻断（A+B 都标，必须修）

**MISSING 级别被 drift-cron.sh state hash 静默吞掉**：
- `drift-cron.sh:26` `alerts = [b for b in report['branches'] if b.get('level') in ('CRITICAL','WARN')]`
- MISSING 不在过滤集合 → 不进 state hash → hash 不变 → "状态未变化,不发卡片"
- 后果：配置漂移（如未来加错分支名 agent/typo）永远静默漏报
- 与 drift-check.sh 新加 ref 检查的初衷（防御配置漂移告警）自相矛盾

修复方案（选一）：
- drift-check.sh: MISSING 改 level="CRITICAL"（推荐，语义最准）
- drift-check.sh: MISSING 时 exit 1（fail-closed，把配置漂移当 fatal）
- drift-cron.sh: hash 白名单加 MISSING（材料包§七说不动 drift-cron.sh，不推荐）

## A 独有阻断（B/C 降为软观察）

**B1 注入面**：`python3 <<PYEOF`（无引号）+ `branches = "$BRANCHES_STR".split()` 实测可被构造分支名触发任意代码执行。A 实测 `os.system("echo PWNED")` 在 .split() 的 TypeError 之前已执行。

B/C 认为：git ref 规则禁止分支名含 `"` `\` `$()` 等特殊字符，unreachable。但 A 强调"去硬编码的意义就是真值源交给配置，配置值不可信时必须 fail-closed 或转义"。

**判断**：A 技术上对，但威胁模型弱（drift-config.json 是 git 真值，攻击者能改 config = 已能改仓库代码）。但既然修复成本不高（改 argv 传值），值得修。

## 三方软观察（共性）

1. **材料包§五.1 自述失准**：称"bash 用 mapfile"，实际无 mapfile，用 `for b in $BRANCHES_STR`（词分割）
2. **材料包§2.2.3 断言错误**：声称 drift-check exit 1 时 drift-cron 不写 drift-latest.json 旧报告保留。实际 drift-cron.sh:17-18 先 redirect 再 cp，失败时 latest.json 被截断为空
3. **§8.4.6 引用不规范**：lessons 文件无独立 §8.4.6 小节，实为 §8.4 列表第 6 项
4. **归档语义污染**：archive/ecs-scripts/drift-check.sh 被 B 层和 C 层两轮评审共用，旧版实证被覆盖（git 历史可追溯）
5. **lessons 根因偏浅**（C 强调）：只解释"探明为什么错"，未把"基于二手报告让用户做不可逆配置裁定"上升为强制 gate。建议：Explore 探明远端分支强制用 `git ls-remote`（不打 stale 缓存）+ 配置裁定必须附一手命令输出
6. **gen-card.py 未归档**：归档集缺关键消费方，MISSING 卡片渲染行为无法核验
7. **conflict-tracker.py 假 RESOLVED**（C 发现）：CRITICAL（带 conflicts）→ MISSING 时，conflict-tracker.py 第 76-87 行会误发"冲突已解决"卡片（分支是消失了不是解决了）
8. **drift-cron.sh:17-18 半成品 cp**：drift-check exit 非 0 时仍 cp 部分输出为 latest（既有问题，本轮去硬编码放大失败面）

## 修复优先级

P0（必修，A+B 共识）：
- MISSING 静默 → drift-check.sh 把 MISSING 改 level="CRITICAL"（保留 status_desc 区分配漂移 vs 真分叉）

P1（建议修，A 独有但成本低）：
- 注入面 → heredoc 改 `<<'PYEOF'` + argv 传 BRANCHES_STR，或合并到单个 python 进程

P2（软观察，独立任务或下轮）：
- lessons §8.4 第 6 项根因深化
- drift-cron.sh:17-18 半成品 cp 保护
- conflict-tracker.py 假 RESOLVED
- gen-card.py 归档
- 归档版本化子目录
