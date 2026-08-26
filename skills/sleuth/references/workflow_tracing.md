# 步骤 3–6：深度溯源、漏洞、攻击链与遗留风险

SKILL.md 进入步骤 3 时加载本文件。安全护栏以 SKILL.md 为准，本文只写操作细则。

## 步骤 3.1 按需加载调查指南与实战技巧

**读取 `references/playbook_index.md`**，按其路由表选择并读取对应文件：

- **调查指南**（按告警类型）：webshell / ASP.NET 上传溯源 / 挖矿 / 反弹 shell / 暴破 / 异常登录 / 提权 / 数据外传 / 勒索 / SQLi / RCE / DNSLog / 持久化
- **实战技巧**（按场景）：日志分析 / 反向推理 / 云助手取证（父链含 `aliyun-service`）/ 云日志路由 / SAS 遥测坑 / SSH 归因（父链含 `sshd`）/ 进程文件关联 / 对抗手法 / 威胁情报

**模式二**：先据用户描述的异常推断最可能的攻击类型，再从相应指南入手。命令仅供参考，按实际参数调整。

大输出（大日志、全盘 `find`、SLS 大结果集）按 `references/runtime_compat.md`「重输出隔离」处理。

## 步骤 3.2 阿里云云侧交叉验证 —— 直接工具优先

主机侧日志常被清除、轮转或定位不到。云侧证据只作**补充证据源**，主线仍是 SIREN。调用优先级（`$sas` 告警 → `sls` 已投递日志 → 只读 `opencli-aliyun-ir` 控制面/专用能力）见 SKILL.md 安全护栏「云侧分层」，`$sas` 契约见步骤 1.2。

- **委派输入**：目标 UID、已确认的站点/地域、资产标识、调查时间窗、待验证问题和已知 IoC；不传整段调查对话或无关主机输出。
- **委派输出**：只接收查询身份与范围、已确认事实、未确认项、IoC、覆盖缺口和只读下一步；原始大日志先在委派侧收窄。
- **路由**以 **`references/cloud_log_queries.md`** 为准。`sls` 自己管理查询契约；OpenCLI 适配器、参数和字段由 `opencli-aliyun-ir` 自己管理。
- 模式一已有 UID；模式二没有则索取。对应直接 skill 不可用时才尝试下一层；全部不可用则跳过并披露缺口（影响对照见 `references/preflight_probe.md`），不改用本地 shell、SSH、浏览器或任意云 CLI。

## 步骤 4 漏洞定位和分析

基于溯源结果识别被利用的漏洞（类型 / 受影响组件与版本 / Payload），用运行环境提供的联网检索工具查 CVE、Exploit、修复方案；不可联网时说明该部分未做外部验证。

## 步骤 5 攻击链重建

**读取 `references/attack_framework.md`** 获取 ATT&CK 战术/技术编号，按 ATT&CK 战术阶段映射并构建时间线。

**映射要求**：使用具体子技术编号；每条映射必须有证据支撑；未涉及的战术在文字映射里省略。注意这只针对文字映射——报告里的 `::: attack` 矩阵版式固定，不删战术（版式细则见 `references/report_writing_rules.md`，步骤 8 读取）。

## 步骤 6 遗留风险排查

并行执行 6 个独立维度：恶意文件（tmp 类目录） / cron（含全用户 crontab） / systemd unit + rc.local + init.d / 账户安全（passwd + `authorized_keys` + sudoers.d） / 网络连接 / 系统完整性（`rpm -Va`/`dpkg -V` + `ld.so.preload` + 多 profile 中的 `LD_PRELOAD`）。

任一组返回可疑项 → **读取 `references/recon_residual.md`** 取下一步排查（含 rootkit 路由提示）。
