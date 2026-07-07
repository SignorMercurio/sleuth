# 挖矿木马调查指南

## 调查重点（只读检查项）

1. **确认挖矿进程**：定位高 CPU 进程，取其 `cmdline`、`/proc/<PID>/exe` 真实路径与哈希。
2. **网络连接**：查该进程外连，识别矿池地址:端口。
3. **追溯入口与持久化**：看父进程确认由 cron / Web / 登录拉起。挖矿常用 **cron 定时重拉** 和 **`/tmp /var/tmp /dev/shm` 下的 `.sh` 下载脚本**，重点核对这两处；完整持久化排查见 `references/invest_persistence.md`。
4. **按时间扩展**：以已知恶意文件 mtime/ctime 为锚搜同窗口落地文件，重点上述临时目录。

## 云端日志补充

主机进程可能被隐藏/命令替换，云端遥测可旁证——按 `references/cloud_log_queries.md`「恶意进程」行用 `sls` skill 查 SAS（`aegis-log-process` 启动链/父进程、`aegis-log-network` 矿池连接）。

## 关键 IoC
- 挖矿程序路径和哈希
- 矿池地址和端口
- 挖矿进程名
- 下载源 URL
- 持久化机制配置文件路径

## ATT&CK 映射
- **T1496** - 资源劫持（影响）
- **T1053.003** - Cron（持久化）
- **T1543.002** - Systemd 服务（持久化）
- **T1071.001** - Web 协议（命令与控制，如果有）
