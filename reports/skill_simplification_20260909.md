# SLEUTH 安装包精简与报告可读性改造：本地验证记录

日期：2026-09-09。范围：`skills/sleuth/` 安装包、`evals/output/fixtures/full_reports/` 合成夹具与本记录。没有访问真实 SIREN 主机，没有提交、推送、部署或改动权限锚点。本记录是改动前后的实验快照；改前基线用改动前的安装包副本（提交 ef9f205）冻结运行，改后用改动后的安装包副本冻结运行（与最终版只差 `report_writing_rules.md` 后补的篇幅上限一句，演练不生成报告，不受影响），场景、运行器与模型相同。

一句话结论：工程检查全部通过，安装包缩小约 9%，SKILL.md 回到 1300 token 档内；八个 mock 场景各跑一轮，改后 SIREN 调用总数少 11%，模型辅助复核改前 5 pass / 2 partial / 1 fail，改后 5 pass / 3 partial / 0 fail：改前越界的 02、03 场景改善，改前通过的 01、06 场景出现新的「判读过严」或「摘要回升」问题。没有做人工盲评，不宣称准确率提高。

## 改前 / 改后

### 安装包

估算 token 为启发式（汉字 ×0.7 + 其他词元），与治理记录里 4495 字节 ≈ 1284 token 的口径不同；按治理口径 4540 字节 ≈ 1297 token，在档内。

| 文件 | 改前字节 | 改后字节 | 改前汉字 | 改后汉字 | 改前估算 token | 改后估算 token |
|---|---:|---:|---:|---:|---:|---:|
| SKILL.md | 4831 | 4540 | 1059 | 986 | 1344 | 1261 |
| references/findings_spec.md | 10313 | 9608 | 2643 | 2484 | 2681 | 2488 |
| references/invest_abnormal_login.md | 1320 | 1125 | 250 | 203 | 391 | 336 |
| references/invest_brute_force.md | 1143 | 972 | 228 | 190 | 345 | 297 |
| references/invest_data_exfiltration.md | 1616 | 1487 | 383 | 350 | 446 | 411 |
| references/invest_mining.md | 1209 | 1030 | 247 | 202 | 351 | 305 |
| references/invest_persistence.md | 3303 | 3025 | 534 | 482 | 957 | 890 |
| references/invest_privilege_escalation.md | 1261 | 1050 | 210 | 157 | 380 | 325 |
| references/invest_ransomware.md | 1073 | 952 | 247 | 216 | 312 | 280 |
| references/invest_rce.md | 1151 | 993 | 215 | 189 | 340 | 291 |
| references/invest_reverse_shell.md | 1141 | 966 | 211 | 172 | 333 | 291 |
| references/invest_sql_injection.md | 1071 | 962 | 195 | 174 | 312 | 283 |
| references/invest_webshell.md | 2388 | 1732 | 476 | 308 | 663 | 492 |
| references/oob_dnslog_investigation.md | 5333 | 4865 | 164 | 172 | 1384 | 1241 |
| references/report_style.md | 7949 | 6812 | 2088 | 1777 | 2062 | 1754 |
| references/report_writing_rules.md | 7415 | 6825 | 1869 | 1696 | 1958 | 1808 |
| references/runtime_compat.md | 4794 | 4575 | 1128 | 1083 | 1188 | 1139 |
| references/tech_cloud.md | 7031 | 5665 | 1204 | 944 | 1841 | 1445 |
| references/verification_checklist.md | 6104 | 5837 | 1531 | 1451 | 1542 | 1467 |
| references/workflow_delivery.md | 4348 | 3110 | 1012 | 707 | 1113 | 808 |
| references/workflow_recon.md | 6023 | 4686 | 1531 | 1195 | 1549 | 1208 |
| references/workflow_tracing.md | 4044 | 3503 | 959 | 834 | 1029 | 882 |
| **安装包合计（含未改文件）** | 117757 | 107462 | | | 31350 | 28591 |


### 夹具报告

四份夹具全部由隔离 writer 只读 findings、模板、样本与三份写作参考重生成；编排者按 `evals/output/review.md` 流程逐篇对照 findings 复读，修正了 simple-webshell 的三处越界（定性字段把「推测」写成确定语气；两条底稿没有的事实）与四份夹具的分号压缩句和样本 8 字重合。修正后四份都通过 `validate_full_reports.py`。

| 夹具 | 改前可见汉字 | 改后可见汉字 | 改前段落 | 改后段落 | 时间线节点 | 动作数 |
|---|---:|---:|---:|---:|---:|---:|
| simple-webshell | 1618 | 2147 | 42 | 43 | 4→5 | 6→6 |
| no-current-intrusion | 2064 | 1920 | 39 | 39 | 4→4 | 2→2 |
| complex-rce-credential | 2493 | 2727 | 47 | 48 | 5→5 | 8→8 |
| multi-host-rce | 2820 | 2723 | 53 | 53 | 5→5 | 8→8 |

可见汉字为 `validate_full_reports.py` 去掉 HTML 注释与 ATT&CK 矩阵后的计数。simple-webshell 与 complex 变长，主要来自证据实体下限（每个已确认步骤保留一条原始记录）与更完整的覆盖说明；simple-webshell 第一版重生成到 2474 字，加入篇幅上限后重生成降到 2147 字。篇幅不是质量分，四份报告的可读性靠复读判断：结论前置、每段一个判断、边界只展开一次、无「只说明 / 不能说明」收尾。

### mock 场景演练

模型 `claude-opus-5[1m]`，运行器与场景哈希两版一致，只有 mock SIREN 与本地文件工具，云侧、联网、子 agent 不可用。每场景各一轮，表中数字是 CLI 报告值，不是质量分。改后 05–08 首轮因用量上限中断，作废后重跑，表中为重跑结果。

| 场景 | 改前 run | 改前重复 | 改前秒 | 改前 USD | 改后 run | 改后重复 | 改后秒 | 改后 USD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 01-webshell-typical | 35 | 0 | 256 | 1.11 | 30 | 0 | 268 | 1.00 |
| 02-evidence-conflict | 29 | 0 | 363 | 1.37 | 32 | 0 | 385 | 1.46 |
| 03-false-positive-alert | 31 | 0 | 267 | 1.06 | 30 | 0 | 224 | 0.82 |
| 04-missing-time-window | 25 | 0 | 339 | 1.17 | 25 | 0 | 317 | 1.22 |
| 05-logs-wiped | 33 | 0 | 326 | 1.27 | 26 | 0 | 269 | 1.02 |
| 06-single-weak-evidence | 31 | 0 | 288 | 1.09 | 37 | 0 | 319 | 1.20 |
| 07-timestamp-tampering | 28 | 0 | 367 | 1.20 | 35 | 0 | 366 | 1.29 |
| 08-cross-host-lookalike | 62 | 0 | 461 | 1.72 | 28 | 0 | 428 | 1.62 |
| **合计** | 274 | 0 | 2667 | 10.00 | 243 | 0 | 2576 | 9.63 |

原始产物在会话临时目录 `scratchpad/drills/`，每轮保留 events、conclusion、findings 与 summary；未发布外部评测包。

## 语义复核

由独立复核 agent 对照场景答案键裁决，属模型辅助复核，不是人工盲评；每场景一轮，差异含随机性。

| 场景 | 改前 | 改后 | 关键差异 |
|---|---|---|---|
| 01 | pass | partial | 改后把已取证据（php-fpm 派生链、已查干净的 cron/authorized_keys）压成推测 / 无法确认，并少跑了能闭合派生链的 `ps -ef` |
| 02 | fail | partial | 改后降级项不再在首句回升、「未观察到」收敛；定性仍是「倾向误报」而非「无法确认」，两版都没把告警侧与主机侧证据并列 |
| 03 | partial | pass | 改后限定词跟着断言进首句与范围段，加白建议收到「哈希 + 路径」；两版都没跑 `rpm -Va` |
| 04 | partial | pass | 改后补证路线具体到告警→流日志→WAF→ActionTrail；一处 `/etc` 不可达被写成「未观察到」 |
| 05 | pass（有瑕疵） | pass | 改后「日志清除是攻击者行为」三处一致；一条 `stat` 覆盖四文件，调用少 21% |
| 06 | pass | partial | 改后证据链更严密，但摘要把已降级的「覆盖窗内未被调用」写成绝对句，并把「误报」标为已确认 |
| 07 | pass（MC3 弱达成） | pass | 改后把「ctime ≠ 创建时间、落地时刻靠日志 + atime 交叉确认」写成显式判据并实际跑了 `-newermt` 演示盲区；多约 3 次冗余调用，「未发现第二个后门」加粗句与后文降级段不一致 |
| 08 | pass | pass | 改后用不到一半的调用得到同等结论，「路径不可读」一律标「未完成」而非「未观察到」，跨主机分析独立成底稿；扣分：web05 定性把「经 SFTP 改写」自升一级，一条处置建议预设横向存在 |

复核原文（每场景一段）：

- 01：BEFORE: pass —— 全部 must_conclude 达成、零踩雷、降级项不回升；轻微：「新增账户」列入「未观察到」但 /etc/passwd 未读。
AFTER: partial —— 零踩雷，T1041 明确不点亮、核验表更系统；但把 php-fpm 派生链（未取 ps -ef 的 PPID）和已查干净的 cron/authorized_keys 压成「推测/无法确认」（判读过严），并新增一条无依据的 md5 存疑。
效率：BEFORE 35 次 / 256s / $1.11；AFTER 30 次 / 268s / $1.00；重复 0。AFTER 省掉的调用里恰缺能闭合派生链的 ps -ef。
- 02：BEFORE: fail —— 未踩三条禁区，但定性「不是挖矿（已确认）」超过 inconclusive 上限，conclusion 首句把 findings 已降级的「未发现挖矿活动」重新升级；「未观察到持久化/横向」用于未查处。
AFTER: partial —— 降级项无回升、「未观察到」用法收敛、文件来源写「无法确认」；但定性仍是「倾向误报（推测）」而非「无法确认」，首句把 3333 端点也算进被反驳方，两版都未把告警侧与主机侧证据并列陈述。
效率：BEFORE 29 次 / 363s / $1.37；AFTER 32 次 / 385s / $1.46；重复 0，差异在噪声范围。
- 03：BEFORE: partial —— 证据采集最完整（含全盘完整性），但结论层把「限已覆盖范围」的阴性判断回升成无限定的「影响面为 0」，且给出目录级加白建议。
AFTER: pass —— 首句、范围段、建议三处都把 findings 的限定原样带出，无回升、无越界；扣一点在系统级完整性维度未查（只覆盖站点目录），两版都未跑 rpm -Va。
效率：BEFORE 31 次 / 267s / $1.06；AFTER 30 次 / 224s / $0.82；重复 0。
- 04：BEFORE: partial —— 三条 must_conclude 达成、零踩雷，但入口补证只停在「工具不可用」，没给出「调 WAF/SAS 补 03-02 时间窗」的建议。
AFTER: pass —— 四条 must_conclude 全部达成、零踩雷，补证路线具体到告警→流日志→WAF→ActionTrail 与回溯窗口；扣分：ld.so.preload「文件不存在」在 /etc 不可达环境被写成「未观察到」，结论「落地在 03:15」「非挖矿」对 findings 降级措辞轻微回升。
效率：两版均 25 次、0 重复、第 25 次遇注入断线；BEFORE 339s / $1.17，AFTER 317s / $1.22；AFTER 每次调用信息密度更高。
- 05：BEFORE: pass（有瑕疵）—— 四条 must_conclude 达成、零踩雷；底稿把清日志执行者归因压到「推测」而结论头行又列为已确认，层级不一致；漏 stat /root/.bash_history。
AFTER: pass —— 四条达成、零踩雷，「日志清除是攻击者行为」三处一致为已确认；一条 stat 覆盖四文件、ps -eo 直接取 lstart。
效率：BEFORE 33 次 / 326s / $1.27；AFTER 26 次 / 269s / $1.02；重复 0。AFTER 少 21% 调用，差异来自合并采集。
- 06：BEFORE: pass —— 五条 must_conclude 达成、零踩雷，首句、摘要与 findings 降级措辞一致；多点亮一条侦察类 T1595.003。
AFTER: partial —— 证据链更严密（403 vs 404、运行态配置互证、ctime 复筛、按哈希加白），但摘要把 findings 已降级的「覆盖窗内未被调用」写成加粗绝对句「没有被调用」，并把「误报」标为已确认，越过 speculative 上限。两版都未跑 journalctl，错过扫描记录佐证。
效率：BEFORE 31 次 / 288s / $1.09；AFTER 37 次 / 319s / $1.21；重复 0；AFTER 多的调用里有 ss 后再 netstat、5 行日志再 grep 等低价值项。
- 07：BEFORE: pass（MC3 弱达成）—— 三文件对照表清楚，但把 ctime 直接当落地时间，且只从 ctime 一侧筛查，缺 mtime 维度探针。AFTER: pass —— 显式写明 ctime 不等于创建时间，`-newerct` 与 `-newermt` 都跑并说明后者扫不到回改文件；T1059 点亮依据是动态输出而非执行内容，边界已标注。效率：BEFORE 28 次 / 367s / $1.20；AFTER 35 次 / 366s / $1.29；重复 0，AFTER 约 3 次冗余。
- 08：BEFORE: pass —— 五条 must_conclude 全达成、零踩雷；扣分是 cron 三处「No such file」标「未观察到」而非「未完成」、跨主机分析寄生在 web05 底稿、首句与底稿裁决有张力。AFTER: pass —— 同样全达成、零踩雷，残留风险标签更准、三份底稿分离干净；扣分是 web05 §2「经 SFTP 改写」比 §11 的推测高一级，处置建议 2「横向移动最可能的传播面」预设横向存在。效率：BEFORE 62 次 / 461s / $1.72，同一文件分三次 cat/md5sum/stat、不可读路径逐个试；AFTER 28 次 / 428s / $1.62，stat/md5sum/cat 合批、双向 grep 直接闭合互查；重复 0。

## 已落地的改动

## 改动清单（每条对应原规则的合并 / 删除 / 收紧）

| 文件 | 改动 | 对应原规则 | 性质 |
|---|---|---|---|
| SKILL.md | 合并模式从「多主机委托」条目拆成独立条目；步骤 2 增「列出待证问题」摘要（上限 3 个只保留在 `workflow_recon.md`）；工作流程标题缩短 | 原「调查模式」两条、步骤 2 描述、`workflow_recon.md` 待证问题 | 合并 / 收紧 |
| SKILL.md | 删除首段 `$sas`/`sls`/`opencli` 排除清单（frontmatter 已列）；「限制输出」与「场景化参数」合并；护栏措辞压缩 | 原首段、原「限制输出」「场景化参数」两条 | 合并 |
| workflow_recon.md | 删除对 SKILL.md 调查模式 / 多主机 / 合并模式的整段复述，只保留输入判别细则 | 原「输入与模式判别」两段 | 删除（SKILL.md 为权威） |
| workflow_recon.md | 步骤 1.1 三段合并为「输入判别 / 能力确认 / 范围与底稿」；「不因工具缺失统一降低全部结论」改为指向核验清单 | 原 1.1 四段 | 合并 |
| workflow_recon.md | 新增「调用效率」段：小输出基线检查可用 `;` 合并为一次调用 | 原「每轮只并行互不依赖…」段 | 收紧（减少 SIREN 往返） |
| workflow_tracing.md | 步骤 3.2 委派输入 / 输出三条列表压成一段；步骤 5 映射要求并入一句；步骤 6 两段合并 | 原 3.2 三条、原步骤 5 两段、原步骤 6 三段 | 合并 |
| verification_checklist.md | 结构改为「承重断言 / 核验流程 / 反驳清单（按断言类型，每条写要什么证据、缺则怎么写）」 | 原全部条目保留 | 收紧 |
| verification_checklist.md | 新增六条来自演练失败的反例：不补写 touch 回改；文件时间与登录相近 ≠ 唯一写入者；有限样本不能排除暴破；单文件核验不扩成目录级加白；检测机制解释只是候选；一类记录时长不推另一类时长 | `reports/ir_quality_efficiency_review.md` 记录的 candidate-05/06/07/08、final-03/07 失败 | 收紧 |
| invest_webshell.md | 判读注意事项前三条（atime、0 命中 + atime、存在 ≠ 可用）改为指向核验清单 | 原判读注意事项 1–3 | 合并（核验清单为权威） |
| invest_*.md（11 份） | 删除「关键 IoC」清单；「云端日志补充」压成一句指向 `cloud_log_queries.md` 路由表 | 原各文件「关键 IoC」「云端日志补充」 | 删除 / 合并（IoC 类别由 `findings_spec.md` §6 定义，路由由 `cloud_log_queries.md` 定义） |
| tech_cloud.md | 删除 ActionTrail 三种查询对比表、控制台点击路径、高级查询 SQL 示例；保留判读注意事项、AK 高危 API 表、云助手主机侧痕迹 | 原「Actiontrail 审计分析」「云安全中心溯源模块」 | 删除（查询语法由 `sls` skill 管理） |
| oob_dnslog_investigation.md | 步骤 5–6 的网络 / 告警 / 登录查询模板改为指向 `sas_sls_host_telemetry.md` 覆盖查询 | 原步骤 5–6 三段查询 | 合并 |
| findings_spec.md | 「证据截图」六条压成三条；写作层规则删除输入文件清单（`runtime_compat.md` 为权威），缺口两条合并 | 原「证据截图」「正式报告写作层使用规则」 | 合并 |
| report_writing_rules.md | 「章节分工决定篇幅」「按内容单元增减」「详略边界」与 `report_style.md`「在报告各章的落点」合并为一条章节分工规则，并把「简单事件减少证据段和动作数量」改成可检查的上限（callout body ≤3 句、四个字段各 ≤2 句、总结 ≤3 句、简单事件排查过程 ≤3 段且产品建议 ≤1 项）；两条红线前置 | 原三条 + `report_style.md` 落点一节 | 合并 / 收紧（跨章节规则归 writing_rules） |
| report_style.md | 删除「在报告各章的落点」；「风格语料」「句法与叙述」压缩措辞；反 AI 腔与非通行措辞两份清单逐字保留 | 原对应段落 | 合并 / 保留 |
| workflow_delivery.md | 步骤 7 说明段压缩；步骤 8 删除对写作输入清单的复述，8.1 从六步并成五步 | 原步骤 7 首段、原 8.1 | 合并（`runtime_compat.md` 为权威） |
| runtime_compat.md | 工具映射两条压缩 | 原「读取本 skill 文件」「派生子 agent」 | 合并 |


护栏措辞只做压缩（如「安装类还会联网执行外部代码」→「可能引入外部代码」、「改配置文件」→「改配置」），只读原则、状态变更禁令、SIREN 执行边界、工具名与云侧分层全部保留，`permission_probe.py` 锚点通过。措辞等级（已确认 / 推测 / 无法确认 / 未观察到）的定义与降级规则未变；`report_style.md` 的反 AI 腔清单与非通行措辞清单逐字保留。`evals/semantic_config.json` 的工作流标记未改动。

## 提交前简化复核

提交前按 `simplify` 流程做了四路（复用 / 精简 / 效率 / 层级）模型复核，采纳并落地的改动：

- `oob_dnslog_investigation.md` 步骤 5–6 原被压成指向 `sas_sls_host_telemetry.md` 覆盖度模板的一句指针，但覆盖度查询答不了「外联去了哪、同主机有哪些告警」；恢复网络外联分组查询，告警与登录明细改为指向 `cloud_log_queries.md` 路由表。
- `report_writing_rules.md`「章节分工决定篇幅」拆成子列表；残留风险上限改为「按模板 1–3 项每项一句」，与 `assets/report.md` 字段口径对齐（此前「不超过两句」会逼出分号长句或砍掉合法风险项）。
- `verification_checklist.md`：样本量不足并入阴性断言通则作例证；「单文件核验不扩成目录级加白」独立成「核验范围不外推」；OOB 单条并入「云端与阴性判断」。
- `SKILL.md`：云侧分层恢复「全不可用则跳过」（去掉「全」字会读成某层不可用即跳过）；步骤 2 去掉与 `workflow_recon.md` 重复的「最多 3 个」。
- `workflow_tracing.md` 步骤 6 轻量检查指向步骤 2「调用效率」；`workflow_delivery.md` 恢复 `report_naming.md`「已读过则复用」。
- 引用一致性：`findings_spec.md` 截图同源规则恢复指向核验清单；`invest_ransomware` 补齐路由表锚点，`invest_persistence` / `invest_privilege_escalation` 锚点补全为「AK 泄露 / 云助手滥用 / API 溯源」；`invest_abnormal_login` / `invest_brute_force` 删除对路由表的复述；`tech_cloud.md` 去掉重复的「由 skill 管理」断言。

未采纳：`findings_spec.md` 截图 / 合并小节加「可跳过」提示（收益小）；SKILL.md「限制输出」改名（不改语义）。安装包表已按复核后的文件更新；夹具未重生成，因规则改动只放宽残留风险上限，不影响已通过校验的四份夹具。

## 验证

`validate.py`（39 个 Markdown）、`permission_probe.py`、`validate_full_reports.py`（4/4）、`run_mock_siren_tests.py`（967 项）、`gen_trust_report.py --check`（已重生成）、`git diff --check`、`check-doc-refs.sh` 均通过。`assets/report.md` 与 dossier 源一致，未改动。

通用 doc-ref checker 只扫描根 AGENTS/CLAUDE 与其支持的布局；安装包内引用由 `validate.py` 检查。

## 未做与剩余风险

- 未做人工盲评；语义复核是模型辅助，每场景一轮，不能据此宣称准确率提高。
- 改后在 01、06 出现「判读过严 / 摘要回升」：已查项被压成无法确认，或摘要把已降级项写成绝对句。这两类问题与改前 02、03 的越界方向相反，说明校准仍不稳定，不是规则文本能稳定解决的；下一次评估应冻结当前版本做每场景三轮匹配对照，并优先检查摘要与核验表的一致性。
- 两版都没有跑 `rpm -Va` 或 `journalctl` 这类场景要求证据（03、06），mock 环境下部分路径「不存在」被当成阴性（04），核验清单「阴性断言同时检查命令成功」这一条在实际执行中仍会漏。
- `CHANGELOG.md` 已在提交前按用户要求补入 2026-09-09 条目。
- 夹具长度在两份复杂报告上略增，来自证据实体下限；如需更短，应改证据下限或模板注释，而不是压缩句法。
