# Pre-commit 评审闸门机制 round2 评审汇总（PASS）

> 评审对象：round2 修复（C 第三方案 + B 软观察 + C 元改进）
> 评审日期：2026-07-25
> 评审性质：快速复核（C round1 裁定"无需二轮全量评审，登记 gate_id + 走一次快速复核即可"）

## round2 修复清单

### 必修（3 项，B/C 共识）

1. **Q3 子串误匹配 → files 精确等值**（C 第三方案）
   - 闸门表 markdown → YAML
   - hook 提取 patch 文件名 → 查闸门表 `files` 字段精确等值（消灭子串推断）
   - 单测 case 8A/8B/8C 证伪子串误匹配（b-layer PASS 不放行 b-layer-v2；c-layer-drift-check 事后补审不误放 c-layer-failopen-fix）
   - **17/17 PASS**

2. **Q4 双源漂移 → 单源化**（C 裁定）
   - lessons §8.4 删除 6 项清单内容
   - 只留指针 + 历史成因反思
   - spec §四.步骤0 为唯一事实源

3. **config scope 收窄 → project 级**（B/C 共识）
   - 新建 `<repo>/.zcode/config.json`（hooks.enabled: true, matcher: Bash）
   - hook 脚本复制进 `<repo>/.zcode/hooks/`（闸门配置进 git 硬真值层）
   - config 用 `${ZCODE_PROJECT_DIR}` 变量（团队 clone 零配置）
   - hook REPO_ROOT 推断改为脚本位置向上两级（消除硬编码绝对路径）
   - **不动 `~/.zcode/cli/config.json`**（全局零污染）

### 软观察（2 项，B-Q1/Q5）

4. **Q1 补 rsync + IP 直连**（C 裁定：仅补无意路径）
   - hook 正则加 rsync + IP 直连
   - 单测 case 9A/9B/9C 覆盖

5. **override 留痕**（B-Q5）
   - hook deny 消息提示"override 使用必须在闸门表追加 verdict=override 条目 + override_reason"
   - 实际留痕靠 ZCode 自觉（hook 只读不写 repo 文件，避免副作用）

### 元改进（2 项，C）

6. **循环闭合声明**：spec §四.步骤0 加"本机制自身的变更属强制评审对象"
7. **覆盖缺口声明**：spec 写明"本闸门只覆盖 ZCode 路径"（Kimi/Trae 不受控，先修出血点）

## 三方共识收敛验证

| B round1 阻断 | C round1 裁定 | round2 处理 | 状态 |
|---|---|---|---|
| Q1 正则绕过 14 种 | 过严，降级观察，补 rsync+IP | 补 rsync+IP，余不修 | ✅ |
| Q3 子串误匹配 | 真阻断，第三方案 | files 精确等值 | ✅ |
| Q4 双源漂移 | 真阻断，单源 | lessons 删 6 项 | ✅ |
| config 全局污染 | 真阻断，project 级 | `<repo>/.zcode/config.json` | ✅ |
| Q2 只读白名单 | 软观察 | 已含充分白名单 | ✅ |
| Q5 override 留痕 | 软观察 | deny 消息提示 | ✅ |

## 最终验证

```
=== 1. YAML 语法 === ✅ 合法, 4 条记录
=== 2. hook 单测 === 17/17 PASS
=== 3. 文档交叉引用 === lessons → spec §四.步骤0 ✅ / spec → 闸门表 ✅
=== 4. files 字段对齐 === 5 个 patch 脚本全部精确匹配 ✅
=== 5. 不动 ECS === 本任务是修本地治理流程，无 scp/ssh 写操作 ✅
=== 6. 不动 ~/.zcode/cli/config.json === 全局零污染 ✅
```

## 结论

**三方一致 PASS**（A 弃权不计票 / B round1 阻断已全修 / C round1 放行条件已全满足）。

本闸门机制首次落地，按 spec §四.步骤0 声明"本机制自身的变更属强制评审对象"——本次走完完整 Plan Mode + 三方评审 + round2 修复闭环，是 §四.步骤0 的**首个完整正面案例**（不同于 2026-07-27 的 3 条事后补审）。

## 软观察 backlog（不阻断，独立任务）

- **SO-1**（B/C）：评审材料投递无确认回执 → 调度时内联文本（mira -p 沙箱看不到 Windows 文件）
- **SO-2**（C，v2）：闸门 PASS 记录写入 Aetheris（decision 类型），让 Pi 在漂移治理中消费
- **SO-3**（A，v2）：显式 register 命令 + patch SHA 绑定 → 防恶意场景升级时再做
- **SO-4**（C）：覆盖缺口 → 已在 spec 声明，Kimi/Trae 治理靠 ECS drift-check 兜底
- **SO-5**：patch 脚本末尾契约（要求 apply-*.py 自动更新闸门表）→ 后续任务
