# SSH 登录来源归因：SAS 主机遥测口径

适用场景：用户给出 ECS 实例 ID、公网/私网 IP、SAS 告警事件或父进程链含 `sshd`，询问告警是否由 SSH 登录触发、能否查到 SSH 客户端来源 IP。

## 推荐查询顺序

1. 先用 SAS `sas-security-log` / 告警明细确认父进程链。
   - 关键字段：`detail`、`cmdline`、`ppcmdline`、`pppcmdline`、`ppppcmdline`、`complex_report_info`、`suspicious_event_id`。
   - 若链路形如 `sshd listener -> sshd: <user> [priv] -> sshd: <user>@notty -> -bash -> <command>`，可确认命令在 SSH 会话下执行。

2. 查同实例 `aegis-log-login` 获取 SSH 登录来源。
   - 过滤：`__topic__: aegis-log-login AND instance_id: <instance_id>`。
   - 字段：`from_unixtime(__time__) AS log_time, username, login_type, src_ip, pid, host_ip`。
   - `login_type=SSH` 且 `pid` 与告警进程链中的 sshd PID 接近/一致时，是较强关联证据。

3. 查同窗口 `aegis-log-process` 复核执行链。
   - 过滤：`__topic__: aegis-log-process AND instance_id: <instance_id> AND username: <ssh_user>`，时间窗围绕登录/告警时间。
   - 字段：`cmd_chain, cmdline, proc_name, proc_path, pcmdline, pid, ppid, username`。
   - `cmd_chain` 中常能看到 `command -> -bash -> /usr/sbin/sshd -D -R -> sshd listener`，用于把告警命令挂回 SSH 会话。

4. 若 `aegis-log-login.src_ip` 是私网 IP，谨慎表述。
   - 该 IP 通常是堡垒机、跳板机、VPC 内代理或内网运维出口。
   - SAS 只能证明主机看到的 SSH 客户端来源，不等于真实公网操作人 IP。
   - 真实公网来源需继续查堡垒机审计、跳板机 sshd/auth 日志、VPN/NAT/VPC 流日志或运维平台日志。

5. 如用户给了公网 IP，可补查 CFW 入方向 22 端口，但不要把无命中当成否定 SSH。
   - 若 SSH 来源是私网跳板，CFW 公网 `dst_ip:<公网IP> AND dst_port:22` 可能无记录。
   - 无 CFW 命中只能说明所查 CFW 口径下未看到公网 22 入方向流量，不能推翻 SAS 登录证据。

## 输出措辞

- 能确认：告警命令是否处在 SSH 会话父链下；SAS 记录到的 SSH 客户端来源 IP；登录用户与登录时间。
- 不能过度确认：私网 `src_ip` 背后的真实公网 IP、具体自然人、是否恶意登录。
- 推荐格式：
  - “已确认告警在 `<user>` 的 SSH 登录会话下触发。”
  - “SAS `aegis-log-login` 记录到的 SSH 客户端来源为 `<src_ip>`；该地址为私网地址时，应按跳板/堡垒机来源继续溯源。”
  - “当前 CFW 未检出公网 22 入方向记录，不影响上述主机侧 SSH 会话结论。”
