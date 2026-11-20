# scripts/

仓库级校验脚本，非安装包内容（见 `docs/agent-guidance/repository-boundaries.md`）。均为 Python 3，依赖见 `requirements.txt`。

- **`validate.py`** —— 只读一致性检查：SKILL.md frontmatter 与近邻路由排除标记、护栏锚点与流程语义标记（清单在 `evals/semantic_config.json`，改措辞时在那里校准）、`agents/interface.yaml` 信任块不变量、`agents/openai.yaml` 未声明超范围执行权限、引用完整性与孤立文件、git 跟踪文件的凭据扫描（AccessKey ID、私钥块、带引号的凭据赋值）。`python3 scripts/validate.py`
- **`air_session_stats.py`** —— 统计 Codex AIR 会话 rollout 的模型调用次数、上下文 token 中位/峰值、总用量、压缩次数、工具调用计数、非图片 exec 输出字节分布与 SKILL.md 读取次数；仅用标准库。
  `python3 scripts/air_session_stats.py ROLLOUT.jsonl [...]`（服务器上可 `python3 - ROLLOUT.jsonl < scripts/air_session_stats.py`）
