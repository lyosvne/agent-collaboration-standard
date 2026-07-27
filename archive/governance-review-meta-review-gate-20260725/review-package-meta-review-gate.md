# 评审材料包：Pre-commit 评审闸门机制（meta-review-gate）

> 评审对象：本方案的 3 个新文件 + 2 个改文件 + 1 个待改用户全局配置
> 评审性质：**meta-review**（修评审流程的方案本身走评审，避免循环依赖——scope 限定技术正确性，不评"评审流程本身是否合理"）
> 评审日期：2026-07-25
> 触发依据：用户要求"这个也要走评审" + 本方案改 `review-process-lessons.md` / `governance-review-process.md` / 新增 hook（治理流程改动）

## 一、背景

用户在 Pi 治理纳入 B/C 层过程中 3 次跳过 pre-commit 评审直接改 ECS（bac6e95 / fail-open round2 / round3）。用户原话纠正：

> "现在的问题不在自审自修，都是你修，但是你总是忘了审。"

真根因（用户修正后）不是"审的人不对"，是**评审环节没有强制触发机制**——靠 ZCode 自觉，每次都能找到"小改动/1 行修复"理由跳过。

## 二、改动清单（评审对象）

### 2.1 改 `governance/specs/governance-review-process.md`（已应用）
- §四 加"步骤 0：pre-commit 评审前置闸门（强制触发）"
- 含 6 类强制清单表格 + 闸门流程 + 强制机制说明
- §四.步骤5 归档说明加"ECS 改动必须更新闸门表"钩子

### 2.2 改 `governance/specs/review-process-lessons.md`（已应用）
- §8.4 改为"强制清单已迁至 spec §四.步骤0，本节保留教训反思"
- 加 2026-07-25 meta-review 后补的"结构性根因"段
- 指向本评审目录

### 2.3 新增 `governance/specs/pre-commit-review-gate-log.md`（已应用）
- 闸门日志表（唯一事实源）
- 回填 3 条历史（bac6e95 / 6bd4804 / 4535842，状态=事后补审）
- 字段约定 + Hook 读取说明

### 2.4 新增 `C:\Users\Admin\.zcode\hooks\review-gate-precommit.py`（已应用，未挂 config）
- PreToolUse hook，matcher: `Bash`
- 正则匹配 scp/ssh 到 ECS 的强制触发路径
- 查闸门表 → 无 PASS 条目则 exit 2 deny
- 含 override 机制（30 分钟窗口）
- 单测 `test-review-gate.py` 12/12 PASS

### 2.5 待改 `C:\Users\Admin\.zcode\cli\config.json`（**评审 PASS 后才应用**）
- 在 `hooks.events.PreToolUse` 数组追加一条 matcher=`Bash` 指向新 hook
- **红线**：这是用户全局 ZCode 应用配置，ExitPlanMode 已授权

## 三、要评审方回答的技术问题（scope 限定）

### Q1：hook 正则是否会漏拦？
具体场景：
- `scp -i ~/.ssh/aetheris-ecs.pem apply-foo.py root@aetherisonline.xyz:/opt/...`（带 -i 参数）
- `rsync apply-foo.py root@aetherisonline.xyz:/opt/...`（rsync 不在正则里）
- `cat apply-foo.py | ssh root@aetherisonline.xyz 'cat > /opt/...'`（管道绕过 scp）
- `scp` 命令里 ECS 主机用 IP 而非域名（如 `root@1.2.3.4`）

请评审方判断：当前正则是否覆盖？漏拦是否可接受（hook 是"防忘记"非"防恶意"）？

### Q2：hook 正则是否会误伤？
具体场景：
- `ssh root@aetherisonline.xyz 'systemctl status pi-dispatch-server'`（只读，应放行）
- `ssh root@aetherisonline.xyz 'journalctl -u pi-dispatch-server'`（只读日志）
- `ssh root@aetherisonline.xyz 'curl http://localhost:8080/health'`（健康检查）
- `ssh root@aetherisonline.xyz 'cat /opt/pi-orchestrator/logs/drift-latest.json'`（读日志，但路径命中 `/opt/pi-orchestrator/`）

请评审方判断：SSH_WRITE_PATTERN 匹配 `/opt/pi-orchestrator/` 是否会误伤"读 /opt/pi-orchestrator 下文件"？当前靠 SSH_READONLY_PATTERN 白名单优先放行，白名单是否够全？

### Q3：闸门日志表的对象名匹配逻辑是否健壮？
hook 提取的对象名（如 `b-layer`）和表里对象名（如 `pi-b-layer`）匹配逻辑：
```python
obj_no_pi = obj_clean[3:] if obj_clean.startswith("pi-") else obj_clean
if object_name in obj_clean or object_name in obj_no_pi or obj_no_pi in object_name:
```
风险：
- `c-layer-drift-check` vs `c-layer-failopen-fix`——两个都是 `c-layer-*`，会互相匹配吗？
- 子串匹配的歧义（`b-layer` 是 `sub-layer` 的子串）

请评审方判断：当前匹配是否够精确？是否应改为精确匹配（去 pi- 前缀后 ==）？

### Q4：文档迁移是否引入双源漂移？
- `governance-review-process.md` §四.步骤0 有 6 类强制清单
- `review-process-lessons.md` §8.4 保留了"历史教训反思"6 项（措辞相似）
- 风险：未来维护者改了 spec 的清单但忘了同步 lessons，或反之

请评审方判断：lessons §8.4 保留的 6 项是否应该删掉只留指针？还是保留作为历史反思材料？

### Q5：override 机制的留痕是否充分？
当前 override 只是一个本地 JSON 文件（`~/.zcode/hooks/.review-gate-override.json`），不进闸门表。
风险：紧急 hotfix 用 override 后，事后忘了补闸门表条目，闸门表永久缺失记录。

请评审方判断：override 是否应该在闸门表留"override 跳闸"行？还是靠事后人工补？

## 四、验证证据

### 4.1 单测结果（12/12 PASS）
```
✅ PASS | 1A: scp apply-pi-b-layer.py + 状态=事后补审 → deny
✅ PASS | 1B: scp apply-*.py + 表有 PASS 条目 → 放行（临时表）
✅ PASS | 2: scp apply-unknown-obj.py + 表无条目 → deny
✅ PASS | 3: scp apply-c-layer-drift-check.py + 状态=事后补审 → deny
✅ PASS | 4A: ssh 只读 git log → 放行
✅ PASS | 4B: ssh systemctl status → 放行
✅ PASS | 4C: ssh curl /health → 放行
✅ PASS | 5: ssh systemctl restart → deny（写操作）
✅ PASS | 6: ssh 直接改 /opt/pi-orchestrator 文件 → deny
✅ PASS | 7: scp 到非 ECS 主机 → 放行
✅ PASS | 8: 非 Bash 工具（Write） → 放行
✅ PASS | 9: override 生效 → 放行
```

### 4.2 文档交叉引用检查
- `governance-review-process.md` §四.步骤0 ← lessons §8.4 指向 ✅
- `pre-commit-review-gate-log.md` ← spec §四.步骤0 + lessons §8.4 指向 ✅
- 本评审目录 ← lessons §8.4 指向 ✅

### 4.3 不动 ECS（本任务是修本地治理流程）
- 无 scp / ssh 写操作
- 无 ECS 文件改动

## 五、风险（已在 plan 列出）

1. hook 误伤只读 ssh（Q2）
2. config.json 全局生效影响所有 ZCode session
3. 闸门表人工维护可能漏更新
4. 循环依赖（修评审流程的方案走评审）—— scope 限定技术正确性
5. 正则可绕过（agent 改命令文本）—— hook 是"防忘记"非"防恶意"

## 六、不评的 scope

- **不评**"评审流程本身是否合理"（避免循环依赖）
- **不评**"三方评审制度是否该存在"
- **不评**"用户该不该是唯一裁判"
- 只评方案的技术正确性（正则/表结构/文档迁移）

---

## 评审方

- **A**：opus4.8p（via Mira 同步）—— 重点评 Q3/Q4（逻辑健壮性 + 文档漂移）
- **B**：gpt5.6sol（via Mira 同步）—— 重点评 Q1/Q2（正则覆盖 + 误伤）
- **C**：cantus（via Qoder 异步）—— 重点评 Q5（override 留痕）+ 整体架构判断
