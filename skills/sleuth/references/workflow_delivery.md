# 步骤 7–8：对抗式验证、结论交付与报告生成

SKILL.md 进入步骤 7 时加载本文件。报告确认门以 SKILL.md 为准，本文只写操作细则。

## 步骤 7 结论对抗式验证与交付

**读取 `references/verification_checklist.md`** 并按其执行：承重断言范围、独立核验方式、裁决与措辞降级规则都以该清单为准；子 agent 派生与降级见 `references/runtime_compat.md`。

- 每台主机过完验证门后，把逐轮维护的 findings 标记为「已验证」，核对定稿断言与证据引用，未决问题保留在工作区段（结构见 `references/findings_spec.md`）。
- **控制台截图**（可选）：按 `references/findings_spec.md`「证据截图」。
- 多主机委托时继续下一台的定向调查，复用已采最小快照并补查可能已变化的状态；全部完成后统一交付。
- **跨主机关联断言**（同源攻击、横向移动、同一攻击者）基于多份 findings 提出，同样要过验证门；裁决连同所引的另一份底稿名写入相关各台 findings。
- **核实模式**：把既有报告或 findings 的承重断言当作待核断言过同一验证门，交付 `references/verification_checklist.md` 步骤 4 核验表的对外版（附证据编号），并指出话术与证据不符处。
- 交付形式是对话中的精炼调查结论，内容见 `references/findings_spec.md`「结论交付层使用规则」，按下节起草、复核并原样发送。

### 结论交付隔离

全部 findings 标记「已验证」后，运行时支持子 agent 时派生一个全新结论 writer 起草交付结论。只给它全部 findings 文件路径与 `references/findings_spec.md`，不传调查对话、工具输出、编排者推理或核验表。它按「结论交付层使用规则」返回草稿，不创建文件，不调用 SIREN、SAS、SLS、OpenCLI 或联网工具。

编排者逐句对照 findings 复核，只判通过或不通过，不改写草稿：每条断言都要对得上已验证章节的措辞等级、数量与范围，IoC、时间与路径逐字一致。不通过时，findings 本身有误或需要新增、加强断言的，先改 findings（新增或加强的断言回到 `references/verification_checklist.md` 过门）；草稿越界的，把问题清单交回 writer 重写。问题清单只写原句、违反的规则和对应 findings 章节，不附改写文本或新事实。重写稿重新复核。通过后把 writer 稿原样发送，不增删字句，不追加调查过程说明；末尾只可另起一行询问是否生成报告。

运行时不支持子 agent 时，编排者重新读取全部 findings 后内联起草，只用文件内容，不凭会话记忆补事实或改措辞，再做同一复核。

进入步骤 8 前，按 `references/findings_spec.md` 的定稿条件核对必填信息和已核实的未知边界，不把缺口留给写作层猜测。

## 步骤 8 经用户确认后生成 Markdown 应急响应报告

只有通过报告确认门后才执行。每次委托只在当前工作目录生成**一份** `IR-….md` 正式报告（findings 底稿不算交付物），写作只以 findings 为事实来源。

### 8.1 入侵路径示意图（派 writer 前，编排者执行）

findings「入侵路径」有已验证步骤时，按 `references/runtime_compat.md`「生成图片」生成一张示意图，保存为 `<报告名>.assets/attack-chain.png`；多主机只画一张。

- **内容**：只画已验证步骤，节点标签原样写 IP、路径、接口、进程、主机名等具体值；无法确认的后续环节画成灰色虚线框并注明未见记录。要求横向流程图、白底、扁平商务风格、16:9、简体中文。
- **提示词措辞**：按「防守方事件复盘流程图」描述，节点用「外部来源」「请求」「写入文件」「启动进程」等中性说法，不写「攻击」「利用」「webshell」「木马」这类词，否则容易被生图服务的内容审核拦截；被拒时改成中性说法重试一次。
- **失败不阻塞**：工具不可用或仍被拒就不传路径，writer 用文字写入侵路径，交付时说明未生成示意图。

### 8.2 报告写作隔离

运行时支持子 agent 时默认派生一个全新 writer 生成报告。只给 writer 以下文件路径，不传调查对话、工具输出、编排者推理或预期答案：

- 全部 findings 文件
- `assets/report.md`
- `assets/style/curated-ir-excerpts.md`
- `references/findings_spec.md`
- `references/report_naming.md`
- `references/report_style.md`
- `references/report_writing_rules.md`
- 入侵路径示意图路径（生成成功时）

writer 只读取这些文件（互不依赖的读取一次性并行发出），不调用 SIREN、SAS、SLS、OpenCLI 或联网工具：

1. 按 `references/report_naming.md` 在当前工作目录确定 `IR-{YYYYMMDD}-{hostname}-{event_type}[-{event_id}].md`
2. 将 `assets/report.md` 复制为该文件，只编辑该副本，按 `references/report_writing_rules.md` 逐块替换占位内容
3. 只交付这一份 Markdown：不创建报告目录、`index.html`、CSS/JS、字体资源或 dev server；`<报告名>.assets/` 由编排者产出，writer 不碰

是否因字段缺失停止定稿，以 `references/findings_spec.md`「正式报告写作层使用规则」为准；区分漏填与编排者已核实的未知边界。

writer 完成后先自检，编排者再按相同边界复核：

1. 按 `references/findings_spec.md` 检查事实边界、措辞等级、严重等级、影响统计口径与处置进展；数量和状态逐项核对来源，已核实的未知边界不能改写成确定结果
2. 按模板 HTML 注释检查原有标题、`:::` 指令块、占位符和各块内容；图片引用逐条核对路径来自 findings 或编排者传入，且文件存在
3. 按 `references/report_writing_rules.md` 检查跨章节分工、证据实体下限、内部标识、IoC、样本串案与重复
4. 按 `references/report_style.md` 通读中文，清理不自然或机械化表达
5. 检查篇幅：概述字段按模板注释的字数上限，正文自然段按 `references/report_writing_rules.md` 的段落上限。超限时按该规则处理，不逐句缩写、不删具体证据值、不把段落挪进表格或列表，并在 QA 结果里写明每处超限的处理方式；修订模式另按 8.4 核对篇幅

QA 结果只返回编排者。全部通过才交付报告；失败就修报告，事实或必填字段缺失则回到步骤 2–7。运行时不支持子 agent 时，编排者重新读取上述文件后内联写作，仍执行相同自检，不凭会话记忆补事实。

### 8.3 多主机合并

多主机委托与合并模式按 `references/findings_spec.md`「多主机合并规则」块级合并；单主机跳过。

### 8.4 修订已交付报告

复核意见、新证据或用户指出的错误都按同一流程进入已交付报告：

1. **裁决写回 findings**：原 findings 仍在时写回原 findings，不在时以报告当前版本为 findings 等价物（规则同合并模式），每条意见按 `references/verification_checklist.md` 过门，裁决为维持、降级、撤回或改正并附依据，写回对应断言。复核方只给裁决，不给行号和改写文本。
2. **整章重写**：把受裁决影响的章节交给全新 writer，输入边界同 8.2，加上当前报告路径；writer 依据更新后的 findings 重写这些章节，未受影响的章节原样保留。不在原句后追加「但不能排除……」，撤回的结论直接删去，限定语仍按「证据边界只完整展开一次」只落一处。
3. **版本与篇幅**：按模板 rev 注释递增 minor 版本。重写后的正文不应比上一版长，变长时交稿 QA 要说明新增的是哪个已确认阶段，否则删回。
