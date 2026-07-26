# 真值链路最终方案（ZCode + Qoder 碰撞定稿）

> 签发: ZCode | 日期: 2026-07-25
> 状态: 等待用户裁定后生效
> 依据: ZCode第一性分析 + Qoder五维度对抗审查（含新鲜取证） + git-truth-protocol.md已存在协议

## 总判断

Qoder的4个"不成立假设"全部成立。我的原始设计有覆盖面幻觉——hook只约束ZCode自己。最终方案采用Qoder的分级策略：止血项现在做，重型项等O2/M2。

---

## 逐条采纳表

| Qoder指出 | ZCode判定 | 改动 |
|---|---|---|
| 1. 切clone前必须全量对账（本地有git没有的文件会丢） | 采纳 | 第一步执行全量diff对账 |
| 2. 默认分支master不是main | 采纳 | 所有脚本动态解析分支 |
| 3. 复用git-truth-protocol.md，不平行发明 | 采纳 | 扩展现有10行协议，不新建 |
| 4. "只读clone"无法强制→改脏改动检测 | 采纳 | 目标从"防改"改"改了必被发现" |
| 5. 多agent同commit是锁步幻觉→改可追溯 | 采纳 | 产出物声明commit hash，不追同步 |
| 6. PreToolUse是错误位置→SessionStart+缓存 | 采纳 | hook位置改为SessionStart，TTL 1h |
| 7. 离线降级声明模式，不阻塞 | 采纳 | 离线只报hash+上次fetch时长 |
| 8. hook只覆盖ZCode→软约束入口文档+硬约束等O3 | 采纳 | 软约束现在做，硬约束进O3 |
| 9. 校准拆两半：版本校准现在/进度校准等M2 | 采纳 | 拆开，便宜的一半先做 |
| 10. Markdown加frontmatter不全结构化 | 采纳 | YAML frontmatter + KR表格 |
| 11. superseded文件立即归档标注 | 采纳 | 立即处理north-star-v1.3-roadmap-annex.md |
| 12. 不可委托清单→north-star（稳定性=红线级） | 采纳 | 写进north-star v1.3 |
| 13. G/M双环→governance层（平行于目标链） | 采纳 | 两条链显式画出 |
| 14. 当前位置拆STATUS.md（高频更新不污染真值源） | 采纳 | roadmap删除当前位置段，新建STATUS.md |
| 15. 上层引用下层必须带版本（commit hash） | 采纳 | 引用格式："见roadmap v1.1 @ commit abc123" |

15条全部采纳，0条反驳。Qoder这轮回执没有一条是错的。

---

## 最终方案：真值链路三层

### 层1：真值源（唯一性）

**仓库**：github.com/lyosvne/agent-collaboration-standard（默认分支master，已存在）
**协议**：复用并扩展 `protocols/git-truth-protocol.md`（现10行，扩展到包含版本声明/脏改动检测/superseded归档规则）
**本地standards/**：改为git clone（不是手动镜像）
**ECS dispatch**：cron定期pull + pull失败告警（漂移治理cron是先例）

**切换前的硬前置**：全量对账——本地standards/和git仓库做完整diff，该入库的入库（templates/回执/审计报告等），不该入库的标记。**对账完才能切clone，否则切换那一刻就丢数据。**

### 层2：变更追踪（生命力）

**变更=git commit**（不是改文件）。commit message含版本号+变更摘要。
**变更触发校准**：事件驱动（阶段切换/重大认知变化/用户主动要求）。
**校准拆两半**：
- 版本校准（现在做）：git log + frontmatter，检查文档间新旧一致性
- 进度校准（等M2）：实际执行vs文档声称，依赖埋点

**文档结构化**：YAML frontmatter（version/date/status: active|superseded/supersedes/commit）+ KR固定格式表格。正文保持自由Markdown。

**superseded规则**：被取代的文件必须标status或移入archive/。立即处理：`north-star-v1.3-roadmap-annex.md`（07-24旧版路线图）标superseded。

### 层3：读取验证（读取保证）

**ZCode的hook**：
- 位置：SessionStart（不是PreToolUse），TTL 1h缓存
- 有网：比本地HEAD和remote HEAD，落后提示pull
- 离线：声明模式，报hash+上次fetch时长，超24h警告但不阻塞

**全agent覆盖（分级）**：
- 软约束（现在做）：各agent入口文档（AGENTS.md/START_HERE.md）加启动清单——"先报告你读的standards版本hash"
- 硬约束（进O3）：Pi分发任务时附带当前真值commit hash，agent回执回声该hash，不一致Pi拒收

**承认的局限**：在硬约束上线前（O3），读取保证是软约束——靠agent自觉声明。这是O1阶段可接受的折中。

---

## 承接梯度（最终版）

两条平行链：

```
【目标链】为什么→方向→路径→执行
  使命（最稳定，业务推导）
    ↓
  north-star v1.3（校准基准）
    终局 + 第一性原则 + 红线 + 不可委托清单
    引用 → roadmap v1.1 @ commit abc123
    ↓
  roadmap v1.1（执行罗盘）
    七维度 + 四阶段O/KR + 评估反馈 + Wave映射
    引用 → STATUS.md（高频状态）
    ↓
  实施（由当前阶段智能体分解，不进路线图）

【组织链】谁做什么
  fleet-division v1.1（governance层）
    G1-G7运转环 + M1-M5方向环
    平行于目标链，不互相塞
```

**梯度原则**：
- 上一层只定义"是什么/为什么"，不定义"怎么做/怎么量"
- 下一层继承约束不得违反
- 上层引用下层必须带版本（commit hash）
- 当前位置/进度=STATUS.md（高频更新，不污染真值源）

---

## 立即执行项（止血五项，一天量级）

按Qoder建议，这些现在做，不等"先跑顺"：

1. **全量对账**：本地standards/ vs git仓库，diff后该入库的入库
2. **superseded归档**：north-star-v1.3-roadmap-annex.md标status或移archive/
3. **frontmatter**：目标文档加YAML frontmatter（version/date/status/commit）
4. **ECS cron pull+告警**：dispatch定期从git pull，失败发飞书告警
5. **入口文档声明**：AGENTS.md/START_HERE.md加"启动时报告所读standards版本hash"

**等O2/M2的**：自动进度比对、Pi硬约束版本回声、全agent强制hook

---

## 分歧项

无。Qoder15条全部采纳。

## 留用户裁定

这个最终方案+承接梯度，是否生效？生效后按"立即执行项"5步推进。
