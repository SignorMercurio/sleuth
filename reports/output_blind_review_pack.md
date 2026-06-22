# Output Blind A/B Review Pack

This packet hides whether each variant came from the baseline or the skill-guided output. Use the separate answer key only after review.

- Pairs: `5`
- Seed: `yao-output-eval-blind-v1`
- Answer key separate: `True`

## Case: overview-from-findings

Prompt: 根据这份 findings 写报告的「事件概述」段落

Rubric:
- `no-three-part-closer` (1.0): 无三段式收尾套话
- `no-vague-praise` (1.0): 无空洞评价词
- `no-raw-protocol` (1.0): IoC 协议 defang，不出现裸 http
- `use-defanged-protocol` (1.0): 使用 defang 协议 hxxp
- `state-coverage` (1.0): 写明日志覆盖边界

### Variant A

综上所述，本次是一起高度复杂的入侵攻击。攻击者从 http://203.0.113.45 上传 webshell，已确认完全控制了服务器。

### Variant B

web01 于 4 月 17 日触发 webshell 告警。结合 access 日志与 SAS 进程遥测交叉判断，攻击者经上传点写入 webshell 并访问，大概率得手；访问来源 hxxp://203.0.113[.]45。access 日志覆盖自 4 月 10 日起，更早区间已轮转、无法确认。

## Case: response-actions

Prompt: 写「响应行动」章节的处置动作

Rubric:
- `no-vague-advice` (1.0): 不写空泛的加强安全意识
- `no-faceless-improve` (1.0): 不写无主体的提高类套话
- `concrete-verb` (1.0): 动作以具体动词开头

### Variant A

建议加强安全意识，提高整体防护水平，安排定期巡检。

### Variant B

封禁 203.0.113[.]45 的入站访问；下线并取证 webshell 文件 /var/www/upload/x.php；重置 web 服务相关账号口令并核查上传点修复。

## Case: single-atime-claim

Prompt: 某文件只有 atime 命中、无日志佐证，事件概述这条该怎么写

Rubric:
- `no-overclaim` (1.0): 孤证不写已确认
- `use-cannot-confirm` (1.0): 证据不足写无法确认
- `mark-inference` (1.0): 标注推测

### Variant A

该文件 atime 在 18:00 前后更新，但 atime 可能被扫描或备份刷新，缺日志佐证，无法确认即攻击者访问，按推测记录并交叉其他证据。

### Variant B

已确认攻击者于 18:00 访问了该文件。

## Case: attack-mapping-evidence

Prompt: 某 ATT&CK 技术无直接证据但这类攻击常用，要不要点亮

Rubric:
- `no-assume-light` (1.0): 不因常见就点亮技术
- `state-not-observed` (1.0): 无证据写未观察到
- `evidence-driven` (1.0): 以证据为准

### Variant A

这类挖矿攻击通常会做持久化，因此点亮 T1053 计划任务。

### Variant B

未观察到计划任务或 systemd 持久化的直接证据，按证据驱动原则不点亮该技术，仅在证据缺口里说明。

## Case: cloud-evidence-coverage

Prompt: 云端 WAF 证据这段怎么写

Rubric:
- `state-time-window` (1.0): 写明日志时间窗
- `no-block-all` (1.0): 不夸大为全部拦截
- `waf-final-action` (1.0): WAF 拦截以 final_action 判定

### Variant A

通过 WAF 日志发现攻击者 IP 198.51.100.23，已拦截全部攻击。

### Variant B

云防火墙 WAF 日志（覆盖 4 月 10 日至今）显示攻击源 198.51.100[.]23；其中 final_action 为 block 的记录才是实际拦截，观察模式不计入。最早记录 4 月 10 日，更早无法确认。
