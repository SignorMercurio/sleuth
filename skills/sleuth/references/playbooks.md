# 调查指南与实战技巧（步骤 3）

按告警类型或异常现象读对应小节；模式二按用户描述推断最可能的类型。命令只是参考，按实际线索调整参数。判读边界统一见 `references/verification_checklist.md`，云侧证据源按 `references/cloud_log_queries.md` 路由表选择。

## 实战技巧路由

| 场景 | 参考 |
|---|---|
| 找不到 Web 日志、只有应用日志、正向证据链断裂、WAF 来源归因 | `references/tech_log_analysis.md` |
| AK/STS 滥用、云助手、ActionTrail 异常调用，或进程父链含 `aliyun-service` / `AliyunService.exe` | `references/tech_cloud.md`（审计看「ActionTrail 审计要点」「AK 泄露利用方式总结」） |
| 需要阿里云云侧证据（WAF / SAS / 云防火墙 / ActionTrail / 云资源配置） | `references/cloud_log_queries.md` |
| SAS 主机遥测覆盖时间窗；`w3wp.exe` 子进程；父链含 `sshd` 或要确认 SSH 来源 IP；DNSLog / OOB 域名请求 | `references/sas_sls_host_telemetry.md` |
| 进程关联、文件时间分析 | `references/tech_process_file.md` |
| 进程隐藏、命令替换、Python 标准库注入 | `references/tech_attack_countermeasures.md` |
| 威胁情报 | 用运行环境的联网检索查哈希、IP、域名（如 VirusTotal 的 Relations / Community、微步）；平台无检出时，用主机上看似无关的目录名或报错原文检索社区分析与 GitHub Issue |

## Web Shell

1. **确认文件**：取内容、`stat` 元数据与哈希。
2. **上传时间与方式**：按 `references/tech_process_file.md` 同时检查 mtime/ctime 候选，结合访问日志定位上传请求；时间窗校准按 `references/tech_log_analysis.md`，不把告警时间或 ctime 当成上传时间。
3. **利用漏洞**：access.log 里找上传相关 POST 与利用特征（`eval|system|exec|shell_exec|passthru`）。
4. **使用记录**：对 WebShell 的访问请求与执行的命令（`cmd=` 等参数）。
5. **关联进程**：web 用户（www-data 等）的进程与 web 服务子进程。

发现一个 WebShell 时，扩展排查同目录同时段批量落地的文件、压缩包和数据库探测脚本（常见 `shell*.php`、`s.php`、`mysql.php`、`db_*.php`、`dump*.php`、`rd*.php`、`rde*.php`、`arc.tar.gz`），并检查硬编码数据库凭据与数据导出风险。

**ASP.NET / IIS 上传目录**（`.ashx`、`.aspx`，或 `uploadfiles/YYYYMMDD/` 一类路径）：

- 文件名前 18 位可能是 .NET ticks（自 0001-01-01 起的 100ns 计数），如 `638126088411272500` 按 `datetime(1,1,1) + timedelta(microseconds=ticks/10)` 得 2023-02-21 20:40:41。它是强时间窗线索，不证明上传来源。
- 先用 SAS 按路径、文件名或哈希取资产、首末发现与文件时间，再查推算上传时间与 SAS `firstFound` 前后的 WAF：精确文件名、日期目录（含大小写变体）、上传接口的 `POST`。WAF/SAS 保留期覆盖不到时，写明无法据此证明原始来源 IP。
- SLS 查不到时读 IIS 日志，在文件时间前后至少 5 分钟内搜 `POST`、文件名或 ticks 前缀、上传目录与 `upload`、`.ashx`、`.aspx` 关键字，未命中再扩窗。

## 挖矿木马

1. **确认挖矿进程**：高 CPU 进程的 `cmdline`、`/proc/<PID>/exe` 真实路径与哈希。
2. **网络连接**：该进程外连，识别矿池地址:端口。
3. **入口与持久化**：父进程确认由 cron / Web / 登录拉起。重点核对 cron 定时重拉和 `/tmp`、`/var/tmp`、`/dev/shm` 下的 `.sh` 下载脚本；完整排查见本文「持久化后门」。
4. **按时间扩展**：以已知恶意文件 mtime/ctime 为锚搜同窗口落地文件。

## 反弹 Shell

1. **确认反弹进程**：与外部 IP 建连的 shell 进程（`bash/sh/zsh`）的 `cmdline` 与打开的 fd。
2. **连接信息**：远程 IP:端口，归属用联网检索查。
3. **触发来源**：看进程树与父进程；父进程是 Web 服务器（nginx/php/tomcat 等）时转查 access.log 中对应攻击 IP，反弹常由 Web RCE 触发。
4. **命令历史与脚本**：读各用户 `.bash_history`（读文件，不用交互式 history 内建）；在临时目录与相关路径搜 `/dev/tcp`、`bash -i`、`sh -i`、`nc -e`。

## 暴力破解与异常登录

1. **攻击源与模式**：失败登录（`lastb`、Debian `auth.log`、RHEL `secure`）按源 IP 聚合，统计被尝试的用户名与时间分布；auth.log 用户名常在 `$(NF-5)`，随格式偏移，先核对再取。
2. **是否得手**：同源成功登录（`Accepted`）找「失败→成功」转折点，区分密码（`Accepted password`）与密钥（`Accepted publickey`）登录；密钥登录核对该用户 `authorized_keys` 是否被植入。得手后查登录后的命令历史、进程与连接。
3. **来源研判**：来源 IP 未必是真实操作人，判断代理 / VPN / 跳板；私网来源见 `references/sas_sls_host_telemetry.md`「SSH 登录来源归因」。
4. **账户变更与防护**：`awk -F: '$3>=1000'` 列普通用户，警惕与 root 同 UID 0 的隐藏账户，查 `password changed`；核对 fail2ban / 防火墙是否已拦截该 IP。

主机登录日志可能被清除或不含 RDP / 数据库登录，用 SAS 登录遥测补证。

## 权限提升

1. **本地提权方式**：sudo/su 记录（auth.log / secure 的 `COMMAND=`）。
2. **SUID/SGID**：`find / -perm /6000`；重点 `find / -perm /4000 -mtime -7` 与 `/tmp`、`/var/tmp` 下带 `rws` 的文件。
3. **内核与配置滥用**：内核版本与可疑模块；配置型提权查 `/etc/sudoers`、`/etc/sudoers.d/`、`LD_PRELOAD`、`/etc/ld.so.preload`、PATH 劫持。
4. **提权后活动**：root 命令历史与非内核 root 进程。

云上提权（AK 泄露后建 RAM 用户、附加策略、改角色权限）按 `references/tech_cloud.md`「AK 泄露利用方式总结」查 ActionTrail。

## 数据外传

1. **当前通道**：一次性读取连接与计数（如 `ss -tinp`、`/proc/net/dev`、`netstat -s`），不运行需要交互或持续采样的工具。当前连接只说明采集时状态，网卡累计量不能归属本次攻击；连接已关闭也不能据此排除历史传输。
2. **外传目标**：提取外部 IP:端口，识别云存储外联（`amazonaws|aliyun|qcloud|s3` 等），归属用联网检索查。
3. **追踪进程**：按外部 IP 反查发起进程及其 `cmdline`。
4. **历史传输与对象**：围绕事件窗口查相关打包文件、命令记录、进程/网络遥测和存储访问记录，先取元数据再读内容。分别核对发起动作、成功状态、传输对象与可归属字节量，区分正常备份流量；命令出现或文件 atime 更新都不能单独证明数据已传出。

依次区分「外联」「传输尝试」「传输成功」「敏感数据泄露」，每次升级补对应的成功 / 对象证据；只确认外联时不填写臆测的数据量，无法核对内容或字节归属时写「无法确认」。

## 勒索软件

1. **确认勒索进程**：异常高资源进程及其父进程、启动时间。
2. **加密行为**：`find -mmin -60` 找正在被改写的文件窗口；勒索信文件名常含 `*README*`、`*DECRYPT*`、`*RANSOM*`，读其内容取勒索渠道 / 钱包地址。
3. **追溯入口**：进程启动链与父进程，下载目录与临时目录的近期落地物。
4. **影响范围**：按加密扩展名统计受影响文件数与目录。

主机被加密后本地证据可能不可靠，用 SAS 进程与网络遥测还原加密进程父链及外联。

## SQL 注入

1. **攻击源与目标**：access.log 里按注入特征筛 `union.*select|' or |' and |--|#|/*`（按数据库方言调整），提取攻击 IP 与被打的 URL。
2. **数据库日志**：MySQL 慢查询 / 错误日志、PostgreSQL 日志中的异常查询。
3. **评估影响**：注入是否带 `into outfile|into dumpfile`（写文件 / 导数据的强信号）；web 目录在攻击时间窗是否有新文件（写 WebShell）。
4. **代码定位**：源码里找拼接型查询（如 `SELECT ... $_GET/$_POST`）。

## 远程代码执行

1. **确认漏洞利用**：access.log 里按命令执行特征筛 `system(|exec(|passthru(|shell_exec(|反引号|%00`，结合攻击 IP 的可疑 POST。
2. **执行的命令**：Web 服务器进程（如 `java`、`php-fpm`、`w3wp.exe`）的异常子进程链。
3. **执行痕迹**：web 用户命令历史（如有）、进程启动记录。
4. **代码定位与后续**：源码里的 `system/exec/passthru/shell_exec/eval` 危险调用；临时目录在攻击时间窗的下载物与 web 用户的反向连接。

## 持久化后门

告警本身是持久化类（恶意 cron / 服务 / SSH key 植入）时用本节深挖；步骤 6 的六维扫查与命中项的通用下一步见 `references/workflow_tracing.md` 与 `references/recon_residual.md`。

1. **定时任务全覆盖**：逐用户 `crontab -l` 之外，核对 `/etc/crontab`、`/etc/cron.d/`、`cron.{hourly,daily,weekly,monthly}/`，以及易漏的 systemd timer（`systemctl list-timers --all`）和 at 任务（`at -l`、`ls /var/spool/at* /var/spool/cron`）。
2. **服务与启动链**：`systemctl list-unit-files --type=service` 配合 `/etc/systemd/system`、`/usr/lib/systemd/system` 的文件元数据筛查，按 `references/tech_process_file.md` 分别查看 mtime/ctime 候选；读可疑 unit 的 `ExecStart`、`User=`、`WorkingDirectory=`，用 `journalctl -u <unit>` 核实启动记录。
3. **登录触发点**：`/etc/profile`、`/etc/profile.d/`、各用户 `~/.bashrc` / `~/.bash_profile`、`/etc/rc.local`、`/etc/init.d/`；先看元数据再按 mtime/ctime 筛近期变化并读内容，未命中时间窗不能排除已有持久化。
4. **SSH 通道**：各用户 `authorized_keys` 的公钥条目与文件时间（配 `last` 交叉该窗口的登录）；`sshd_config` 有效配置（`grep -v '^#'`），关注 `AuthorizedKeysFile`、`PermitRootLogin` 被改。

- 运维自动化（备份、监控 agent、证书续期）也长这样：指向 `/opt`、`/usr/local` 且落地时间久远的 cron/unit 先与客户核对，不按「存在即恶意」写。
- 恶意持久化的强信号是组合：落地时间在攻击窗口内，`ExecStart` 或命令指向 `/tmp`、`/dev/shm`、`/home` 下近期文件，并含外网下载（`curl|wget`）或 base64 编码命令体；单一 mtime 命中不足以定性。`@reboot` 与分钟级 cron 优先深挖。
- 公钥植入的定性要有使用证据（`last` / `aegis-log-login` 命中该 key 窗口的登录），否则写「发现植入，未观察到使用」。
- 怀疑云侧重入通道（云助手 RunCommand 定期下发、AK 泄露后反复操作）时，核对主机 `/var/log/aliyun/assist/` 并按 `references/tech_cloud.md` 查 ActionTrail。
