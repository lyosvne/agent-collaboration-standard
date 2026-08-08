# Analysis artifacts

本目录保存历史代码、知识和仓库分析产物，不是当前角色或运行真源。

`full-code-index-v2.json` 曾收录外部源码中的 GitHub service token 形态和 private-key header。当前 HEAD 已完成模式化脱敏：

- 不保留原值；
- 不用这些字符串执行认证；
- Git 历史保持不改写；
- 后续生成索引时必须先脱敏；
- 当前治理门禁会阻止新的凭据形态进入跟踪文件。

分析结论进入活动治理前，必须回到 `governance/`、`specs/` 和 `version-manifest.json` 核验。
