# 步骤 7：对抗式验证与结论交付

SKILL.md 进入步骤 7 时加载本文件。报告交接以 SKILL.md 步骤 8 为准，本文只写操作细则。

## 步骤 7 结论对抗式验证与交付

**读取 `references/verification_checklist.md`** 并按其执行：承重断言范围、独立核验方式、裁决与措辞降级规则都以该清单为准；子 agent 派生与降级见 `references/runtime_compat.md`。

- 运行环境提供 `case_update` 时，未过验证门的 `confirmed` 事件改为 `inferred` 或 `withdrawn`，然后按 `references/findings_spec.md`「攻击时间线位置」把事件快照写入 §3 和 §5。
- 每台主机过完验证门后，把逐轮维护的 findings 标记为「已验证」，核对定稿断言与证据引用，未决问题保留在工作区段（结构见 `references/findings_spec.md`）。
- **控制台截图**（可选）：按 `references/findings_spec.md`「证据截图」。
- 多主机委托时继续下一台的定向调查，复用已采最小快照并补查可能已变化的状态；全部完成后统一交付。
- **跨主机关联断言**（同源攻击、横向移动、同一攻击者）基于多份 findings 提出，同样要过验证门；裁决连同所引的另一份底稿名写入相关各台 findings。
- **核实模式**：把既有报告或 findings 的承重断言当作待核断言过同一验证门，交付 `references/verification_checklist.md` 步骤 4 核验表的对外版（附证据编号），并指出话术与证据不符处。
- 交付形式是对话中的精炼调查结论，内容见 `references/findings_spec.md`「结论交付层使用规则」，按下节起草、复核并原样发送。

### 结论交付隔离

全部 findings 标记「已验证」后，运行时支持子 agent 时派生一个全新结论 writer 起草交付结论。只给它全部 findings 文件路径与 `references/findings_spec.md`，不传调查对话、工具输出、编排者推理或核验表。它按「结论交付层使用规则」返回草稿，不创建文件，不调用 SIREN、SAS、SLS、OpenCLI 或联网工具。

编排者逐句对照 findings 复核，只判通过或不通过，不改写草稿：每条断言都要对得上已验证章节的措辞等级、数量与范围，IoC、时间与路径逐字一致。不通过时，findings 本身有误或需要新增、加强断言的，先改 findings（新增或加强的断言回到 `references/verification_checklist.md` 过门）；草稿越界的，把问题清单交回 writer 重写。问题清单只写原句、违反的规则和对应 findings 章节，不附改写文本或新事实。重写稿重新复核。通过后把 writer 稿原样发送，不增删字句，不追加调查过程说明；末尾只可另起一行给出 findings 路径并询问是否生成报告。

运行时不支持子 agent 时，编排者重新读取全部 findings 后内联起草，只用文件内容，不凭会话记忆补事实或改措辞，再做同一复核。

交付前核对 findings §2 的严重等级、§9 的当前事件状态与处置进展已填写或已核实为未知，不把缺口留给 dossier 的写作层猜测。
