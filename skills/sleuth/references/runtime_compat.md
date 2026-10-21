# 运行机制（跨客户端工具映射 / 子 agent / SIREN 异常）

本 skill 兼容 Claude Code 与 Codex。不同客户端的工具界面名称可能不同，按下列映射执行，不要因为名称不完全一致而跳过流程。

## 按需加载

若读不到 skill 目录文件，以 SKILL.md 常驻内容继续执行并披露缺失细则，不凭记忆编造规则，不跳过验证门与报告确认门。

## 跨客户端工具映射

- **读取本 skill 文件**：用本地文件读取工具读相对 skill 根目录的 `references/...` 或 `assets/...`。
- **SIREN MCP**：使用环境实际暴露的 list client / remote run 等价工具；名称与只读边界以 SKILL.md 为准。
- **调用云侧 skill**：只调用已安装的 skill，路由与委派契约见 `references/workflow_tracing.md` 步骤 3.2；参数格式、默认值、分页和支持区域由对应 skill 管理。不可用则记录覆盖缺口，不自行执行云 CLI。模式一缺 `$sas` 时向用户索取告警摘要，区分用户提供与独立核验的事实；拿不到摘要则按模式二继续。
- **联网查询**：需要查 CVE、Exploit 或修复方案时，使用运行环境提供的搜索工具、浏览器或官方/可信来源检索工具；不可联网时说明该部分未做外部验证。
- **生成图片**：Codex 用内置图片生成工具，生成后复制到目标路径；Claude Code 在本地用 `codex exec --skip-git-repo-check -s workspace-write -C <工作目录> "<提示词>"` 转调，提示词里写明保存路径。
- **派生子 agent**：隔离大输出（步骤 3）、独立核验与结论交付（步骤 7）或隔离写作（步骤 8）时用运行环境的 subagent / 委托机制。调查与核验子 agent 同受只读护栏约束，能访问 SIREN 就让它跑定向只读命令，不能就只处理传入的证据文本；writer 不得访问 SIREN。运行时不提供子 agent 时按各节的内联方式降级，不跳过对应步骤。

## 重输出隔离（调查子 agent）

大日志、目录搜索、SLS 大结果先按待证问题限定资产、时间和字段；预估仍大时才派子 agent 读取，回传决定性原文和 `references/findings_spec.md` 规定的证据记录，不只给结论。内联降级遵守同一完整性要求。

每次读取先检查命令退出状态及工具的 `truncated`、`shown_ranges`、`omitted_ranges` 等实际返回字段；头尾预览不代表全量，`wc -l` 也不能证明传输未截断。字段未提供时记「完整性未知」，不得猜为完整。截断后优先按时间/条件分块补读，必要时使用工具实际支持的完整输出模式并再次检查；仍有省略就记录未读范围，不凭已展示部分断言没有其他命中。错误输出、权限拒绝与空结果分开处理。

## 上下文预算

- **exec 脚本**：Codex 经 exec 脚本调工具时只取 `structuredContent` 中需要的字段（如 `outcome`、`truncated`、`omitted_ranges`、`audit_id` 与所需输出片段），不 `text()` 整个结果；首行声明 `// @exec: {"max_output_tokens": N}`。
- **大输出**：`run_batch` 每台预览 1 KiB；`audit_id` 用 `search_run_result` 定位、`read_run_result` 按字节范围补读，结果 60 分钟后过期。需保留的大段原文按运行环境既有证据规则落盘（如 AIR 的 `evidence/`），之后用 `grep`/`sed -n` 读片段，不整文件回读。
- **图片**：需读小字才用 `view_image` 的 `original`，且一次一张。

## SIREN 异常处理

- SIREN 超时/失败：简化命令重试一次，仍失败则跳过并记录为证据缺口；不换写法反复跑同一重扫描
- 客户端断线：告知用户，等待重连或切换备用客户端
- 日志被清除：标注后转向其他证据源（进程、网络、文件时间戳）
