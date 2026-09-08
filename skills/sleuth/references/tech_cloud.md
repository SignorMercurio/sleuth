# 云环境特有技巧

## 云助手命令日志

**重要性**：AK 泄露后通过 `RunCommand` / `InvokeCommand` 下发命令的攻击，云侧绕开 SSH/WebShell 入口，主机也无 `bash_history` 痕迹——只能靠这里。云助手命令日志是溯源的关键证据，且**无法在控制台删除**。

### 主机侧痕迹（SIREN 可直接捞 — Linux）

**进程父链只作路由线索**：祖先含 `aliyun-service` / `aliyun_assist_main` 时，核对 task/invocation、命令、实例和执行时间，再关联云侧事件。合法云助手任务启动的长期服务后来被利用，也会保留该祖先；不能仅凭父链确认本次攻击由 RunCommand 下发，更不能直接推定 AK 泄露。

```bash
# agent 主进程：aliyun-service 是常驻 daemon，aliyun_assist_main 是执行任务时短暂派生的工作进程
pgrep -fa 'aliyun-service|aliyun_assist'

# 当前由 agent 派生的子孙进程（仅活进程；历史任务靠下面的日志 + ActionTrail 复盘）
pid=$(pgrep -fo 'aliyun-service'); [ -n "$pid" ] && pstree -ap "$pid"
```

**命令执行日志**：`/var/log/aliyun/assist/<ver>/aliyun_assist_main.log` 含 task id、命令、执行时间、stdout/stderr 截断。按大小轮转，旧日志同目录 `.gz`。

```bash
# 先确认版本目录（升级后可能有多个历史版本残留）
ls -lt /var/log/aliyun/assist/

# 最近任务
tail -n 200 /var/log/aliyun/assist/<ver>/aliyun_assist_main.log

# 提取所有 task id、命令片段、时间戳
grep -E 'taskId|invokeId|RunCommand|Execute|cmd' /var/log/aliyun/assist/<ver>/aliyun_assist_main.log

# 历史归档
zgrep -E 'taskId|RunCommand' /var/log/aliyun/assist/<ver>/aliyun_assist_main.log.*.gz
```

**临时脚本落地**：

```bash
# script 类型任务在 /tmp 建临时目录，留有原始脚本和 stdout 副本
ls -lat /tmp/AliyunAssistScript-*/ 2>/dev/null

# cloud-init 阶段下发的脚本
ls -lat /var/lib/cloud/instance/scripts/ 2>/dev/null
```

**Agent 自身路径**：
```
/usr/local/share/aliyun-assist/<ver>/aliyun-service     # 常驻 daemon
/usr/local/share/aliyun-assist/<ver>/aliyun_assist_main # 执行任务的工作进程
systemctl status aliyun.service                          # systemd 单元
```

**判定"未预期"任务**：执行时间落在攻击窗口内 / 命令含外网下载（`curl|wget`）写 cron 改 `sshd_config` 等典型恶意行为 / ActionTrail 中对应 RunCommand 的 `sourceIpAddress` 不在已知运维网段。

### 主机侧痕迹（SIREN 可直接捞 — Windows）

进程：`AliyunService.exe`；日志：`C:\ProgramData\aliyun\assist\<ver>\log\`；脚本暂存：`C:\ProgramData\aliyun\assist\work\script\`。父链判读与 Linux 一致，须继续对齐任务与事件。

### 云侧入口（交叉验证）

控制台路径：
```
ECS 控制台 -> 运维与监控 -> 云助手 -> 命令执行结果
```

拿到主机侧 task/invocation ID、实例与时间戳后，回查 ActionTrail 的 `RunCommand` / `InvokeCommand` / `CreateCommand` 事件，核对命令与成功状态，再识别 `sourceIpAddress`、`userIdentity` 及凭据类型（长期 AK、角色/临时会话等）。将任务关联、API 调用身份、非预期使用和凭据泄露分别裁决；查不到任务对应关系就保留缺口，不把长期服务的祖先链当成当前任务证据。

云安全中心侧有"云助手异常命令"和"CreateCommand 可疑命令"告警可作触发线索；批量主机感染时优先翻这块日志。

---

## Actiontrail 审计分析

### 三种查询功能对比

| 功能 | 覆盖范围 | 特点 |
|------|---------|------|
| AccessKey 审计 | 所有类型事件（管控+数据） | 只记录每个云产品的最后一次调用时间，每个 API 最后一次管控事件详情 |
| 事件查询 | 90 天内管控事件 | 完整的 API 调用记录列表 |
| 高级查询 | 需提前创建跟踪 | 支持 90 天以前数据，可投递到 SLS 进行复杂查询 |

### 使用技巧

**快速定位可疑 AK**：
```
AccessKey 审计 -> 查看 AK 调用的云产品
重点关注：
- ECS: RunCommand (云助手)
- RAM: CreateUser, AttachPolicyToUser (创建后门账号)
- SAS: ModifySecurityCheckScheduleConfig (修改安全配置)
```

**梳理攻击时间线**：
```
事件查询 -> 按时间排序
关注第一次异常调用的时间（AK 开始被利用的时间）
```

**复杂查询场景（需高级查询）**：
```sql
-- 查询同一攻击者（源 IP）的所有调用
SELECT * WHERE sourceIpAddress = '<攻击IP>'

-- 查询特定 AK 的所有敏感操作
SELECT * WHERE userIdentity.accessKeyId = '<AK>'
AND eventName IN ('RunCommand', 'CreateUser', 'AttachPolicyToUser')

-- 梳理 AK 白名单（统计所有 AK 及其调用次数）
SELECT userIdentity.accessKeyId, COUNT(*) cnt
GROUP BY userIdentity.accessKeyId ORDER BY cnt DESC
```

### 注意事项

1. **无 errorCode 不等于成功**：部分 API（如 DescribeInstances）权限不足时不会返回 errorCode，而是直接返回空数据，需结合 AK 实际权限判断
2. **操作者名称大小写敏感**：角色名称可能在事件查询中显示为小写（如 `AliyunServiceRoleForECSWorkbench` 显示为 `aliyunserviceroleforecsworkbench`），导致查询不到记录
3. **数据事件需要单独投递**：默认只记录管控事件，数据事件（如 OSS GetObject）需要创建跟踪并投递

---

## AK 泄露利用方式总结

按目的归类的高危 API（在 ActionTrail 按 `eventName` 检索，重点核 `sourceIpAddress` 与 `userIdentity`）：

| 目的 | 关键 API |
|---|---|
| 控制台操作 | `ConsoleSignin`、`ModifySecurityCheckScheduleConfig`（处置告警）、`Describe*`（查资源） |
| 主机控制 | `RunCommand`（云助手执行）、`ModifyInstanceAttribute`（改 root 密码）、`ModifyInstanceVncPasswd`、`RebootInstance`、`StartTerminalSession`（Workbench 免密登录） |
| 权限提升 | `CreateUser`、`AttachPolicyToUser`、`UpdateRole` / `AttachPolicyToRole`、`CreateAccessKey` |
| 数据窃取 | `DescribeInstances`、`ListBuckets`、`GetObject`、`CreateSnapshot` / `ExportImage` |
| 痕迹清除 | `DeleteSnapshot`、`DeleteTrail`、`UpdateLogStore` |

**检测**：ActionTrail 敏感 API 调用 + 云安全中心 AK 异常调用告警 + 源 IP 非预期地域 + 创建时间较新的 RAM 用户。

---

## 云安全中心溯源模块

**使用场景**：了解攻击者执行的完整命令序列、查看进程启动链和父子关系、确定恶意文件植入方式

**使用方法**：
```
云安全中心 -> 告警详情 -> 溯源模块
或
云安全中心 -> 调查响应 -> 进程启动 -> 选择时间范围
```

**能看到的信息**：完整的进程启动链、进程启动时间、进程命令行参数、父进程信息

**局限性**：只能看到云安全中心已记录的进程启动日志；未安装时期无法查询；日志保留时间有限

**技巧**：结合进程启动时间查询 WAF 日志；通过父进程确定攻击来源（如 VNC 登录）
