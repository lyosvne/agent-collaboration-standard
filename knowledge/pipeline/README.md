# Daily Knowledge Pipeline

每日自动抓取飞书自聊中的微信文章，分析OSS项目，归档到Obsidian知识库。

## 架构

```
飞书自聊 → lark-cli/OpenAPI → 微信URL → Playwright全文抓取
                                          ↓
                                    GitHub URL提取
                                          ↓
                                    git clone新仓库
                                          ↓
                                    代码级扫描+star数据
                                          ↓
                                    分析+分类+评分
                                          ↓
                              Obsidian知识库归档 (Knowledge/wiki/)
```

## 文件说明

| 文件 | 用途 |
|------|------|
| `config.json` | 配置：飞书chat_id、路径、分析参数 |
| `daily-pipeline.cjs` | 主pipeline脚本，7个步骤 |
| `fetch-daily-articles.cjs` | Playwright微信文章全文抓取 |
| `clone-daily-repos.cjs` | 新仓库clone |
| `run-daily.ps1` | Windows Task Scheduler入口 |
| `register-task.ps1` | 注册Windows定时任务 |
| `log-YYYY-MM-DD.txt` | 每日运行日志 |

## 一次性配置

### 1. 配置飞书访问（两种方式二选一）

**方式A: lark-cli（推荐）**
- 安装lark-cli到Windows，在`config.json`中设置`lark_cli_path`为完整路径
- 完成`lark-cli auth login`

**方式B: 飞书开放平台API**
- 在[飞书开放平台](https://open.feishu.cn/)创建自建应用
- 赋予`im:message:readonly`权限
- 在`config.json`中设置`app_id`和`app_secret`
- 注意：需要额外实现token获取逻辑

### 2. 注册定时任务

以管理员身份运行PowerShell：
```powershell
cd C:\Users\Admin\Documents\Codex\knowledge-audit-2026-07\daily
.\register-task.ps1
```

任务将在每天9:00 AM和用户登录时触发，自动检测网络后运行。

### 3. 手动运行测试

```powershell
cd C:\Users\Admin\Documents\Codex\knowledge-audit-2026-07
node daily\daily-pipeline.cjs
```

## 手动触发（无lark-cli时）

如果暂时没有配置lark-cli，可以手动将新消息JSON放到：
`raw/daily-messages-YYYY-MM-DD.json`

消息格式参考`raw/self-messages-all.json`的结构。

## 输出

- 每日摘要: `Knowledge/wiki/insights/daily-YYYY-MM-DD.md`
- 新文章全文: `raw/daily-articles-fulltext-YYYY-MM-DD.json`
- 新仓库代码: `repos/`
- 更新的wiki页面和index
