# 运行机制（跨客户端工具映射 / 子 agent / SIREN 异常）

本 skill 兼容 Claude Code 与 Codex。不同客户端的工具界面名称可能不同，按下列映射执行，不要因为名称不完全一致而跳过流程。

## 按需加载

若读不到 skill 目录文件，以 SKILL.md 常驻内容继续执行并披露缺失细则，不凭记忆编造规则，不跳过验证门与报告确认门。

## 跨客户端工具映射

- **读取本 skill 文件**：用本地文件读取工具读相对 skill 根目录的 `references/...` 或 `assets/...`。
- **SIREN MCP**：使用环境实际暴露的 list client / remote run 等价工具；名称与只读边界以 SKILL.md 为准。
- **Case Board**：`case_read`/`case_update` 只在 SIREN AIR 的 Project 端点提供；Raven 等其他运行时没有这些工具，按 `references/findings_spec.md`「排查清单位置」使用 Markdown 清单。
- **多 Agent 分工**：`delegate` 只在 SIREN AIR 的 Project 端点提供。何时派和收到结果后的核对见 SKILL.md「多 Agent 分工」，参数和 worker 的行为以 `delegate` 的工具说明为准；worker 的规则由 SIREN 写在它的首条提示里。
- **主机快照**：`recon` 由运行环境提供时按 `references/workflow_recon.md` 步骤 2 使用；`hunt` Profile 只有操作者能在 WebUI 运行。
- **证据保存**：`save_evidence` 把 `audit_id` 对应的结果原样存入 Project 的 `evidence/`，只在 SIREN AIR 的 Project 端点提供；其他运行时把决定性原文写进 findings 证据记录。
- **run 结果文件**：SIREN 的 Project 端点把每次有输出的 run 存为 Project 目录的 `runs/<audit_id>.txt`，文件头记录主机、命令和时间，之后是完整输出；用本地文件工具读取和搜索。其他端点不保存完整输出，超出预览的部分用完整输出模式或缩小命令重取。
- **调用云侧 skill**：只调用已安装的 skill，路由与委派契约见 `references/workflow_tracing.md` 步骤 3.2；参数格式、默认值、分页和支持区域由对应 skill 管理。`aliyun` 是命令行工具，不是 skill：先运行 `aliyun configure list`，空列表表示当前 Project 没有 AccessKey；有多个 profile 时每条命令带 `--profile <名称>`。Raven 等没有 Project AccessKey 的运行时跳过这一层。全部不可用则记录覆盖缺口，不用未列入 SKILL.md「云侧分层」的云 CLI。模式一缺 `$sas` 时向用户索取告警摘要，区分用户提供与独立核验的事实；拿不到摘要则按模式二继续。
- **联网查询**：需要查 CVE、Exploit 或修复方案时，使用运行环境提供的搜索工具、浏览器或官方/可信来源检索工具；不可联网时说明该部分未做外部验证。
- **派生子 agent**：隔离大输出（步骤 3）或独立核验与结论交付（步骤 7）时用运行环境的 subagent / 委托机制。调查与核验子 agent 同受只读护栏约束，能访问 SIREN 就让它跑定向只读命令，不能就只处理传入的证据文本；结论 writer 不得访问 SIREN。运行时不提供子 agent 时按各节的内联方式降级，不跳过对应步骤。

## 重输出隔离（调查子 agent）

大日志、目录搜索、SLS 大结果先按待证问题限定资产、时间和字段；预估仍大时才派子 agent 读取，回传决定性原文和 `references/findings_spec.md` 规定的证据记录，不只给结论。内联降级遵守同一完整性要求。

每次读取先检查命令退出状态及工具的 `truncated`、`shown_ranges`、`omitted_ranges` 等实际返回字段；头尾预览不代表全量，`wc -l` 也不能证明传输未截断。字段未提供时记「完整性未知」，不得猜为完整。截断后优先按时间/条件分块补读，必要时使用工具实际支持的完整输出模式并再次检查；仍有省略就记录未读范围，不凭已展示部分断言没有其他命中。错误输出、权限拒绝与空结果分开处理。

## 上下文预算

- **exec 脚本**：Codex 经 exec 脚本调工具时只取 `structuredContent` 中需要的字段（如 `outcome`、`truncated`、`omitted_ranges`、`audit_id` 与所需输出片段），不 `text()` 整个结果；首行声明 `// @exec: {"max_output_tokens": N}`。
- **大输出**：`run_batch` 每台预览 1 KiB；结果被截断时返回 `path`（`runs/<audit_id>.txt`）和正文起始行 `body_start_line`，按此读文件，不为补读重跑命令。需保留的大段原文按运行环境既有证据规则落盘（如 AIR 的 `evidence/`），之后用 `grep`/`sed -n` 读片段，不整文件回读。
- **图片**：默认 `detail: "low"`；需读小字才用 `view_image` 的 `original`，且一次一张。

## 本地长任务

本节只适用于 agent 所在环境的本地脚本，如云 API 翻页和 SLS 批量查询。经 SIREN 在受害主机上执行的命令不适用本节。

- 预计运行超过 60 秒或总页数未知时，不跑同步前台命令。用 `nohup` 在后台运行，每页结果立即追加到工作目录的 JSONL，并写入翻页游标和完成标记。
- 用短命令读取进度，不用长 `sleep` 等待。等待期间继续做不依赖该结果的排查项。
- 前台命令超时且没有可用输出时，不缩小窗口重跑同一脚本。改为后台运行，并从游标续跑。

## SIREN 异常处理

- SIREN 超时/失败：简化命令重试一次，仍失败则跳过并记录为证据缺口；不换写法反复跑同一重扫描。命令默认 30 秒超时；大目录 `find`、大日志 `journalctl`/`zgrep` 这类确实需要更久的扫描，先缩小范围，仍不够再用 `timeout_seconds`（上限 120）重试一次。客户端一次只跑一条命令，长命令会让其他会话排队
- Client busy：多个会话同查一台主机时，`run`/`run_batch` 排队约两分钟才报 busy；隔一会儿重试同一命令，不简化、不换写法重扫
- 客户端断线：告知用户，等待重连或切换备用客户端
- 日志被清除：标注后转向其他证据源（进程、网络、文件时间戳）
