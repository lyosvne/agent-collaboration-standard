---
schema: governance-decision-v1
decision_id: zcode-execution-capability-20260812
status: effective
approved_by: user
approved_at: 2026-08-12
scope: local-and-repository-execution
---

# ZCode 执行能力裁定

## 裁定

ZCode 从“非终端评审角色”升级为“评审优先的受派执行者”。

ZCode 可以：

- 使用本地 shell、文件读写和进程执行；
- 安装项目级依赖；
- 运行测试、Lint 和构建；
- 在独立 clone 和自身分支中修改代码；
- commit、推送自身分支和创建 PR；
- 使用用户此前单独批准的公共 Lark、Mira、Ark 和健康检查入口。

公共 CLI 权限继续以本机公共基础设施注册表为唯一真源，本裁定不增加新 CLI 或新远程权限。

## 不授予

本裁定不授予：

- 中央协调权；
- 直接推送或合并 `master`；
- SSH；
- 部署和服务重启；
- 生产环境读取或写入；
- secrets；
- 数据库迁移；
- 对自身实现作唯一最终评审或批准。

上述生产和敏感能力不能通过本任务临时开启。如未来需要，必须另立治理裁定并由其他执行者承担。

## 评审隔离

- ZCode 启动时必须明确使用 `review` 或 `implementation` 模式；
- implementation 模式的结果必须移交独立终审；
- review 模式必须声明目标提交；
- ZCode authored change 不得由 ZCode 输出最终批准；
- 最终集成仍由 Trae 或用户授权的集成者执行。

## 责任关系

- Pi 继续作为中央协调者；
- Trae 继续负责集成、主分支推进和产品测试；
- Qoder 继续负责设计与前端优先任务；
- Kimi 继续负责文件、数据和飞书协同优先任务；
- ZCode 的新增执行能力不改变以上角色优先级。
