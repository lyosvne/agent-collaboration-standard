# Round5 汇总 — Pi ECS 部署方案评审

> 三方判决：A 条件通过（3 P0）/ B 条件通过（3 硬门槛）/ C PASS（3 条件）
> 核心共振：飞书 App 身份冲突（三方一致头号问题）

## 三方共振 P0（必修）

### ① 飞书 App 身份冲突（A/B 都 P0）
- 同一 FEISHU_APP_ID 两个 backend 同时订阅事件回调 → 飞书只推给最后注册的，kill switch"Pi 停"指令失效
- **二选一**：(a) Pi 用独立飞书应用（新建 app_id）；(b) Pi"只出不进"（只推日报，kill switch 走 SSH + .kill-flag 轮询，不依赖飞书反向通道）
- A 建议最紧急——上线前必须裁定

### ② 独立 uid + HOME（B P0）
- 同 uid 跑 → 共享 `~/.config/lark-cli/` token 缓存（并发覆盖）+ `~/.npm` 缓存冲突 + journal 难区分
- **必须**：新建系统用户 `User=pi-growth` + 独立 HOME + `SyslogIdentifier=pi-self-growth`

### ③ HERMES_RUNTIME_MODE=skip 代码验证（B P0）
- 代码里若无此分支，sidecar 调用照旧走 fetch(8642) → 连接拒绝 → 可能启动即崩
- **必须**：部署前 grep 全仓 HERMES_RUNTIME_MODE，无匹配则补短路逻辑

## A 独家
- QuotaTracker 双算：两 backend 内存各自计额度，共享 provider 池会双向踩爆 → Pi 配额砍半或迁 Redis
- refactor env diff：部署前 diff master..refactor 的 env 字段兼容性
- pi 用户 systemctl 权限：限制无 sudo，防 Pi 触发 reload 制造 kill-watcher 空窗

## C 独家（3 条件）
- ① qoder-bridge 复用方式钉死：vendor 副本或版本锁，禁止裸路径引用
- ② 预定义切换判据：Pi 闭环 N 任务 + 漂移指标不劣于现行 → 才替代旧系统，否则双系统长期并存变漂移源
- ③ Pi DB 只作私有工作数据，matter/decision/knowledge 须写回 Aetheris，**禁止第二真值层**
- 提醒：kill-watcher 自动拉活须让位于 M5 紧急制动（制动标志最高优先级）

## 修订行动项（round6 前补）
| # | 行动 | 来源 |
|---|---|---|
| 1 | 飞书选边：Pi 只出不进（推荐，最快）或新建独立 app | A/B 共振① |
| 2 | 新建 User=pi-growth 系统用户 + 独立 HOME + SyslogIdentifier | B ② |
| 3 | grep HERMES_RUNTIME_MODE，无则补 skip 短路 | B ③ |
| 4 | Pi QuotaTracker 配额砍半（防双向踩爆） | A |
| 5 | qoder-bridge vendor 副本或版本锁 | C ① |
| 6 | 预定义 Pi→旧系统切换判据 | C ② |
| 7 | Pi DB 定位私有，matter/knowledge 写回 Aetheris | C ③ |
| 8 | kill-watcher 让位 M5 制动标志 | C 提醒 |
