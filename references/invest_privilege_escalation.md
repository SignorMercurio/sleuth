# 权限提升调查指南

## 调查重点

### 1. 确认权限提升方式
```bash
# 查看 sudo 使用记录
grep "sudo" /var/log/auth.log | tail -n 50
grep "COMMAND=" /var/log/secure

# 查看 su 切换记录
grep "su:" /var/log/auth.log
```

### 2. 检查 SUID/SGID 文件
```bash
# 查找 SUID/SGID 文件
find / -perm /6000 -type f -ls 2>/dev/null

# 查找最近修改的 SUID 文件
find / -perm /4000 -type f -mtime -7 -ls 2>/dev/null

# 检查可疑的 SUID 文件
ls -la /tmp /var/tmp | grep -E "rws"
```

### 3. 检查内核漏洞利用
```bash
# 查看内核版本
uname -a
cat /proc/version

# 检查是否加载了可疑的内核模块
lsmod
dmesg | tail -n 50

# 查找可疑的提权工具
find / -type f -name "*exploit*" -o -name "*dirty*" 2>/dev/null | head -n 20
```

### 4. 检查系统配置滥用
```bash
# 检查 sudoers 配置
cat /etc/sudoers
ls -la /etc/sudoers.d/

# 检查 PATH 劫持
echo $PATH
cat /etc/environment

# 检查 LD_PRELOAD
echo $LD_PRELOAD
cat /etc/ld.so.preload
```

### 5. 查看提权后的活动
```bash
# 查看 root 用户最近的命令
cat /root/.bash_history

# 查看 root 进程
ps aux | grep "^root" | grep -v "\["
```

## 云端日志补充

主机本地提权（SUID/内核漏洞/sudo 滥用）靠上面的主机命令；若涉及**云上权限提升**（AK 泄露后创建 RAM 用户、附加策略、改角色权限）——按 `references/cloud_log_queries.md`「AK 泄露 / 云助手滥用」行用 `sls` skill 查 ActionTrail（`CreateUser`/`AttachPolicyToUser`/`AttachPolicyToRole`/`CreateAccessKey` 等敏感 API 的 `sourceIpAddress` 与 `userIdentity`），详见 `references/tech_cloud.md`。

## 关键 IoC
- 使用的提权漏洞或技术
- 提权工具路径和哈希
- 提权前后的用户和权限
- 提权后执行的操作

## ATT&CK 映射
- **T1068** - 利用漏洞提权
- **T1548.001** - Setuid 和 Setgid
- **T1548.003** - Sudo 和 Sudo Caching
- **T1574.006** - LD_PRELOAD
