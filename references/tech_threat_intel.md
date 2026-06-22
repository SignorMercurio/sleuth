# 威胁情报利用

## 平台与查询

- **威胁情报平台**：VirusTotal (https://www.virustotal.com)、微步在线 (https://x.threatbook.cn)、奇安信 (https://ti.qianxin.com)、360 (https://ti.360.cn)。查文件哈希 / 攻击源 IP / 恶意域名的标签、归属、历史与关联 IoC。
- **VirusTotal 进阶**：多数人只看检出结果——**"Relations"/"Graph"** 从已知 IoC 发现关联文件/IP/域名与别名、加载的 so；**"Community"** 标签有其他研究者的行为分析、关联样本、攻击活动名。

## 广义情报：搜索引擎是最大情报源

- **搜索策略**：`<文件名/哈希> malware|trojan|virus`；`<框架名> <版本> 漏洞|CVE`；把**应用日志里的报错原文**直接搜常能命中漏洞分析文；GitHub 搜 PoC / 恶意分析 / Issue 里的完整事件报告；安全社区 FreeBuf、先知 (xz.aliyun.com)、安全客、Exploit-DB。

## 方法要点（案例：oneinstack 木马）

平台直接检出无果时，**留意主机上看似无关的线索**反推：主机有 `oneinstack` 目录 → 搜 "oneinstack trojan" → VT 社区 / GitHub Issue 找到完整分析 → 回主机核对对应文件确认被植入。不要局限单一平台，灵活用搜索引擎与社区讨论。
