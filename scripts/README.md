# scripts/

仓库级校验脚本，非安装包内容（见 `docs/agent-guidance/repository-boundaries.md`）。均为 Python 3，依赖见 `requirements.txt`。

- **`validate.py`** —— SKILL.md frontmatter 近邻路由排除、问题驱动/CVE 归因流程语义锚点、agents 元数据与引用完整性一致性检查。`python3 scripts/validate.py`
- **`gen_trust_report.py`** —— 生成治理发布信任报告（密钥扫描、脚本执行面、依赖锁定、`skills/sleuth/` 安装包哈希），产物为 `reports/trust_report.json` 与 `reports/trust_report.md`。默认覆盖重新生成；`--check` 只重算比对、不写盘，产物过期或未通过则非零退出。
  `python3 scripts/gen_trust_report.py` / `python3 scripts/gen_trust_report.py --check`
- **`permission_probe.py`** —— 运行时权限探测：校验 `agents/interface.yaml` 信任块不变量、`agents/openai.yaml` 未声明超范围执行权限、`SKILL.md` 仍含护栏语义锚点（锚点清单见 `permission_probe_anchors.yaml`，未来 SKILL.md 改版时在此处校准，无需改脚本）。
  `python3 scripts/permission_probe.py`
- **`air_session_stats.py`** —— 统计 Codex AIR 会话 rollout 的模型调用次数、上下文 token 中位/峰值、总用量、压缩次数、工具调用计数、非图片 exec 输出字节分布与 SKILL.md 读取次数；仅用标准库。
  `python3 scripts/air_session_stats.py ROLLOUT.jsonl [...]`（服务器上可 `python3 - ROLLOUT.jsonl < scripts/air_session_stats.py`）
