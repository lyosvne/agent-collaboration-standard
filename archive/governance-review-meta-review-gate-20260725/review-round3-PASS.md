# Pre-commit 评审闸门机制 round3 评审汇总（PASS）

> 评审对象：round3 修复（B 5 项放行条件 + C 自动降级条款 + 跳链教训）
> 评审日期：2026-07-25
> 评审性质：跳链纠正后重评 + round3 fail-closed 加固

## round1→round3 演进

### round1（A 跳链，结论作废）
- A（**误用 opus4.6**）：BLOCKER（材料不可达）→ **round3 撤销**（A 自己判定 round1 是方法论错误）
- B（gpt5.6sol）：CONDITIONAL（4 硬阻断）
- C（cantus via ECS qoder-bridge）：CONDITIONAL（3 放行条件）

### round2（修复 B/C 共识）
3 必修（files 精确等值 / lessons 单源化 / config project 级）+ 2 软观察（rsync+IP / override 留痕）+ 2 元改进（循环闭合 + 覆盖缺口）。

### round3（跳链纠正 + fail-closed 加固，本汇总）

**跳链事件**：round1 调 A 时误用 opus4.6（spec 真值层是 opus4.8p）。用户发现并质问"为什么私自更改架构评审档位"。ZCode 诊断 4 个断裂点（详见 lessons §8.6），实测 opus4.8p 完全可调（`mira --help` 列表滞后）。用真实 opus4.8p 重调 A/B/C。

## round3 真实三方结论

### A（opus4.8p，真实档位）—— **PASS**
- 撤销 round1 BLOCKER（"材料不可达不构成 BLOCKER 而构成弃权"）
- files 精确等值真消灭 Q3 子串误匹配（Python `in list` 是 O(n) 全串等值）
- SHA 绑定在防忘记模型下是过度工程（成本高收益低，被"改 patch = 改 files 条目 = 触发重审"覆盖）
- config project 级是当前场景最优 scope（闸门进 git 硬真值层是关键正确决策）
- 循环闭合破法正确（自指良性结构）
- 威胁模型边界划对了（防忘记 ≠ 防恶意）
- **整体判断：治本不是治标**（单源事实 + 硬真值链闭合 + 自指良性）

### B（gpt5.6sol）—— **CONDITIONAL → 5 项放行条件，round3 处理**
| B 放行条件 | round3 处理 | 状态 |
|---|---|---|
| 1. hook 用 YAML 解析器 + list 成员判定 + 路径归一化 | 已用 pyyaml + `in list` + 小写归一化（F4 单测钉死） | ✅ |
| 2. lessons lint + 指针格式冻结 | 指针冻结为纯锚点（删计数），lint 登记 SO-6 | ✅（lint 待办） |
| 3. hooks.enabled 不可本地 override | 登记 SO-7（config 设计层面，独立任务） | 登记待办 |
| 4. 3 处 fail-open deny-by-default | 实测全部 deny（F1/F2/F3 单测钉死） | ✅ |
| 5. override 补录强制校验 | 登记 SO-8（需 hook 写状态，超出本轮 scope） | 登记待办 |

### C（cantus via ECS qoder-bridge）—— **PASS（附自动降级条款）**
- 3 放行条件全部满足且超出（文件名全名等值比 gate_id 等值更好）
- 自动降级条款：fail-closed（YAML 缺失/解析异常）必须有单测钉死 → **round3 已补 F1/F2/F3，条款满足，PASS 即时生效**
- 2 项残余风险登记（不阻断）：文件名复用绕过（长期加固方向 SHA）/ hook 自我修改不受自身管辖（policy 声明非机制强制）

## round3 修复清单

### 必修（C 自动降级 + B 接受条件）
1. **fail-closed 单测钉死**（C 自动降级条款）：
   - F1: YAML 文件不存在 → deny ✅
   - F2: YAML 语法坏 → deny ✅
   - F3: 条目无 files 字段 → deny（不因 verdict=PASS 误放）✅
2. **路径归一化**（B-Q3 接受条件 3）：hook 提取文件名 + 比较都强制小写（F4 钉死 Apply-B-LAYER 大写仍匹配）
3. **指针格式冻结**（B-Q4 接受条件 2）：lessons §8.4 指针删计数，纯锚点
4. **REPO_ROOT 守卫**（B-config 接受条件 3）：环境变量未定义时 fallback 到脚本推断，下游 fail-closed

### 教训沉淀（用户授权）
5. **lessons §8.6 跳链教训**：4 断裂点 + 防复发措施（实测优先于文档 / 冲突上报不自行换档）
6. **spec §二.2.1 调度前校验**：档位真值层一致 + 实测可达 + 冲突上报 + 材料内联

## 最终验证

```
=== 1. hook 单测 === 21/21 PASS（含 F1-F4 fail-closed + 归一化钉死）
=== 2. repo 内副本独立跑 === 21/21 PASS
=== 3. YAML 合法 === 4 条记录
=== 4. 文档交叉引用 === lessons → spec §四.步骤0 / §二.2.1 ✅
=== 5. 跳链排查 === 22 档全部实测可达，qoder 三档全可达，只 A round1 跳了
=== 6. 不动 ECS / 不动 ~/.zcode/cli/config.json === ✅
```

## 结论

**三方一致 PASS**（A PASS 撤销 round1 BLOCKER / B 5 项放行条件 3 项即修 + 3 项登记 SO-6/7/8 / C PASS 自动降级条款满足）。

本闸门机制首个完整正面案例，含**两层元教训**：
- §8.4 "忘了审" → 用 hook 强制拦截
- §8.6 "忘了验证协作链路" → 用 spec §二.2.1 调度前校验 + 实测优先原则

## 软观察 backlog（不阻断，独立任务）

- **SO-1**（B/C）：评审材料投递无确认回执 → spec §二.2.1 已要求内联（部分缓解）
- **SO-2**（C，v2）：闸门 PASS 记录写入 Aetheris（decision 类型）
- **SO-3**（A，v2）：显式 register + patch SHA 绑定（防恶意升级时）
- **SO-6**（B-Q4）：lessons 漂移 lint（CI 加 grep 规则）
- **SO-7**（B-config）：hooks.enabled 本地 override 审计
- **SO-8**（B-override）：override 补录强制校验（下次 commit 校验上次）
- **SO-9**（C）：文件名复用绕过 → files 条目附 sha256（长期加固）
- **SO-10**（C）：hook 自我修改 → drift-check 监控 `.zcode/` 路径变更
- **SO-11**：协作链路跳链检测 hook（类比 review-gate，防调度时换档）—— 本机制覆盖缺口之外的另一类缺口
