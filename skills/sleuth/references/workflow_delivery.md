# 步骤 7–8：对抗式验证、结论交付与报告生成

SKILL.md 进入步骤 7 时加载本文件。报告确认门以 SKILL.md 为准，本文只写操作细则。

## 步骤 7 结论对抗式验证与交付

**读取 `references/verification_checklist.md`** 并按其执行：承重断言范围、独立核验方式、裁决与措辞降级规则都以该清单为准；子 agent 派生与降级见 `references/runtime_compat.md`。

- 每台主机过完验证门后，把逐轮维护的 findings 标记为「已验证」，核对定稿断言与证据引用，未决问题保留在工作区段（结构见 `references/findings_spec.md`）。
- **控制台截图**（可选）：`opencli-aliyun-ir` 可用且事件含云侧承重事实时，在定稿前把「已确认事实 → 待截对象」清单委派给它的控制台截图流程，回传路径按 `references/findings_spec.md`「证据截图」挂到对应证据记录下；截图不改变任何裁决。
- 多主机委托时继续下一台的定向调查，复用已采最小快照并补查可能已变化的状态；全部完成后统一交付。
- **跨主机关联断言**（同源攻击、横向移动、同一攻击者）基于多份 findings 提出，同样要过验证门。
- 交付形式是对话中的精炼调查结论：事件定性、关键证据与边界、影响 / 残留风险、处置进展和建议动作，并说明影响结论的能力与证据缺口。

进入步骤 8 前，确认严重等级、当前事件状态和三阶段处置进展完整；缺失就先补查或向用户确认，不把缺口留给写作层猜测。

## 步骤 8 经用户确认后生成 Markdown 应急响应报告

只有通过报告确认门后才执行。每次委托只在当前工作目录生成**一份** `IR-….md` 正式报告（findings 底稿不算交付物）。写作只以 findings 为事实来源，输入清单、隔离方式与交稿 QA 以 `references/runtime_compat.md`「报告写作隔离」为准；运行时不支持子 agent 才内联降级，并重新读取全部 findings 后按同一输入边界写作。

### 8.1 生成步骤

互不依赖的文件读取一次性并行发出：

1. **确定输出文件**：按 `references/report_naming.md`（本次会话已读过则复用）在当前工作目录确定 `IR-{YYYYMMDD}-{hostname}-{event_type}[-{event_id}].md`
2. **读取写作规则**：`references/report_writing_rules.md`（逐块填充 + 本项目约束，含两条红线）与 `references/report_style.md`（文风，含样本读取规则）
3. **拷贝模板**：将 `assets/report.md` 复制为该输出文件，只编辑该副本，按逐块细则替换占位内容
4. **交稿前 QA**：按 `references/runtime_compat.md` 的清单复核；问题回报编排者，不写进客户报告
5. **只交付 Markdown**：不创建报告目录、`index.html`、CSS/JS、字体资源或 dev server；`<报告名>.assets/` 由编排者在步骤 7 产出，写手不碰

### 8.2 多主机合并

多主机委托与合并模式按 `references/findings_spec.md`「多主机合并规则」块级合并；单主机跳过。
