# 反向推理方法

Web 日志缺失 / 正向证据链断裂 / 只有应用日志时，用反向推理快速缩小漏洞范围（证据充分时不必）。

## 步骤

1. **定框架与版本**：进程命令行（jar 名、`-D` 参数）、框架标识文件（`pom.xml` / `package.json` / `composer.json`）、`nohup.out` 等启动日志里的 version。
2. **从日志提攻击特征**：搜 `error|exception|fail|fatal|forbidden|eval|exec|runtime`、异常请求路径；留意 **leetspeak 混淆**（`3v4l`、`sy5t3m`）。
3. **查框架历史漏洞**：搜 `<框架名> <版本> 漏洞|CVE|0day`。
4. **按特征锁定漏洞（捷径映射）**：
   - `rememberMe` → Shiro（默认密钥 / 反序列化）
   - `freemarker` → 模板注入
   - `fastjson` → 反序列化
   - SQL 报错 → SQL 注入
5. **验证**：云安全中心漏洞扫描结果 / 公开 PoC（searchsploit、GitHub，复现需客户授权）/ 代码审计。

## 案例：RuoYi Shiro

`/root/nohup.out` 见 `ruoyi-admin.jar` → 日志有 `/bin/sh` 启动尝试 → 搜 “RuoYi 历史漏洞” 命中 Shiro 默认密钥 → 日志搜 `rememberMe` 大量命中 → 反编译 / 复现确认。
