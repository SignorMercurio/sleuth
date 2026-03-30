# 进程和文件分析技巧

## 进程关联技巧

### 方法 1: 通过 /proc 目录关联

**检查文件描述符**：
```bash
# 查看进程打开的所有文件描述符
ls -la /proc/<恶意进程PID>/fd

# 可能发现其他进程的 fd
# 例如：/proc/250303/fd/X
# 说明恶意进程与进程 250303 有关联
```

**检查工作目录**：
```bash
# 查看进程的当前工作目录
ls -la /proc/<PID>/cwd

# 从工作目录路径可以推测进程归属
# 例如：/opt/rocketmq -> RocketMQ 进程
```

**检查可执行文件路径**：
```bash
ls -la /proc/<PID>/exe
cat /proc/<PID>/environ | tr '\0' '\n'
```

### 方法 2: 通过 systemd 关联

**查看 systemd 服务信息**：
```bash
# 直接通过 PID 查询服务
systemctl status <PID>

# 会显示：
# - 启动该进程的服务名称
# - 服务的最近日志
# - CGroup 中的其他关联进程
```

**查看详细日志**：
```bash
journalctl -u <service_name>
journalctl -u <service_name> --since "2024-05-27 18:00" --until "2024-05-27 19:00"
```

**CGroup 信息**：systemctl status 输出中的 CGroup 字段会显示该服务相关的所有进程，可以帮助发现关联的子进程。

### 方法 3: 通过网络连接关联

```bash
# 查看特定进程的连接
lsof -i -P -n | grep <PID>
netstat -antp | grep <PID>
ss -antp | grep <PID>

# 根据远程 IP:端口反查其他进程
lsof -i @<远程IP>:<端口>
```

### 方法 4: 通过进程树关联

```bash
# 以树形显示进程关系
pstree -ap | grep <关键进程名>

# 或
ps -ef --forest | grep <关键进程名>

# 向上追溯父进程
ps -o ppid= <PID>
ps aux | grep <父进程PID>
```

---

## 文件时间分析

### Linux 文件三个时间属性

```bash
stat <文件路径>
```

**时间含义**：
- **atime** (访问时间): 读取文件、执行文件时更新
- **mtime** (修改时间): 文件内容被修改时更新（ls -l 显示的时间）
- **ctime** (改动时间): 文件状态改变时更新（内容修改、权限变更等）

### 应用场景

**1. 检测文件是否被篡改**：
```bash
# 查看系统命令的 ctime
stat /usr/bin/ps
stat /usr/sbin/crond

# 如果 ctime 接近告警时间，说明文件可能被替换
```

**2. 基于时间全盘搜索恶意文件**：
```bash
# 查找某个时间范围内修改的所有文件
find / -type f -newermt "2024-05-27 18:00" ! -newermt "2024-05-27 19:00" -ls 2>/dev/null

# 查找最近 7 天修改的文件
find /tmp /var/tmp /dev/shm -type f -mtime -7 -ls 2>/dev/null

# 查找最近 1 小时内被访问的文件
find /var/www -type f -amin -60 -ls 2>/dev/null
```

**3. 时间戳伪造检测**：
攻击者可能修改 atime 和 mtime，但通常无法修改 ctime。如果 mtime 很早但 ctime 很新，说明时间戳被篡改。

### Windows 文件三个时间属性

- **创建时间**：文件首次出现在磁盘上的时间
- **修改时间**：文件内容最后被修改的时间
- **访问时间**：文件状态最后改变的时间

```powershell
Get-Item <文件路径> | Format-List *Time*
```

---

## 基于已知恶意文件时间搜索

**核心思路**：攻击者通常会在短时间内植入多个恶意文件。

**步骤**：
1. 确定已知恶意文件的时间（通常取 mtime 或 ctime）
2. 在该时间前后一个小时内搜索所有新增/修改的文件
3. 人工分析这些文件是否可疑

```bash
# 假设已知恶意文件 /tmp/malware 的时间为 2024-05-27 18:35:07
stat /tmp/malware

# 搜索 18:00 - 19:00 之间修改的所有文件
find / -type f -newermt "2024-05-27 18:00" ! -newermt "2024-05-27 19:00" \
  -ls 2>/dev/null | grep -v "/proc\|/sys" > suspicious_files.txt

# 重点关注的目录
find /tmp /var/tmp /dev/shm /var/www /opt -type f \
  -newermt "2024-05-27 18:00" ! -newermt "2024-05-27 19:00" -ls 2>/dev/null
```
