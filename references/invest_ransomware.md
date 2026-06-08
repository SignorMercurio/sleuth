# 勒索软件调查指南

## 调查重点

### 1. 确认勒索软件进程
```bash
# 查找可疑进程
ps aux | grep -v "^\["
top -b -n 1

# 查看进程详情
ps -ef --forest
lsof -p <PID>
```

### 2. 分析加密行为
```bash
# 查找最近修改的文件
find / -type f -mmin -60 2>/dev/null | head -n 100

# 查找勒索信息文件
find / -type f -name "*README*" -o -name "*DECRYPT*" -o -name "*RANSOM*" 2>/dev/null

# 查看勒索信息内容
cat <勒索信息文件路径>
```

### 3. 追溯入侵源头
```bash
# 查看进程的启动时间和父进程
ps -eo pid,lstart,cmd | grep <勒索软件进程名>

# 检查是如何启动的
pstree -ap <PID>

# 检查邮件附件、下载目录
ls -lat ~/Downloads
ls -lat /tmp
```

### 4. 检查网络通信
```bash
# 查看勒索软件的网络连接
lsof -i -P -n | grep <PID>
netstat -antup | grep <PID>
```

### 5. 确定影响范围
```bash
# 统计被加密的文件数量
find / -type f -name "*.encrypted" 2>/dev/null | wc -l

# 查看受影响的目录
find / -type f -name "*.encrypted" 2>/dev/null | xargs dirname | sort -u
```

## 云端日志补充

主机被加密后本地证据可能不可靠——按 `references/cloud_log_queries.md`「恶意进程」「C2 外联 / 数据外传」行用 `sls` skill 查 SAS（`aegis-log-process` 还原加密进程的启动链/父进程、`aegis-log-network` 查 C2 与密钥/勒索服务器外联）；入口若疑似暴破或异常登录再配 `aegis-log-login`。

## 关键 IoC
- 勒索软件文件路径和哈希
- C2 服务器地址
- 加密文件扩展名
- 勒索信息内容
- 比特币钱包地址

## ATT&CK 映射
- **T1486** - 数据加密以造成影响
- **T1490** - 抑制恢复
- **T1529** - 系统关闭/重启（可能）
