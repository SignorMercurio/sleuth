# 暴力破解调查指南

## 调查重点

### 1. 确认攻击源
```bash
# 查看失败登录记录
lastb | head -n 50
lastb | grep "<攻击IP>"

# 统计失败登录次数
lastb | awk '{print $3}' | sort | uniq -c | sort -rn | head -n 20

# 查看认证日志
grep "Failed password" /var/log/auth.log | tail -n 100
grep "authentication failure" /var/log/secure | tail -n 100
```

### 2. 分析攻击模式
```bash
# 按时间段统计失败登录
grep "Failed password" /var/log/auth.log | grep "<日期>" | wc -l

# 查看尝试的用户名
grep "Failed password" /var/log/auth.log | awk '{print $(NF-5)}' | sort | uniq -c | sort -rn

# 查看攻击的目标用户
grep "Failed password for" /var/log/auth.log | grep "<攻击IP>"
```

### 3. 检查是否成功登录
```bash
# 查看成功登录记录
last | grep "<攻击IP>"
grep "Accepted password" /var/log/auth.log | grep "<攻击IP>"

# 如果成功登录，查看登录后的活动
grep "<攻击IP>" /var/log/auth.log | grep -A 20 "Accepted"
```

### 4. 检查防护措施
```bash
# 查看 fail2ban 状态
fail2ban-client status
fail2ban-client status sshd

# 查看防火墙规则
iptables -L -n -v | grep "<攻击IP>"
```

## 云端日志补充

主机 `lastb`/`auth.log` 可能被清除或不含 RDP/数据库登录——按 `references/cloud_log_queries.md`「异常登录 / 暴力破解」行用 `sls` skill 查 SAS（`aegis-log-login` 找暴破源 IP 和「失败→成功」转折点、`sas-security-log` 查告警）。

## 关键 IoC
- 攻击源 IP 地址
- 攻击时间段
- 尝试的用户名列表
- 是否成功登录

## ATT&CK 映射
- **T1110.001** - 密码猜测（凭证访问）
- **T1110.003** - 密码喷洒（凭证访问）
- **T1021.004** - SSH（横向移动，如果成功）
