# 反向推理方法

## 什么时候使用反向推理

**适用场景**：
- Web 日志缺失或不完整
- 正向证据链无法构建
- 只有应用日志或系统日志
- 需要快速缩小漏洞范围

**不适用场景**：证据充分的情况、可以直接定位漏洞的情况

---

## 反向推理步骤

### 步骤 1: 确定应用框架和版本

**方法 1: 检查进程信息**
```bash
ps aux | grep java
# 从命令行参数中提取 jar 包名称

ps aux | grep -E "node|python|php|ruby"
```

**方法 2: 检查主机文件**
```bash
# 常见框架标识文件
find / -name "pom.xml" -o -name "package.json" -o -name "composer.json" 2>/dev/null

# 常见日志文件中的框架信息
grep -r "framework\|version" /opt /var/log 2>/dev/null | grep -i "spring\|struts\|ruoyi"

# 检查 nohup.out 等启动日志
cat /root/nohup.out | grep -i "started\|version"
```

**方法 3: 反编译 jar 包**
```bash
unzip -q app.jar -d app_source
cat app_source/META-INF/MANIFEST.MF
```

### 步骤 2: 从日志中提取攻击特征

**在应用日志中搜索关键词**：
- `warn`, `error`, `fail`, `fatal`
- `wrong`, `not permitted`, `not allowed`, `forbidden`
- `cannot`, `unable`, `5xx`, `exception`, `stacktrace`
- `eval`, `exec`, `runtime`
- Leetspeak (如 `3v4l`, `sy5t3m`)

```bash
# 搜索错误和异常
grep -iE "error|exception|fail|fatal" /path/to/app.log | tail -n 100

# 搜索可疑的执行行为
grep -iE "eval|exec|runtime|getruntime|processbuilder" /path/to/app.log

# 搜索异常的请求路径
grep "request" /path/to/app.log | grep -v "^#" | awk '{print $NF}' | sort -u
```

### 步骤 3: 查询框架历史漏洞

**搜索策略**：
```
<框架名> <版本> 历史漏洞
<框架名> <版本> CVE
<框架名> vulnerability
<框架名> 0day
```

**根据攻击特征排除漏洞**：
- 日志中有 `rememberMe` -> 可能是 Shiro 漏洞
- 日志中有 `freemarker` -> 可能是模板注入
- 日志中有 `fastjson` -> 可能是反序列化
- 日志中有 SQL 错误 -> 可能是 SQL 注入

### 步骤 4: 验证猜测

**方法 1: 云安全中心漏洞扫描**
```
检查云安全中心 -> 漏洞管理 -> 应用漏洞
看是否已经扫描出对应的漏洞
```

**方法 2: 漏洞复现（需客户授权）**
```bash
# 查找公开 PoC
searchsploit <漏洞名称>
# 或在 GitHub 搜索
```

**方法 3: 代码审计**
```bash
# 反编译应用，根据日志中的堆栈信息追踪代码
# 分析是否存在对应的漏洞点
```

### 步骤 5: 反向查找支撑证据

```bash
# 如果怀疑是 Shiro 漏洞
grep -i "shiro\|rememberme\|cipher" /path/to/logs/*

# 如果怀疑是 RCE
grep -iE "runtime|exec|processbuilder|/bin/sh|/bin/bash" /path/to/logs/*

# 如果怀疑是文件上传
grep -i "upload\|multipart\|filename" /path/to/logs/*
```

---

## 反向推理案例示例

**案例：RuoYi Shiro 漏洞**

1. **发现应用框架**：在 `/root/nohup.out` 中发现 `ruoyi-admin.jar`
2. **提取攻击特征**：日志中发现 `/bin/sh` 启动尝试和异常请求路径
3. **查询历史漏洞**：搜索 "RuoYi 历史漏洞"，发现 Shiro 默认密钥漏洞
4. **反向验证**：在日志中搜索 `rememberMe`，发现大量相关记录
5. **确认结论**：通过反编译 jar 包、复现漏洞等方式最终确认
