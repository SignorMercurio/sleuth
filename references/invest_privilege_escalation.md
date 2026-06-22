# 权限提升调查指南

## 调查重点（只读检查项）

1. **本地提权方式**：查 sudo/su 使用记录（auth.log / secure 的 `COMMAND=`）。
2. **SUID/SGID**：列 `find / -perm /6000`；重点 **`find / -perm /4000 -mtime -7`** 找近期被植入/改动的 SUID，及 `/tmp /var/tmp` 下带 `rws` 的可疑文件。
3. **内核/配置滥用**：核对内核版本与可疑模块；**配置型提权重点查 `/etc/sudoers` + `/etc/sudoers.d/`、`LD_PRELOAD` / `/etc/ld.so.preload`、PATH 劫持**。
4. **提权后活动**：看 root 命令历史与非内核 root 进程。

## 云端日志补充

主机本地提权（SUID / 内核漏洞 / sudo 滥用）靠上面的主机命令；若涉及**云上权限提升**（AK 泄露后创建 RAM 用户、附加策略、改角色权限）——按 `references/cloud_log_queries.md`「AK 泄露 / 云助手滥用」行用 `sls` skill 查 ActionTrail（`CreateUser` / `AttachPolicyToUser` / `AttachPolicyToRole` / `CreateAccessKey` 等敏感 API 的 `sourceIpAddress` 与 `userIdentity`），详见 `references/tech_cloud.md`。

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
