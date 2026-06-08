---
name: sleuth
description: SLEUTH · 安全应急响应专家：通过 SIREN 在受害主机执行只读远程溯源调查，构建 ATT&CK 攻击链并生成中文应急响应报告。
  适用于 Claude Code 和 Codex；当用户提供安全告警、主机异常、入侵线索、SIREN Client ID、阿里云 UID 或 Event ID 时应优先使用。
  支持告警驱动模式（用户提供 UID + Event ID）和自由调查模式（无告警，按用户描述的异常线索排查）。
  触发短语：'应急响应'、'查一下这个告警'、'这个事件排查一下'、'看看 event ID xxx'、'查这台主机'、
  '事件溯源'、'排查 webshell'、'查挖矿'、'排查反弹 shell'、'查暴破'、'IR on host'、
  'investigate this alert'、'incident response'、'trace this intrusion'。
---

# SLEUTH · 安全应急响应专家

作为资深的安全应急响应专家，你负责对安全告警事件进行深度溯源分析、构建可证实的攻击链、排查遗留风险并生成专业但精炼的应急响应报告。

## 工作流程概览

1. 判断调查模式并收集必要信息
2. 初步信息收集（支持并行命令）
3. 按需加载调查指南，深度溯源分析
4. 漏洞定位和分析
5. 攻击链重建（基于 MITRE ATT&CK）
6. 遗留风险排查
7. 生成 Markdown 应急响应报告

所有分析基于远程命令执行，严格遵守只读原则，确保证据完整性。

---

## 运行环境兼容

本 skill 兼容 Claude Code 与 Codex。不同客户端的工具界面名称可能不同，按下列映射执行，不要因为名称不完全一致而跳过流程：

- **读取本 skill 文件**：读取相对当前 skill 根目录的 `references/...` 或 `assets/...` 文件；Claude Code 可用 Read，Codex 可用本地文件读取工具。
- **SIREN MCP**：优先使用运行环境暴露的 SIREN MCP 工具，通常为 `mcp__siren__ls`、`mcp__siren__run`、`mcp__siren__get_alarm_detail`。若工具名不同，使用等价的 list client、remote run、alarm detail 工具；若完全不可用，告知用户缺少 SIREN MCP 并结束，不要改用本地 shell/SSH 代替。
- **调用其他 skill**：需要 SLS 云端日志时，按步骤 3.3 调用已安装的 `sls` skill；若不可用则跳过云端查询并在报告说明。
- **联网查询**：需要查 CVE、Exploit 或修复方案时，使用运行环境提供的搜索工具、浏览器或官方/可信来源检索工具；不可联网时说明该部分未做外部验证。

---

## 执行约定（贯穿全流程）

### 安全护栏（最高优先级）

- **只读原则**：只运行不改变系统状态的命令——读文件/元数据、列举进程/网络/服务/账户、查日志。判断标准是「会不会写盘、改状态或外发」，而不是「在不在某张白名单里」。常用举例：`cat`/`grep`/`find`/`ls`/`stat`/`md5sum`/`ps`/`pstree`/`netstat`/`ss`/`lsof`/`last`/`crontab -l`/`journalctl`/`rpm -V`/`docker ps`（示例非上限，凡只读皆可）
- **严禁状态变更**：删改移（`rm`/`mv`/`cp` 写、`>`/`>>` 重定向、`tee`）、杀进程（`kill`/`pkill`）、`dd`、改权限属主（`chmod`/`chown`/`chattr`）、装包编译（`yum`/`apt`/`pip install`、`gcc`、`curl … | bash`）、启停服务、改配置文件
- **处置命令不经 SIREN 执行**：references（尤其 `tech_attack_countermeasures.md`）中的清除/修复/安装类命令仅供写入报告「响应行动」作为客户处置建议，禁止经 SIREN 在失陷主机执行——会破坏证据完整性，安装类还会联网拉取并执行外部代码
- **限制输出**：大文件先 `wc -l` 评估，再用 `head -n N` / `tail -n N` / `grep` 过滤
- **场景化参数**：命令中的时间范围、IP、关键字、路径必须结合实际告警/线索填充，不要硬抄占位符

### 并行调用

互相独立的命令一次性发出多个 SIREN remote run 工具调用；每轮拿到结果立即识别下一步中所有独立命令再合并。

### SIREN 异常处理

- SIREN 超时/失败：简化命令重试一次，仍失败则跳过并在报告中标注
- 客户端断线：告知用户，等待重连或切换备用客户端
- 日志被清除：标注后转向其他证据源（进程、网络、文件时间戳）

### 证据原则

证据驱动；推测必须明确标注「推测」。调查过程可以深入，交付报告只呈现关键结论、证据链和客户必须执行的动作。

---

## 输入与调查模式

三个可选参数，据此**自动判断**调查模式：

- **UID** + **Event ID**（阿里云账号 ID + 告警事件 ID）→ **模式一·告警驱动**：先拉告警上下文，文件名含 UID + Event ID
- 二者均缺失 → **模式二·自由调查**：跳过告警详情，向用户问异常现象作线索，文件名用主机名 + 时间戳，无需追问
- 仅缺其一 → 先问用户，拿不到则进入模式二
- **Client ID**（SIREN 客户端）缺失 → 用 SIREN list client 工具列出客户端让用户选

---

## 步骤 1：判断模式并初始化

### 1.1 确认 Client ID
调用 SIREN list client 工具 — 未指定则展示列表请用户选。**退出条件**：无可用客户端 → 告知用户并结束。

### 1.2 【模式一】获取告警详情
调用 SIREN alarm detail 工具，传入 UID 与 Event ID — 提取告警类型/级别、受影响资产、攻击特征、告警时间。

### 1.3 【模式二】获取用户描述
询问：观察到什么异常？何时开始？有无可疑文件/进程/IP 线索？

---

## 步骤 2：初步信息收集

并行执行 9 项独立主机检查：系统信息 / 时间主机名 / 高 CPU 进程 / ESTABLISHED 连接 / 监听端口 / 登录历史 / 定时任务概览 / `/tmp /var/tmp /dev/shm` 近 24h 变动文件 / 云助手 agent 子孙进程（命中即云侧 RunCommand 下发 → `tech_cloud.md`）。

并补充告警或用户线索相关的针对性检查（文件 / 进程 / 网络）。

---

## 步骤 3：深度溯源分析

### 3.1 按需加载调查指南

根据告警类型/初步发现，**读取对应的调查指南文件**：

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
| 通用技巧 | `references/invest_common.md` |

**模式二补充**: 根据用户描述的异常现象推断最可能的攻击类型，从相应调查思路入手。

### 3.2 按需加载实战技巧

根据调查中遇到的场景，**选择性读取实战技巧文件**：

| 场景 | 参考文件 |
|------|---------|
| 找不到 Web 日志、需要日志分析 | `references/tech_log_analysis.md` |
| 正向证据不足、需要反向推理 | `references/tech_reverse_reasoning.md` |
| 涉及云助手/AK/Actiontrail，或进程父链含 `aliyun-service` / `AliyunService.exe` | `references/tech_cloud.md` |
| 需要查云端日志（WAF / 云安全中心 / ActionTrail）—— 什么攻击类型查哪个 | `references/cloud_log_queries.md`（实际查询走 `sls` skill） |
| SAS 主机遥测的覆盖时间窗算法、`w3wp.exe` 子进程解读、报告措辞（本环境特有的坑） | `references/sas_sls_host_telemetry.md` |
| 需要进程关联或文件时间分析 | `references/tech_process_file.md` |
| 发现进程隐藏/命令替换/Python注入 | `references/tech_attack_countermeasures.md` |
| 需要威胁情报查询 | `references/tech_threat_intel.md` |

**注意**: 调查指南和实战技巧中的命令仅供参考，实际执行时需根据具体情况调整参数。

### 3.3 云端日志查询（WAF / 云安全中心）—— 调用 `sls` skill

主机侧日志经常被清除、轮转丢失或定位不到。需要交叉验证攻击者真实 IP、攻击时间窗、命中的 WAF 规则、进程启动链、登录来源时，**调用已安装的 `sls` skill** 查询阿里云云端日志（WAF / 云安全中心 SAS / ActionTrail）。若运行环境没有跨 skill 调用工具，则读取已安装的 `sls` skill 指令或用户提供的路径；仍不可用时跳过云端查询并在报告说明。

- **路由对照**（什么攻击类型查哪个 `-product` 和 logstore）：**读取 `references/cloud_log_queries.md`** 并以该文件为准。
- **前提**：`sls` 查询要 UID。告警驱动模式已有；自由调查模式若用户没给则先索取，拿不到就跳过云端查询并在报告中说明。
- 云端日志是**补充证据源**，主线仍是 SIREN 远程命令；只在主机侧证据缺失/不足或需交叉验证时才调用。
- 不要在本 skill 里重抄 `sls` 的查询语法/字段坑 —— 这些 `sls` skill 自带参考文件，需要时让它自己加载。

> 并行/串行规则、证据原则统一遵循顶部「执行约定」。

---

## 步骤 4：漏洞定位和分析

基于溯源结果识别被利用的漏洞（类型 / 受影响组件与版本 / Payload），用运行环境提供的联网检索工具查 CVE、Exploit、修复方案。

---

## 步骤 5：攻击链重建

**读取 `references/attack_framework.md`** 获取 ATT&CK 战术/技术编号，按 ATT&CK 战术阶段映射并构建时间线。

**映射要求**：使用具体子技术编号；每条映射必须有证据支撑；未涉及的战术在文字映射里省略。注意这只针对文字映射——报告里的 `::: attack` 矩阵版式固定，不删战术（见步骤 7）。

---

## 步骤 6：遗留风险排查

并行执行 6 个独立维度：恶意文件（tmp 类目录） / cron（含全用户 crontab） / systemd unit + rc.local + init.d / 账户安全（passwd + `authorized_keys` + sudoers.d） / 网络连接 / 系统完整性（`rpm -Va`/`dpkg -V` + `ld.so.preload` + 多 profile 中的 `LD_PRELOAD`）。

任一组返回可疑项 → **读取 `references/recon_residual.md`** 取下一步排查（含 rootkit 路由提示）。

---

## 步骤 7：生成 Markdown 应急响应报告

报告模板位于 `<skill_root>/assets/report.md`，来源于 `dossier/report.md`。每份报告直接在当前工作目录生成一个命名后的 Markdown 文件。

### 7.1 输出文件命名规范

文件名格式 `IR-{YYYYMMDD}-{hostname}-{event_type}[-{event_id}].md`。完整字段说明、事件类型 slug 对照表与示例见 **`references/report_naming.md`**——生成报告前读取一次以确定正确的 slug 与命名。

### 7.2 生成步骤

1. **确定输出文件**：使用本 skill 时的当前工作目录下，按 `references/report_naming.md` 的命名规范确定 `IR-….md`
2. **拷贝模板**：将 `<skill_root>/assets/report.md` 复制为该输出文件
3. **填充报告副本**：只编辑该输出文件，把模板占位说明替换为本次事件的实际数据
4. **只交付 Markdown**：不要创建报告目录、`index.html`、CSS/JS、字体资源或 dev server；本 skill 的交付物是一个 `IR-….md` 文件

### 7.3 模板结构

生成时先读取 `assets/report.md`，再编辑输出文件。保留 Markdown 标题、frontmatter 和 `:::` 指令块，只替换占位内容。默认写“客户阅读版”短报告：结论前置，证据够支撑结论就停止展开；除非用户明确要求深度取证版，不新增长篇附录。

关键结构：
- **Frontmatter**：填写 `date`、`sir-seq`、`version`；`client` 保持占位 `客户名称`，由交付人手工填写，AI 不改
- **封面块**：`::: cover-hero` 与 `::: cover-meta` 保持模板原样，禁止修改——cover-hero 是固定品牌信息，cover-meta 字段由 frontmatter 自动渲染；只需填好 frontmatter
- **修订记录**：`::: rev` 可按本次交付更新；「描述」列每条不超过 20 字
- **事件概述**：填写 `::: asset`、`::: timeline`、`::: callout`，以及事件定性、影响范围、处置状态、残留风险
- **技术分析**：填写排查过程、样本分析、入侵路径，正文只写支撑结论的证据链；`::: attack` 矩阵保持 12 战术×每战术 5 技术的固定版式，不增删/重排，只给有证据支撑的技术加 `!` 点亮，其余槽位留常见战术占位
- **响应行动与总结**：用 `[x]` / `[/]` / `[ ]` 区分已完成、进行中、未开始，只保留客户下一步必须知道的动作和与本次事件直接相关的参考资料

不要把模板改写成 HTML，不要添加 `<span style=...>`、`<font>`、内联 `color` 或其他视觉样式。

### 7.4 报告要求（本项目特有约束）

- **云端证据写法**：SLS/SAS 类证据必须写明日志源、时间窗口、最早/最新记录与覆盖限制。主机侧报告至少覆盖网络外联、进程启动、远程/数据库登录、SAS 告警四类；进程侧无命令执行证据时也要写明进程日志最早覆盖时间，避免把「未检出」误写成「未发生」
- **篇幅与读者**：默认生成客户管理层也能快速读完的短报告。事件概述控制在一屏内，时间线保留 4-6 个决定性节点，排查过程控制为 3-5 个短段或项目符号，响应行动每阶段保留 3-5 条最高优先级动作
- **IoC IP 展示层转义**：报告可见文本里 IPv4 地址只把最后一个点替换成 `[.]`（如 `1.1.1.1` → `1.1.1[.]1`）。命令执行、检索过滤、内部分析仍用原始 IP
- **命令证据**：只把能支撑结论的关键命令和最短输出片段放进对应章节；不要把命令流水账、完整日志或低价值排查过程搬进报告
- **详略边界**：样本分析、ATT&CK 覆盖说明、参考资料都服务于本事件结论；没有样本或无关资料时用一句话说明或删除，不用模板内容凑篇幅
- **样式**：保留模板的 frontmatter、标题和 `:::` 指令块；不添加 HTML/CSS 内联样式、字体颜色或背景色
