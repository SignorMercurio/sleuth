# 攻击手法对抗

> ⚠️ **执行边界**：本文件区分两类命令。**检测/取证类**（`ls`/`cat`/`readelf`/`rpm -V`/`stat`/`netstat` 等只读命令）可经 SIREN 在受害主机执行；**处置/修复/安装类**（`rm`/`kill`/`chattr`/`reinstall`/`gcc`/`wget`/`curl … | bash` 等）一律「⚠️ 供客户执行，SIREN 不运行」——会破坏证据完整性、违反只读护栏，安装类还会在受害主机联网拉取并执行外部代码。这些处置步骤写入报告「响应行动」作建议。

## libprocesshider 进程隐藏

- **现象**：CPU 接近 100% 但 `ps`/`top`/`lsof` 找不到高 CPU 进程；有网络连接却看不到对应进程（`netstat -antup` 里那条连接的 PID/进程名为空 `-`）。
- **原理**：`LD_PRELOAD` 或 `/etc/ld.so.preload` 优先加载恶意 so，劫持 glibc 的 `readdir`/`readdir64`，遍历 /proc 时跳过指定进程名。
- **检测**：查 `/etc/ld.so.preload`（客户系统通常默认不存在，存在大概率是攻击者加的）；拿到可疑 so 后 **`readelf -p .rodata <so>`** 找特征串 `/proc/self/fd/%d`、`/proc/%s/stat`、`readdir64`、`readdir`（第一个串常是被隐藏的进程名）；IDA 看到 **仅 4 个有效函数 `get_dir_name`/`get_process_name`/`readdir`/`readdir64`** 即可坐实。
- **清除（⚠️ 客户执行）**：删 so 与 ld.so.preload 加载行、清 `LD_PRELOAD` 环境变量、`unhide proc` 后 `kill -9`。

## 系统命令替换

- **检测**：`rpm -V <包>` / `rpm -Va`（RHEL）或 `dpkg -V`（Debian）。**标记位含义**：`S` 大小、`M` 权限、`5` MD5、`D` 设备号、`L` 符号链接、`U` 属主、`G` 组、`T` 修改时间——命令被替换通常见 `S.5....T.`。
- **恢复（⚠️ 客户执行）**：`yum/apt reinstall <包>`。**若文件被设不可变位**（`lsattr` 显示 `----i-`）需先 `chattr -ai`；**连 chattr 也被篡改时用 busybox 兜底**（`./busybox chattr -ai /usr/bin/<cmd>` 后再删并 reinstall）。

## Python 标准库注入

- **现象**：系统进程（如 systemd-logind）被注入，常规手段清不掉。
- **检测**：`rpm -V python2/python3` / `dpkg -V`；重点核 `os.py`、`site.py`、`sitecustomize.py`，看是否有 **`from ctypes import CDLL; CDLL('/path/to/malicious.so')`** 注入。
- **清除（⚠️ 客户执行）**：`reinstall` Python，或从同版本正常主机复制覆盖，或手删 CDLL 加载代码。
