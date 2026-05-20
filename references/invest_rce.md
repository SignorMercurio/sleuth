# 远程代码执行 (RCE) 调查指南

## 调查重点

### 1. 确认漏洞利用
```bash
# 查看 Web 访问日志中的命令注入尝试
grep -E "system\(|exec\(|passthru\(|shell_exec\(|`|%00" /var/log/nginx/access.log | tail -n 50

# 查看可疑的 POST 请求
grep "POST" /var/log/nginx/access.log | grep "<攻击IP>"
```

### 2. 分析执行的命令
```bash
# 查看 Web 服务器进程的子进程
pstree -ap | grep -A 10 "nginx\|apache\|httpd"

# 查看 www-data 用户的进程
ps aux | grep www-data
```

### 3. 检查命令执行痕迹
```bash
# 查看 Web 用户的命令历史（如果有）
cat /var/www/.bash_history

# 查看系统日志中的进程启动记录
journalctl -u nginx -n 100
```

### 4. 追溯漏洞代码
```bash
# 查找可能存在 RCE 的代码
grep -r "system\|exec\|passthru\|shell_exec\|eval" /var/www --include="*.php" --include="*.jsp"
```

### 5. 检查后续行为
```bash
# 查看是否下载了其他恶意文件
find /tmp /var/tmp -type f -newermt "<攻击时间>" -ls

# 查看是否建立了反向连接
lsof -i -P -n | grep www-data
```

## 云端日志补充

按 `references/cloud_log_queries.md`「Web 类攻击」+「恶意进程」行用 `sls` skill 交叉验证：WAF 定位利用请求与真实 IP，SAS `aegis-log-process` 还原命令执行链/父进程（web 进程名如 `java`/`php-fpm`/`w3wp.exe`）、`aegis-log-network` 查后续外联。

## 关键 IoC
- 攻击源 IP
- 漏洞利用 URL 和 payload
- 执行的命令
- 下载的恶意文件

## ATT&CK 映射
- **T1190** - 利用面向公众的应用程序
- **T1059** - 命令和脚本解释器
- **T1105** - 远程文件复制（如果有下载行为）
