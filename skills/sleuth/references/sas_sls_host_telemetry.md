# SAS 主机遥测判读（SLS）

查询交给 `sls` skill 执行，实例绑定与跨资产边界按 `references/cloud_log_queries.md`「调用要点」；本文只写本环境特有的字段坑与判读边界。

## 字段坑

- `start_time` 可能是字符串，直接 `from_unixtime(start_time)` 会报 `Unexpected parameters (varchar)`，先 `CAST(start_time AS bigint)`；`proc_start_time` 可能为 `N/A` 或空，筛选时排除。
- `aegis-log-dns-query` 按进程记录 DNS 请求（`domain`、`pid`/`ppid`、`proc_path`、`cmdline`、`cmd_chain`），常无 `answer` 字段，没有应答不等于没有解析行为。
- `sas-security-log` 的 `detail` 含父链（`cmdline`、`ppcmdline`…`ppppcmdline`、`complex_report_info`）；异常登录类告警的 RDP 来源、用户、协议也在 `detail` 里。
- 云安全中心告警详情的溯源模块与「调查响应 → 进程启动」看的是 `aegis-log-process` 同一份数据。

## 覆盖时间窗

每个用到的 topic 都查该实例的最早 / 最新记录与数量：进程 topic 用 `MIN(proc_start_time)`，登录 topic 条件改为 `(instance_id: … OR src_ip: <HOST_IP> OR host_ip: <HOST_IP>)`，告警按 `name` 分组。覆盖结果按 `references/findings_spec.md`「云端证据覆盖」记录，阴性写法按 `references/verification_checklist.md`「云端与阴性判断」。

## IIS / ASP.NET（`w3wp.exe`）

子进程按 `parent_proc_name: w3wp.exe OR pcmdline: w3wp.exe` 查，外联按 `proc_name: w3wp.exe` 查并按 `dst_ip, dst_port` 分组。

- `w3wp.exe -> csc.exe`（路径在 `.NET Framework*/Temporary ASP.NET Files`）通常是 ASP.NET 动态编译，单独不算恶意。
- `w3wp.exe -> cmd.exe / powershell.exe / certutil / bitsadmin / mshta / rundll32 / regsvr32 / wscript / cscript` 是较强的执行证据。
- `w3wp.exe` 外联公网 22 端口属异常，除非客户确认有 SFTP/SSH 业务逻辑。

## SSH 登录来源归因

以下查询都限告警实例与告警时间窗。

1. 先用 `sas-security-log` 告警明细确认父链：形如 `sshd listener -> sshd: <user> [priv] -> sshd: <user>@notty -> -bash -> <command>` 可确认命令在 SSH 会话下执行。
2. 查 `aegis-log-login`（`login_type=SSH`），按准确的 sshd PID / 父链、进程启动时间和登录时间对齐会话，有会话标识时一并核对；PID 相同也要排除复用、重启和不同容器命名空间。
3. 查 `aegis-log-process`（`username: <ssh_user>`）复核执行链，`cmd_chain` 里的 `-bash -> /usr/sbin/sshd -D -R -> sshd listener` 把命令挂回会话。同账号并发登录分不开时分别列候选来源，不强选一个 IP。
4. `src_ip` 是私网地址时通常是堡垒机、跳板、VPC 内代理或运维出口，真实来源要查堡垒机审计、跳板 sshd/auth 日志、VPN/NAT/VPC 流日志或运维平台。
5. 用户给了公网 IP 时可补查云防火墙入方向 22 端口；来源走私网跳板时公网侧可能无记录，无命中不能推翻 SAS 登录证据。

能确认的只有：命令是否处在 SSH 会话父链下、SAS 记录的客户端来源 IP、登录用户与时间。私网 `src_ip` 背后的公网 IP、具体自然人和是否恶意登录都不能据此确认。

## DNSLog / OOB 域名告警

适用：「恶意DNS请求拦截」「请求带外攻击(OOB)域名」，或域名以 `dnslog.cn`、`interact.sh`、`oast.*`、`burpcollaborator.*`、`ceye.io` 等结尾。

这类请求默认不是普通 DNS 误报：它说明 payload 已进入某个进程并触发解析，常见于 RCE 探测、SSRF、带外回显的 SQL 注入、模板注入、JNDI/Log4j 类探测，或应用本身会解析攻击者可控的输入；能否升级为主机失陷按 `references/verification_checklist.md`「云端与阴性判断」。

从告警取实例与时间窗，在 `aegis-log-dns-query` 按域名（含小写变体）找到触发进程，再在同实例同时间窗查后续证据：进程用 `ppid: <PID> OR pcmdline: <触发进程> OR parent_proc_name: <进程名>`，并看 `cmdline` 是否含域名、`dnslog.cn`、`curl`、`wget`、`nc`、`bash`、`sh`、`python`、`perl`、`/tmp`；外联按 `dst_ip, dst_port, proc_name, proc_path` 分组；其他告警与登录按 `start_time` 排序；按 OOB 根域名跨 topic 计数看是否反复出现。

建议客户按告警时间排查触发进程的应用日志、SQL / 查询历史、调度任务与 JDBC/ODBC/HTTP 访问来源；`impalad`、`spark`、`hadoop`、`java` 类大数据服务另看 YARN/Spark 应用日志。
