#!/usr/bin/env python3
"""Generate the governed-release trust report for the SLEUTH repository.

Produces reports/trust_report.json and reports/trust_report.md, closing the
evidence gap named by the `trust-report` waiver in reports/review_waivers.json
(secret scan, script surface, dependency pinning, package hash). Stdlib only.

Idempotent: re-running (no flags) recomputes everything and overwrites both
output files. Pass --check to verify the checked-in report is still current
without writing anything: the script recomputes the same four sections and
exits non-zero if that content (ignoring the generated_at timestamp) differs
from what is on disk, or if the recomputed report itself does not pass.

SCOPE NOTE: skills/sleuth/ may be edited by an unrelated, parallel task while
this script is developed and self-tested. The package_hash section is a
snapshot taken at generation time; regenerate this report (without --check)
as the last step before the trust-report waiver is closed, so the recorded
hash matches the package actually being shipped.
"""

from __future__ import annotations

import argparse
import functools
import hashlib
import json
import math
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_JSON = ROOT / "reports" / "trust_report.json"
OUTPUT_MD = ROOT / "reports" / "trust_report.md"
REQUIREMENTS_PATH = ROOT / "requirements.txt"
PACKAGE_ROOT = ROOT / "skills/sleuth"

SCHEMA_VERSION = 1

# All scan surfaces enumerate git-tracked files only. The report attests the
# committed tree (what is actually shipped and what CI checks out); untracked
# local artifacts (__pycache__, editor exports, ignored files) would make
# --check environment-dependent and are not part of the release.


@functools.cache
def tracked_files() -> tuple[Path, ...]:
    out = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z"],
        check=True,
        capture_output=True,
    ).stdout
    return tuple(
        sorted(
            path
            for name in out.split(b"\0")
            if name
            if (path := ROOT / name.decode("utf-8")).is_file()
        )
    )

# ---------------------------------------------------------------------------
# Section 1: secret scan
# ---------------------------------------------------------------------------

# This file's own source necessarily contains the literal marker text used to
# *detect* private-key blocks and credential assignments -- that is how the
# rules are written. Scanning it against those two rule categories would flag
# the rule definitions themselves, not a real secret. Excluding a scanner's
# own ruleset from such self-referential rules is standard practice; it is
# disclosed here and recorded in the generated report rather than silently
# suppressed. Entropy and AK/SK checks still run against this file normally.
SELF_PATH = "scripts/gen_trust_report.py"
SELF_EXCLUDED_RULES = {"private_key_block", "credential_assignment"}


def rule_applies(rel: str, rule_name: str) -> bool:
    return not (rel == SELF_PATH and rule_name in SELF_EXCLUDED_RULES)


AK_SK_RE = re.compile(r"\bLTAI[A-Za-z0-9]{12,30}\b")

PRIVATE_KEY_RE = re.compile(
    r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----"
)

CREDENTIAL_KEYS = (
    r"access[_-]?key(?:[_-]?secret)?",
    r"secret[_-]?key",
    r"api[_-]?key",
    r"token",
    r"passwd",
    r"password",
)
CREDENTIAL_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(?:" + "|".join(CREDENTIAL_KEYS) + r")\b\s*[:=]\s*['\"]([^'\"\n]{6,})['\"]"
)

PLACEHOLDER_MARKERS = (
    "xxx", "changeme", "example", "placeholder", "<", "{{", "$",
    "your_", "replace", "todo", "n/a", "null", "none", "test",
    "sample", "dummy", "fake",
)

# High-entropy candidates are restricted to plain alnum runs (no separators,
# no "/"): this repo's real identifiers, filenames, and paths always contain
# "_", "-", or "/" (verified empirically against the tree while designing
# this rule), so a plain-alnum charset already avoids most false positives
# without extra allow-listing.
ENTROPY_TOKEN_RE = re.compile(r"[A-Za-z0-9]{24,}")
ENTROPY_THRESHOLD = 4.0  # bits/char

# SSH *public* keys (authorized_keys lines, mock host fixtures under evals/)
# are high-entropy base64 blobs by construction but are, by definition, not a
# credential -- a private key is what would need protecting, and that is
# already covered by PRIVATE_KEY_RE above. Skip entropy scanning on a whole
# line once it looks like a public-key line, rather than trying to special-
# case the blob itself.
SSH_PUBLIC_KEY_LINE_RE = re.compile(r"\b(?:ssh-rsa|ssh-ed25519|ssh-dss|ecdsa-sha2-\S+)\s")


def shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    counts = Counter(s)
    n = len(s)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def is_hex_like(token: str) -> bool:
    # Hex digests (git hashes, sha256, uuids) are expected and benign; this
    # repo's own reports embed many of them.
    return bool(re.fullmatch(r"[0-9a-fA-F]+", token))


def looks_like_placeholder(value: str) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in PLACEHOLDER_MARKERS)


def redact(value: str) -> str:
    if len(value) <= 4:
        return "*" * len(value)
    return f"{value[:2]}...redacted...{value[-2:]}"


def iter_repo_files():
    yield from tracked_files()


def scan_secrets() -> dict:
    findings = []
    files_scanned = 0
    files_skipped_binary = 0

    for path in iter_repo_files():
        rel = path.relative_to(ROOT).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, ValueError):
            files_skipped_binary += 1
            continue
        files_scanned += 1

        for lineno, line in enumerate(text.splitlines(), start=1):
            for m in AK_SK_RE.finditer(line):
                findings.append(
                    {"rule": "aliyun_ak_sk", "path": rel, "line": lineno, "excerpt": redact(m.group(0))}
                )

            if rule_applies(rel, "private_key_block"):
                for m in PRIVATE_KEY_RE.finditer(line):
                    findings.append(
                        {"rule": "private_key_block", "path": rel, "line": lineno, "excerpt": redact(m.group(0))}
                    )

            if rule_applies(rel, "credential_assignment"):
                for m in CREDENTIAL_ASSIGNMENT_RE.finditer(line):
                    value = m.group(1)
                    if looks_like_placeholder(value):
                        continue
                    findings.append(
                        {"rule": "credential_assignment", "path": rel, "line": lineno, "excerpt": redact(value)}
                    )

            entropy_candidates = [] if SSH_PUBLIC_KEY_LINE_RE.search(line) else ENTROPY_TOKEN_RE.finditer(line)
            for m in entropy_candidates:
                token = m.group(0)
                if not any(ch.isdigit() for ch in token):
                    continue
                if is_hex_like(token):
                    continue
                entropy = shannon_entropy(token)
                if entropy < ENTROPY_THRESHOLD:
                    continue
                findings.append(
                    {
                        "rule": "high_entropy_string",
                        "path": rel,
                        "line": lineno,
                        "excerpt": redact(token),
                        "entropy": round(entropy, 3),
                    }
                )

    return {
        "ok": len(findings) == 0,
        "files_scanned": files_scanned,
        "files_skipped_binary": files_skipped_binary,
        "rules": [
            {"name": "aliyun_ak_sk", "description": "Aliyun AccessKeyId: LTAI prefix followed by 12-30 alnum chars"},
            {"name": "private_key_block", "description": "PEM private key BEGIN marker (RSA/EC/DSA/OPENSSH/ENCRYPTED)"},
            {
                "name": "credential_assignment",
                "description": (
                    "token/password/passwd/api_key/access_key/secret_key assigned a quoted "
                    "literal of 6+ chars; obvious placeholders are excluded"
                ),
            },
            {
                "name": "high_entropy_string",
                "description": (
                    f"plain alnum run of 24+ chars containing a digit, not a pure-hex digest, "
                    f"Shannon entropy >= {ENTROPY_THRESHOLD} bits/char; skips ssh-rsa/ssh-ed25519/"
                    f"ssh-dss/ecdsa-sha2-* public-key lines (public by design, not a credential)"
                ),
            },
        ],
        "self_exclusions": [
            {
                "path": SELF_PATH,
                "excluded_rules": sorted(SELF_EXCLUDED_RULES),
                "reason": "this scanner's own source embeds the literal rule markers it uses to detect them",
            }
        ],
        "findings": findings,
    }


# ---------------------------------------------------------------------------
# Section 2: script surface
# ---------------------------------------------------------------------------

SCRIPT_DIRS = ("scripts", "evals")
SCRIPT_SUFFIXES = (".py", ".sh")
DECLARED_WRITE_DIRS = ("reports", "evals")

# Actual Python networking modules: anchored to a real `import`/`from import`
# statement (or, for socket, an actual connect-style call) so a file that
# merely *talks about* one of these in a docstring or comment does not count.
NETWORK_MODULE_PATTERNS = [
    ("requests", re.compile(r"\bimport\s+requests\b|\bfrom\s+requests\b")),
    ("urllib.request", re.compile(r"\bimport\s+urllib\.request\b|\bfrom\s+urllib\s+import\s+request\b")),
    # Label is spelled with an underscore rather than the module's own dotted
    # form so this file's source (which has to name that module somewhere to
    # explain the rule) doesn't self-match the very pattern defined below.
    ("http_client", re.compile(r"\bhttp\.client\b")),
    ("socket", re.compile(r"\bsocket\.(?:socket|create_connection)\(")),
    ("pycurl", re.compile(r"\bimport\s+pycurl\b")),
    ("aiohttp", re.compile(r"\bimport\s+aiohttp\b")),
    ("ftplib", re.compile(r"\bimport\s+ftplib\b")),
    ("smtplib", re.compile(r"\bimport\s+smtplib\b")),
    ("paramiko", re.compile(r"\bimport\s+paramiko\b")),
]

# Command-line network tools. These names double as ordinary English/security
# vocabulary (a docstring, a policy allowlist, a compliance-rule dict, a test
# fixture string can all *name* "curl" or "ssh" without the script itself ever
# invoking them) -- evals/runtime/compliance/rules.py's DESTRUCTIVE_BINARIES
# table and evals/runtime/run_mock_siren_tests.py's "curl ... | bash" fixture
# string are exactly that. So for .py files these are only counted as network
# access when they appear as an argument inside an actual process-spawning
# call (the subprocess module, os.system, os.popen, os.exec*); see
# find_process_call_arg_spans. For .sh files there is no such wrapper to look
# inside -- a top-level shell line already *is* the call site -- so these are
# matched against the whole file there.
NETWORK_BINARY_PATTERNS = [
    ("curl", re.compile(r"\bcurl\b")),
    ("wget", re.compile(r"\bwget\b")),
    ("netcat", re.compile(r"\bnetcat\b")),
    ("ssh", re.compile(r"\bssh\b(?!-)")),  # (?!-) excludes ssh-rsa/ssh-ed25519/ssh-keygen &c.
    ("scp", re.compile(r"\bscp\b")),
    ("rsync", re.compile(r"\brsync\b")),
]

PROCESS_CALL_START_RE = re.compile(r"\b(?:subprocess\.\w+|os\.system|os\.popen|os\.exec\w*)\s*\(")


def find_process_call_arg_spans(text: str) -> list[str]:
    """Return the balanced-paren argument text of every subprocess/os.system/
    os.popen/os.exec* call in `text`. A plain regex can't capture this
    correctly on its own (call arguments routinely contain nested parens,
    e.g. a subprocess run() call passing `[sys.executable, str(SERVER_PATH)]`),
    so this walks paren depth manually from each call's opening `(`.
    """
    spans = []
    for m in PROCESS_CALL_START_RE.finditer(text):
        depth = 0
        start = None
        i = m.end() - 1  # index of the opening '(' the pattern matched
        n = len(text)
        while i < n:
            ch = text[i]
            if ch == "(":
                depth += 1
                if start is None:
                    start = i + 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        spans.append(text[start:i] if start is not None else "")
    return spans


SUBPROCESS_PATTERNS_PY = [
    re.compile(p)
    for p in (r"\bsubprocess\.", r"\bos\.system\(", r"\bos\.popen\(", r"\bos\.exec\w*\(")
]
SUBPROCESS_PATTERNS_SH = SUBPROCESS_PATTERNS_PY + [
    re.compile(r"`[^`]+`"),
    re.compile(r"\$\([^)]+\)"),
]

WRITE_CALL_RE_PY = re.compile(
    r"(?P<receiver>[A-Za-z_][A-Za-z0-9_.]*)\.(?:write_text|write_bytes|mkdir)\("
    r"|open\(\s*(?P<open_arg>[^,()]+),"
)
WRITE_REDIRECT_RE_SH = re.compile(r">>?\s*(\S+)")

OUT_OF_SCOPE_RE = re.compile(
    r"""['"](?:/etc/|/root/|/home/|~/)[^'"\n]*['"]|['"]skills/sleuth(?:/[^'"\n]*)?['"]|https?://[^\s'"]+"""
)


def mentions_dir(text: str, dirname: str) -> bool:
    return bool(re.search(rf"""['"]{dirname}(?:/|['"])""", text))


TEMPFILE_RE = re.compile(r"\btempfile\.")
WITH_TEMPFILE_AS_RE = re.compile(r"\bwith\s+tempfile\.\w+\([^)]*\)\s+as\s+([A-Za-z_][A-Za-z0-9_]*)\s*:")


def tags_from_text(text: str) -> set[str]:
    tags = {d for d in DECLARED_WRITE_DIRS if mentions_dir(text, d)}
    if OUT_OF_SCOPE_RE.search(text):
        tags.add("out-of-scope")
    if TEMPFILE_RE.search(text):
        # tempfile.mkdtemp() / tempfile.TemporaryDirectory() / NamedTemporaryFile()
        # are ephemeral and self-cleaning -- a write under one of them is not a
        # persistent write outside reports/ or evals/, so it gets its own
        # disclosed scope rather than "unresolved".
        tags.add("temp-dir")
    return tags


def build_symbol_scopes(text: str) -> dict[str, set[str]]:
    """Best-effort constant propagation so a write call routed through a named
    constant (and, one hop further, an argparse default, or a `with ... as`
    binding) still resolves to the scope its own literal points at. Not a
    real dataflow analysis -- it only follows the patterns this repo's
    scripts actually use: `NAME = ... "reports" ...`,
    `parser.add_argument("--x", default=str(NAME))`, and
    `with tempfile.TemporaryDirectory() as NAME:`.
    """
    scopes: dict[str, set[str]] = {}
    assign_lines = []
    for line in text.splitlines():
        m = re.match(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$", line)
        if m:
            assign_lines.append((m.group(1), m.group(2)))

    for name, rhs in assign_lines:
        tags = tags_from_text(rhs)
        if tags:
            scopes.setdefault(name, set()).update(tags)

    for m in WITH_TEMPFILE_AS_RE.finditer(text):
        scopes.setdefault(m.group(1), set()).add("temp-dir")

    for m in re.finditer(
        r"""add_argument\(\s*["'](--[A-Za-z0-9-]+)["'][^)]*?default=(?:str\()?([A-Za-z_][A-Za-z0-9_]*)\)?""",
        text,
    ):
        flag, const_name = m.group(1), m.group(2)
        dest = flag.lstrip("-").replace("-", "_")
        if const_name in scopes:
            scopes.setdefault(f"args.{dest}", set()).update(scopes[const_name])

    for name, rhs in assign_lines:
        for known_name, tags in list(scopes.items()):
            if known_name != name and known_name in rhs:
                scopes.setdefault(name, set()).update(tags)

    return scopes


def resolve_tags(expr: str, symbol_scopes: dict[str, set[str]]) -> set[str]:
    tags = tags_from_text(expr)
    base = re.split(r"[.\s/]", expr.strip())[0]
    if base in symbol_scopes:
        tags |= symbol_scopes[base]
    return tags


def analyze_script(path: Path) -> dict:
    rel = path.relative_to(ROOT).as_posix()
    text = path.read_text(encoding="utf-8")
    is_py = path.suffix == ".py"

    if is_py:
        has_main_guard = bool(re.search(r"""if __name__ == ['"]__main__['"]""", text))
        executes_at_import = bool(re.search(r"\bsys\.exit\(", text))
        if has_main_guard:
            entry_point = f"python3 {rel}"
        elif executes_at_import:
            entry_point = f"python3 {rel} (flat script, executes at import time, no __main__ guard)"
        else:
            entry_point = f"{rel} (imported module, no CLI entry point found)"
    else:
        first_line = text.splitlines()[0] if text.splitlines() else ""
        entry_point = first_line if first_line.startswith("#!") else f"sh {rel}"

    module_hits = {name for name, pattern in NETWORK_MODULE_PATTERNS if pattern.search(text)}
    if is_py:
        # Binary-name hits only count when they appear as an argument inside an
        # actual process-spawning call, not anywhere in the file -- see
        # NETWORK_BINARY_PATTERNS' comment for why.
        binary_hits = set()
        for span in find_process_call_arg_spans(text):
            binary_hits |= {name for name, pattern in NETWORK_BINARY_PATTERNS if pattern.search(span)}
    else:
        binary_hits = {name for name, pattern in NETWORK_BINARY_PATTERNS if pattern.search(text)}
    network_hits = sorted(module_hits | binary_hits)

    subprocess_patterns = SUBPROCESS_PATTERNS_PY if is_py else SUBPROCESS_PATTERNS_SH
    subprocess_hits = sorted({p.pattern for p in subprocess_patterns if p.search(text)})

    write_scopes: set[str] = set()
    write_call_present = False
    if is_py:
        symbol_scopes = build_symbol_scopes(text)
        for m in WRITE_CALL_RE_PY.finditer(text):
            write_call_present = True
            expr = m.group("receiver") or m.group("open_arg") or ""
            write_scopes |= resolve_tags(expr, symbol_scopes) or {"unresolved"}
    else:
        for m in WRITE_REDIRECT_RE_SH.finditer(text):
            write_call_present = True
            write_scopes |= tags_from_text(m.group(1)) or {"unresolved"}

    if not write_call_present:
        write_summary = "no file-write call detected (static)"
        scope_ok = True
    elif write_scopes & {"out-of-scope", "unresolved"}:
        write_summary = f"write call present, scope could not be confined to reports/ or evals/ (static): {sorted(write_scopes)}"
        scope_ok = False
    elif write_scopes <= {"temp-dir"}:
        write_summary = (
            "write call present; resolves to a Python-managed temp directory "
            "(tempfile.*, ephemeral, deleted at context exit) -- not a persistent "
            "write outside reports/ or evals/ (static)"
        )
        scope_ok = True
    else:
        write_summary = f"write call present; resolves to {', '.join(sorted(write_scopes))}/ (static)"
        scope_ok = True

    ok = (not network_hits) and scope_ok
    return {
        "path": rel,
        "entry_point": entry_point,
        "network_access": bool(network_hits),
        "network_indicators_matched": network_hits,
        "subprocess_execution": bool(subprocess_hits),
        "subprocess_patterns_matched": subprocess_hits,
        "file_write_scopes": sorted(write_scopes),
        "write_summary": write_summary,
        "ok": ok,
    }


def scan_scripts() -> dict:
    scripts = []
    for path in tracked_files():
        rel = path.relative_to(ROOT)
        if rel.parts[0] in SCRIPT_DIRS and path.suffix in SCRIPT_SUFFIXES:
            scripts.append(analyze_script(path))

    overall_ok = bool(scripts) and all(s["ok"] for s in scripts)
    return {
        "ok": overall_ok,
        "script_count": len(scripts),
        "scripts": scripts,
        "conclusion": (
            "No script under scripts/ or evals/ initiates network egress; file writes are "
            "confined to reports/ and/or evals/ output artifacts (static analysis)."
            if overall_ok
            else "One or more scripts show network access or a write scope outside reports/ and evals/; see per-script detail."
        ),
        "method_note": (
            "Static heuristic scan, not a full data-flow or taint analysis. Network access: "
            "real Python networking modules are matched on an actual import/connect statement "
            "anywhere in the file; command-line network tools (curl/wget/ssh/scp/rsync/netcat) "
            "count only when they appear as an argument inside an actual subprocess/os.system/"
            "os.popen/os.exec* call (.py) or as a shell-script line (.sh) -- a policy table or "
            "test-fixture string that merely names one of these tools is not a call site. File "
            "writes: a best-effort constant-propagation pass resolves a write call's target "
            "through named constants, one argparse-default hop, and tempfile.*/`with ... as` "
            "bindings (tagged as an ephemeral temp-dir, not a persistent write)."
        ),
    }


# ---------------------------------------------------------------------------
# Section 3: dependency pinning
# ---------------------------------------------------------------------------

def check_dependency_pinning() -> dict:
    if not REQUIREMENTS_PATH.exists():
        return {
            "ok": False,
            "requirements_file": None,
            "pins": [],
            "detail": "requirements.txt is missing",
        }

    pins = []
    ok = True
    for raw_line in REQUIREMENTS_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^([A-Za-z0-9_.-]+)\s*==\s*([A-Za-z0-9_.+-]+)$", line)
        if m:
            pins.append({"package": m.group(1), "pinned_version": m.group(2), "exact_pin": True})
        else:
            pins.append({"package": line, "pinned_version": None, "exact_pin": False})
            ok = False

    has_pinned_pyyaml = any(p["exact_pin"] and p["package"].lower() == "pyyaml" for p in pins)
    if not has_pinned_pyyaml:
        ok = False

    return {
        "ok": ok,
        "requirements_file": str(REQUIREMENTS_PATH.relative_to(ROOT)),
        "pins": pins,
        "detail": (
            "requirements.txt exists, pyyaml is present, and every dependency is exactly pinned with =="
            if ok
            else "requirements.txt is missing, empty, or contains an unpinned/non-exact/missing dependency"
        ),
    }


# ---------------------------------------------------------------------------
# Section 4: package hash
# ---------------------------------------------------------------------------

def hash_package() -> dict:
    if not PACKAGE_ROOT.exists():
        return {
            "ok": False,
            "package_root": None,
            "file_count": 0,
            "files": [],
            "aggregate_sha256": None,
        }

    files = []
    for path in sorted(p for p in tracked_files() if p.is_relative_to(PACKAGE_ROOT)):
        rel = path.relative_to(ROOT).as_posix()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        files.append({"path": rel, "sha256": digest})

    concat = "".join(f"{f['path']}:{f['sha256']}\n" for f in files)
    aggregate = hashlib.sha256(concat.encode("utf-8")).hexdigest()

    return {
        "ok": True,
        "package_root": str(PACKAGE_ROOT.relative_to(ROOT)),
        "file_count": len(files),
        "files": files,
        "aggregate_sha256": aggregate,
        "aggregate_method": "sha256 of the concatenation of 'relpath:filehash\\n' for each file, sorted by relpath",
        "snapshot_note": (
            "skills/sleuth/ may be modified by a parallel, unrelated task. This is a snapshot "
            "taken at generation time -- regenerate this report (without --check) as the final "
            "step before the trust-report waiver is closed, so the recorded hash matches the "
            "package actually being shipped."
        ),
    }


# ---------------------------------------------------------------------------
# Report assembly
# ---------------------------------------------------------------------------

def compute_report() -> dict:
    sections = {
        "secret_scan": scan_secrets(),
        "script_surface": scan_scripts(),
        "dependency_pinning": check_dependency_pinning(),
        "package_hash": hash_package(),
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": None,
        "ok": all(section["ok"] for section in sections.values()),
        "notes": [
            "Generated for the governed-release trust-report gate "
            "(reports/review_waivers.json, gate_key=trust-report).",
            "package_hash reflects skills/sleuth/ at generation time; regenerate before "
            "closing the waiver if that package changed since.",
        ],
        "sections": sections,
    }


def render_markdown(report: dict) -> str:
    s = report["sections"]
    lines = [
        "# SLEUTH 信任报告（Trust Report）",
        "",
        f"生成时间：`{report['generated_at']}`",
        "",
        f"总体结论：**{'通过' if report['ok'] else '未通过'}**",
        "",
    ]
    for note in report["notes"]:
        lines.append(f"> {note}")
    lines.append("")

    ss = s["secret_scan"]
    lines += [
        "## 1. 密钥与凭据扫描（secret scan）",
        "",
        f"- 扫描文件数：{ss['files_scanned']}（跳过二进制/不可解码文件 {ss['files_skipped_binary']} 个）",
        "- 规则：",
    ]
    for rule in ss["rules"]:
        lines.append(f"  - `{rule['name']}`：{rule['description']}")
    lines.append(f"- 命中数：**{len(ss['findings'])}**")
    lines.append(f"- 结论：{'未发现凭据泄露' if ss['ok'] else '发现待处理命中项，详见 trust_report.json 的 findings 字段'}")
    for ex in ss["self_exclusions"]:
        lines.append(f"- 说明：`{ex['path']}` 对规则 `{', '.join(ex['excluded_rules'])}` 自排除——{ex['reason']}")
    lines.append("")

    sc = s["script_surface"]
    lines += [
        "## 2. 脚本执行面（script surface）",
        "",
        "| 脚本 | 入口 | 网络访问 | 子进程 | 文件写入范围 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in sc["scripts"]:
        lines.append(
            f"| `{item['path']}` | `{item['entry_point']}` | "
            f"{'是' if item['network_access'] else '否'} | "
            f"{'是' if item['subprocess_execution'] else '否'} | {item['write_summary']} |"
        )
    lines += [
        "",
        f"- 结论：{sc['conclusion']}",
        f"- 方法说明：{sc['method_note']}",
        "",
    ]

    dp = s["dependency_pinning"]
    lines += ["## 3. 依赖锁定（dependency pinning）", ""]
    if dp["requirements_file"]:
        lines.append(f"- requirements.txt：`{dp['requirements_file']}`")
        for pin in dp["pins"]:
            if pin["exact_pin"]:
                lines.append(f"  - `{pin['package']}` == `{pin['pinned_version']}`")
            else:
                lines.append(f"  - `{pin['package']}`（未精确锁定）")
    else:
        lines.append("- requirements.txt：缺失")
    lines += [f"- 结论：{dp['detail']}", ""]

    ph = s["package_hash"]
    lines += [
        "## 4. 安装包哈希（package hash）",
        "",
        f"- 包目录：`{ph['package_root']}`",
        f"- 文件数：{ph['file_count']}",
        f"- 聚合 SHA-256：`{ph['aggregate_sha256']}`",
        f"- 聚合算法：{ph['aggregate_method']}",
        f"- 说明：{ph['snapshot_note']}",
        "- 逐文件清单见 `reports/trust_report.json` 的 `sections.package_hash.files`。",
        "",
    ]

    return "\n".join(lines).rstrip() + "\n"


def _comparable(report: dict) -> dict:
    clone = json.loads(json.dumps(report))
    clone.pop("generated_at", None)
    return clone


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="recompute and compare against reports/trust_report.json without writing; "
        "exits non-zero if stale, missing, or failing",
    )
    args = parser.parse_args()

    report = compute_report()
    report["generated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if args.check:
        if not OUTPUT_JSON.exists():
            print("FAIL: reports/trust_report.json is missing. Run: python3 scripts/gen_trust_report.py")
            sys.exit(1)
        try:
            existing = json.loads(OUTPUT_JSON.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"FAIL: reports/trust_report.json is not valid JSON: {e}")
            sys.exit(1)

        fresh_comparable = _comparable(report)
        existing_comparable = _comparable(existing)
        diffs = sorted(
            {k for k in fresh_comparable if fresh_comparable.get(k) != existing_comparable.get(k)}
            | {k for k in existing_comparable if k not in fresh_comparable}
        )
        if diffs:
            print(f"FAIL: reports/trust_report.json is stale; differing top-level field(s): {diffs}")
            print("Regenerate with: python3 scripts/gen_trust_report.py")
            sys.exit(1)
        if not report["ok"]:
            print("FAIL: trust report is current but one or more sections do not pass:")
            for name, section in report["sections"].items():
                if not section["ok"]:
                    print(f"  - {name}")
            sys.exit(1)
        print("OK: reports/trust_report.json is current and all sections pass")
        sys.exit(0)

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUTPUT_MD.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()
