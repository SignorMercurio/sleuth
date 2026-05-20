# 挖矿木马调查指南

## 调查重点

### 1. 确认挖矿进程
```bash
# 查看高 CPU 进程
top -b -n 1 | head -n 20
ps aux --sort=-%cpu | head -n 10

# 查看进程详细信息
ps -ef | grep <挖矿进程名>
cat /proc/<PID>/cmdline | tr '\0' ' '
ls -la /proc/<PID>/exe
```

### 2. 分析挖矿程序
```bash
# 查找挖矿程序文件
ls -la /proc/<PID>/exe
readlink /proc/<PID>/exe

# 计算文件哈希
md5sum <挖矿程序路径>
sha256sum <挖矿程序路径>

# 查看文件创建时间
stat <挖矿程序路径>
```

### 3. 检查网络连接
```bash
# 查看挖矿进程的网络连接
lsof -i -P -n | grep <PID>
netstat -antup | grep <PID>
ss -antp | grep <PID>
```

### 4. 追溯入侵源头与持久化
```bash
# 查看挖矿进程的父进程，确认是 cron / Web / 登录后拉起
ps -ef --forest | grep <挖矿进程名>
pstree -ap <PID>
```
持久化机制（cron / systemd / rc.local / profile / SSH key）完整排查见 `references/invest_persistence.md`；挖矿常用 cron 定时重拉和 `/tmp /var/tmp /dev/shm` 下的 `.sh` 下载脚本，重点核对这两处。

### 5. 搜索相关恶意文件
```bash
# 按时间查找可疑文件
find / -type f -newermt "<入侵时间>" ! -newermt "<当前时间>" 2>/dev/null | grep -E "(tmp|var/tmp|dev/shm)"

# 查找可疑的下载脚本
find / -type f -name "*.sh" -o -name "*.py" | xargs grep -l "curl\|wget" 2>/dev/null
```

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
