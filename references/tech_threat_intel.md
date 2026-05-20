# 威胁情报利用

## 传统威胁情报平台

**常用平台**：
1. VirusTotal (https://www.virustotal.com)
2. 微步在线 (https://x.threatbook.cn)
3. 奇安信威胁情报中心 (https://ti.qianxin.com)
4. 360 威胁情报中心 (https://ti.360.cn)

**方法 1: 文件哈希查询**
```bash
md5sum <文件>
sha1sum <文件>
sha256sum <文件>
# 在威胁情报平台搜索哈希值
```

**方法 2: IP 地址查询** - 直接在威胁情报平台搜索攻击源 IP，查看 IP 归属地、历史攻击记录、恶意标签、关联的其他 IoC

**方法 3: 域名查询** - 搜索恶意域名，查看域名注册信息、历史解析记录、关联 IP、恶意标签

---

## VirusTotal 高级功能

### Graph 功能

**使用场景**：从已知 IoC 发现关联的其他 IoC

**操作步骤**：
1. 在 VirusTotal 搜索文件哈希或 IP
2. 点击 "Relations" 或 "Graph"
3. 可以看到文件之间的关联、文件与 IP/域名的关联、历史上传记录

**示例：oneinstack trojan 案例**
- 在 VirusTotal 社区发现 "oneinstack trojan" Graph
- Graph 中显示了恶意文件的别名和加载的动态链接库列表

### Community 标签

查看 VirusTotal 页面的 "Community" 标签，可以看到其他安全研究人员的分析报告，包含文件行为描述、相关的其他样本、攻击活动名称、防御建议。

---

## 广义威胁情报：搜索引擎

**核心思想**：互联网是最大的威胁情报源

### 搜索策略

**策略 1: 文件名/哈希搜索**
```
<文件名> malware
<文件名> trojan
<文件哈希> virus
```

**策略 2: 攻击活动搜索**
```
<框架名> <版本> 漏洞
<组件名> supply chain attack
<工具名> malware campaign
```

**策略 3: 错误信息搜索** - 将应用日志中的错误信息直接搜索，通常能找到相关的漏洞分析文章

**策略 4: GitHub 搜索**
```
在 GitHub 搜索漏洞 PoC、恶意软件分析、防御脚本
例如："oneinstack trojan"、"libprocesshider detection"、"Shiro rememberMe exploit"
```

**策略 5: 安全社区搜索**
- FreeBuf (https://www.freebuf.com)
- 先知社区 (https://xz.aliyun.com)
- 安全客 (https://www.anquanke.com)
- Exploit-DB (https://www.exploit-db.com)

---

## 威胁情报结合案例分析

**案例：供应链攻击**

1. **发现异常**：主机上发现可疑的 crond 进程
2. **常规检测无果**：威胁情报平台无法检出
3. **扩大搜索范围**：在 VirusTotal 社区发现 "oneinstack trojan"
4. **关联主机信息**：想起主机上有 oneinstack 目录
5. **搜索引擎深挖**：Google 搜索 "oneinstack trojan"
6. **找到详细分析**：在 GitHub Issue 中找到完整的事件报告
7. **验证结论**：检查主机上对应文件，确认被植入恶意代码

**关键点**：不要局限于单一威胁情报平台；留意主机上看似无关的信息；灵活使用搜索引擎；关注安全社区的讨论
