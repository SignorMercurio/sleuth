# 攻击手法对抗

## libprocesshider 进程隐藏

### 典型特征

**现象**：CPU 使用率极高（接近 100%），使用 `ps`, `top`, `lsof` 找不到高 CPU 进程，网络连接存在但看不到对应进程。

### 检测方法

**方法 1: 检查网络连接**
```bash
# 查找没有进程信息的网络连接
netstat -antup | grep -v "PID"
ss -antp

# 如果看到类似这样的输出，说明进程被隐藏：
# tcp  0  0  10.0.0.1:54321  1.2.3.4:3333  ESTABLISHED -
#                                                      ^ 这里应该显示 PID/进程名
```

**方法 2: 使用 chkrootkit**
```bash
yum install chkrootkit  # CentOS
apt install chkrootkit  # Ubuntu
chkrootkit
# 重点关注 /etc/ld.so.preload 检查结果
```

**方法 3: 使用 unhide**
```bash
yum install unhide  # CentOS
apt install unhide  # Ubuntu
unhide proc
# 会列出被隐藏的进程
```

**方法 4: 检查 ld.so.preload**
```bash
ls -la /etc/ld.so.preload
cat /etc/ld.so.preload
# 通常客户系统中默认不存在此文件，如果存在大概率是攻击者添加的
```

### 原理分析

**利用方式**：
```bash
# 1. 修改 processhider.c 中的进程名
static const char* process_to_filter = "xmrig";  # 要隐藏的进程名

# 2. 编译
gcc -Wall -fPIC -shared -o libprocesshider.so processhider.c -ldl

# 3. 加载
echo "/usr/local/lib/libprocesshider.so" >> /etc/ld.so.preload
# 或
export LD_PRELOAD=/usr/local/lib/libprocesshider.so
```

**原理**：利用 `LD_PRELOAD` 或 `/etc/ld.so.preload` 优先加载恶意动态链接库，覆盖 glibc 的 `readdir` 和 `readdir64` 函数，当 ps、lsof 等工具遍历 /proc 目录时跳过指定进程名。

### 识别 libprocesshider 文件

**方法 1**: 上传到 VirusTotal、微步在线等平台

**方法 2**: 检查 .rodata 段
```bash
readelf -p .rodata <so文件>
# 查找特征字符串：/proc/self/fd/%d, /proc/%s/stat, readdir64, readdir
# 第一个字符串通常就是被隐藏的进程名
```

**方法 3**: IDA 逆向分析 - Functions 列表中只有 4 个有效函数：get_dir_name, get_process_name, readdir, readdir64

### 清除方法

**步骤 1: 删除动态链接库文件**
```bash
cat /etc/ld.so.preload
env | grep LD_PRELOAD
rm -f /path/to/malicious.so
```

**步骤 2: 阻止加载**
```bash
# 方法 A: 删除 ld.so.preload 中的加载行（如果只有一行，直接删除文件）
rm -f /etc/ld.so.preload

# 方法 B: 删除环境变量设置
grep -r "LD_PRELOAD" /etc/profile* /root/.* /home/*/.*
```

**步骤 3: 清除隐藏的进程**
```bash
unhide proc
kill -9 <PID>
```

**步骤 4: 检查残留后门**
```bash
crontab -l
ls -la /etc/cron.* /var/spool/cron/
netstat -antup
ss -antp
systemctl list-unit-files --type=service | grep -i mining
```

**注意**：如果 `chattr`、`lsattr` 等命令也被篡改，使用 busybox 恢复：
```bash
wget https://busybox.net/downloads/binaries/1.35.0-x86_64-linux-musl/busybox
chmod +x busybox
./busybox chattr -ai /usr/bin/chattr
rm -f /usr/bin/chattr
yum reinstall e2fsprogs  # CentOS
apt install --reinstall e2fsprogs  # Ubuntu
```

---

## 系统命令替换

### 检测方法

**使用系统包管理器验证**：
```bash
# CentOS/RHEL
rpm -V procps-ng  # 验证 ps, top 等命令
rpm -V coreutils  # 验证 ls, cat 等命令
rpm -Va           # 验证所有已安装的软件包

# Ubuntu/Debian
dpkg -V procps
dpkg -V coreutils
dpkg -V
```

**输出含义**：
```
S.5....T.  /usr/bin/top
```
S=文件大小改变, M=权限改变, 5=MD5改变, D=设备号改变, L=符号链接改变, U=用户改变, G=组改变, T=修改时间改变

如果系统命令被替换，通常会看到 `S.5....T.` 的标记。

### 恢复方法

**标准恢复流程**：
```bash
yum reinstall procps-ng     # CentOS
apt install --reinstall procps  # Ubuntu
```

**如果无法安装（文件不可变）**：

1. 检查文件属性：`lsattr /usr/bin/top`（如果显示 `----i--------`，说明设置了不可变属性）
2. 尝试 `chattr -ai /usr/bin/top`
3. 如果 chattr 也被篡改，使用 busybox：
```bash
wget https://busybox.net/downloads/binaries/1.35.0-x86_64-linux-musl/busybox
chmod +x busybox
./busybox chattr -ai /usr/bin/top
./busybox chattr -ai /usr/bin/chattr
./busybox chattr -ai /usr/bin/lsattr
rm -f /usr/bin/top /usr/bin/chattr /usr/bin/lsattr
yum reinstall procps-ng e2fsprogs
```

### 防御建议
```bash
# 定期执行完整性检查
rpm -Va > /var/log/rpm-verify-$(date +%Y%m%d).log  # CentOS
dpkg -V > /var/log/dpkg-verify-$(date +%Y%m%d).log  # Ubuntu

# 使用 AIDE (Advanced Intrusion Detection Environment)
yum install aide && aide --init && aide --check
```

---

## Python 标准库注入

### 典型案例

**现象**：系统进程（如 systemd-logind）被注入，无法通过常规方法清除。

### 检测方法
```bash
# 使用 rpm/dpkg 检查 Python 标准库
rpm -V python2  # CentOS
rpm -V python3
dpkg -V python2.7  # Ubuntu
dpkg -V python3

# 重点关注 os.py, sys.py 等核心模块
```

**分析被篡改的文件**：
```bash
stat /usr/lib/python2.7/os.py
stat /usr/lib64/python2.7/os.py
grep -n "import\|__init__\|CDLL" /usr/lib/python2.7/os.py
```

**常见植入位置**：`os.py` 的 `__init__` 函数、`site.py` 的初始化代码、`sitecustomize.py`

**典型植入代码**：
```python
from ctypes import CDLL
CDLL('/path/to/malicious.so')
```

### 清除方法

```bash
# 方法 1: 重新安装 Python
yum reinstall python2  # CentOS
apt install --reinstall python2.7  # Ubuntu

# 方法 2: 从备份恢复（从其他正常主机复制相同版本的 Python 文件）

# 方法 3: 手动删除恶意代码（编辑被篡改的文件，删除 CDLL 加载代码）
```

### 检测工具

**使用 sysdig 抓取文件访问**：
```bash
curl -s https://s3.amazonaws.com/download.draios.com/stable/install-sysdig | bash
sysdig proc.name=python | grep open
# 可以看到 Python 打开了哪些 .so 文件
```
