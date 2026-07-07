# 日志定位与分析技巧

## Web 日志定位（找不到日志时按序试）

1. 从告警详情提取路径（WebShell 路径反推站点根；Java 进程 `-Dcatalina.base` 反推工作目录）。
2. 定位 Web 进程：按监听端口（80/443/8080）找进程，再看 `/proc/<PID>/cwd`、`exe`、`cmdline`。
3. 查中间件配置取日志路径：Nginx `access_log`、Apache `CustomLog`、Tomcat `$CATALINA_HOME/logs/`（`localhost_access_log*`、`catalina.out`）。
4. 按时间搜 `*.log -mtime -1`；**注意无后缀日志**，用 `file` 过滤出文本文件。
5. 容器环境：`docker/crictl logs <id>`（Web 日志常打到 stdout）；从进程链前缀提容器 ID。
6. 无 Web 日志时用应用日志兜底，搜 `ERROR|Exception|eval|exec|Runtime`。

## 围绕告警时间过滤

告警时间是最可靠线索，取其前后几秒的日志比对。适用 Web / 应用 / WAF / 系统（messages、syslog）/ 云助手命令日志。

## 多次告警取交集定位关键请求（高价值技巧）

攻击请求往往多次出现，每个告警时间点都该有对应攻击请求，**取交集大幅缩小范围**：列出全部告警时间点 → 各取该点前后约 2 秒内的请求 URL（`awk '{print $7}' | sort -u`）→ 求在所有时间点都出现的 URL。

```bash
# N 个告警时间点各出一份 urls_*.txt 后取交集（出现 N 次的即可疑）：
cat urls_*.txt | sort | uniq -c | awk '$1 == 6 {print $2}'
```

告警次数越多越准，通常能收窄到 1-3 个请求。

## WAF 日志字段分析与会话反向匹配

> 查 WAF 原始日志走 `sls` skill（`-product waf`）；调用方式、测试模式 vs 实际拦截、高防解读见 `references/cloud_log_queries.md` 与 `sls` 自带参考。本节是拿到日志后的分析。

- 看分布：`request_path`、`status`、`request_length`（异常大请求）、`real_client_ip`；聚合用 `GROUP BY real_client_ip / request_path` 找高频源与扫描者。
- **会话反向匹配**（攻击者换 IP 也能串起来）：靠会话 Cookie 唯一性——先取攻击 IP 的会话 ID，再用会话 ID 反查其所有请求。常见会话字段：`acw_tc`(WAF)、`aliyungf_tc`(阿里云)、`PHPSESSID`(PHP)、`JSESSIONID`(Java)、`ASP.NET_SessionId`(.NET)。

## 时区坑

日志与告警时区不一致会导致比对错误。`+0800` 是 UTC+8；`+0000` 或结尾 `Z` 是 UTC+0（ISO 8601）。UTC+0→UTC+8 加 8 小时。系统时区看 `timedatectl` / `date +%Z`。

## 攻击源 IP 追溯（判读规则）

反向代理架构 **真实攻击者 → WAF → SLB → Nginx → 应用** 下：应用日志看到的是 Nginx IP，Nginx 看到的是 SLB IP，**只有 WAF 日志才是真实攻击者 IP**。核对应用是否从 `X-Forwarded-For` / `X-Real-IP` 取真实 IP。
