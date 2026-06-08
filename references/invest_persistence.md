# 持久化后门调查指南

## 调查重点

### 1. 检查定时任务
```bash
# 查看所有用户的 crontab
for user in $(cut -f1 -d: /etc/passwd); do echo "=== $user ==="; crontab -u $user -l 2>/dev/null; done

# 查看系统定时任务
cat /etc/crontab
ls -la /etc/cron.d/
ls -la /etc/cron.daily/
ls -la /etc/cron.hourly/
```

### 2. 检查系统服务
```bash
# 查看所有服务
systemctl list-unit-files --type=service

# 查看最近修改的服务文件
find /etc/systemd/system /usr/lib/systemd/system -type f -mtime -7 -ls

# 查看可疑服务
systemctl status <可疑服务名>
cat /etc/systemd/system/<可疑服务名>.service
```

### 3. 检查启动脚本
```bash
# 检查 rc.local
cat /etc/rc.local

# 检查 init.d
ls -la /etc/init.d/

# 检查 profile 脚本
cat /etc/profile
ls -la /etc/profile.d/
```

### 4. 检查用户配置文件
```bash
# 检查所有用户的 bashrc
find /home /root -name ".bashrc" -exec ls -la {} \;
find /home /root -name ".bashrc" -exec cat {} \;

# 检查 .bash_profile
find /home /root -name ".bash_profile" -exec cat {} \;
```

### 5. 检查 SSH 配置
```bash
# 查看 authorized_keys
find /home /root -name "authorized_keys" -exec ls -la {} \;
find /home /root -name "authorized_keys" -exec cat {} \;

# 查看 SSH 配置
cat /etc/ssh/sshd_config | grep -v "^#"
```

## 云端日志补充

主机侧持久化（cron / systemd / rc.local / profile / SSH key）靠上面的命令；若怀疑**云侧重入通道**（云助手 RunCommand 定期下发、AK 泄露后反复操作）——按 `references/cloud_log_queries.md`「AK 泄露 / 云助手滥用」行用 `sls` skill 查 ActionTrail 的 `RunCommand`/`CreateCommand`，并核对主机 `/var/log/aliyun/assist/` 任务记录，详见 `references/tech_cloud.md`。

## 关键 IoC
- 持久化文件路径
- 定时任务配置
- 系统服务名称
- SSH 公钥

## ATT&CK 映射
- **T1053** - 计划任务/作业
- **T1543** - 创建或修改系统进程
- **T1546** - 事件触发执行
- **T1098** - 账户操纵（如果涉及 SSH 密钥）
