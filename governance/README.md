# Governance（编队治理文档）

> 治理文档的 git 真值目录。依据协议 §9.2（2026-07-23 用户授权入库）。
> 本目录任何修订 = git commit，历史可溯。本地冻结快照（只读，Phase D 起降级）：`C:\Users\Admin\.agent-collaboration\standards\`

## 文档层级

| 文件 | 层级 | 状态 |
|------|------|------|
| `north-star-v1.2.md` | 北极星（canonical 稳定路径，逻辑版本见 frontmatter） | v1.5 用户定稿生效 2026-08-12 |
| `global-roadmap-v1.1.md` | 全局路线图（canonical 稳定路径，逻辑版本见 frontmatter） | v1.19 用户定稿生效 2026-08-12 |
| `version-manifest.json` | canonical 路径与逻辑版本契约 | 生效 |
| `../specs/pi-cognitive-plane-and-self-evolution-v1.0.md` | Pi 认知平面与自进化质量门 | v1.0 用户定稿生效 2026-08-08 |
| `workspace-collaboration-v2.1.md` | 协作协议（canonical 稳定路径） | v2.3 用户裁定生效 2026-08-12 |
| `agent-matrix-architecture-v1.0.md` | 架构真值（canonical 稳定路径） | v1.2 用户裁定生效 2026-08-12 |
| `fleet-division-v1.1.md` | G+M 双环分工 + 真值/工具链注册表 | v1.3 用户裁定生效 2026-08-12 |
| `specs/zcode-execution-capability-decision.md` | ZCode 评审执行能力裁定 | 用户裁定生效 2026-08-12 |
| `specs/qoder-sse-consumer-design.md` | 实施规格：Pi 侧 Qoder SSE 消费器 | 待 ZCode review |
| `specs/pi-feishu-bridge-design.md` | 实施规格：飞书移动端桥接 | 待 ZCode review |
| `specs/pi-drift-governance-spec.md` | 实施规格：漂移治理（push 授权已签发） | 待 ZCode review |

## 阅读顺序（新 agent 接入）

1. `north-star-v1.2.md`（为什么存在；逻辑版本读 frontmatter）
2. `global-roadmap-v1.1.md`（当前阶段与退出条件；逻辑版本读 frontmatter）
3. `../specs/pi-cognitive-plane-and-self-evolution-v1.0.md`（Pi 自进化质量门）
4. `workspace-collaboration-v2.1.md`（怎么协作）
5. `agent-matrix-architecture-v1.0.md` + `fleet-division-v1.1.md`（谁做什么）
6. `specs/`（怎么施工）

canonical 文件名为了运行时兼容保持稳定。消费者必须读取文档 frontmatter 或 `version-manifest.json`，不得从文件名推断逻辑版本。
