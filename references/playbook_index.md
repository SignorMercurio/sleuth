# 调查指南 / 实战技巧路由索引（步骤 3）

根据告警类型、初步发现与调查中遇到的场景，按下表选择并**读取对应文件**。命令仅供参考，实际执行时按具体告警/线索调整参数。

## 调查指南（按告警类型）

| 告警类型 | 参考文件 |
|---------|---------|
| Web Shell 后门 | `references/invest_webshell.md` |
| ASP.NET/IIS 上传目录 WebShell 溯源 | `references/aspnet_webshell_upload_tracing.md` |
| 挖矿木马 | `references/invest_mining.md` |
| 反弹 Shell | `references/invest_reverse_shell.md` |
| 暴力破解 | `references/invest_brute_force.md` |
| 异常登录 | `references/invest_abnormal_login.md` |
| 权限提升 | `references/invest_privilege_escalation.md` |
| 数据外传 | `references/invest_data_exfiltration.md` |
| 勒索软件 | `references/invest_ransomware.md` |
| SQL 注入 | `references/invest_sql_injection.md` |
| 远程代码执行 (RCE) | `references/invest_rce.md` |
| DNSLog / OOB 域名请求 | `references/oob_dnslog_investigation.md` |
| 持久化后门 | `references/invest_persistence.md` |

**模式二补充**：根据用户描述的异常现象推断最可能的攻击类型，从相应调查思路入手。

## 实战技巧（按场景）

| 场景 | 参考文件 |
|------|---------|
| 找不到 Web 日志、需要日志分析 | `references/tech_log_analysis.md` |
| 正向证据不足、需要反向推理 | `references/tech_reverse_reasoning.md` |
| 涉及云助手/AK/Actiontrail，或进程父链含 `aliyun-service` / `AliyunService.exe` | `references/tech_cloud.md` |
| 需要查云端日志（WAF / 云安全中心 / ActionTrail）—— 什么攻击类型查哪个 | `references/cloud_log_queries.md`（实际查询走 `sls` skill） |
| SAS 主机遥测的覆盖时间窗算法、`w3wp.exe` 子进程解读、报告措辞（本环境特有的坑） | `references/sas_sls_host_telemetry.md` |
| 告警父链含 `sshd`、用户问是否 SSH 登录触发 / SSH 客户端来源 IP | `references/ssh_login_attribution_sas.md` |
| 需要进程关联或文件时间分析 | `references/tech_process_file.md` |
| 发现进程隐藏/命令替换/Python注入 | `references/tech_attack_countermeasures.md` |
| 需要威胁情报查询 | `references/tech_threat_intel.md` |
