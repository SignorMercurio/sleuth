# 数据外传调查指南

## 调查重点（只读检查项）

1. **确认外传通道**：看 ESTABLISHED 外连。**评估流量必须用一次性快照——`ss -tinp`（每连接收发字节）、`cat /proc/net/dev`（网卡累计）、`netstat -s`；切勿用 `iftop` / `nethogs` / `vnstat` 等需交互终端的工具，远程执行会挂起。**
2. **外传目标**：提取外部 IP:端口，识别云存储外联（`amazonaws|aliyun|qcloud|s3` 等），归属用联网检索查。
3. **追踪进程**：按外部 IP 反查发起进程及其 `cmdline`。
4. **外传数据与工具**：查临时目录近 1 天的打包文件（`tar/zip/7z`）、近期被读的敏感文件（database/backup/sql）；读 `.bash_history` 找 `scp` / `rsync` / `curl -T` / `wget --post` 等外传命令（读文件，不用交互式 history）。

## 云端日志补充

按 `references/cloud_log_queries.md`「C2 外联 / 数据外传」行用 `sls` skill 查 SAS `aegis-log-network`（外联目标与发起进程，DNS 隧道配 `aegis-log-dns-query`）；外传走 Web 通道（大响应体、下载/导出接口）再查 WAF。

## 关键 IoC
- 外传目标 IP/域名
- 外传工具和方法
- 外传的数据路径
- 外传时间和数据量

## ATT&CK 映射
- **T1041** - 通过 C2 通道外传
- **T1048** - 通过备用协议外传
- **T1567.002** - 外传到云存储
- **T1020** - 自动化外传
