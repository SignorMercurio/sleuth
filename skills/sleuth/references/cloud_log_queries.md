# 阿里云云侧交叉验证路由——直接工具优先

本文件只负责选择云端日志源。调用顺序与委派边界见 SKILL.md「云侧分层」和 `references/workflow_tracing.md` 步骤 3.2；查询语法、schema 探测与字段解读由 `sls` skill 管理，按需让它加载自己的参考文件，不硬编码上游内部路径。

## 前提：UID

`sls` 查询必须有 UID。
- **告警驱动模式**：UID 已知，直接用。
- **自由调查模式**：用户没给 UID 时先索取；拿不到就跳过云端查询，并在 findings 记录「未做云端日志交叉验证」。

## 什么场景查什么 —— 路由表

| 攻击 / 告警类型 | `sls` 产品 / topic | 待证问题与判读入口 |
|---|---|---|
| **WebShell / SQL 注入 / RCE / 文件上传** | WAF | 定位上传或利用请求、来源与实际处置结果。规则命中不等于拦截，须让 `sls` 核对测试模式、最终动作与回源结果；来源归因见 `references/tech_log_analysis.md`，上传链见 `references/aspnet_webshell_upload_tracing.md` |
| **挖矿 / 可疑进程 / RCE 后续执行** | SAS：`aegis-log-process`，必要时配 `aegis-log-network` | 用命令行、父进程和启动时间还原启动链，区分 Web、定时任务与登录后执行；时间字段与关联陷阱见 `references/sas_sls_host_telemetry.md` |
| **反弹 Shell / C2 / 数据外传** | SAS：`aegis-log-network`，DNS 配 `aegis-log-dns-query` | 关联外联目标、端口与发起进程 |
| **DNSLog / 带外域名请求** | SAS：`aegis-log-dns-query` | 核对域名、进程链及请求来源，见 `references/oob_dnslog_investigation.md` |
| **异常登录 / 暴力破解** | SAS：`aegis-log-login` + `sas-security-log` | 前者是 SSH / RDP / 数据库等原始登录遥测，后者是告警；核对源 IP、用户、协议和失败到成功的转折 |
| **AK 泄露 / 云助手滥用 / API 溯源** | ActionTrail | 关联调用身份、任务与资源行为，见 `references/tech_cloud.md` |
| **应用防护 / RASP** | SAS：`sas-rasp-log` | 委派 `sls` 加载其 RASP 判读参考 |

SAS 遥测的覆盖时间窗、`w3wp.exe` 子进程判读与措辞要求统一见 `references/sas_sls_host_telemetry.md`。

## 调用要点

- 目标主机查询必须绑定已核对的实例/资产标识，结果保留该标识；PID、用户名、私网 IP 和进程名不单独作为跨记录关联键。跨资产扩展与单机取证分开，超出授权清单先确认。
- `opencli-aliyun-ir` 只补充云防火墙、ACK/DAS、OSS/RDS/ECS/VPC/SLB、内部控制台、免费 ActionTrail 事件窗或其他直接工具覆盖缺口；前一层已完整回答时不重复调用。
- 拿到结果后，按 `references/findings_spec.md` 记录查询身份、范围、原始证据与完整性；云端覆盖另记最早/最新记录与保留期。不要把「未检出」写成「未发生」。
