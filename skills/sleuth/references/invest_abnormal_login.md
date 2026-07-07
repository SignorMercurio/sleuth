# 异常登录调查指南

## 调查重点（只读检查项）

1. **登录详情**：从 `last`/`w`/`who` 与 `auth.log` 的 `Accepted` 记录确认用户、时间、来源。
2. **来源研判**：查来源 IP 归属；**判断是否代理/VPN/跳板**——来源 IP 未必是真实操作人（私网 IP 归因判读见 `references/ssh_login_attribution_sas.md`）。
3. **登录方式**：区分密码登录(`Accepted password`)与密钥登录(`Accepted publickey`)；密钥登录则核对该用户 `authorized_keys` 是否被植入。
4. **登录后活动 + 账户变更**：看该用户命令历史/进程/连接；查新增账户——**`awk -F: '$3>=1000'` 列普通用户**，并警惕与 root 同 UID(0) 的隐藏后门账户；查 `password changed`。

## 云端日志补充

主机 `auth.log`/`secure` 可能被清除或不含 RDP/数据库登录——按 `references/cloud_log_queries.md`「异常登录 / 暴力破解」行用 `sls` skill 查 SAS（`aegis-log-login` 原始登录遥测、`sas-security-log` 异常登录告警，注意区分两者）。

## 关键 IoC
- 登录用户名
- 登录来源 IP 和地理位置
- 登录时间
- 登录方式（密码/密钥）
- 登录后执行的操作

## ATT&CK 映射
- **T1078** - 有效账户（初始访问）
- **T1021.004** - SSH（横向移动）
- **T1552.004** - 私钥（凭证访问，如果涉及）
