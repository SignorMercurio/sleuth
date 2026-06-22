# SQL 注入调查指南

## 调查重点（只读检查项）

1. **确认攻击源/目标**：在 access.log 里按注入特征筛 **`union.*select|' or |' and |--|#|/*`**（按目标数据库方言调整），提取攻击 IP 与被打的页面 URL。
2. **数据库日志**：查 MySQL 慢查询/错误日志、PostgreSQL 日志中的异常查询。
3. **评估影响**：注入是否带 **`into outfile|into dumpfile`**（落地写文件/导数据的强信号）；同时查 web 目录在攻击时间窗是否有新文件（写 WebShell）。
4. **代码定位**：在源码里找拼接型查询（如 `SELECT ... $_GET/$_POST`）。

## 云端日志补充

主机 `access.log` 常被清除/轮转，WAF 里才是攻击者真实 IP——按 `references/cloud_log_queries.md`「Web 类攻击」行用 `sls` skill 查 WAF（定位注入请求、注入点 URL 与真实 IP）；数据库审计日志若投递到 SLS 可 direct 模式查异常查询。

## 关键 IoC
- 攻击源 IP
- 注入点 URL
- 注入 payload
- 受影响的数据库和表

## ATT&CK 映射
- **T1190** - 利用面向公众的应用程序
- **T1505.003** - Web Shell（如果植入了 Web Shell）
