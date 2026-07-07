# 反弹 Shell 调查指南

## 调查重点（只读检查项）

1. **确认反弹进程**：找与外部 IP 建连的 shell 进程（`bash/sh/zsh`），取其 `cmdline` 与打开的 fd。
2. **连接信息**：提取远程 IP:端口，归属地用联网检索查。
3. **追溯触发来源**：看进程树与父进程；**父进程若是 Web 服务器（nginx/php/tomcat 等），转去查 access.log 里对应攻击 IP**——反弹常由 Web RCE 触发。
4. **命令历史与脚本**：读各用户 `.bash_history`（读文件，不用交互式 history 内建）；搜临时目录与全盘的反弹特征 **`/dev/tcp`、`bash -i`、`sh -i`、`nc -e`**。

## 云端日志补充

按 `references/cloud_log_queries.md`「反弹 Shell / C2 外联」行用 `sls` skill 查 SAS（`aegis-log-network` 反弹连接与发起进程、`aegis-log-process` 还原父进程；域名回连配 `aegis-log-dns-query`）。

## 关键 IoC
- 反弹 Shell 目标 IP 和端口
- 反弹 Shell 命令或脚本路径
- 触发反弹 Shell 的漏洞或途径
- 相关进程 PID 和命令行

## ATT&CK 映射
- **T1071** - 应用层协议（命令与控制）
- **T1059.004** - Unix Shell（执行）
- **T1571** - 非标准端口（命令与控制）
