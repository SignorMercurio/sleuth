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
- `defang-attacker-ip` (1.0): 攻击者 IP 已转义
- `natural-evidence-terms` (1.0): 使用客户可理解的证据用语
- `state-coverage` (1.0): 写明日志覆盖边界

### Variant A

综上所述，本次是一起高度复杂的入侵攻击。攻击者从 http://203.0.113.45 上传 webshell，已确认完全控制了服务器。

### Variant B

2026 年 4 月 17 日，web01 触发 Webshell 通信告警。访问日志显示，203.0.113[.]45 向上传接口写入了 PHP 文件；随后取得的进程启动记录表明，Web 进程调用了命令解释器。综合现有证据，攻击者很可能已经通过该文件执行系统命令。现有日志自 4 月 10 日起覆盖，更早的活动无法确认。

## Case: response-actions

Prompt: 根据 findings 中尚未处置的 Webshell 事件，写「响应行动」章节的核心动作

Rubric:
- `no-vague-advice` (1.0): 不写空泛安全建议
- `pending-status-only` (1.0): 未取得处置记录时只使用未开始状态
- `concrete-actions` (1.0): 动作包含明确对象和动词
- `no-compressed-action-chain` (1.0): 不用分号把多项行动压成一句

### Variant A

建议加强安全意识，提高整体防护水平，安排定期巡检。

### Variant B

- [ ] 封禁 203.0.113[.]45 对业务入口的访问，并临时限制受影响的上传接口。
- [ ] 保全必要证据后移除 `/var/www/upload/x.php`，检查上传目录中是否还有同类文件。
- [ ] 修复上传接口，并验证上传目录不能解析或执行 PHP 文件。

## Case: single-atime-claim

Prompt: 某文件只有 atime 命中、无日志佐证，事件概述这条该怎么写

Rubric:
- `no-overclaim` (1.0): 孤证不写已确认
- `state-cannot-confirm` (1.0): 明确说明证据不足
- `no-process-meta` (1.0): 不写工作底稿式过程话术

### Variant A

该文件的 atime 在 18:00 前后更新，但扫描和备份也可能改变这一时间。由于缺少同期日志，无法据此确认攻击者曾访问该文件。

### Variant B

已确认攻击者于 18:00 访问了该文件。

## Case: attack-mapping-evidence

Prompt: 某 ATT&CK 技术无直接证据但这类攻击常用，要不要点亮

Rubric:
- `no-assume-light` (1.0): 不因常见行为点亮技术
- `state-evidence-result` (1.0): 直接写观察结果和矩阵结论
- `no-process-meta` (1.0): 不写规则执行过程

### Variant A

这类挖矿攻击通常会做持久化，因此点亮 T1053 计划任务。

### Variant B

现有记录中未发现计划任务或 systemd 持久化证据，因此不点亮 T1053。

## Case: cloud-evidence-coverage

Prompt: 云端 WAF 证据这段怎么写

Rubric:
- `state-time-window` (1.0): 写明日志时间窗
- `no-block-all` (1.0): 不夸大为全部拦截
- `waf-final-action` (1.0): WAF 拦截以 final_action 判定
- `defang-attacker-ip` (1.0): 攻击者 IP 已转义
- `no-compressed-prose` (1.0): 不用分号压缩多个判断

### Variant A

通过 WAF 日志发现攻击者 IP 198.51.100.23，已拦截全部攻击。

### Variant B

云防火墙日志覆盖 4 月 10 日至今，记录到来源 198.51.100[.]23 的请求。只有 `final_action` 为 `block` 的记录可以确认已拦截。观察模式下的请求不计入拦截结果。4 月 10 日以前的情况无法确认。
