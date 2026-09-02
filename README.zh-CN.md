# SLEUTH

[English](README.md) | 中文

面向 Claude Code 和 Codex 的安全应急响应 agent skill。通过 SIREN MCP server 在失陷主机上执行只读取证命令，重建攻击链，交付经对抗验证的 MITRE ATT&CK 映射结论。正式中文事件报告仅在用户明确请求或确认后生成。

## 功能

- **两种调查模式**：告警 / 资产 / 实例维度的定向调查，以及无告警的自由排查
- **能力预检**：调查前探测主机、云侧、子 agent、Web 证据源的可用性；缺失覆盖会压低结论置信度上限
- **分类型调查 playbook**（webshell、挖矿、反弹 shell、暴破、勒索、RCE、SQL 注入、异常登录、数据外泄、持久化、提权）+ **横向技术指南**（日志分析、反向推理、云取证、威胁情报、进程/文件分析、攻击对抗手段）+ 专项指南（云日志路由、SAS/SLS 主机遥测、OOB/DNSLog、SSH 登录溯源、ASP.NET 上传追踪）+ **MITRE ATT&CK 映射**。路由表见 `skills/sleuth/references/playbook_index.md`
- **并行命令调度**：无依赖关系的远程命令在同一轮发出，压缩调查时间
- **问题驱动证据闭环**：基线扫描后，每轮后续必须回答一个能改变定性、范围或处置的具名问题；不再产出决策相关证据时停止扩张
- **严格只读**：只跑不改系统状态的命令（读文件、列举进程/网络/服务、查日志），绝不执行破坏或安装命令；保全证据完整性
- **对抗验证门**：所有承重断言在交付前经独立反驳（子 agent 或内联），防止错误归因
- **证据触发的漏洞归因**：仅在证据指向漏洞利用时调查 CVE；凭证滥用、配置暴露等非漏洞入口按实际路径报告，不为字段完整强行绑定 CVE
- **报告确认门**：调查默认止于已验证结论；正式 `IR-....md` 报告仅在用户明确请求或确认后生成
- **隔离写手**：确认报告后，子 agent 可用时由一个全新写手只看 findings、模板和写作规则；写手无法访问 SIREN 或调查上下文，写手与主调度均执行同一套交付前检查
- **上下文隔离子 agent**：大量日志 / SLS / 全盘输出由子 agent（或内联）处理后只回传结论，保持主调度上下文精简
- **多主机委托**：逐台调查（SIREN 按 client 工作），每台产出一份已验证的 `*.findings.md`；确认报告后合并为一份（见下文*多主机与合并*）
- **可选 Markdown 事件报告**：确认后从内置 Dossier 风格模板生成一份命名的 `IR-....md`，以 findings 工作表为唯一事实来源；已验证的云侧事实可由 `opencli-aliyun-ir` 只读截取控制台截图，报告按路径引用
- **自然写作风格**：报告行文遵循 `skills/sleuth/references/report_style.md` 和内置的脱敏写作样本

## 前置条件

- **Claude Code 或 Codex**：最新稳定版。skill 遵循开放 agent skills 格式，位于 `skills/sleuth/`（`SKILL.md` + 可选的 `references/`、`assets/`、`agents/openai.yaml`）。
- **SIREN MCP server**：skill 依赖 SIREN 的 list-client 和 remote-run 工具，通常暴露为 `mcp__siren__ls` 和 `mcp__siren__run`。使用前需在客户端配置 SIREN 为 MCP server。
- **`$sas` skill**：告警驱动查询必需。
- **可选 `sls` skill**：WAF / SAS / ActionTrail 云日志交叉验证的首选。
- **可选 `opencli-aliyun-ir` skill**：在 `sas` / `sls` 之后用于阿里云控制面状态、专用适配器、内部控制台、跨产品关联及覆盖缺口。

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

资产 UUID 和 ECS 实例选择器返回告警列表。SLEUTH 整体使用返回的告警集，按请求范围继续分页，仅在调查需要时按数字 `Id` 查询单条告警详情。多条告警不需要选定主告警。确认报告后仍产出一份事件报告；列表范围的报告文件名省略 `event_id`。

### 自由排查模式

没有告警、资产或实例选择器时，提供 Client ID 加一段异常描述（如"进程 X CPU 100%"、"/tmp/x.sh 可疑文件"）。Skill 从宽泛排查开始逐步收窄。

### 多主机与合并

指定多台主机 / Client ID（或指向涉及多资产的告警），skill 逐台调查，每台写一份 `*.findings.md` 工作表，默认返回已验证结论而不创建报告。确认后合并为一份报告（`IR-{date}-{primary-host}-multiN-{type}.md`）。递交多份已有 `IR-*.md` 报告并明确要求合并视同报告确认，触发纯合并模式：跳过步骤 1-6，以已有报告作为 findings 输入，对跨报告新断言执行步骤 7 验证，然后产出一份合并报告。

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
│       ├── SKILL.md                        # 常驻层：安全护栏、模式路由、8 步骨架、报告确认门
│       ├── agents/
│       │   ├── interface.yaml              # 跨平台接口契约
│       │   └── openai.yaml                 # Codex 应用元数据与 SIREN MCP 依赖提示
│       ├── assets/
│       │   ├── report.md                   # Markdown 报告模板（来自 dossier/report.md）
│       │   └── style/                      # 脱敏写作样本；首选 curated-ir-excerpts.md
│       └── references/
│           ├── preflight_probe.md          # 能力预检：缺口 → 置信度上限
│           ├── workflow_recon.md           # 步骤 1-2 细则：模式路由、client/主机清单、首轮扫描
│           ├── workflow_tracing.md         # 步骤 3-6 细则：playbook 路由、云侧交叉验证、ATT&CK、残留风险
│           ├── workflow_delivery.md        # 步骤 7-8 细则：验证门交接、findings、报告生成
│           ├── playbook_index.md           # 步骤 3 路由表
│           ├── invest_*.md                 # 11 个分类型调查 playbook
│           ├── tech_*.md                   # 6 个横向技术指南
│           ├── attack_framework.md         # ATT&CK 战术/技术参考（v18 基准）
│           ├── runtime_compat.md           # 跨客户端工具映射、子 agent、SIREN 异常处理
│           ├── report_naming.md            # IR-….md 文件名格式、event_type slug、多主机规则
│           ├── findings_spec.md            # 每主机 findings 工作表：调查→报告交接
│           ├── report_writing_rules.md     # 模板逐块填写规则 + 项目约束
│           ├── report_style.md             # 写作风格指南（来自手写文章提炼）
│           ├── cloud_log_queries.md        # WAF / SAS / ActionTrail 日志路由
│           ├── sas_sls_host_telemetry.md   # SAS SLS 主机遥测查询（环境特定注意事项）
│           ├── oob_dnslog_investigation.md # dnslog.cn / interact.sh / OOB 回调
│           ├── ssh_login_attribution_sas.md # 基于 SAS 遥测的 SSH 登录源追溯
│           ├── recon_residual.md           # 六轴扫描后的残留风险跟进
│           ├── verification_checklist.md   # 交付前对抗验证门
│           └── aspnet_webshell_upload_tracing.md # ASP.NET webshell 上传追踪
├── scripts/
│   ├── validate.py                         # Frontmatter、链接、孤立引用检查
│   ├── permission_probe.py                 # 运行时信任与只读护栏锚点检查
│   ├── permission_probe_anchors.yaml       # permission_probe.py 的预期信任锚点
│   └── gen_trust_report.py                 # 密钥扫描、脚本执行面、依赖锁定、包哈希证据
├── evals/
│   ├── semantic_config.json                # 语义评估配置
│   ├── blind_holdout/                      # 人工盲审 trigger cases
│   ├── dev/                                # 开发用 trigger cases
│   ├── output/                             # 报告契约 fixture 与结构验证器
│   │   └── fixtures/                       # Findings 工作表与完整报告 fixture
│   └── runtime/                            # Mock SIREN、场景、转录合规与故障测试
└── reports/                                # 信任证据、评分卡、盲审与 waiver
```

加载分两阶段。`SKILL.md` 是唯一常驻层：安全护栏、调查模式路由、8 步骨架和报告确认门。`skills/sleuth/references/` 下的其余内容按需加载——进入某阶段时读取对应 `workflow_*.md`，playbook、技术指南和写作规则仅在当前告警或场景需要时加载，保持初始上下文精简。

## 报告输出示例

Skill 默认返回简洁的已验证调查结论，不创建正式报告。用户明确请求或确认后，在 cwd 写入一份 Markdown 报告：

- `IR-20260417-web01-webshell-123456.md`：告警驱动，告警 `Id` `123456`
- `IR-20260417-web01-webshell.md`：资产或实例范围的告警集
- `IR-20260417-db-prod-rce.md`：自由排查模式
- `IR-20260417-web01-multi3-miner-123456.md`：多主机委托（3 台主机，主机 `web01`）

报告文件从 `skills/sleuth/assets/report.md` 复制后按事件填充。

event_type slug（如 `webshell`、`rce`、`unknown`）的完整表见 `skills/sleuth/references/report_naming.md`。

## 验证

安装锁定的仓库检查依赖，然后在仓库根运行完整基线：

```bash
python3 -m pip install -r requirements.txt
python3 scripts/validate.py
python3 scripts/permission_probe.py
python3 scripts/gen_trust_report.py --check
python3 evals/output/validate_full_reports.py
python3 evals/runtime/run_mock_siren_tests.py
git diff --check
```

`scripts/gen_trust_report.py --check` 为只读模式。如果在包、脚本、依赖或跟踪文件变更后报告证据过时，运行一次 `python3 scripts/gen_trust_report.py` 并提交刷新的 `reports/trust_report.json` 和 `reports/trust_report.md`。

完整报告 fixture 与 mock SIREN 套件是契约回归测试，验证报告结构、运行时策略、场景证据、故障处理、转录合规和并发，但不证明 agent 能得出正确结论。模型行为审查使用 `evals/runtime/README.md` 中的手动演练，人工盲审报告作为独立门控。

## 贡献

Playbook 和技术指南在 `skills/sleuth/references/`，报告模板在 `skills/sleuth/assets/report.md`，均为纯 Markdown。欢迎提交新攻击类型或环境特定指南的 PR。通用命令方法不要放进 references——模型已经知道这些，指南只承载判断规则、环境特定注意事项和具体攻击指标。

写作规则分层，每条规则只有一个权威归属：块级填写规则在模板的 HTML 注释中，横向约束在 `skills/sleuth/references/report_writing_rules.md`，行文风格在 `skills/sleuth/references/report_style.md`。新规则放在对应层，不跨文件重复。模板变更（含注释）应在上游 `dossier` 项目修改后同步到此 skill。

变更报告规则后，通过隔离的步骤 8 写手重新生成 `evals/output/fixtures/full_reports/` 下受影响的 fixture，运行上述验证命令，并手动对照风格指南审查中文行文。
