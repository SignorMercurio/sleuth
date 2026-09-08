# 运行机制（跨客户端工具映射 / 子 agent / SIREN 异常）

本 skill 兼容 Claude Code 与 Codex。不同客户端的工具界面名称可能不同，按下列映射执行，不要因为名称不完全一致而跳过流程。

## 按需加载

按 SKILL.md 的流程入口读取当前步骤细则，调查指南与写作规则同样按需加载。

若读不到 skill 目录文件，以 SKILL.md 常驻内容继续执行并披露缺失细则，不凭记忆编造规则，不跳过验证门与报告确认门。

## 跨客户端工具映射

- **读取本 skill 文件**：读取相对当前 skill 根目录的 `references/...` 或 `assets/...` 文件；Claude Code 可用 Read，Codex 可用本地文件读取工具。
- **SIREN MCP**：使用环境实际暴露的 list client / remote run 等价工具；名称与只读边界以 SKILL.md 为准。
- **调用云侧 skill**：只调用已安装的 skill，路由与委派契约见 `references/workflow_tracing.md` 步骤 3.2；参数格式、默认值、分页和支持区域由对应 skill 管理。不可用则记录覆盖缺口，不自行执行云 CLI。模式一缺 `$sas` 时向用户索取告警摘要，区分用户提供与独立核验的事实；拿不到摘要则按模式二继续。
- **联网查询**：需要查 CVE、Exploit 或修复方案时，使用运行环境提供的搜索工具、浏览器或官方/可信来源检索工具；不可联网时说明该部分未做外部验证。
- **派生子 agent**：需要隔离大输出（步骤 3）、做独立结论核验（步骤 7）或隔离报告写作上下文（步骤 8）时，使用运行环境提供的 subagent / 委托机制（Claude Code 的 Agent 工具；Codex 的等价子 agent 机制）。调查与核验子 agent 同受只读安全护栏约束，且未必能访问 SIREN MCP——能访问就让它跑定向只读命令，不能就只处理传入的证据文本；报告 writer 不得访问 SIREN。运行时完全不提供子 agent 时按各节的内联方式降级，不要因此跳过对应步骤。

## 报告写作隔离（步骤 8，用户确认后）

未通过步骤 7 的报告确认门时不运行 writer。用户确认后，运行时支持子 agent 时默认派生一个全新 writer 生成报告。只给 writer 以下文件路径，不传调查对话、工具输出、编排者推理或预期答案：

- 全部 findings 文件
- `assets/report.md`
- `assets/style/curated-ir-excerpts.md`
- `references/findings_spec.md`
- `references/report_naming.md`
- `references/report_style.md`
- `references/report_writing_rules.md`

writer 只读取这些文件，只创建最终一份 `IR-….md` 报告，不调用 SIREN、SAS、SLS、OpenCLI 或联网工具。发现严重等级、当前状态、处置进展等必填内容缺失时停止定稿，把缺口返回编排者。

writer 完成后先自检，编排者再按相同边界复核：

1. 按 `references/findings_spec.md` 检查事实边界、措辞等级、严重等级与处置进展
2. 按模板 HTML 注释检查原有标题、`:::` 指令块、占位符和各块内容；图片引用逐条核对路径出现在 findings 且文件存在
3. 按 `references/report_writing_rules.md` 检查跨章节分工、证据实体下限、内部标识、IoC、样本串案与重复
4. 按 `references/report_style.md` 通读中文，清理不自然或机械化表达

QA 结果只返回编排者。全部通过才交付报告；失败就修报告，事实或必填字段缺失则回到步骤 2–7。运行时不支持子 agent 时，编排者重新读取上述文件后内联写作，仍执行相同自检，不凭会话记忆补事实。

## 重输出隔离（调查子 agent）

大日志、目录搜索、SLS 大结果先按待证问题限定资产、时间和字段；预估仍大时才派子 agent 读取，回传决定性原文和 `references/findings_spec.md` 规定的证据记录，不只给结论。内联降级遵守同一完整性要求。

每次读取先检查命令退出状态及工具的 `truncated`、`shown_ranges`、`omitted_ranges` 等实际返回字段；头尾预览不代表全量，`wc -l` 也不能证明传输未截断。字段未提供时记「完整性未知」，不得猜为完整。截断后优先按时间/条件分块补读，必要时使用工具实际支持的完整输出模式并再次检查；仍有省略就记录未读范围，不凭已展示部分断言没有其他命中。错误输出、权限拒绝与空结果分开处理。

## SIREN 异常处理

- SIREN 超时/失败：简化命令重试一次，仍失败则跳过并记录为证据缺口；不换写法反复跑同一重扫描
- 客户端断线：告知用户，等待重连或切换备用客户端
- 日志被清除：标注后转向其他证据源（进程、网络、文件时间戳）
