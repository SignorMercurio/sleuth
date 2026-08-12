# 运行机制（跨客户端工具映射 / 子 agent / SIREN 异常）

本 skill 兼容 Claude Code 与 Codex。不同客户端的工具界面名称可能不同，按下列映射执行，不要因为名称不完全一致而跳过流程。

## 跨客户端工具映射

- **读取本 skill 文件**：读取相对当前 skill 根目录的 `references/...` 或 `assets/...` 文件；Claude Code 可用 Read，Codex 可用本地文件读取工具。
- **SIREN MCP**（主线，远程只读取证）：SLEUTH 只使用 `mcp__siren__ls`、`mcp__siren__run`。仅在运行环境实际暴露了其他名称时才使用等价的 list client、remote run 工具；不要臆造 `list_clients`、`exec`、`wait` 等未加载工具。即使运行环境自动批准了 `deploy` 或其他写操作，也不得调用。若完全不可用，告知用户缺少 SIREN MCP 并结束，不要改用本地 shell/SSH 代替。
- **调用 `$sas` skill**：模式一只调用已安装的 `$sas` skill，不直接执行 SAS CLI；选择器、列表 / 详情分支与多告警范围按 SKILL 步骤 1.2，参数默认值、格式、分页和支持区域由 `$sas` 管理。若不可用，说明告警上下文缺口并向用户索取告警摘要；仍拿不到则按模式二继续，不要改用本地 shell、SSH 或其他云 CLI。
- **调用云侧 skill**：按步骤 3.2 保持 `$sas` 告警、`sls` 已投递日志、只读 `opencli-aliyun-ir` 控制面/专用能力的优先级。只传 UID、站点/地域、资产标识、时间窗、待验证问题和必要 IoC；前一层覆盖不了才进入下一层。全部不可用则跳过并在报告说明，不直接执行 OpenCLI、SLS CLI、本地 shell 或 SSH。
- **联网查询**：需要查 CVE、Exploit 或修复方案时，使用运行环境提供的搜索工具、浏览器或官方/可信来源检索工具；不可联网时说明该部分未做外部验证。
- **派生子 agent**：需要隔离大输出（步骤 3）、做独立结论核验（步骤 7）或隔离报告写作上下文（步骤 8）时，使用运行环境提供的 subagent / 委托机制（Claude Code 的 Agent 工具；Codex 的等价子 agent 机制）。调查与核验子 agent 同受只读安全护栏约束，且未必能访问 SIREN MCP——能访问就让它跑定向只读命令，不能就只处理传入的证据文本；报告 writer 不得访问 SIREN。运行时完全不提供子 agent 时按各节的内联方式降级，不要因此跳过对应步骤。

## 报告写作隔离（步骤 8）

运行时支持子 agent 时，默认派生一个全新 writer 生成报告。只给 writer 以下文件路径，不传调查对话、工具输出、编排者推理或预期答案：

- 全部 findings 文件
- `assets/report.md`
- `assets/style/curated-ir-excerpts.md`
- `references/findings_spec.md`
- `references/report_naming.md`
- `references/report_style.md`
- `references/report_writing_rules.md`

writer 只读取这些文件，只创建最终一份 `IR-….md` 报告，不调用 SIREN、SAS、SLS 或联网工具。发现严重等级、当前状态、处置进展等必填内容缺失时停止定稿，把缺口返回编排者。

writer 完成后先自检，编排者再按相同边界复核：

1. 按 `references/findings_spec.md` 检查事实边界、措辞等级、严重等级与处置进展
2. 按模板 HTML 注释检查原有标题、`:::` 指令块、占位符和各块内容
3. 按 `references/report_writing_rules.md` 检查跨章节分工、内部标识、IoC、样本串案与重复
4. 按 `references/report_style.md` 通读中文，清理不自然或机械化表达

QA 结果只返回编排者。全部通过才交付报告；失败就修报告，事实或必填字段缺失则回到步骤 2–7。运行时不支持子 agent 时，编排者重新读取上述文件后内联写作，仍执行相同自检，不凭会话记忆补事实。

## 重输出隔离（调查子 agent）

当某条命令/查询会返回大输出（大日志、全盘 `find`、SLS 大结果集）时，优先派一个子 agent 去读原始输出、只回传结论 + IoC + 决定性的几行，保持编排者上下文精简（见本文「跨客户端工具映射」的派生子 agent 项）。运行时不提供子 agent、或子 agent 拿不到 SIREN 时，按只读护栏内联降级：先 `wc -l` 评估，再 `head`/`tail`/`grep` 收窄。

## SIREN 异常处理

- SIREN 超时/失败：简化命令重试一次，仍失败则跳过并在报告中标注
- 客户端断线：告知用户，等待重连或切换备用客户端
- 日志被清除：标注后转向其他证据源（进程、网络、文件时间戳）
