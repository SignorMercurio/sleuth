# Web Shell 后门调查指南

## 调查重点（只读检查项）

1. **确认 WebShell 文件**：取文件内容、元数据（`stat`）、哈希。
2. **上传时间与方式**：按 `references/tech_process_file.md` 同时检查 mtime/ctime 候选，结合访问日志定位上传请求；时间窗校准按 `references/tech_log_analysis.md`，不直接把告警时间或 ctime 当成上传时间。
3. **追踪利用漏洞**：access.log 里找上传相关 POST 与利用特征（`eval|system|exec|shell_exec|passthru`）。
4. **使用记录**：查对 WebShell 的访问请求与执行的命令（`cmd=` 等参数）。
5. **关联进程**：查 web 用户（www-data 等）的进程与 web 服务子进程。

## 判读注意事项

- `atime`、文件存在与调用、扫描触发解释的判读边界统一见 `references/verification_checklist.md`「时间」「存在 ≠ 利用 / 得手」「云端与阴性判断」，本文不重述。
- 发现一个 WebShell 时，扩展排查同目录同时间段批量落地的文件、压缩包和数据库探测脚本（常见：`shell*.php`、`s.php`、`mysql.php`、`db_*.php`、`dump*.php`、`rd*.php`、`rde*.php`、`arc.tar.gz`），并检查硬编码数据库凭据与数据导出风险。

## 云端日志补充

主机 `access.log` 常被清除或轮转，WAF 更适合确认入口来源；按 `references/cloud_log_queries.md`「WebShell / SQL 注入 / RCE / 文件上传」定位上传/利用请求，用 SAS 遥测还原 WebShell 子进程链。

## ATT&CK 映射
- **T1190** - 利用面向公众的应用程序（初始访问）
- **T1505.003** - Web Shell（持久化）
- **T1059.004** - Unix Shell（执行）
- **T1071.001** - Web 协议（命令与控制）
