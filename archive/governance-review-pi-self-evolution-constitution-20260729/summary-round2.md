# Pi 自进化宪法 v0.2 三方评审汇总 — Round 2

> 评审日期：2026-07-29
> 评审对象：宪法 v0.2（吸收 round1 全部 P0/阻断修订）
> A/B 用 `-r` 续接 round1 session，C fresh + 内嵌 round1 结论

---

## 一、Round 2 三方判决

| 评审方 | Round1 | Round2 | 变化 |
|---|---|---|---|
| A (opus4.8p) | 条件通过 | **PASS** ✅ | 14 条全 ✅，3 个 P2 观察项不阻断，"签发上岗证" |
| B (gpt5.6sol) | 条件通过 | **仍条件通过** | 10✅/4⚠️，发现 2 个新 P0（N1/N2） |
| C (cantus) | 条件通过 | **PASS** ✅ | 5 阻断全实质补齐，3 条观察项非阻断 |

**2 PASS + 1 条件通过**。B 的 N1/N2 是真实结构性问题，A 和 C 都认同同类观察但判为非阻断（纵深防御层）。

---

## 二、Round1 → Round2 修订成效

### 完全闭合（三方一致 ✅）
1. M6（Verifier 世界隔离）—— A/B/C 都判 ✅，B 称"本次修订最漂亮的一处"
2. evolution-engine 拆 core/strategy —— 三方 ✅
3. L1 证据函数（21天+100样本+密封集误报率+3提案进Gate+注入攻击）—— 三方 ✅，A 称"超预期加分"
4. Staging→Adopt 四步原子 —— 三方 ✅
5. Adopt 混合落地（代码 PR + 数据 vault）—— 三方 ✅，C 称"红线冲突解除"
6. kill switch 移进程外 systemd timer —— 三方 ✅
7. 密封测试集 owner（Trae+Mira）+ ledger 脱敏 —— 三方 ✅
8. 档位绑定 O 阶段 —— 三方 ✅（用户裁定即终裁）
9. 编队关键路径排除 —— 三方 ✅
10. 集合闭合律 —— 三方 ✅

### B 标 ⚠️ 部分（A/C 判 ✅）
- #11 两 MemoryGovernanceService：B 指出 L1 期间两类共存违反 M3，需"仲裁规则"
- #12 记忆双真值：B 指出"L2 前定"= L1 期间未定
- B 建议：加"L1 M3 违规豁免清单 + 仲裁规则"附录，L1→L2 前置清零

---

## 三、B 发现的新 P0（N1/N2）—— 核心分歧

### N1：Node fs hook 是 monkey patch，Pi 可再 patch 回去
- **B 证据**：`delete require.cache[require.resolve('fs')]; const rawFs = require('fs')` 或 `process.binding('fs')` 直接拿原生 fs。
- **A 观点**：列为 P2 观察项（运营层），不阻断。
- **C 观点**：⚠️ 同意"不是硬边界"，child_process/worker_threads/native addon 可绕。
- **B 建议**：fs 写入沙盒必须由 Node Permission Model（`--permission --allow-fs-write=<path>`）或 Linux landlock/bwrap 提供。userland hook 降级为辅助层。宪法写明"任何 userland-only 的写保护不构成 M2 的强制执行"。

### N2：数据类走 git 外 + 漂移治理登记，与 M5 相互削弱
- **B 证据**：data/vault 无 git commit hash 锚点；"漂移治理 denylist 登记"= 事后审计非事前拦截；Pi 有能力覆盖历史 skill 版本，依赖 archive-rename"自觉"。
- **B 建议**：数据类可写区挂 append-only 属性（Linux `chattr +a`，非 root 无法解除），或包成独立 git 仓库（Pi 只能 commit 不能 force-push/rebase/delete）。

### 分歧性质
A/C 认为：N1/N2 是"纵深防御层"问题，L1/L2 report-only 或 staging 场景下 userland hook 够用，L3 前补即可。
B 认为：N1/N2 是 round1 P0 第二条（"过度信任写下来的规则，低估运行期物理隔离"）的**复发**，v0.2 用运行期动态检查替代了本应是内核/文件系统层强制的护栏。

---

## 四、ZCode 综合判断

**B 的 N1/N2 技术上完全正确**——这是真实的结构性漏洞，不是挑刺。fs hook 确实可被 `delete require.cache` 绕过，data/vault 确实无内容寻址锚点。A 和 C 也都认同"runtime 检测不是硬边界"，只是判了不同的严重度。

**分歧的根源是"L1 现在就开 vs 等补完再开"的风险容忍度**：
- A/C：L1 是 report-only，Pi 不真写东西，userland hook 够用，N1/N2 留 L3 前补
- B：宪法层就该一次到位，避免 L2→L3 升档时发现宪法还要动大手术

**我的建议**：采纳 B 的 N1/N2，但**不阻塞 L1 启动**。理由：
1. N1/N2 技术正确，补了只有好处
2. 但 L1 是 report-only（Pi 不真写 live/不改代码），N1/N2 的攻击面在 L1 不存在
3. 补进 v0.3 作为"L2 启动硬前置"（L2 才真写东西），既尊重 B 的严谨又不拖慢 L1

这等于：**宪法 v0.3 = v0.2 + N1/N2 补丁（L2 前置）+ B 的 R1/R2 软门槛**。L1 可立即启动，N1/N2 在 L1 期间（21天+）补进 v0.3。

---

## 五、Round2 后的 P2/R 观察项汇总（不阻断，上岗后迭代）

| # | 来源 | 内容 | 处理时机 |
|---|---|---|---|
| P2-1 | A | memory taint check 关键词升级为独立 Judge 语义分类 | L1 跑 30 天内 |
| P2-2 | A | G6 人审最小证据包四件套 + Verifier 报告落只读区 | L1 跑 30 天内 |
| P2-3 | A | L1 拆 L1a/L1b，21 天从测试集就绪日起算 | L1 启动前 |
| P2-4 | A | skill 静态扫描审批 SLA + 超时默认 REJECT | L2 启动前 |
| N1 | B | fs 沙盒移 Node Permission Model/landlock，userland hook 降辅助 | **L2 启动前（硬前置）** |
| N2 | B | 数据类可写区挂 chattr +a 或独立 git 仓库 | **L2 启动前（硬前置）** |
| R1 | B | L1 M3 违规豁免清单 + 仲裁规则附录 | L1 启动首周 |
| R2 | B | 注入攻击题库 14 天轮换 + Pi 侧只见二值 | L1 启动首周 |
| C-obs1 | C | runtime 检测定位为"纵深防御层"非防线本身（措辞） | v0.3 措辞调整 |
| C-obs2 | C | 密封集轮换机制（L2 前加换血条款） | L2 启动前 |
| C-obs3 | C | strategy 层按 ID 注册非序号（实现细节） | 实现时 |

---

## 六、结论与下一步

**评审结论**：2 PASS + 1 条件通过。B 的 N1/N2 技术正确但 L1 阶段（report-only）攻击面不存在，建议作为 L2 硬前置补进 v0.3，不阻塞 L1 启动。

**需用户裁决**：B 坚持"宪法层一次到位" vs A/C/L1-可先开 的分歧。两个选项：
- (a) 采纳我的建议：L1 立即启动，N1/N2 在 L1 期间补 v0.3（L2 前置）
- (b) 采纳 B 的严谨：先补 N1/N2 成 v0.3 再开 L1（多花 1-2 天补代码）

**无论选哪个，宪法 v0.2 已达"可上岗"标准**（2/3 PASS + 第3方的技术异议已被另两方判为非阻断）。

---

## 附：session_id（已回填 index）
- A round2: `337332156435`（-r 续接 round1）
- B round2: `337247830035`（-r 续接 round1）
- C round2: `sess_00kowv30c2e4g4kga99q`（fresh）
