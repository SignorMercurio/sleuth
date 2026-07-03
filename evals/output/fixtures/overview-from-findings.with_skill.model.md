<!-- Provenance: real claude-fable-5 sub-agent output, WITH_SKILL variant (given
report_style + report_writing_rules summaries). Generated live 2026-07-03 via the
Claude Code Agent tool. Grade 80/100 (fails use-defanged-protocol: no `hxxp`, since
the IoC is an IP, not a URL — but note it DID defang the IP to 203.0.113[.]45, which
no current assertion rewards). Archived as the reproducibility snapshot behind
reports/output_execution_runs.json (output_sha256). -->

2026 年 4 月 17 日 18 时 18 分（CST），对外 PHP 业务服务器 web01（公网 203.0.113[.]45）的 access 日志出现针对上传接口 /upload/x.php 的首个 POST 请求，约一分钟后云安全中心的进程遥测记录到 w3wp 派生 php-cgi 的异常子进程，两条证据在时间和链路上吻合，指向攻击者利用上传点过滤缺陷写入 PHP webshell（文件落地于 /var/www/upload/x.php）并成功访问，随后经该 webshell 执行了 id、whoami 等命令。据此判断本次入侵大概率已得手，对应 ATT&CK 的 T1190（利用面向公网应用）与 T1505.003（Web Shell）。截至目前未观察到稳定的 C2 外联，但这不代表外联不存在，仅说明在现有日志范围内未捕获到相关行为。需要说明覆盖限制：本次研判依据云防火墙 WAF 日志（覆盖 2026 年 4 月 10 日至今）与云安全中心进程遥测（覆盖 2026 年 4 月 12 日至今），access 日志同样自 4 月 10 日起留存，更早区间已轮转，首个上传请求之前是否已有探测或写入无法确认。
