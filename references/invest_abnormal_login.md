# 异常登录调查指南

## 调查重点

### 1. 确认登录详情
```bash
# 查看登录记录
last | head -n 50
w
who

# 查看特定用户的登录记录
last <用户名>

# 查看认证日志
grep "Accepted" /var/log/auth.log | tail -n 50
```

### 2. 分析登录来源
```bash
# 查看来源 IP
last | grep "<用户名>"
grep "Accepted.*<用户名>" /var/log/auth.log

# 查询 IP 归属地（使用 WebSearch）

# 检查是否为代理或 VPN
```

### 3. 检查登录方式
```bash
# 确认是密码登录还是密钥登录
grep "Accepted password.*<用户名>" /var/log/auth.log
grep "Accepted publickey.*<用户名>" /var/log/auth.log

# 如果是密钥登录，检查授权密钥
cat /home/<用户名>/.ssh/authorized_keys
```

### 4. 检查登录后的活动
```bash
# 查看用户的命令历史
cat /home/<用户名>/.bash_history

# 查看用户的进程
ps aux | grep "^<用户名>"

# 查看用户的网络连接
lsof -u <用户名> -i -P -n
```

### 5. 检查账户变更
```bash
# 检查是否有新增用户
grep "useradd\|adduser" /var/log/auth.log

# 查看最近创建的用户
awk -F: '$3 >= 1000 {print $1,$3}' /etc/passwd

# 检查密码变更
grep "password changed" /var/log/auth.log
```

## 云端日志补充

主机 `auth.log`/`secure` 可能被清除或不含 RDP/数据库登录——按 `references/cloud_log_queries.md`「异常登录 / 暴力破解」行用 `sls` skill 查 SAS（`aegis-log-login` 原始登录遥测、`sas-security-log` 异常登录告警，注意区分两者）。

## 关键 IoC
- 登录用户名
- 登录来源 IP 和地理位置
- 登录时间
- 登录方式（密码/密钥）
- 登录后执行的操作

## ATT&CK 映射
- **T1078** - 有效账户（初始访问）
- **T1021.004** - SSH（横向移动）
- **T1552.004** - 私钥（凭证访问，如果涉及）
