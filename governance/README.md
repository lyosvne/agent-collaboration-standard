# Governance（编队治理文档）

> 治理文档的 git 真值目录。依据协议 §9.2（2026-07-23 用户授权入库）。
> 本目录任何修订 = git commit，历史可溯。本地冻结快照（只读，Phase D 起降级）：`C:\Users\Admin\.agent-collaboration\standards\`

## 文档层级

| 文件 | 层级 | 状态 |
|------|------|------|
| `north-star-v1.0.md` | 北极星（方向环 M1 唯一校准基准） | 用户定稿生效 2026-07-23 |
| `workspace-collaboration-v2.1.md` | 协作协议（编队宪法） | 用户裁定生效 2026-07-23 |
| `agent-matrix-architecture-v1.0.md` | 架构真值（ZCode 签发） | 生效（webhook 表述经复核确认正确） |
| `fleet-division-v1.1.md` | G+M 双环分工 + 真值/工具链注册表 | 用户批准 2026-07-23 |
| `specs/qoder-sse-consumer-design.md` | 实施规格：Pi 侧 Qoder SSE 消费器 | 待 ZCode review |
| `specs/pi-feishu-bridge-design.md` | 实施规格：飞书移动端桥接 | 待 ZCode review |
| `specs/pi-drift-governance-spec.md` | 实施规格：漂移治理（push 授权已签发） | 待 ZCode review |

## 阅读顺序（新 agent 接入）

1. `north-star-v1.0.md`（为什么存在）
2. `workspace-collaboration-v2.1.md`（怎么协作）
3. `agent-matrix-architecture-v1.0.md` + `fleet-division-v1.1.md`（谁做什么）
4. `specs/`（怎么施工）
