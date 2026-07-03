# 持久化后门调查指南

告警本身是持久化类（恶意 cron / 服务 / SSH key 植入）时用本指南深挖。SKILL.md 步骤 6 的六维扫查已覆盖 cron 全用户、systemd unit + rc.local + init.d、账户与 `authorized_keys`、`ld.so.preload`，命中项的通用下一步见 `references/recon_residual.md`；本文只补充深挖点与判读。

## 调查重点（只读检查项）

1. **定时任务全覆盖**：逐用户 `crontab -l` 之外，核对 `/etc/crontab`、`/etc/cron.d/`、`cron.{hourly,daily,weekly,monthly}/`，以及易漏的 **systemd timer**（`systemctl list-timers --all`）和 **at 任务**（`at -l`、`ls /var/spool/at* /var/spool/cron`）——挖矿与回连脚本最常藏在分钟级重拉里。
2. **服务与启动链**：`systemctl list-unit-files --type=service` 配 `find /etc/systemd/system /usr/lib/systemd/system -type f -mtime -7 -ls` 找近期落地 unit；读可疑 unit 的 `ExecStart`/`User=`/`WorkingDirectory=`，用 `journalctl -u <unit>` 核实实际启动记录。
3. **登录触发点**：`/etc/profile`、`/etc/profile.d/`、各用户 `~/.bashrc` / `~/.bash_profile`（先 `find /home /root -maxdepth 2 -name '.bash*' -newermt <窗口>` 筛近期改动再读内容），以及 `/etc/rc.local`、`/etc/init.d/`。
4. **SSH 通道**：各用户 `authorized_keys` 的公钥条目与文件时间（配 `last` 交叉该窗口的登录）；`sshd_config` 有效配置（`grep -v '^#'`），关注 `AuthorizedKeysFile`、`PermitRootLogin` 被改。

## 判读注意事项

- 运维自动化（备份、监控 agent、证书续期）也长这样：指向 `/opt`、`/usr/local` 且落地时间久远的 cron/unit 先与客户核对，不要按「存在即恶意」写。
- 恶意持久化的强信号是**组合**：落地时间在攻击窗口内 + `ExecStart`/命令指向 `/tmp`、`/dev/shm`、`/home` 下近期文件 + 含外网下载（`curl|wget`）或 base64 编码命令体。单一 mtime 命中不足以定性。
- `@reboot` 条目与分钟级 cron 按可疑优先深挖。
- 公钥植入的定性要有使用证据（`last` / `aegis-log-login` 命中该 key 窗口的登录），否则写「发现植入，未观察到使用」。

## 云端日志补充

主机侧持久化（cron / systemd / profile / SSH key）靠上面的命令；若怀疑**云侧重入通道**（云助手 RunCommand 定期下发、AK 泄露后反复操作）——按 `references/cloud_log_queries.md`「AK 泄露 / 云助手滥用」行用 `sls` skill 查 ActionTrail 的 `RunCommand`/`CreateCommand`，并核对主机 `/var/log/aliyun/assist/` 任务记录，详见 `references/tech_cloud.md`。

## 关键 IoC
- 持久化载体路径（cron 条目 / unit 或 timer 文件 / profile 注入行 / 公钥）及落地时间
- 被拉起的 payload 路径与哈希
- 下载源 URL / 回连地址
- 植入的 SSH 公钥指纹

## ATT&CK 映射
- **T1053.003** - Cron（执行/持久化）
- **T1053.006** - Systemd 定时器（持久化，如涉及）
- **T1053.002** - At（持久化，如涉及）
- **T1543.002** - Systemd 服务（持久化）
- **T1546.004** - Unix Shell 配置修改（profile/bashrc）
- **T1098.004** - SSH Authorized Keys（账户操纵）
