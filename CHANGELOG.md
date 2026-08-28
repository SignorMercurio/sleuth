# 更新日志

本文件记录 sleuth 仓库对外可见的重要变更，格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

**维护规则**：安全护栏（只读原则、状态变更禁令、SIREN 执行边界等）与措辞等级（结论置信度、报告用词分级）的任何变更，必须在此记录变更原因，不得只改代码/文档而不留痕迹。

## [此前历史]

本文件建立之前的变更历史，见仓库 `git log`。

## 2026-08-27

### 变更

- `skills/sleuth/SKILL.md`：把主动狩猎、纯云侧查询、代码审计/修复、无事件加固和仅翻译/总结纳入 frontmatter 路由排除，降低隐式激活的近邻误触发。
- 调查流程改为基线后的问题驱动证据闭环：每轮限定假设、证据范围与裁决，承重断言完成确认/反驳/降级且固定残留风险检查结束后停止扩张。
- 漏洞定位改为证据触发；凭证滥用、合法工具滥用、配置暴露或社会工程不再为了字段完整强行绑定 CVE。

## 2026-08-26

### 新增

- `skills/sleuth/references/preflight_probe.md`：步骤 0 能力探测细则；探测到的缺口计入 findings 的调查限制，并据此压低结论措辞。
- `skills/sleuth/references/workflow_recon.md`、`workflow_tracing.md`、`workflow_delivery.md`：原 SKILL.md 步骤 1–2、3–6、7–8 的操作细则拆分为按需加载的独立文档。
- `scripts/gen_trust_report.py` 与 `reports/trust_report.json`、`reports/trust_report.md`：治理发布信任报告，覆盖密钥扫描、脚本执行面、依赖锁定、安装包哈希四个部分；`--check` 模式接入 CI 门禁。
- `scripts/permission_probe.py` 与 `scripts/permission_probe_anchors.yaml`：运行时权限探针，静态核验 `agents/interface.yaml` 的信任块（只读、本地来源、禁止远程内联执行）、`agents/openai.yaml` 未声明额外执行权限、`SKILL.md` 护栏锚点仍在位；接入 CI 门禁。
- `requirements.txt`：固定 `pyyaml==6.0.3`；CI 改为 `pip install -r requirements.txt`。
- `evals/runtime/`：mock SIREN 运行时回归集，`run_mock_siren_tests.py` 以 mock SIREN server、故障注入、策略与场景校验覆盖 887 项自测。

### 变更

- `skills/sleuth/SKILL.md`：由单层文档重构为两阶段加载——常驻层只保留安全护栏、调查模式判别、8 步骨架与报告确认门，压缩到 4495 字节（约 1284 tokens），回落到治理上下文预算红线内；各步骤操作细则移入对应 `references/workflow_*.md`，进入该步骤时才加载。
- `skills/sleuth/references/attack_framework.md`：声明编号基准为 MITRE ATT&CK v18（2025-10 发布），并补充基准升级时须核对 `T` 编号是否漂移的维护规则。
- `.github/workflows/validate.yml`：追加 `python3 scripts/permission_probe.py`、`python3 scripts/gen_trust_report.py --check`、`python3 evals/runtime/run_mock_siren_tests.py` 三个门禁步骤，依赖安装改为 `pip install -r requirements.txt`。
- `docs/agent-guidance/verification.md`：baseline 清单同步补齐上述新命令。
- `manifest.json` notes：如实更新为——trust report 与 runtime permission probe 已生成并接入 CI，context budget 已压回治理红线内；仍披露 Review Studio 决策页未生成、5 例 output-lab 人工盲审待完成。

### 关闭的 waiver

- `reports/review_waivers.json`、`reports/review_waivers.md`：`context-budget`、`trust-report`、`permission-runtime` 三条 waiver 标记为已解决（保留原始记录不删，延续披露式治理风格）。
