# 调查细则（步骤 1–6）与运行机制

SKILL.md 步骤 1 加载本文件，调查全程按本文执行。安全护栏、调查模式、调查闭环与核验裁决以 SKILL.md 为准，本文只写操作细则。步骤 7 的细则在 `references/verification_checklist.md`。

## 知识路由（命中场景时再读）

| 场景 | 读 |
|---|---|
| 告警或异常属于 Web Shell、挖矿木马、反弹 Shell、暴力破解与异常登录、权限提升、数据外传、勒索软件、SQL 注入、远程代码执行、持久化后门 | `references/playbooks.md` 对应小节；模式二按用户描述推断最可能的类型 |
| 找不到 Web 日志、只有应用日志、正向证据链断裂、WAF 来源归因 | `references/tech_log_analysis.md` |
| AK/STS 滥用、云助手、ActionTrail 异常调用，或进程父链含 `aliyun-service` / `AliyunService.exe` | `references/tech_cloud.md`（审计看「ActionTrail 审计要点」「AK 泄露利用方式总结」） |
| 需要阿里云云侧证据（WAF / SAS / 云防火墙 / ActionTrail / 云资源配置） | `references/cloud_log_queries.md` |
| SAS 主机遥测覆盖时间窗；`w3wp.exe` 子进程；父链含 `sshd` 或要确认 SSH 来源 IP；DNSLog / OOB 域名请求 | `references/sas_sls_host_telemetry.md` |
| 进程关联、文件时间分析 | `references/tech_process_file.md` |
| 进程隐藏、命令替换、Python 标准库注入 | `references/tech_attack_countermeasures.md` |
| 威胁情报 | 用运行环境的联网检索查哈希、IP、域名（如 VirusTotal 的 Relations / Community、微步）；平台无检出时，用主机上看似无关的目录名或报错原文检索社区分析与 GitHub Issue |

## 步骤 1.1 确认输入、能力、Client 与范围

**输入判别**：

- **UID**（阿里云账号 ID）+ 一个 **SAS 选择器**（告警列表返回的数字 `Id` / 云安全中心资产 UUID / ECS 实例 ID）→ 模式一。
- 只缺其一 → 先问用户，拿不到进入模式二；两者都缺 → 直接模式二，不追问，文件名用主机名 + 日期。
- 同时给出多个选择器 → 让用户确认范围，不把互斥参数组合后交给 `$sas`。
- 符合 SKILL.md「云侧事件」→ 必须有 UID，不问 Client ID；模式一、二照常判别。
- **Client ID** 缺失（云侧事件除外）→ 用 SIREN list client 工具列出让用户选。

**能力确认**：调用 SIREN list client 确认可达且目标在线（云侧事件跳过，转主机取证时再调）；已有有效列表直接复用，状态变化才刷新，不为探测在受害主机跑命令。SIREN 工具缺失、不可达或无可用客户端 → 按 SKILL.md「工具边界」降级：有 UID 按云侧事件继续并记主机侧缺口，否则告知用户并结束。从运行环境清单确认 `$sas`、`sls`、`act`、`opencli-aliyun-ir`、子 agent 与联网检索是否可用；不确定的云侧 skill 只在需要时试调一次，失败即记缺口。`aliyun` 是命令行工具，不是 skill：先运行 `aliyun configure list`，空列表表示当前 Project 没有 AccessKey，跳过这一层；有多个 profile 时每条命令带 `--profile <名称>`。模式一缺 `$sas` 时向用户索取告警摘要，区分用户提供与独立核验的事实；拿不到摘要则按模式二继续。

**范围与底稿**：多主机委托在此确定完整主机清单与顺序（首发告警或影响最严重的主机优先）；证据指向清单外主机时，向用户确认后追加。按 `references/findings_spec.md` 为每台主机初始化底稿并标记「调查中」，确认已有文件是续查还是新一轮；记录 Client 与云资产映射、调查起点，之后每轮补写。

能力缺失项、判定依据和受影响方向记入 findings「云端证据覆盖」与「证据缺口」。缺失只限制依赖该证据的断言，不统一压低全部结论，也不把未覆盖写成「未发生」。

## 步骤 1.2 【模式一】获取告警详情

只调用 `$sas` skill，传入 UID 与一个已确认的选择器；用户明确给出的 region 原样传递，其余默认值、分页与参数格式由 `$sas` 管理。

- **数字告警 `Id`**：直接查详情；只用用户提供或列表返回的 `Id`，不用 `AlarmUniqueInfo`。
- **资产 UUID / ECS 实例 ID**：先列告警；用户给的时间窗只传给列表查询，不自行推断。按用户范围继续分页，把返回的全部告警摘要作为调查输入，不要求先选出唯一告警；需要支撑方向、定性或影响范围时再按列表内的数字 `Id` 逐条查详情。空列表是有效结果，询问是否补充线索转入模式二。
- **统一落点**：列表输入即使多条也只形成一组事件结论，确认后由 dossier skill 只生成一份报告。findings 命名按 `references/findings_spec.md`「文件命名」。

## 步骤 1.3 【模式二】获取用户描述

询问：观察到什么异常？何时开始？有无可疑文件/进程/IP 线索？

## 步骤 1.4 【云侧事件】确认调查对象

从告警或首个异常调用确认受影响身份（AK ID / RAM 用户 / 角色 / STS 会话名）或受攻击域名与接口，以及时间窗；推不出再问用户，并标注依据。每个事件一份 findings，命名见 `references/findings_spec.md`。

## 步骤 2 初步信息收集

**云侧事件**按同一顺序：最小快照取告警或首个异常调用的身份、源 IP、地域、API 与时间；轻量基线按线索类型只做一组，凭据类按 `references/tech_cloud.md`「ActionTrail 审计要点」看该身份时间窗内的调用分布与 AK/RAM 变更，WAF 类只看该域名接口的 WAF 命中概况，其余等待证问题需要时再补。

1. **最小快照**：先核对系统类型、主机标识和时间；优先取告警目标进程的父链/启动时间、当前连接、关键文件元数据，再按需读内容。多主机对每台先完成这一轮，避免首台深挖期间其他主机的进程或连接消失。读文件前先取元数据并记录采集时间；只读采集也会刷新 atime。
2. **轻量基线**：运行环境提供 `recon` 时，最小快照后每台主机跑一次默认 Profile，报告和快照自动存入 Artifacts；再只对快照未覆盖的基线项和 `partial` 状态的模块补 `run`。快照只记录客观状态，判断由调查完成；`hunt` Profile 需要时请操作者在 WebUI 运行。没有 `recon` 时逐项采集：系统信息、时间与主机名、高 CPU 进程、当前连接、监听端口、登录历史、定时任务概览、相关临时目录变动、云助手子孙进程九类。按 Linux/Windows/容器及权限选等价只读检查，不适用或不可获取的项写明原因；临时目录时间窗依据事件线索，不固定近 24h。云助手祖先只触发 `references/tech_cloud.md` 的任务关联核验。
3. **排查清单**：按 `references/findings_spec.md`「排查清单位置」建立，维度见 SKILL.md 步骤 2。每项在「问题或待证断言」写当前假设，在「下一步动作」写最短必要证据及资产与时间范围；会改变事件定性、影响范围或处置建议的项排前面。

**调用效率**：每轮只并行互不依赖且成本可控的检查，耗时扫描不与易失证据挤同一批；输出小且互不依赖的基线检查可用 `;` 合并为一次调用，预估总输出保持在截断阈值内。结果仍有效且范围相同时直接复用，重复采集必须说明状态变化或新时段。

发现正在加密、持续外传等紧急迹象时，先对决定动作的最小断言执行步骤 7 的定向核验，及时告知已知事实、限制和建议；继续推进调查，不等全部主机定稿，也不越过只读处置边界。

## 步骤 3.1 调查闭环细则

推进与收尾规则以 SKILL.md「调查闭环与停止条件」为准，本节只补细则。

- **单轮格式**：`问题/断言 → 查询身份与范围 → 新证据或缺口 → 确认/反驳/降级 → 下一步`，按 `references/findings_spec.md` 写回清单和 findings，再选下一项。互不依赖的项同批并行。分支只会增加原始输出时，同样只停该分支并记缺口。
- **新项**：新证据引出的新主机、新身份、新 IoC、更早或更晚的时间窗都追加为新项。
- **受阻**：受阻指等客户数据、授权、主机上线或控制台登录。运行时支持异步提问时不等回复。不把补齐受阻项写成其他项的前提。
- **全部受阻**：交付阶段结论时，受阻项按缺口披露并列出所需事项；用户补齐后回到清单继续。
- **超出只读护栏**：同需要处置授权，说明所需授权与影响后结束回合。
- **用户中途提问**：排查目标未变时，答完回到清单继续。

调查指南的命令只是参考，按实际线索调整参数。

## 步骤 3.2 阿里云云侧交叉验证

主机证据不足或需交叉验证时，按 SKILL.md「云侧分层」和 `references/cloud_log_queries.md` 选择证据源；`$sas` 告警查询按步骤 1.2。委派时只传目标 UID、已确认的站点/地域、资产标识、时间窗、待验证的清单项和已知 IoC，不传整段对话；回传按 `references/findings_spec.md` 的证据记录格式，原始大日志先在委派侧收窄。`aliyun` 由编排者直接调用，不委派。只调用已安装的 skill，查询语法、参数与适配器由对应 skill 管理；不可用时记录覆盖缺口，不用本地 shell 或 SSH 做主机取证，不绕开 `opencli-aliyun-ir` 直接操作浏览器，也不用未列入「云侧分层」的云 CLI。控制台截图等步骤 7 验证门过完再按 `references/findings_spec.md`「证据截图」委派。

## 步骤 4 入口与漏洞定位（按证据）

先判断证据支持的初始入口。只有证据指向漏洞利用时，才识别漏洞类型、受影响组件与版本、Payload，并用运行环境提供的联网检索工具核对 CVE、Exploit 与修复方案；不可联网时说明未做外部验证。入口是凭证滥用、合法工具滥用、配置暴露或社会工程时，记录该入口并写「未发现需要绑定的漏洞」；入口证据不足写「无法确认」。不得为了字段完整或告警名称强行匹配 CVE。

## 步骤 5 攻击链重建

按 ATT&CK 战术阶段映射并构建时间线。编号基准为 MITRE ATT&CK v18。优先用具体子技术编号；每条映射有证据支撑，同一行为可跨多个战术（如定时任务属执行/持久化/权限提升）；未涉及的战术在文字映射里省略（报告矩阵版式固定，由 dossier skill 按模板处理）。

运行环境提供 `case_update` 时，时间节点和 ATT&CK 映射写入 Case Board 的 `events`，规则见 `references/findings_spec.md`「攻击时间线位置」。证据落地的当轮就写，不等到本步骤才集中补。进入步骤 6 前，Case Board 必须已有事件的时间节点；确实无法定时的问题留在清单并记为缺口。

## 步骤 6 遗留风险排查

六维名称见 SKILL.md 步骤 6。先复用步骤 2–5 仍有效的结果，再补缺；未查/失败/截断不能填成「未观察到」。Linux 轻量检查包括相关临时目录、全用户 crontab、systemd/rc.local/init.d、passwd/authorized_keys/sudoers.d、当前连接，以及 `ld.so.preload`/profile 中的 `LD_PRELOAD`，合并调用同步骤 2「调用效率」；Windows 与容器按等价维度，缺工具或权限则记录限制。云侧事件按 `references/tech_cloud.md`「AK 泄露利用方式总结」对应 API 核查，无可疑信号的维度只做最小核查（如 AK 最近使用）并写明范围。

包完整性先核验证据涉及的二进制及所属包；发现工具替换、包级异常或必须排除更广篡改时再做 `rpm -Va`/`dpkg -V`。全盘搜索、全包校验与大日志扫描须先写出待证问题和范围，逐级扩大；超时按「SIREN 异常处理」降级，不将未完成扫描视为阴性。

任一维返回可疑项时，按下表深入排查：

| 可疑发现 | 下一步 |
|---|---|
| 新增 UID < 1000 的账户，或 root 同 UID 的别名账户 | 查该账户的登录历史（`last -F <user>`）+ sudo 日志（`/var/log/auth.log` / `/var/log/secure`） |
| `/etc/ld.so.preload` 非空，或 `LD_PRELOAD` 出现在 profile/bashrc | 立即检查所指共享库的路径、属主、创建时间和 `md5sum`/`sha256sum`，做 VirusTotal 比对 |
| 异常 systemd unit（最近 30 天落地，或属主非 root，或 `ExecStart` 指向 `/tmp`/`/home`） | 看 `ExecStart`、`User=`、`WorkingDirectory=`、unit 文件落地时间；交叉验证启动日志 `journalctl -u <unit>` |
| `rpm -Va` / `dpkg -V` 标关键二进制被改（`/bin/ps`, `/bin/ls`, `/usr/bin/find`, `/usr/sbin/sshd`, `/bin/netstat`） | 高度怀疑 rootkit 或命令替换 → **读取 `references/tech_attack_countermeasures.md`** 转入反制 |
| `authorized_keys` 出现非预期公钥，或 `sudoers.d/` 出现非预期文件 | 提取公钥指纹和 sudoer 规则；查该文件落地时间和 `last` 登录记录交叉 |
| `/var/log/aliyun/assist/` 近期出现非预期 RunCommand task（攻击窗口内执行、命令含外网下载/改 cron/改 sshd_config 等） | 提取 task/invocation、实例、命令和时间戳 → 按 `references/tech_cloud.md` 核验云侧事件、调用身份与凭据滥用 |

## 运行机制

不同运行时的工具名称可能不同，按环境实际暴露的等价工具执行，不因名称不完全一致跳过流程。

### 工具可用性

- **Case Board**：`case_read`/`case_update` 只在 SIREN AIR 的 Project 端点提供；Raven 等其他运行时没有这些工具，按 `references/findings_spec.md`「排查清单位置」使用 Markdown 清单。
- **多 Agent 分工**：`delegate` 只在 SIREN AIR 的 Project 端点提供。何时派和收到结果后的核对见 SKILL.md「多 Agent 分工」，参数和 worker 的行为以 `delegate` 的工具说明为准；worker 的规则由 SIREN 写在它的首条提示里。
- **证据保存**：`save_evidence` 把 `audit_id` 对应的结果原样存入 Project 的 `evidence/`，只在 SIREN AIR 的 Project 端点提供；其他运行时把决定性原文写进 findings 证据记录。
- **run 结果文件**：SIREN 的 Project 端点把每次有输出的 run 存为 Project 目录的 `runs/<audit_id>.txt`，文件头记录主机、命令和时间，之后是完整输出；用本地文件工具读取和搜索。其他端点不保存完整输出，超出预览的部分用完整输出模式或缩小命令重取。
- **子 agent**：隔离大输出或做独立核验与结论交付时，用运行环境的 subagent / 委托机制。调查与核验子 agent 同受只读护栏约束，能访问 SIREN 就让它跑定向只读命令，不能就只处理传入的证据文本；结论 writer 不得访问 SIREN。运行时不提供子 agent 时按内联方式降级，不跳过对应步骤。

### 大输出与截断

大日志、目录搜索、SLS 大结果先按待证问题限定资产、时间和字段；预估仍大时才派子 agent 读取，回传决定性原文和 `references/findings_spec.md` 规定的证据记录，不只给结论。内联降级遵守同一完整性要求。

每次读取先检查命令退出状态及工具的 `truncated`、`shown_ranges`、`omitted_ranges` 等实际返回字段；头尾预览不代表全量，`wc -l` 也不能证明传输未截断。字段未提供时记「完整性未知」，不得猜为完整。截断后优先按时间/条件分块补读，必要时使用工具实际支持的完整输出模式并再次检查；仍有省略就记录未读范围，不凭已展示部分断言没有其他命中。错误输出、权限拒绝与空结果分开处理。

- **run_batch**：每台预览 1 KiB；结果被截断时返回 `path`（`runs/<audit_id>.txt`）和正文起始行 `body_start_line`，按此读文件，不为补读重跑命令。需保留的大段原文按运行环境既有证据规则落盘（如 AIR 的 `evidence/`），之后用 `grep`/`sed -n` 读片段，不整文件回读。
- **exec 脚本**：Codex 经 exec 脚本调工具时只取 `structuredContent` 中需要的字段（如 `outcome`、`truncated`、`omitted_ranges`、`audit_id` 与所需输出片段），不 `text()` 整个结果；首行声明 `// @exec: {"max_output_tokens": N}`。
- **图片**：默认 `detail: "low"`；需读小字才用 `view_image` 的 `original`，且一次一张。

### 本地长任务

本节只适用于 agent 所在环境的本地脚本，如云 API 翻页和 SLS 批量查询。经 SIREN 在受害主机上执行的命令不适用本节。

- 预计运行超过 60 秒或总页数未知时，不跑同步前台命令。用 `nohup` 在后台运行，每页结果立即追加到工作目录的 JSONL，并写入翻页游标和完成标记。
- 用短命令读取进度，不用长 `sleep` 等待。等待期间继续做不依赖该结果的排查项。
- 前台命令超时且没有可用输出时，不缩小窗口重跑同一脚本。改为后台运行，并从游标续跑。

### SIREN 异常处理

- SIREN 超时/失败：简化命令重试一次，仍失败则跳过并记录为证据缺口；不换写法反复跑同一重扫描。命令默认 30 秒超时；大目录 `find`、大日志 `journalctl`/`zgrep` 这类确实需要更久的扫描，先缩小范围，仍不够再用 `timeout_seconds`（上限 120）重试一次。客户端一次只跑一条命令，长命令会让其他会话排队
- Client busy：多个会话同查一台主机时，`run`/`run_batch` 排队约两分钟才报 busy；隔一会儿重试同一命令，不简化、不换写法重扫
- 客户端断线：告知用户，等待重连或切换备用客户端
- 日志被清除：标注后转向其他证据源（进程、网络、文件时间戳）
