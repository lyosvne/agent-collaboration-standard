# Raw Data Index

本目录保存原始数据的索引指针（不含大文件本体）。

## 审计原始数据位置

| 数据 | 路径 | 大小 |
|------|------|------|
| OSS源码扫描索引 | ../analysis/full-code-index-v2.json | 7.1MB |
| 仓库元数据(star等) | ../analysis/repo-metadata.json | - |
| 技能标签归档 | ../analysis/skills-tagged.json | 1.7MB |
| 深度分类 | ../analysis/deep-classification.json | - |
| 文章URL+元数据 | ../raw/wechat-all-articles.json | 461KB |
| 文章全文 | ../raw/articles-fulltext.json | 260万字符 |
| 文章深度分析 | ../analysis/articles-content-deep.json | - |
| 文章主题聚类 | ../analysis/wechat-themes.json | 595KB |
| OSS仓库clone | ../raw/oss-repos/ (323目录) | ~5GB |
| 最终报告 | ../reports/ultimate-report.md | 31KB |
| 文章深度报告 | ../reports/article-content-deep-analysis.md | 14KB |
| 飞书消息原文 | ../raw/self-messages-all.json | 1MB |
| 妙搭项目数据 | ../raw/miaoda-apps.json | 23KB |

## ECS证据
- 地址: aetherisonline.xyz
- SSH key: C:\tmp\aetheris-ecs.pem
- 关键发现: hermes-sidecar PID 419015零流量, backend重启60次, ARK 401

## Aetheris自有代码
- 主仓库: C:\Users\Admin\Documents\trae_projects\Aetheris\
- backend/src/hermes/ (agent runtime)
- backend/src/model-router/ (5 providers)
- backend/src/feishu/ (飞书集成)
- backend/src/matters/ (事项引擎)
- backend/src/knowledge/ (知识图谱+向量)
