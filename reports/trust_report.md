# SLEUTH 信任报告（Trust Report）

生成时间：`2026-08-26T05:47:06Z`

总体结论：**通过**

> Generated for the governed-release trust-report gate (reports/review_waivers.json, gate_key=trust-report).
> package_hash reflects skills/sleuth/ at generation time; regenerate before closing the waiver if that package changed since.

## 1. 密钥与凭据扫描（secret scan）

- 扫描文件数：117（跳过二进制/不可解码文件 10 个）
- 规则：
  - `aliyun_ak_sk`：Aliyun AccessKeyId: LTAI prefix followed by 12-30 alnum chars
  - `private_key_block`：PEM private key BEGIN marker (RSA/EC/DSA/OPENSSH/ENCRYPTED)
  - `credential_assignment`：token/password/passwd/api_key/access_key/secret_key assigned a quoted literal of 6+ chars; obvious placeholders are excluded
  - `high_entropy_string`：plain alnum run of 24+ chars containing a digit, not a pure-hex digest, Shannon entropy >= 4.0 bits/char; skips ssh-rsa/ssh-ed25519/ssh-dss/ecdsa-sha2-* public-key lines (public by design, not a credential)
- 命中数：**0**
- 结论：未发现凭据泄露
- 说明：`scripts/gen_trust_report.py` 对规则 `credential_assignment, private_key_block` 自排除——this scanner's own source embeds the literal rule markers it uses to detect them

## 2. 脚本执行面（script surface）

| 脚本 | 入口 | 网络访问 | 子进程 | 文件写入范围 |
| --- | --- | --- | --- | --- |
| `scripts/gen_trust_report.py` | `python3 scripts/gen_trust_report.py` | 否 | 否 | write call present; resolves to reports/ (static) |
| `scripts/permission_probe.py` | `python3 scripts/permission_probe.py` | 否 | 否 | no file-write call detected (static) |
| `scripts/validate.py` | `python3 scripts/validate.py (flat script, executes at import time, no __main__ guard)` | 否 | 否 | no file-write call detected (static) |
| `evals/output/validate_full_reports.py` | `python3 evals/output/validate_full_reports.py` | 否 | 否 | write call present; resolves to reports/ (static) |
| `evals/runtime/compliance/__init__.py` | `evals/runtime/compliance/__init__.py (imported module, no CLI entry point found)` | 否 | 否 | no file-write call detected (static) |
| `evals/runtime/compliance/check_transcript.py` | `python3 evals/runtime/compliance/check_transcript.py` | 否 | 否 | no file-write call detected (static) |
| `evals/runtime/compliance/rules.py` | `evals/runtime/compliance/rules.py (imported module, no CLI entry point found)` | 否 | 否 | no file-write call detected (static) |
| `evals/runtime/mock_siren/__init__.py` | `evals/runtime/mock_siren/__init__.py (imported module, no CLI entry point found)` | 否 | 否 | no file-write call detected (static) |
| `evals/runtime/mock_siren/api.py` | `evals/runtime/mock_siren/api.py (imported module, no CLI entry point found)` | 否 | 否 | no file-write call detected (static) |
| `evals/runtime/mock_siren/faults.py` | `evals/runtime/mock_siren/faults.py (imported module, no CLI entry point found)` | 否 | 否 | no file-write call detected (static) |
| `evals/runtime/mock_siren/policy.py` | `evals/runtime/mock_siren/policy.py (imported module, no CLI entry point found)` | 否 | 否 | no file-write call detected (static) |
| `evals/runtime/mock_siren/scenario.py` | `evals/runtime/mock_siren/scenario.py (imported module, no CLI entry point found)` | 否 | 否 | no file-write call detected (static) |
| `evals/runtime/mock_siren/server.py` | `python3 evals/runtime/mock_siren/server.py` | 否 | 否 | no file-write call detected (static) |
| `evals/runtime/mock_siren/shell.py` | `evals/runtime/mock_siren/shell.py (imported module, no CLI entry point found)` | 否 | 否 | no file-write call detected (static) |
| `evals/runtime/run_mock_siren_tests.py` | `python3 evals/runtime/run_mock_siren_tests.py` | 否 | 是 | write call present; resolves to a Python-managed temp directory (tempfile.*, ephemeral, deleted at context exit) -- not a persistent write outside reports/ or evals/ (static) |

- 结论：No script under scripts/ or evals/ initiates network egress; file writes are confined to reports/ and/or evals/ output artifacts (static analysis).
- 方法说明：Static heuristic scan, not a full data-flow or taint analysis. Network access: real Python networking modules are matched on an actual import/connect statement anywhere in the file; command-line network tools (curl/wget/ssh/scp/rsync/netcat) count only when they appear as an argument inside an actual subprocess/os.system/os.popen/os.exec* call (.py) or as a shell-script line (.sh) -- a policy table or test-fixture string that merely names one of these tools is not a call site. File writes: a best-effort constant-propagation pass resolves a write call's target through named constants, one argparse-default hop, and tempfile.*/`with ... as` bindings (tagged as an ephemeral temp-dir, not a persistent write).

## 3. 依赖锁定（dependency pinning）

- requirements.txt：`requirements.txt`
  - `pyyaml` == `6.0.3`
- 结论：requirements.txt exists, pyyaml is present, and every dependency is exactly pinned with ==

## 4. 安装包哈希（package hash）

- 包目录：`skills/sleuth`
- 文件数：41
- 聚合 SHA-256：`5b48d6afe13f086367d25ca2163f9c5f81eeb15e6a63460f261b65f6e0b999d5`
- 聚合算法：sha256 of the concatenation of 'relpath:filehash\n' for each file, sorted by relpath
- 说明：skills/sleuth/ may be modified by a parallel, unrelated task. This is a snapshot taken at generation time -- regenerate this report (without --check) as the final step before the trust-report waiver is closed, so the recorded hash matches the package actually being shipped.
- 逐文件清单见 `reports/trust_report.json` 的 `sections.package_hash.files`。
