---
version: "v1.0"
status: "active"
type": "integration-status"
title: "Kimi接入现状"
signoff: "ZCode 2026-07-25"
---

# Kimi 接入现状

> 记录日期: 2026-07-25
> 记录者: ZCode
> 性质: P0第六项 Kimi 部分的当前状态记录

## 已验证可用

### ZCode 终端调度 Kimi（本机形态）

- **调用方式**: ZCode 用 Bash 工具执行 `C:/Users/Admin/.kimi-code/bin/kimi.exe -p "任务" --output-format text`
- **工作目录**: `C:/Users/Admin/Aetheris-clones/kimi/`（agent/kimi 分支，Kimi 独立 clone）
- **模型**: kimi-code/k3（K3，104万上下文，thinking+image+video+tool_use）
- **权限**: config.toml 配置 allow 规则覆盖 Read/Edit/Write/Bash，Kimi 自动执行不需确认
- **session 保持**: 每次 -p 调用返回 session_id，可用 `kimi -C -p "续接"` 保持上下文
- **实测**:
  - 简单问答 ✅
  - 读代码+专业评价 ✅（App.tsx 结构审查）
  - 创建文件（Write权限）✅
  - 多文件读取+关系总结 ✅（App/SensingView/InsightView）

### 代传递确认机制

- Kimi 当前配置下自动执行（allow规则），不会中途求助
- 如果未来收紧权限（改 permission_mode），Kimi 跑完/卡住时输出"需要确认X"
- ZCode 看到后暂停转达给用户，用户决定后用 `kimi -C -p "用户同意X"` 续接

## 已知限制

### 实时过程可视化（ZCode 产品层面限制）

- **限制**: ZCode 的 Bash 工具调用和用户右侧的交互式终端面板是隔离的两个执行通道
- **后果**: ZCode 调度 Kimi 时，用户在编辑器面板看不到 Kimi 的实时处理过程
- **用户只能看到**: ZCode 最终返回的结果摘要
- **用户要看实时过程**: 必须自己在右侧终端手动跑 kimi（但不是 ZCode 调度）
- **归属**: 这是 ZCode 产品架构限制，非当前能解决。未来可考虑工具调用过程可视化

### Kimi -p 模式输出特性

- text 模式：长任务有逐步思考输出（`•` 行），但非逐字流式
- stream-json 模式：JSON 事件流（tool_use/tool_result/assistant），可程序化解析
- 短任务（秒级）：跑完一次性返回，看不出逐步

## 待实现（不在当前阶段）

### Kimi 云端化（接入 Pi 体系）

- **目标**: kimi CLI 部署到 ECS，Pi 通过 subprocess 调度
- **形态**: 飞书 @Pi → Pi 调度 Kimi → 结果回流飞书群
- **前置依赖**: 云端迁移（O1之后）
- **技术同构**: 和 ZCode Bash 调用 kimi 完全同构，只是调度者从 ZCode（本机）换成 Pi（ECS）

### 会话窗口

- **现状**: ZCode 调度时无实时窗口（上面已说明）
- **云端化后**: 飞书群即窗口（@Pi→Kimi→回流，多轮）
- **本机**: 用户直接打开 Kimi 桌面客户端有完整会话窗口

## Kimi 编队画像（fleet-division 原文）

> Kimi = 前端实现主力（前端能力极强），用户裁定
> 执行层：深度(ZCode) / 前端(Kimi) / 平行(Trae) / 生图(Mira) / 批量(G4)

### 实际工作历史

Kimi 不是新成员——已深度参与 Aetheris 项目：
- Wave1: 飞书摘要→accounts 提取（RuleBasedAccountExtractor，35测全绿）
- Wave4: 客户识别、CSM日报
- Wave5: Wave5.5 数据流闭环（当前暂停节点）
- 会审: 审 Qoder 1d，发现 contacts API bug

agent/kimi 分支与 master 同步（0 ahead / 0 behind）。

## 相关配置资产

| 资产 | 位置 | 状态 |
|------|------|------|
| kimi CLI 二进制 | C:/Users/Admin/.kimi-code/bin/kimi.exe (105M) + fd.exe + rg.exe | v0.15.0 |
| CLI 配置 | C:/Users/Admin/.kimi-code/config.toml | active（K3模型，manual权限+allow规则） |
| 凭证 | C:/Users/Admin/.kimi-code/credentials/ (OAuth) | active |
| 桌面客户端 | AppData/Roaming/kimi-desktop/ | active（用户手动用） |
| Aetheris 分支 | Aetheris-clones/kimi/ (agent/kimi) | 与master同步 |
| cc-switch provider | Claude/Codex 都有 Kimi provider（disabled） | 历史配置 |
