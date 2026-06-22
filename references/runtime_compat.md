# 运行机制（跨客户端工具映射 / 子 agent / SIREN 异常）

本 skill 兼容 Claude Code 与 Codex。不同客户端的工具界面名称可能不同，按下列映射执行，不要因为名称不完全一致而跳过流程。

## 跨客户端工具映射

- **读取本 skill 文件**：读取相对当前 skill 根目录的 `references/...` 或 `assets/...` 文件；Claude Code 可用 Read，Codex 可用本地文件读取工具。
- **SIREN MCP**（主线，远程只读取证）：优先使用运行环境暴露的 SIREN MCP 工具，通常为 `mcp__siren__ls`、`mcp__siren__run`、`mcp__siren__get_alarm_detail`。若工具名不同，使用等价的 list client、remote run、alarm detail 工具；若完全不可用，告知用户缺少 SIREN MCP 并结束，不要改用本地 shell/SSH 代替。
- **调用其他 skill**：需要 SLS 云端日志时，按步骤 3.2（云端日志查询）调用已安装的 `sls` skill；若不可用则跳过云端查询并在报告说明。
- **联网查询**：需要查 CVE、Exploit 或修复方案时，使用运行环境提供的搜索工具、浏览器或官方/可信来源检索工具；不可联网时说明该部分未做外部验证。
- **派生子 agent**：需要隔离大输出（步骤 3）或做独立结论核验（步骤 7）时，使用运行环境提供的 subagent / 委托机制（Claude Code 的 Agent 工具；Codex 的等价子 agent 机制）。子 agent 同受只读安全护栏约束，且未必能访问 SIREN MCP——能访问就让它跑定向只读命令，不能就只处理传入的证据文本。运行时完全不提供子 agent 时按内联方式降级，不要因此跳过对应步骤。

## 重输出隔离（子 agent）

当某条命令/查询会返回大输出（大日志、全盘 `find`、SLS 大结果集）时，优先派一个子 agent 去读原始输出、只回传结论 + IoC + 决定性的几行，保持编排者上下文精简（见本文「跨客户端工具映射」的派生子 agent 项）。运行时不提供子 agent、或子 agent 拿不到 SIREN 时，按只读护栏内联降级：先 `wc -l` 评估，再 `head`/`tail`/`grep` 收窄。

## SIREN 异常处理

- SIREN 超时/失败：简化命令重试一次，仍失败则跳过并在报告中标注
- 客户端断线：告知用户，等待重连或切换备用客户端
- 日志被清除：标注后转向其他证据源（进程、网络、文件时间戳）
