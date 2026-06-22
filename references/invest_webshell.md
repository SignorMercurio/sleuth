# Web Shell 后门调查指南

## 调查重点（只读检查项）

1. **确认 WebShell 文件**：取文件内容、元数据（`stat`）、哈希。
2. **上传时间与方式**：以文件 mtime/ctime 为锚，用 `-newermt` 时间窗找同期落地的其他文件；在 access.log 里按文件名 / `POST .php` / 上传时间段定位上传请求。
3. **追踪利用漏洞**：access.log 里找上传相关 POST 与利用特征（`eval|system|exec|shell_exec|passthru`）。
4. **使用记录**：查对 WebShell 的访问请求与执行的命令（`cmd=` 等参数）。
5. **关联进程**：查 web 用户（www-data 等）的进程与 web 服务子进程。

## 判读注意事项

- 不要把可疑文件的 `atime` 自动判定为攻击者访问时间；云安全中心/SAS 扫描读取也会刷新访问时间。必须用 Web 访问日志、SAS 进程/网络遥测或 WAF 日志交叉验证。
- 若 nginx/Apache 日志中告警文件 0 命中、而文件 `atime` 与告警时间接近，应明确写成“告警扫描触发/文件存在告警”，不要写成“攻击者在该时间调用 WebShell”。
- WebShell 文件当前存在不等于当前可利用：检查 nginx/PHP 配置（例如 `location ~ \.php$ { return 403; }`、仅放行 `/index.php`）并实际核对访问日志状态码。
- 发现一个 WebShell 时，扩展排查同目录同时间段批量落地的文件、压缩包和数据库探测脚本（常见：`shell*.php`、`s.php`、`mysql.php`、`db_*.php`、`dump*.php`、`rd*.php`、`rde*.php`、`arc.tar.gz`），并检查硬编码数据库凭据与数据导出风险。

## 云端日志补充

主机 `access.log` 常被清除/轮转，WAF 里才是攻击者真实 IP——按 `references/cloud_log_queries.md`「Web 类攻击」行用 `sls` skill 查 WAF（定位上传/利用请求与真实 IP）+ SAS `aegis-log-process` 还原 WebShell 子进程链。

## 关键 IoC
- Web Shell 文件路径和哈希
- 攻击者 IP 地址
- 上传时间和方式
- 利用的漏洞（CVE 编号）
- 执行的命令记录

## ATT&CK 映射
- **T1190** - 利用面向公众的应用程序（初始访问）
- **T1505.003** - Web Shell（持久化）
- **T1059.004** - Unix Shell（执行）
- **T1071.001** - Web 协议（命令与控制）
