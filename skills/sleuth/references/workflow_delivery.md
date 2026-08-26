# 步骤 7–8：对抗式验证、结论交付与报告生成

SKILL.md 进入步骤 7 时加载本文件。报告确认门的判定以 SKILL.md 为准，本文只写操作细则。

## 步骤 7 结论对抗式验证与交付

交付结论前的质检门，系统化防止误归因（本领域头号交付风险）。**读取 `references/verification_checklist.md`** 并按其执行：承重断言范围、独立核验方式（子 agent 或内联怀疑视角）、裁决与措辞降级规则都以该清单为准，本文不重述；子 agent 派生与降级映射见 `references/runtime_compat.md`。

- 每台主机过完验证门后，把定稿结论写成 findings 工作底稿（结构与命名见 `references/findings_spec.md`）。
- 多主机委托时回到步骤 2 调查下一台；全部完成后再统一交付。
- 交付形式是对话中的精炼调查结论，至少包含事件定性、关键证据与边界、影响 / 残留风险、处置进展和建议动作；能力缺口按 `references/preflight_probe.md` 一并说明。
- **跨主机关联断言**（同源攻击、横向移动、同一攻击者）在合并阶段基于多份 findings 提出，同样要过本验证门，不因属于「合并层」而免检。

进入步骤 8 前，确认严重等级、当前事件状态和三阶段处置进展完整；缺失就先补查或向用户确认，不把缺口留给写作层猜测。

## 步骤 8 经用户确认后生成 Markdown 应急响应报告

只有通过 SKILL.md 的报告确认门后才执行本步骤。每次委托只在当前工作目录生成**一份**命名后的 Markdown 正式报告；报告交付物仅此一个 `IR-….md` 文件（findings 工作底稿不算正式报告交付物）。

写作只以 findings 文件为事实来源；输入文件清单与禁止事项（不得改变事实与措辞等级、证据缺口处理）以 `references/findings_spec.md`「正式报告写作层使用规则」为准。默认按 `references/runtime_compat.md`「报告写作隔离」使用全新 writer 上下文；只传入规定文件路径，不传调查上下文，writer 不碰 SIREN。运行时不支持子 agent 时才内联降级，并重新读取全部 findings 后按同一输入边界写作。

### 8.1 生成步骤

编号只表示逻辑顺序，其中互不依赖的文件读取一次性并行发出：

1. **确定输出文件**：按 `references/report_naming.md`（字段说明、事件类型 slug 对照、多主机命名与示例；本次会话已读过则复用，不重复读取）在当前工作目录确定文件名 `IR-{YYYYMMDD}-{hostname}-{event_type}[-{event_id}].md`
2. **读取写作规则**：读取 `references/report_style.md`（文风，含 `assets/style/` 样本读取规则）与 `references/report_writing_rules.md`（模板逐块填充 + 本项目特有约束，含两条不可让渡红线：结论可信度、IoC 展示层转义）并执行
3. **拷贝模板**：将 `<skill_root>/assets/report.md`（来源于 `dossier/report.md`）复制为该输出文件
4. **填充报告副本**：只编辑该输出文件，按 `references/report_writing_rules.md` 的逐块细则替换占位内容
5. **交稿前 QA**：按 `references/runtime_compat.md`「报告写作隔离」的清单复核事实边界、必填字段、章节、占位符、内部术语、IoC、样本串案、重复与文风；问题回报编排者，不写进客户报告
6. **只交付 Markdown**：不要创建报告目录、`index.html`、CSS/JS、字体资源或 dev server

### 8.2 多主机合并规则（多主机委托与合并模式）

多主机委托与合并模式下，按 `references/findings_spec.md`「多主机合并规则」一节执行块级合并；单主机跳过本节。
