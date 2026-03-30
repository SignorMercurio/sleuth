# Web Shell 后门调查指南

## 告警特征
- 检测到可疑的脚本文件（.php, .jsp, .asp, .aspx 等）
- Web 目录下出现异常文件
- 检测到 Web Shell 通信行为

## 调查重点

### 1. 确认 Web Shell 文件
```bash
# 查看文件内容
cat /var/www/html/suspicious.php

# 查看文件元数据
stat /var/www/html/suspicious.php
ls -la /var/www/html/suspicious.php

# 计算文件哈希
md5sum /var/www/html/suspicious.php
sha256sum /var/www/html/suspicious.php
```

### 2. 分析上传时间和方式
```bash
# 查找同一时间段创建的其他文件
find /var/www -type f -newermt "2024-01-01 10:00" ! -newermt "2024-01-01 11:00" -ls

# 检查 Web 服务器访问日志（根据告警时间调整）
# Nginx
grep "suspicious.php" /var/log/nginx/access.log
grep "POST.*\.php" /var/log/nginx/access.log | grep "<上传时间段>"

# Apache
grep "suspicious.php" /var/log/apache2/access.log
grep "POST" /var/log/httpd/access_log | grep "<时间段>"
```

### 3. 追踪利用的漏洞
```bash
# 查找文件上传相关的 POST 请求
grep "POST.*upload" /var/log/nginx/access.log | grep "<攻击IP>"

# 查找可能的漏洞利用特征
grep -E "(eval|system|exec|shell_exec|passthru)" /var/log/nginx/access.log
```

### 4. 检查 Web Shell 的使用记录
```bash
# 查找访问 Web Shell 的请求
grep "suspicious.php" /var/log/nginx/access.log | tail -n 100

# 分析执行的命令（从访问日志或 Web Shell 日志中）
grep "cmd=" /var/log/nginx/access.log
```

### 5. 排查相关进程
```bash
# 查找可能由 Web Shell 启动的进程
ps aux | grep www-data
lsof -u www-data

# 查看 Web 服务器进程的子进程
pstree -ap | grep -A 10 "nginx\|apache\|httpd"
```

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
