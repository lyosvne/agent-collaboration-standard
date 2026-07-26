# O1收尾并行任务包（交给Qoder客户端）

> 来源: ZCode | 日期: 2026-07-25
> 用途: O1基座就绪收尾阶段，ZCode在治理ECS基础设施，以下2项可并行交给你独立完成
> 原则: 你做完产出报告+方案，由ZCode实现或用户裁定。你不碰仓库/不碰密钥/不改系统。

## 背景

ZCode正在做ECS治理（swap已加✓，时钟已自愈✓，下一步Desktop密钥守卫）。路线图O1收尾还有两项可并行——你独立做调研和验证，产出报告。

路线图全文：`https://aetherisonline.xyz/dispatch/roadmap`（WebFetch可读）
真值源commit：`3e66a24`（agent-collaboration-standard, governance/）

**注意**：本任务包只含路线图O1退出条件相关的事项。知识库里的其他建议（如model-router bug诊断）不在此列——那些需先经"知识库建议→评估→是否纳入路线图"流程，不能直接执行。

---

## 任务B：hermes-sidecar三步新鲜验证（最重要）

### 背景
知识库（action-roadmap/redundancy-audit/first-principles三份文档一致）建议删hermes-sidecar，理由是"src空+ECS零流量"。
但WO-0111审计报告（2026-05-23，Trae SOLO实测）显示它曾是核心组件（`127.0.0.1:8642`，Python v0.14.0，`/api/chat`/`/api/models`走它），CHG-007曾专门升级它。
ECS现状：还在跑，348MB，2个月未重启。
**矛盾证据未消解——删之前必须新鲜验证。**

### 你的任务（三步验证）
SSH到ECS（用户授权ZCode SSH，你可以让用户代为执行命令或基于ZCode给你的输出分析）：

1. **端口连接检查**：
   ```
   ss -tnp | grep 8642
   # 或 netstat -tnp | grep 8642
   ```
   看最近有没有客户端连8642端口。如果有→还在被使用，不能删。

2. **7天日志检查**：
   ```
   journalctl -u aetheris-hermes-sidecar --since "7 days ago" | grep -E "POST|GET|request" | head -20
   ```
   看有没有真实HTTP请求。如果只有启动日志没有请求→零流量佐证。

3. **backend代码引用检查**：
   ```
   cd /opt/aetheris-controlplane-backend
   grep -rn "8642\|hermes-sidecar\|sidecar" backend/src/ --include="*.ts" | head -20
   ```
   看backend现行代码还有没有引用sidecar。如果没有→已被backend/hermes/替代。

### 产出
**验证报告**（按格式）：
```
[VERIFIED] 三步验证结果：
- 端口连接：xxx（有/无连接，具体数据）
- 日志请求：xxx（有/无真实请求，具体数据）
- 代码引用：xxx（有/无引用，具体文件:行号）

[VERDICT] 能否安全停用：是/否/需进一步验证
- 如果是：建议先stop观察48h再卸载（Qoder方案）
- 如果否：列出阻断原因+依赖链
```

---

## 任务D：Desktop明文密钥盘点

### 背景
你07-25审查时发现 `C:\Users\Admin\Desktop\Aetheris\key\` 有明文密钥（ark/kimi/minimax/zai/deepseek + qoder API key + .pem），这是ZCode的盲区，没进任何路线图。
红线：修改密钥必须用户授权。**我们不主动改这些文件，只盘点+给脱敏方案。**

### 你的任务
盘点这个目录的内容，**只读不写**：

1. **列出所有文件**（不读内容，只看文件名和大小）：
   ```
   ls -la "C:\Users\Admin\Desktop\Aetheris\key\"
   ```

2. **每个key文件的用途判断**（基于文件名，不读内容）：
   - ark.key → 火山方舟ARK API（model-router用）
   - kimi.key → Kimi/Moonshot API
   - minimax.key → MiniMax API
   - zai.key → 智谱AI API
   - deepseek.key → DeepSeek API
   - qoder API key.txt → Qoder Cloud Agents PAT
   - *.pem → SSH密钥或证书

3. **对比已知的key使用点**：
   - ark key：ECS .env有QODER_PAT，model-router配置可能在backend里
   - zai key：.zcode/v2/config.json有GLM-5.2 apiKey（智谱）
   - qoder key：ECS .env的QODER_PAT
   - 哪些key在Desktop是"唯一副本"（其他地方没有）？哪些是冗余副本？

### 产出
**盘点报告**：
```
[VERIFIED] Desktop\Aetheris\key\ 文件清单：
- ark.key (size) — 用途：xxx — 其他副本位置：xxx/无
- kimi.key (size) — 用途：xxx — 其他副本位置：xxx/无
- ...

[RISK] 评估：
- 哪些key是唯一副本（删除会丢）
- 哪些key已过时（对应服务已停用）
- 哪些key在用（当前活跃）

[PROPOSAL] 脱敏方案（不执行，等用户授权）：
- 立即迁移到xxx（密钥守卫位置）
- 过期key归档到xxx
- 保留副本清理
```

---

## 协作约定

- **产出位置**：写到 `C:\Users\Admin\.agent-collaboration\templates\qoder-o1-parallel-tasks-response.md`
- **真值声明**：回执首部声明你读的governance commit hash
- **不碰红线**：不删文件/不改密钥/不push/不改系统配置
- **需要ZCode配合时**：在回执里标注 `[NEED-ZCODE]`，ZCode会跟进
- **用户裁定项**：标注 `[NEED-USER]`

## 优先级
B（hermes-sidecar验证）> D（密钥盘点）
B是退役清理的前置，最优先。
