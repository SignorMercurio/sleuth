<!-- Provenance: real claude-fable-5 sub-agent output, BASELINE variant (no skill
material — only the case prompt + findings fixture). Generated live 2026-07-03 via
the Claude Code Agent tool. Grade 80/100 (fails use-defanged-protocol: no `hxxp`,
because this findings has IP-form IoCs, not a URL). Archived as the reproducibility
snapshot behind reports/output_execution_runs.json (output_sha256). -->

2026年4月17日，监测发现对外提供 PHP 业务的 Web 服务器 web01（公网 IP 203.0.113.45，私网 IP 10.0.0.11）遭受攻击。攻击者利用该服务器文件上传功能的过滤缺陷（对应 ATT&CK T1190 利用面向公网应用），向 /var/www/upload/x.php 写入了一个 PHP webshell（T1505.003）。根据 access 日志记录，当日 18:18:12（CST）出现针对 /upload/x.php 的首个 POST 请求，来源 IP 为 203.0.113.45；约一分钟后的 18:19:40，主机进程遥测捕获到 w3wp 派生 php-cgi 的异常子进程。攻击者随后经由该 webshell 执行了 id、whoami 等命令进行环境探测。综合上传写入、进程遥测与命令执行等证据，判断攻击者大概率已成功获得服务器控制权限（该结论为基于现有证据的推测）。截至目前，未观察到稳定的 C2 外联行为。需要说明的是，本次调查依托的 access 日志仅覆盖 2026年4月10日至今，更早区间因日志轮转已无法获取，不排除攻击起始时间早于当前记录的可能。
