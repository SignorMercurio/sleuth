# 数据外传调查指南

## 调查重点

### 1. 确认外传通道
```bash
# 查看当前网络连接
netstat -antup | grep ESTABLISHED
ss -antp | grep ESTABLISHED

# 查看大流量连接
iftop -n -P
nethogs

# 统计流量
vnstat -d
```

### 2. 分析外传目标
```bash
# 提取外部 IP 和端口
netstat -antup | awk '{print $5}' | grep -v "127.0.0.1\|0.0.0.0" | sort -u

# 查询目标 IP（使用联网检索工具）

# 检查是否连接到云存储服务
netstat -antup | grep -E "amazonaws|aliyun|qcloud|s3"
```

### 3. 追踪外传进程
```bash
# 查看建立外部连接的进程
lsof -i -P -n | grep ESTABLISHED
lsof -i -P -n | grep "<外部IP>"

# 查看进程详情
ps aux | grep <PID>
cat /proc/<PID>/cmdline | tr '\0' ' '
```

### 4. 检查外传的数据
```bash
# 查找打包的数据文件
find /tmp /var/tmp /dev/shm -type f -name "*.tar*" -o -name "*.zip" -o -name "*.7z" -mtime -1

# 查看最近访问的文件
find / -type f -atime -1 2>/dev/null | grep -E "(database|backup|data|sql)"

# 检查命令历史中的数据收集命令
history | grep -E "tar|zip|7z|scp|rsync|curl.*upload"
```

### 5. 检查外传工具
```bash
# 查找文件传输工具的使用
ps aux | grep -E "scp|rsync|curl|wget|nc"

# 检查命令历史
cat ~/.bash_history | grep -E "scp|rsync|curl.*-T|wget.*--post"
```

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
