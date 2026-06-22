# 远程代码执行 (RCE) 调查指南

## 调查重点（只读检查项）

1. **确认漏洞利用**：access.log 里按命令执行特征筛 **`system(|exec(|passthru(|shell_exec(|反引号|%00`**，结合攻击 IP 的可疑 POST。
2. **执行的命令**：看 Web 服务器（nginx/apache/httpd，进程如 `java`/`php-fpm`/`w3wp.exe`）的异常子进程链。
3. **执行痕迹**：查 web 用户命令历史（如有）、进程启动记录。
4. **代码定位与后续**：源码里找 `system/exec/passthru/shell_exec/eval` 危险调用；查临时目录攻击时间窗的下载物与 web 用户的反向连接。

## 云端日志补充

按 `references/cloud_log_queries.md`「Web 类攻击」+「恶意进程」行用 `sls` skill 交叉验证：WAF 定位利用请求与真实 IP，SAS `aegis-log-process` 还原命令执行链/父进程（web 进程名如 `java`/`php-fpm`/`w3wp.exe`）、`aegis-log-network` 查后续外联。

## 关键 IoC
- 攻击源 IP
- 漏洞利用 URL 和 payload
- 执行的命令
- 下载的恶意文件

## ATT&CK 映射
- **T1190** - 利用面向公众的应用程序
- **T1059** - 命令和脚本解释器
- **T1105** - 远程文件复制（如果有下载行为）
