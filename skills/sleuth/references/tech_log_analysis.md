# 日志定位与分析技巧

## Web 日志定位（找不到日志时按序试）

1. 从告警详情提取路径（WebShell 路径反推站点根；Java 进程 `-Dcatalina.base` 反推工作目录）。
2. 定位 Web 进程：按监听端口（80/443/8080）找进程，再看 `/proc/<PID>/cwd`、`exe`、`cmdline`。
3. 查中间件配置取日志路径：Nginx `access_log`、Apache `CustomLog`、Tomcat `$CATALINA_HOME/logs/`（`localhost_access_log*`、`catalina.out`）。
4. 按时间搜 `*.log -mtime -1`；**注意无后缀日志**，用 `file` 过滤出文本文件。
5. 容器环境：`docker/crictl logs <id>`（Web 日志常打到 stdout）；从进程链前缀提容器 ID。
6. 无 Web 日志时用应用日志兜底，搜 `ERROR|Exception|eval|exec|Runtime`。

## 时间窗与请求关联

先区分事件时间、检测时间和入库时间，保留原始时间、时区与采集时间。扫描发现、延迟上报、异步任务都可能晚于攻击；时区一致也不代表主机时钟一致。用可对应的请求 ID、任务 ID、进程启动记录校准偏差，不修改受害机时钟。

先查证据支持的最小时间窗；窗口未命中时检查覆盖与字段语义，再依据延迟、任务持续时间逐步扩窗，并记录理由。不要仅凭告警前后几秒无命中排除入口。

多次告警附近的 URL 交集只用于候选排序：各窗口先去重，同时保留非交集请求，排除健康检查等正常高频请求。通过载荷、请求 ID、目标文件与执行链确认因果关系，不要求每个告警都有同一个攻击 URL。

## WAF 日志字段分析与会话反向匹配

> 查 WAF 原始日志优先调用 `sls` skill。调用边界见 `references/cloud_log_queries.md`，本节只负责拿到日志后的分析。

- 看分布：`request_path`、`status`、`request_length`（异常大请求）、`real_client_ip`；聚合用 `GROUP BY real_client_ip / request_path` 找高频源与扫描者。
- **会话反向匹配**（攻击者换 IP 也能串起来）：靠会话 Cookie 唯一性——先取攻击 IP 的会话 ID，再用会话 ID 反查其所有请求。常见会话字段：`acw_tc`(WAF)、`aliyungf_tc`(阿里云)、`PHPSESSID`(PHP)、`JSESSIONID`(Java)、`ASP.NET_SessionId`(.NET)。

## 时区坑

日志与告警时区不一致会导致比对错误。`+0800` 是 UTC+8；`+0000` 或结尾 `Z` 是 UTC+0（ISO 8601）。UTC+0→UTC+8 加 8 小时。系统时区看 `timedatectl` / `date +%Z`。

## 攻击源 IP 追溯（判读规则）

先核对实际代理链（含 WAF 前的 CDN/高防/代理），区分连接源 IP、转发头声明的 IP 与经可信代理配置确认的客户端地址。查明 WAF 和应用从哪个字段取地址，以及上游是否覆盖并保护该字段；`X-Forwarded-For` / `X-Real-IP` 的值不能天然视为可信。

配置无法核实时写「WAF 记录的客户端来源 IP」，不升级为真实操作人地址；即使确认客户端地址，也可能是代理、VPN 或 NAT 出口。来源地址、恶意请求关联与攻击者身份分别核验。
