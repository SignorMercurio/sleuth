# 进程和文件分析技巧

## 进程关联（非显然的 pivot）

- **`/proc/<PID>/` 反查归属**：`cwd` 推测进程所属业务（如 `/opt/rocketmq`→RocketMQ），`exe` 取真实可执行路径，`environ` 看启动环境；某进程 fd 指向另一进程 → 两者关联。
- **systemd 关联**：`systemctl status <PID>` 不止给服务名，**CGroup 字段会列出该服务的所有兄弟/子进程**，是发现关联进程的捷径；再 `journalctl -u <service>` 限时间窗看日志。
- **网络/进程树**：按远程 IP:端口反查进程，按父进程链向上追溯到拉起者。

## 文件时间分析（判读规则）

- **时间戳篡改判读**：攻击者通常能改 atime/mtime，**但难改 ctime**。若 `mtime` 很早而 `ctime` 很新 → 时间戳大概率被篡改，别采信 mtime。
- **命令是否被替换**：看系统命令（如 `/usr/bin/ps`）的 `ctime` 是否接近告警时间。
- **以已知恶意文件时间为锚扩展搜索**：取已确认恶意文件的 mtime 或 ctime，用 `find -newermt` 时间窗搜前后约 1 小时内新增/修改的文件，重点 `/tmp /var/tmp /dev/shm /var/www /opt`，再人工研判（命中即恶意是误判，需交叉）。

> Windows 取文件时间：`Get-Item <文件> | Format-List *Time*`。
