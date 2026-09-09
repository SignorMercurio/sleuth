# 云环境特有技巧

## 云助手命令日志

AK 泄露后通过 `RunCommand` / `InvokeCommand` 下发命令的攻击，绕开 SSH/WebShell 入口，主机也无 `bash_history` 痕迹，只能靠云助手命令日志溯源；该日志**无法在控制台删除**。

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

## ActionTrail 审计要点

投递方式与查询语法见 `sls` skill，免费事件窗与控制台功能见 `opencli-aliyun-ir`；本节只写判读要点。

- AccessKey 审计只记录每个云产品/API 的最后一次调用；完整调用列表靠事件查询（90 天内管控事件），更早或复杂关联需要已投递 SLS 的跟踪。
- **无 `errorCode` 不等于成功**：部分 API（如 `DescribeInstances`）权限不足时直接返回空数据，需结合 AK 实际权限判断。
- 操作者名称大小写敏感：角色名可能以小写出现（`AliyunServiceRoleForECSWorkbench` → `aliyunserviceroleforecsworkbench`），查不到先换大小写。
- 数据事件（如 OSS `GetObject`）默认不记录，需单独创建跟踪投递。
- 时间线以第一次异常调用为 AK 开始被利用的时间；同一 `sourceIpAddress` 或 `userIdentity.accessKeyId` 的全部调用一起看。

## AK 泄露利用方式总结

按目的归类的高危 API（按 `eventName` 检索，重点核 `sourceIpAddress` 与 `userIdentity`）：

| 目的 | 关键 API |
|---|---|
| 控制台操作 | `ConsoleSignin`、`ModifySecurityCheckScheduleConfig`（处置告警）、`Describe*`（查资源） |
| 主机控制 | `RunCommand`（云助手执行）、`ModifyInstanceAttribute`（改 root 密码）、`ModifyInstanceVncPasswd`、`RebootInstance`、`StartTerminalSession`（Workbench 免密登录） |
| 权限提升 | `CreateUser`、`AttachPolicyToUser`、`UpdateRole` / `AttachPolicyToRole`、`CreateAccessKey` |
| 数据窃取 | `DescribeInstances`、`ListBuckets`、`GetObject`、`CreateSnapshot` / `ExportImage` |
| 痕迹清除 | `DeleteSnapshot`、`DeleteTrail`、`UpdateLogStore` |

**检测**：ActionTrail 敏感 API 调用 + 云安全中心 AK 异常调用告警 + 源 IP 非预期地域 + 创建时间较新的 RAM 用户。

## 云安全中心溯源模块

告警详情的溯源模块与「调查响应 → 进程启动」能看完整进程启动链、启动时间、命令行与父进程，等价于 `aegis-log-process` 遥测；只覆盖已记录时段，未安装时期无法查询。用父进程确定攻击来源（如 VNC 登录），结合进程启动时间查 WAF 日志。
