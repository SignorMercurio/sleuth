# 运行机制（跨客户端工具映射 / 子 agent / SIREN 异常）

本 skill 兼容 Claude Code 与 Codex。不同客户端的工具界面名称可能不同，按下列映射执行，不要因为名称不完全一致而跳过流程。

## 按需加载

若读不到 skill 目录文件，以 SKILL.md 常驻内容继续执行并披露缺失细则，不凭记忆编造规则，不跳过验证门与报告确认门。

## 跨客户端工具映射

- **读取本 skill 文件**：用本地文件读取工具读相对 skill 根目录的 `references/...` 或 `assets/...`。
- **SIREN MCP**：使用环境实际暴露的 list client / remote run 等价工具；名称与只读边界以 SKILL.md 为准。
- **Case Board**：`case_read`/`case_update`/`case_handoff` 只在 SIREN AIR 的 Project 端点提供（`case_handoff` 仅 Case Run 的 worker 会话可用，见「多 Agent 角色」）；Raven 等其他运行时没有这些工具，按 `references/findings_spec.md`「排查清单位置」使用 Markdown 清单。
- **主机快照**：`recon` 由运行环境提供时按 `references/workflow_recon.md` 步骤 2 使用；`hunt` Profile 只有操作者能在 WebUI 运行。
- **证据保存**：`save_evidence` 把 `audit_id` 对应的结果原样存入 Project 的 `evidence/`，只在 SIREN AIR 的 Project 端点提供；其他运行时把决定性原文写进 findings 证据记录。
- **跨结果搜索**：`search_run_result` 不带 `audit_id` 时，只有 SIREN 的 Project 端点支持，返回 24 小时内的 run 摘要；其他端点按已记录的 `audit_id` 读取。
- **调用云侧 skill**：只调用已安装的 skill，路由与委派契约见 `references/workflow_tracing.md` 步骤 3.2；参数格式、默认值、分页和支持区域由对应 skill 管理。`aliyun` 是命令行工具，不是 skill：先运行 `aliyun configure list`，空列表表示当前 Project 没有 AccessKey；有多个 profile 时每条命令带 `--profile <名称>`。Raven 等没有 Project AccessKey 的运行时跳过这一层。全部不可用则记录覆盖缺口，不用未列入 SKILL.md「云侧分层」的云 CLI。模式一缺 `$sas` 时向用户索取告警摘要，区分用户提供与独立核验的事实；拿不到摘要则按模式二继续。
- **联网查询**：需要查 CVE、Exploit 或修复方案时，使用运行环境提供的搜索工具、浏览器或官方/可信来源检索工具；不可联网时说明该部分未做外部验证。
- **派生子 agent**：隔离大输出（步骤 3）或独立核验与结论交付（步骤 7）时用运行环境的 subagent / 委托机制。调查与核验子 agent 同受只读护栏约束，能访问 SIREN 就让它跑定向只读命令，不能就只处理传入的证据文本；结论 writer 不得访问 SIREN。运行时不提供子 agent 时按各节的内联方式降级，不跳过对应步骤。

## 多 Agent 角色（SIREN Case Run）

SIREN 以 Case Run 方式启动调查时，会话的首条提示注明角色。角色由 SIREN 分派，会话自己不切换角色，也不替其他角色推进。角色会话按本节收尾，不按 `references/workflow_tracing.md`「调查闭环与停止条件」。

- **Lead**：kickoff 回合只做步骤 1–2：用 `case_update` 建清单、写 summary，给每项指定 `owner`（`entry`/`host`/`cloud`），只有必须由 Lead 裁决的项才把 `owner` 留为 `lead`；要等别的项先有结果的项按 worker 的规则标 `blocked`。清单建好就结束回合。所有 worker 都停下后 SIREN 用新提示唤醒 Lead：先 `case_read`，逐项核对 confirmed/refuted 的证据是否支撑结论，只裁决不取证；证据不够的项改回 `open`、`owner` 指回对应 worker 并在 `next_action` 写明还缺什么，然后结束回合，等 SIREN 再次唤醒；没有退回时改写 summary，写 findings 并交付。
- **Entry / Host / Cloud worker**：同一角色可能有几个会话并行，每个会话分到最多两项。只改分给自己的项，同角色其他会话正在推进的项会被拒绝，自己新建的项归自己；按步骤 2–6 取证，不写 summary，不生成报告。每一项一有结果就立刻用 `case_update` 写回状态和证据，按 `references/findings_spec.md`「写回规则」补齐该状态要求的字段，不攒到回合末：只有 Board 上的内容能传给 Lead 和接手的新会话，回合超时或会话关闭后没写回的全部丢失。发现属于其他角色的线索时，新建一项，`dimension` 用 `lead`，`owner` 指给对应 worker；不能把自己的项改给别的角色。工具、凭据、环境问题只在自己的项上记 `gap` 或 `blocked`，不为此新建 `owner` 为 `lead` 的项。等的是 Board 上另一项时把那项编号写进 `blocked_by`，那项结束后 SIREN 会把本项派回来；只等操作员的 blocked 项交给 Lead。每项推进到无法再前进（confirmed、refuted、gap、blocked）后调用 `case_handoff(note, remaining)` 写一句收尾和剩余项编号，然后结束回合，收尾后不开始新工作。回合快到时间上限时 SIREN 会插入收尾提醒：收到后停止取证，把手头证据写回 Board，`case_handoff` 并结束回合。
- **再次唤醒**：worker 会话独立调度，不等其他角色。回合结束后，Board 有进展（有项改变了状态或 owner）且你仍有 open/active 项时，SIREN 在原会话里再次唤醒你，已取过的证据不用重取；只追加证据或改写 `next_action` 不算进展。blocked 项不会派给 worker。一个回合做不完就如实 handoff，下次唤醒接着做。

## 重输出隔离（调查子 agent）

大日志、目录搜索、SLS 大结果先按待证问题限定资产、时间和字段；预估仍大时才派子 agent 读取，回传决定性原文和 `references/findings_spec.md` 规定的证据记录，不只给结论。内联降级遵守同一完整性要求。

每次读取先检查命令退出状态及工具的 `truncated`、`shown_ranges`、`omitted_ranges` 等实际返回字段；头尾预览不代表全量，`wc -l` 也不能证明传输未截断。字段未提供时记「完整性未知」，不得猜为完整。截断后优先按时间/条件分块补读，必要时使用工具实际支持的完整输出模式并再次检查；仍有省略就记录未读范围，不凭已展示部分断言没有其他命中。错误输出、权限拒绝与空结果分开处理。

## 上下文预算

- **exec 脚本**：Codex 经 exec 脚本调工具时只取 `structuredContent` 中需要的字段（如 `outcome`、`truncated`、`omitted_ranges`、`audit_id` 与所需输出片段），不 `text()` 整个结果；首行声明 `// @exec: {"max_output_tokens": N}`。
- **大输出**：`run_batch` 每台预览 1 KiB；`audit_id` 用 `search_run_result` 定位、`read_run_result` 按字节范围补读，结果 24 小时后过期，SIREN 服务重启后清空。需保留的大段原文按运行环境既有证据规则落盘（如 AIR 的 `evidence/`），之后用 `grep`/`sed -n` 读片段，不整文件回读。
- **图片**：需读小字才用 `view_image` 的 `original`，且一次一张。

## 本地长任务

本节只适用于 agent 所在环境的本地脚本，如云 API 翻页和 SLS 批量查询。经 SIREN 在受害主机上执行的命令不适用本节。

- 预计运行超过 60 秒或总页数未知时，不跑同步前台命令。用 `nohup` 在后台运行，每页结果立即追加到工作目录的 JSONL，并写入翻页游标和完成标记。
- 用短命令读取进度，不用长 `sleep` 等待。等待期间继续做不依赖该结果的排查项。
- 前台命令超时且没有可用输出时，不缩小窗口重跑同一脚本。改为后台运行，并从游标续跑。

## SIREN 异常处理

- SIREN 超时/失败：简化命令重试一次，仍失败则跳过并记录为证据缺口；不换写法反复跑同一重扫描
- Client busy：多个会话同查一台主机时，`run`/`run_batch` 排队最多 90 秒才报 busy；隔一会儿重试同一命令，不简化、不换写法重扫
- 客户端断线：告知用户，等待重连或切换备用客户端
- 日志被清除：标注后转向其他证据源（进程、网络、文件时间戳）
