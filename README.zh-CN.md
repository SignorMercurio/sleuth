# SLEUTH

[English](README.md) | 中文

面向 Claude Code 和 Codex 的安全应急响应 agent skill。通过 SIREN MCP server 在失陷主机上执行只读取证命令，重建攻击链，交付经对抗验证的 MITRE ATT&CK 映射结论。正式事件报告由配套的 `dossier` skill 从已验证 findings 写出，只在用户明确要求时进行。

## 功能

- **调查模式**：告警 / 资产 / 实例维度的定向调查、无告警的自由排查，以及无需 SIREN Client 的云侧调查（AK/STS 凭据滥用、ActionTrail 异常调用、WAF 攻击入口、SAS 告警研判）；核实模式逐条核验既有报告或 findings 的结论
- **能力预检**：调查前探测主机、云侧、子 agent、Web 证据源的可用性；缺失覆盖约束依赖该证据的具体断言
- **分类型调查 playbook**（webshell、挖矿、反弹 shell、暴破、勒索、RCE、SQL 注入、异常登录、数据外泄、持久化、提权）+ **横向技术指南**（日志分析与反向推理、云取证、进程/文件分析、攻击对抗手段）+ 专项指南（云日志路由、SAS/SLS 主机遥测、OOB/DNSLog、SSH 登录溯源）+ **MITRE ATT&CK 映射**。调查指南、ASP.NET 上传追踪与技巧路由表见 `skills/sleuth/references/playbooks.md`
- **并行命令调度**：无依赖关系的远程命令在同一轮发出，压缩调查时间
- **问题驱动证据闭环**：基线扫描后，每轮后续必须回答一个能改变定性、范围或处置的具名问题；不再产出决策相关证据时停止扩张
- **严格只读**：只跑不改系统状态的命令（读文件、列举进程/网络/服务、查日志），绝不执行破坏或安装命令；保全证据完整性
- **对抗验证门**：所有承重断言在交付前经独立反驳（子 agent 或内联），防止错误归因
- **证据触发的漏洞归因**：仅在证据指向漏洞利用时调查 CVE；凭证滥用、配置暴露等非漏洞入口按实际路径报告，不为字段完整强行绑定 CVE
- **持续排查**：按排查清单逐项推进，清单有可执行项时不结束回合；单项受阻只挂起该项，其他项继续。SIREN AIR 把清单和当前结论写入 Case Board，其他运行时写入 findings，会话结束前即可查看进展
- **报告交接**：调查止于已验证结论；正式 `IR-....md` 报告由配套的 `dossier` skill（同级 `dossier` 仓库的 `skills/dossier/`）从 findings 写出，只在用户明确要求时进行
- **隔离写手**：子 agent 可用时，步骤 7 的交付结论由一个全新写手只看已验证 findings 起草，主调度只判通过与否，通过稿原样发送。写手无法访问 SIREN 或调查上下文
- **上下文隔离子 agent**：大输出由子 agent（或内联）收窄，回传决定性证据、范围及截断信息，保持主调度上下文精简
- **多主机委托**：先对已授权主机取最小易失证据快照，再逐台深入；每台持续维护一份 findings，交付前验证；用户要求时由 `dossier` skill 合并为一份报告（见下文*多主机与合并*）
- **控制台截图证据**：已验证的云侧事实可由 `opencli-aliyun-ir` 只读截取控制台截图，记入 findings 并由报告按路径引用

## 前置条件

- **Claude Code 或 Codex**：最新稳定版。skill 遵循开放 agent skills 格式，位于 `skills/sleuth/`（`SKILL.md` + `references/`、`agents/`）。
- **dossier skill**（出正式报告时需要）：把同级 `dossier` 仓库的 `dossier` skill 装进同一个 skills 目录。它从 sleuth 的 findings 生成、合并、修订和审校 `IR-….md`，并读取旁边 sleuth 包里的 `skills/sleuth/references/findings_spec.md`。
- **SIREN MCP server**：主机侧调查依赖 SIREN 的 list-client 和 remote-run 工具（云侧调查不需要），通常暴露为 `mcp__siren__ls` 和 `mcp__siren__run`。使用前需在客户端配置 SIREN 为 MCP server。
- **`$sas` skill**：告警驱动查询必需。
- **可选 `sls` skill**：WAF / SAS / ActionTrail 云日志交叉验证的首选。
- **可选 `aliyun` CLI**：SIREN AIR 的 Project 配有 AccessKey 时，用于云控制面单点只读查询。
- **可选 `opencli-aliyun-ir` skill**：在 `sas` / `sls` 之后用于没有 AccessKey 时的阿里云控制面状态、专用适配器、内部控制台、跨产品关联及覆盖缺口。

## 安装

### Codex：用户级安装

Codex 从 `$HOME/.agents/skills` 发现用户 skill。用 `skills` CLI 从 GitHub 安装：

```bash
npx skills add SignorMercurio/sleuth -y -g -a codex
```

开发期间可用符号链接代替二次克隆：

```bash
mkdir -p ~/.agents/skills
ln -s /path/to/sleuth/skills/sleuth ~/.agents/skills/sleuth
```

Codex 也会从当前目录到仓库根扫描 `.agents/skills` 下的仓库级 skill。

### Claude Code：`npx skills`

使用社区 CLI [vercel-labs/skills](https://github.com/vercel-labs/skills)：

```bash
npx skills add SignorMercurio/sleuth -a claude-code
```

### 手动复制或 rsync

Claude Code 复制到 `~/.claude/skills/sleuth`，Codex 复制到 `~/.agents/skills/sleuth` 或仓库级 `.agents/skills/sleuth`。

```bash
# Codex
rsync -avz ./sleuth/skills/sleuth/ \
  <host>:~/.agents/skills/sleuth/

# Claude Code
rsync -avz ./sleuth/skills/sleuth/ \
  <host>:~/.claude/skills/sleuth/
```

安装后，在 Claude Code 中运行 `/skills`，或在 Codex 中提及 `$sleuth` / 使用 skills 选择器确认 skill 已加载。skill 在上下文匹配时自动激活，也可显式调用。

## 使用

### 告警驱动模式

提供：
- 阿里云租户 **UID**
- 一个 SAS 查询选择器：
  - SAS 告警列表返回的数字告警 **`Id`**
  - 安全中心**资产 UUID**
  - ECS **实例 ID**
- SIREN **Client ID**（省略时 skill 列出可用 client 供选择）

Skill 将 UID 和选择器传给 `$sas`，获取告警上下文，端到端运行匹配的 playbook。

资产 UUID 和 ECS 实例选择器返回告警列表。SLEUTH 整体使用返回的告警集，按请求范围继续分页，仅在调查需要时按数字 `Id` 查询单条告警详情。多条告警不需要选定主告警。仍只产出一组 findings；列表范围的 findings 文件名省略 `event_id`。

### 自由排查模式

没有告警、资产或实例选择器时，提供 Client ID 加一段异常描述（如"进程 X CPU 100%"、"/tmp/x.sh 可疑文件"）。Skill 从宽泛排查开始逐步收窄。

### 多主机与合并

指定多台主机 / Client ID（或指向涉及多资产的告警），skill 先对已授权主机取最小快照，再逐台深挖；每个 Client 的工作底稿逐轮更新，复查不覆盖旧轮次，返回已验证结论。把多份底稿合并为一份报告（`IR-{date}-{primary-host}-multiN-{type}.md`），以及合并多份已有 `IR-*.md` 报告，都由 `dossier` skill 完成；合并产生跨报告新断言时，先由 sleuth 核实模式执行步骤 7 并把裁决写回 findings。

### 报告

正式报告的生成、合并、修订和审校都在 `dossier` skill（同级 `dossier` 仓库的 `skills/dossier/`，报告模板和写作规则也在那里）。两个 skill 装在同一个 skills 目录：`dossier` 读取旁边 sleuth 包里的 `skills/sleuth/references/findings_spec.md` 理解 findings，sleuth 不读 `dossier`。补充新证据或改变结论一律先走 sleuth 核实模式，裁决写回 findings 后再由 `dossier` 重写受影响章节。

## 目录结构

```
.
├── AGENTS.md                               # Agent 项目指令（Claude Code / Codex）
├── CHANGELOG.md                            # 工作流与安全护栏变更记录
├── manifest.json                           # 包元数据：责任人、成熟度、审查周期、预算等级
├── requirements.txt                        # 仓库检查的 Python 依赖精确锁定
├── docs/
│   ├── agent-guidance/                     # AI agent 协作本仓库的分任务指南
│   └── sleuth-design-principles.*          # 设计原则（HTML + PDF）
├── skills/
│   └── sleuth/
│       ├── SKILL.md                        # 常驻层：安全护栏、模式路由、8 步骨架、闭环与停止条件、委派与核验裁决
│       ├── agents/
│       │   ├── interface.yaml              # 跨平台接口契约
│       │   └── openai.yaml                 # Codex 应用元数据与 SIREN MCP 依赖提示
│       └── references/
│           ├── workflow_recon.md           # 步骤 1-2：能力确认、模式路由、client/主机清单、首轮扫描
│           ├── workflow_tracing.md         # 步骤 3-6 细则：playbook 路由、云侧交叉验证、ATT&CK、残留风险
│           ├── workflow_delivery.md        # 步骤 7 细则：验证门交接与结论 writer 隔离
│           ├── playbooks.md                # 步骤 3 分类型调查指南与技巧路由表
│           ├── tech_*.md                   # 4 个横向技术指南
│           ├── runtime_compat.md           # 跨客户端工具映射、子 agent、上下文预算、SIREN 异常
│           ├── findings_spec.md            # 每主机 findings 工作表：命名、slug、结构；dossier 据此写报告
│           ├── cloud_log_queries.md        # WAF / SAS / ActionTrail 日志路由
│           ├── sas_sls_host_telemetry.md   # SAS 主机遥测：字段坑、w3wp.exe、SSH 登录归因、OOB/DNSLog
│           ├── recon_residual.md           # 六轴扫描后的残留风险跟进
│           └── verification_checklist.md   # 交付前对抗验证门
├── scripts/
│   ├── validate.py                         # Frontmatter、链接、孤立引用检查
│   ├── permission_probe.py                 # 运行时信任与只读护栏锚点检查
│   ├── permission_probe_anchors.yaml       # permission_probe.py 的预期信任锚点
│   ├── gen_trust_report.py                 # 密钥扫描、脚本执行面、依赖锁定、包哈希证据
│   └── air_session_stats.py                # Codex AIR 会话的往返次数、上下文负载与 exec 输出分布
├── evals/
│   ├── semantic_config.json                # 语义评估配置
│   ├── blind_holdout/                      # 人工盲审 trigger cases
│   ├── dev/                                # 开发用 trigger cases
│   └── runtime/                            # Mock SIREN、场景、转录合规与故障测试
└── reports/                                # 信任证据、评分卡、盲审与 waiver
```

加载分两阶段。`SKILL.md` 是唯一常驻层：安全护栏、调查模式路由、8 步骨架、报告交接，以及每步必须遵守的规则（调查闭环与停止条件、多 Agent 何时派、核验裁决口径），只读 SKILL.md 的模型也能走完一次排查。`skills/sleuth/references/` 下的其余内容只放细则，按需加载——每步开头写明先读哪个 `workflow_*.md`，playbook 和技术指南仅在当前告警或场景需要时加载，保持初始上下文精简。

## Findings 输出

Skill 返回简洁的已验证调查结论，并在 cwd 为每台主机维护一份 findings 底稿：

- `IR-20260417-web01-webshell-123456-client7.findings.md`：告警驱动，告警 `Id` `123456`，SIREN client 7
- `IR-20260417-uid1234567890-akabuse-123456.findings.md`：没有 SIREN client 的云侧事件

命名字段和 event_type slug（如 `webshell`、`rce`、`unknown`）见 `skills/sleuth/references/findings_spec.md`「文件命名」。`dossier` skill 从 findings 名推导正式报告名 `IR-….md`。

## 验证

安装锁定的仓库检查依赖，然后在仓库根运行完整基线：

```bash
python3 -m pip install -r requirements.txt
python3 scripts/validate.py
python3 scripts/permission_probe.py
python3 scripts/gen_trust_report.py --check
python3 evals/runtime/run_mock_siren_tests.py
git diff --check
```

`scripts/gen_trust_report.py --check` 为只读模式。如果在包、脚本、依赖或跟踪文件变更后报告证据过时，运行一次 `python3 scripts/gen_trust_report.py` 并提交刷新的 `reports/trust_report.json` 和 `reports/trust_report.md`。

mock SIREN 套件是契约回归测试，验证运行时策略、场景证据、故障处理、转录合规和并发，但不证明 agent 能得出正确结论。使用[隔离模型演练](evals/runtime/README.md)采集真实输出与成本，再按 dossier 仓库的 `evals/output/review.md` 做事实复核。演练运行器需要显式启动，会调用已配置的模型服务并写入仓库外的新目录，不进入离线 CI；人工盲评仍单独进行。

## 贡献

Playbook 和技术指南在 `skills/sleuth/references/`，均为纯 Markdown。欢迎提交新攻击类型或环境特定指南的 PR。通用命令方法不要放进 references——模型已经知道这些，指南只承载判断规则、环境特定注意事项和具体攻击指标。

报告模板、写作规则和完整报告 fixture 在 `dossier` 仓库。`skills/sleuth/references/findings_spec.md` 中 `dossier` 写手读取的几节（文件命名、内容结构、结论交付层规则）是跨仓库契约，改动后也要跑那个仓库的检查。
