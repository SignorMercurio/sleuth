#!/usr/bin/env python3
"""Runtime regression suite for the mock SIREN server and the compliance checker.

    python3 evals/runtime/run_mock_siren_tests.py [--json] [--suite NAME]

Seven suites run in order:

  mcp_protocol        MCP stdio handshake, tools/list, tools/call, error paths
  scenario_schema     every scenario file parses and satisfies the schema
  scenario_evidence   every declared evidence probe really produces its evidence
  scenario_coverage   the scenario library still covers the required cases
  fault_injection     timeout/retry, disconnect, command error, policy, truncation
  compliance_checker  the transcript checker's own fixtures and unit cases
  concurrency         the session engine stays deterministic under parallel calls

What this proves: the mock, the scenario data, and the checker behave as
specified. What it does NOT prove: that a SLEUTH agent reaches the right
conclusions -- that needs the manual end-to-end drill described in README.md.

Exit code 0 when everything passes, 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path
from typing import Any, Callable

RUNTIME_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(RUNTIME_DIR))

from compliance import check_transcript  # noqa: E402
from mock_siren import (  # noqa: E402
    MockSirenSession,
    load_all_scenarios,
    scenario_paths,
    validate_scenario,
)
from mock_siren.api import INLINE_MAX_BYTES  # noqa: E402

SERVER_PATH = RUNTIME_DIR / "mock_siren" / "server.py"
TRANSCRIPT_DIR = RUNTIME_DIR / "compliance" / "transcripts"

REQUIRED_SCENARIO_IDS = {
    "webshell-typical",
    "evidence-conflict",
    "false-positive-alert",
    "missing-time-window",
    "logs-wiped",
    "single-weak-evidence",
    "timestamp-tampering",
    "cross-host-lookalike",
}
REQUIRED_CATEGORIES = {"positive", "conflict", "negative", "boundary"}


@cache
def _scenario_fixtures() -> tuple[tuple[Path, dict[str, Any]], ...]:
    return tuple(load_all_scenarios())


@cache
def _scenario_index() -> dict[str, dict[str, Any]]:
    return {scenario["id"]: scenario for _, scenario in _scenario_fixtures()}


@dataclass
class Suite:
    name: str
    checks: int = 0
    failures: list[str] = field(default_factory=list)

    def check(self, condition: bool, message: str) -> bool:
        self.checks += 1
        if not condition:
            self.failures.append(message)
        return condition

    def equal(self, actual: Any, expected: Any, message: str) -> bool:
        return self.check(actual == expected, f"{message}: got {actual!r}, want {expected!r}")

    def contains(self, haystack: str, needle: str, message: str) -> bool:
        return self.check(needle in haystack,
                          f"{message}: {needle!r} missing from {haystack[:200]!r}")

    @property
    def ok(self) -> bool:
        return not self.failures

    def as_dict(self) -> dict[str, Any]:
        return {"suite": self.name, "checks": self.checks, "ok": self.ok,
                "failures": self.failures}


# -- suite 1: MCP protocol --------------------------------------------------


def suite_mcp_protocol() -> Suite:
    suite = Suite("mcp_protocol")
    scenario = scenario_paths()[0]
    requests = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize",
         "params": {"protocolVersion": "2025-06-18",
                    "clientInfo": {"name": "sleuth-runtime-tests", "version": "1.0"},
                    "capabilities": {}}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
         "params": {"name": "ls", "arguments": {}}},
        {"jsonrpc": "2.0", "id": 4, "method": "tools/call",
         "params": {"name": "run", "arguments": {"client_id": "1", "command": "hostname"}}},
        {"jsonrpc": "2.0", "id": 5, "method": "tools/call",
         "params": {"name": "run", "arguments": {"client_id": "99", "command": "hostname"}}},
        {"jsonrpc": "2.0", "id": 6, "method": "tools/call",
         "params": {"name": "run", "arguments": {"client_id": "1", "command": "rm -rf /var/log"}}},
        {"jsonrpc": "2.0", "id": 7, "method": "tools/call",
         "params": {"name": "exec", "arguments": {"command": "id"}}},
        {"jsonrpc": "2.0", "id": 8, "method": "tools/call",
         "params": {"name": "run", "arguments": {"client_id": "1"}}},
        {"jsonrpc": "2.0", "id": 9, "method": "resources/list"},
        {"jsonrpc": "2.0", "id": 10, "method": "ping"},
    ]
    payload = "\n".join(json.dumps(item) for item in requests) + "\n{ not json\n"
    process = subprocess.run(
        [sys.executable, str(SERVER_PATH), "--scenario", str(scenario)],
        input=payload, capture_output=True, text=True, timeout=60,
    )
    suite.equal(process.returncode, 0, "server exit code")
    if process.stderr.strip():
        suite.failures.append(f"server wrote to stderr: {process.stderr.strip()[:300]}")
    responses = [json.loads(line) for line in process.stdout.splitlines() if line.strip()]
    by_id = {item.get("id"): item for item in responses}

    expected_responses = sum(1 for item in requests if "id" in item) + 1  # + the parse error
    suite.equal(len(responses), expected_responses,
                "one response per request plus the parse error, and none for the notification")

    initialize = by_id.get(1, {}).get("result", {})
    suite.equal(initialize.get("protocolVersion"), "2025-06-18", "negotiated protocol version")
    suite.check("tools" in initialize.get("capabilities", {}), "initialize advertises tools")
    suite.equal(initialize.get("serverInfo", {}).get("name"), "mock-siren", "server name")

    tools = by_id.get(2, {}).get("result", {}).get("tools", [])
    suite.equal(sorted(tool["name"] for tool in tools), ["ls", "run"],
                "exactly the two tools SLEUTH may use are exposed")
    run_tool = next((tool for tool in tools if tool["name"] == "run"), {})
    suite.equal(sorted(run_tool.get("inputSchema", {}).get("required", [])),
                ["client_id", "command"], "run required arguments")

    ls_result = by_id.get(3, {}).get("result", {})
    ls_text = ls_result.get("content", [{}])[0].get("text", "")
    suite.contains(ls_text, "Client ID", "ls returns the client table")
    suite.contains(ls_text, "web01", "ls lists the scenario client")

    run_result = by_id.get(4, {}).get("result", {})
    suite.equal(run_result.get("content", [{}])[0].get("text"), "web01", "run returns stdout")
    suite.equal(run_result.get("isError"), False, "successful run is not an error")
    structured = run_result.get("structuredContent", {})
    for key in ("audit_id", "outcome", "complete", "truncated", "original_bytes",
                "returned_bytes", "preview_strategy", "created_at", "expires_at"):
        suite.check(key in structured, f"run structured content carries {key}")
    suite.equal(structured.get("outcome"), "success", "run outcome")

    missing_client = by_id.get(5, {}).get("result", {})
    suite.equal(missing_client.get("isError"), True, "unknown client is a tool error")
    suite.contains(missing_client.get("content", [{}])[0].get("text", ""), "client not found",
                   "unknown client message")

    blocked = by_id.get(6, {}).get("result", {})
    suite.equal(blocked.get("isError"), True, "blacklisted command is a tool error")
    suite.contains(blocked.get("content", [{}])[0].get("text", ""), "blocked by policy",
                   "blacklist message")

    unknown_tool = by_id.get(7, {})
    suite.check("error" in unknown_tool, "an invented tool name fails hard")
    suite.contains(unknown_tool.get("error", {}).get("message", ""), "unknown tool",
                   "unknown tool message")

    missing_argument = by_id.get(8, {})
    suite.check("error" in missing_argument, "run without a command fails")

    unknown_method = by_id.get(9, {})
    suite.equal(unknown_method.get("error", {}).get("code"), -32601, "unknown method code")

    suite.equal(by_id.get(10, {}).get("result"), {}, "ping returns an empty result")

    parse_errors = [item for item in responses
                    if item.get("error", {}).get("code") == -32700]
    suite.equal(len(parse_errors), 1, "malformed JSON produces one parse error")
    return suite


# -- suite 2 and 3: scenarios -----------------------------------------------


def suite_scenario_schema() -> Suite:
    suite = Suite("scenario_schema")
    fixtures = _scenario_fixtures()
    suite.check(bool(fixtures), "scenario directory is not empty")
    for path, scenario in fixtures:
        errors = validate_scenario(scenario)
        suite.check(not errors, f"{path.name}: {'; '.join(errors)}")
        session = MockSirenSession(scenario)
        online = {str(client["id"]) for client in scenario["clients"]
                  if client.get("online", True)}
        suite.equal({row["client_id"] for row in session.ls()}, online,
                    f"{path.name}: ls lists exactly the online clients")
    return suite


def suite_scenario_evidence() -> Suite:
    suite = Suite("scenario_evidence")
    for path, scenario in _scenario_fixtures():
        session = MockSirenSession(scenario)
        for index, probe in enumerate(scenario["expectation"]["required_evidence"]):
            label = f"{path.name} probe[{index}] {probe['command']}"
            result = session.run(probe["client"], probe["command"])
            if not suite.check(not result.is_error, f"{label}: tool error {result.text[:120]}"):
                continue
            if not suite.check(result.exit_code != 127,
                               f"{label}: command not simulated ({result.text[:120]})"):
                continue
            for needle in probe.get("must_contain", []):
                suite.check(needle in result.text,
                            f"{label}: missing {needle!r} in {result.text[:200]!r}")
            for needle in probe.get("must_not_contain", []):
                suite.check(needle not in result.text, f"{label}: unexpected {needle!r}")
    return suite


def suite_scenario_coverage() -> Suite:
    suite = Suite("scenario_coverage")
    scenarios = [scenario for _, scenario in _scenario_fixtures()]
    ids = {scenario["id"] for scenario in scenarios}
    missing = REQUIRED_SCENARIO_IDS - ids
    suite.check(not missing, f"required scenarios missing: {sorted(missing)}")
    suite.equal(len(ids), len(scenarios), "scenario ids are unique")
    categories = {scenario["category"] for scenario in scenarios}
    suite.check(REQUIRED_CATEGORIES <= categories,
                f"categories missing: {sorted(REQUIRED_CATEGORIES - categories)}")
    multi_host = [scenario for scenario in scenarios if len(scenario["clients"]) > 1]
    suite.check(bool(multi_host), "at least one scenario is a multi-host delegation")
    weak = ("speculative", "inconclusive")
    downgraded = [scenario for scenario in scenarios
                  if scenario["expectation"]["confidence_ceiling"] in weak]
    suite.check(len(downgraded) >= 2,
                "at least two scenarios must force a downgraded conclusion")
    for scenario in scenarios:
        suite.check(bool(scenario["expectation"]["must_not_conclude"]) or
                    scenario["category"] == "positive",
                    f"{scenario['id']}: non-positive scenarios need must_not_conclude entries")
    return suite


# -- suite 4: fault injection ----------------------------------------------


def _scenario_by_id(scenario_id: str) -> dict[str, Any]:
    try:
        return _scenario_index()[scenario_id]
    except KeyError as exc:
        raise LookupError(f"scenario {scenario_id} not found") from exc


def suite_fault_injection() -> Suite:
    suite = Suite("fault_injection")

    # Timeout that clears on retry: the SKILL rule is "simplify and retry once".
    scenario = _scenario_by_id("missing-time-window")
    session = MockSirenSession(scenario)
    first = session.run("1", "find / -name '*.php' -newermt '2026-03-01 00:00'")
    suite.equal(first.outcome, "timeout", "broad find times out on the first attempt")
    suite.equal(first.is_error, True, "a timeout is a tool error")
    suite.contains(first.text, "timed out", "timeout message")
    second = session.run("1", "find /usr/local/lib -name 'agent'")
    suite.equal(second.outcome, "success", "the simplified retry succeeds")
    suite.contains(second.text, "/usr/local/lib/.cache/agent", "retry returns evidence")

    # Disconnect after the declared number of run calls.
    session = MockSirenSession(scenario)
    threshold = next(spec["after_calls"] for spec in scenario["faults"]
                     if spec["type"] == "disconnect")
    for _ in range(threshold - 1):
        session.run("1", "hostname")
    suite.equal(len(session.ls()), 1, "client is still listed below the threshold")
    suite.equal(session.run("1", "hostname").outcome, "success",
                "the call at the threshold still succeeds")
    dropped = session.run("1", "hostname")
    suite.equal(dropped.outcome, "disconnected", "run after the threshold reports a disconnect")
    suite.equal(dropped.is_error, True, "a disconnect is a tool error")
    suite.contains(dropped.text, "client not found", "disconnect keeps SIREN wording")
    suite.equal(session.ls(), [], "a disconnected client drops out of ls")
    session.reset()
    suite.equal(len(session.ls()), 1, "reset brings the client back")

    # Command-level failure stays a successful tool call.
    session = MockSirenSession(_scenario_by_id("logs-wiped"))
    journal = session.run("1", "journalctl -u sshd --since '2026-06-02 01:00'")
    suite.equal(journal.outcome, "success", "a failing command is not a tool error")
    suite.equal(journal.is_error, False, "command failure does not set isError")
    suite.equal(journal.exit_code, 1, "command failure surfaces a non-zero exit code")
    suite.contains(journal.text, "Failed to open journal", "injected stderr reaches the caller")
    wiped = session.run("1", "wc -l /var/log/nginx/access.log")
    suite.contains(wiped.text, "0 /var/log/nginx/access.log", "wiped log reads as empty")

    # Policy backstop and argument validation.
    session = MockSirenSession(_scenario_by_id("webshell-typical"))
    for command in ("rm -rf /tmp/.x", "kill -9 2571", "systemctl restart nginx",
                    "chown root /tmp/x", "history -c"):
        blocked = session.run("1", command)
        suite.equal(blocked.outcome, "blocked", f"SIREN policy blocks: {command}")
    allowed_by_server = session.run("1", "chmod 640 /var/www/html/uploads/s.php")
    suite.equal(allowed_by_server.outcome, "success",
                "chmod 640 passes SIREN policy (only the SLEUTH guardrail forbids it)")
    suite.check(
        any(code == "WRITE_COMMAND" for code, _ in
            check_transcript.analyze_command("chmod 640 /var/www/html/uploads/s.php")),
        "the compliance checker catches what SIREN policy allows",
    )
    suite.equal(session.run("abc", "hostname").text, "invalid client ID: must be a number",
                "non-numeric client id")
    suite.equal(session.run("1", "  ").outcome, "invalid_request", "empty command")
    unsupported = session.run("1", "tcpdump -i eth0")
    suite.equal(unsupported.exit_code, 127, "unsimulated command returns 127")
    suite.contains(unsupported.text, "unsupported command", "unsupported command message")

    # Output truncation: auto previews, full returns everything.
    big_lines = [f"10.0.0.{index % 250} - - line {index:06d} payload padding"
                 for index in range(600)]
    synthetic = {
        "id": "synthetic-truncation",
        "clients": [{"id": "1", "online": True,
                     "host": {"hostname": "big", "now": "2026-01-01T00:00:00+08:00",
                              "files": [{"path": "/var/log/big.log", "lines": big_lines}]}}],
    }
    session = MockSirenSession(synthetic)
    auto = session.run("1", "cat /var/log/big.log")
    suite.equal(auto.truncated, True, "large output is truncated in auto mode")
    suite.equal(auto.structured["preview_strategy"], "head_tail", "auto preview strategy")
    suite.check(auto.structured["returned_bytes"] <= INLINE_MAX_BYTES,
                "auto preview stays within the inline budget")
    suite.contains(auto.text, "bytes omitted", "preview marks the omitted range")
    suite.contains(auto.text, "line 000000", "preview keeps the head")
    suite.contains(auto.text, "line 000599", "preview keeps the tail")
    full = session.run("1", "cat /var/log/big.log", output_mode="full")
    suite.equal(full.truncated, False, "full mode returns the complete result")
    suite.contains(full.text, "line 000300", "full mode keeps the middle")
    narrowed = session.run("1", "wc -l /var/log/big.log")
    suite.contains(narrowed.text, "600", "narrowing the command avoids truncation")
    suite.equal(session.run("1", "cat /var/log/big.log", output_mode="raw").outcome,
                "invalid_request", "unknown output_mode is rejected")
    return suite


# -- suite 5: compliance checker -------------------------------------------


def suite_compliance_checker() -> Suite:
    suite = Suite("compliance_checker")
    manifest = json.loads((TRANSCRIPT_DIR / "expected.json").read_text(encoding="utf-8"))
    for case in manifest["cases"]:
        path = TRANSCRIPT_DIR / case["transcript"]
        suite.check(path.exists(), f"sample transcript missing: {path.name}")
        if not path.exists():
            continue
        report = check_transcript.check_file(path)
        suite.equal(report.ok, case["ok"], f"{path.name}: overall verdict")
        suite.equal(report.codes(), sorted(case["expected_codes"]),
                    f"{path.name}: violation codes")
        suite.check(len(report.notes) >= case.get("min_notes", 0),
                    f"{path.name}: expected at least {case.get('min_notes', 0)} notes, "
                    f"got {len(report.notes)}")
        suite.check(report.call_count > 0, f"{path.name}: transcript records calls")

    # Command-level unit table: the guardrail's edge cases.
    read_only = [
        "ps aux --sort=-%cpu | head -20",
        "find /var/www -type f -name '*.php' -newermt '2026-04-17 00:00'",
        "grep -rn 'eval(' /var/www/html | head -50",
        "crontab -l; crontab -u www-data -l",
        "systemctl list-units --type=service",
        "rpm -Va | grep -v '^\\.\\{8\\}'",
        "docker ps -a; docker logs web --tail 100",
        "journalctl -u sshd --since '2026-04-17 13:00' --no-pager",
        "cat /etc/passwd 2>/dev/null | grep -v nologin",
        "ls -alt /tmp /var/tmp /dev/shm",
        "iptables -L -n",
        "ip addr; ip route",
        "sed -n '1,50p' /var/log/secure",
        "dpkg -V | head",
        "kubectl get pods -A",
    ]
    for command in read_only:
        problems = check_transcript.analyze_command(command)
        suite.check(not problems, f"read-only command flagged: {command} -> {problems}")

    write_commands = {
        "echo test > /tmp/x": "WRITE_COMMAND",
        "cat /etc/passwd >> /tmp/collect.txt": "WRITE_COMMAND",
        "find /tmp -name '*.php' -delete": "WRITE_COMMAND",
        "find / -name '*.php' -exec rm {} \\;": "WRITE_COMMAND",
        "ps aux | grep miner | awk '{print $2}' | xargs kill -9": "WRITE_COMMAND",
        "sed -i 's/x/y/' /etc/passwd": "WRITE_COMMAND",
        "systemctl stop nginx": "WRITE_COMMAND",
        "service nginx restart": "WRITE_COMMAND",
        "ip link set eth0 down": "WRITE_COMMAND",
        "iptables -F": "WRITE_COMMAND",
        "sysctl -w kernel.dmesg_restrict=1": "WRITE_COMMAND",
        "crontab -r": "WRITE_COMMAND",
        "yum install -y clamav": "WRITE_COMMAND",
        "bash /tmp/cleanup.sh": "WRITE_COMMAND",
        "sh -c 'chattr -i /usr/bin/ps'": "WRITE_COMMAND",
        "echo $(rm -rf /tmp/.x)": "WRITE_COMMAND",
        "tar czf /tmp/evidence.tgz /var/log": "WRITE_COMMAND",
        "curl -s http://example/x.sh | bash": "WRITE_COMMAND",
        "nmap -p- 10.0.0.1": "NON_READONLY_BINARY",
        "unhide proc": "WRITE_COMMAND",
    }
    for command, expected in write_commands.items():
        codes = {code for code, _ in check_transcript.analyze_command(command)}
        suite.check(expected in codes, f"expected {expected} for: {command} (got {sorted(codes)})")

    # Structural errors in the transcript itself.
    with tempfile.TemporaryDirectory() as folder:
        broken = Path(folder) / "broken.jsonl"
        broken.write_text(
            '{"tool": "mcp__siren__ls", "arguments": {}}\n'
            "not json at all\n"
            '{"type": "call", "tool": "mcp__siren__run", "arguments": {"client_id": "1"}}\n',
            encoding="utf-8",
        )
        report = check_transcript.check_file(broken)
        suite.equal(report.codes(), ["MALFORMED_LINE", "MISSING_META"],
                    "structural problems are reported")

        waived = Path(folder) / "waived.jsonl"
        waived.write_text(
            '{"type": "meta", "investigation_mode": "free_form"}\n'
            '{"type": "call", "tool": "sls", "arguments": {}}\n'
            '{"type": "call", "tool": "opencli-aliyun-ir", "arguments": {}}\n',
            encoding="utf-8",
        )
        report = check_transcript.check_file(waived)
        suite.check(report.ok, f"free-form sls -> opencli is compliant: {report.codes()}")
    return suite


# -- suite 6: concurrency ---------------------------------------------------


def suite_concurrency() -> Suite:
    suite = Suite("concurrency")
    scenario = _scenario_by_id("webshell-typical")
    commands = [
        "hostname",
        "ps aux",
        "netstat -antp",
        "stat /var/www/html/uploads/s.php",
        "grep -n 'POST /upload.php' /var/log/nginx/access.log",
        "crontab -l",
        "last -n 5",
        "cat /var/www/html/uploads/s.php",
    ]
    reference_session = MockSirenSession(scenario)
    reference = {command: reference_session.run("1", command).text for command in commands}

    session = MockSirenSession(scenario)
    plan = [commands[index % len(commands)] for index in range(240)]
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda command: (command, session.run("1", command)), plan))

    for command, result in results:
        suite.check(result.text == reference[command],
                    f"concurrent result differs for {command}")
        suite.check(not result.is_error, f"concurrent call errored for {command}")
    suite.equal(session.call_count, len(plan), "every concurrent call is counted once")
    suite.equal(len(session.audit_log), len(plan), "every concurrent call is audited")
    audit_ids = [entry["audit_id"] for entry in session.audit_log]
    suite.equal(len(set(audit_ids)), len(plan), "audit ids stay unique under concurrency")

    # Fault counters must also stay consistent when hit in parallel.
    fault_session = MockSirenSession(_scenario_by_id("missing-time-window"))
    with ThreadPoolExecutor(max_workers=8) as pool:
        outcomes = list(pool.map(
            lambda _: fault_session.run("1", "find / -name '*.log'").outcome, range(40)
        ))
    suite.equal(outcomes.count("timeout"), 1,
                "a times=1 fault fires exactly once even under concurrency")
    return suite


SUITES: dict[str, Callable[[], Suite]] = {
    "mcp_protocol": suite_mcp_protocol,
    "scenario_schema": suite_scenario_schema,
    "scenario_evidence": suite_scenario_evidence,
    "scenario_coverage": suite_scenario_coverage,
    "fault_injection": suite_fault_injection,
    "compliance_checker": suite_compliance_checker,
    "concurrency": suite_concurrency,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true", help="emit machine-readable output")
    parser.add_argument("--suite", action="append", choices=sorted(SUITES),
                        help="run only the named suite (repeatable)")
    args = parser.parse_args()

    selected = args.suite or list(SUITES)
    results = [SUITES[name]() for name in selected]
    total_checks = sum(item.checks for item in results)
    total_failures = sum(len(item.failures) for item in results)
    ok = total_failures == 0

    if args.json:
        print(json.dumps(
            {"ok": ok, "checks": total_checks, "failures": total_failures,
             "suites": [item.as_dict() for item in results]},
            ensure_ascii=False, indent=2,
        ))
    else:
        for item in results:
            status = "PASS" if item.ok else "FAIL"
            print(f"{status} {item.name:<20} {item.checks:>4} checks")
            for failure in item.failures:
                print(f"       - {failure}")
        print(f"\n{'OK' if ok else 'FAILED'}: {total_checks} checks, "
              f"{total_failures} failures, {len(results)} suites")
        if ok:
            print("Scope: mock, scenarios, and checker only. Agent behaviour on these "
                  "scenarios still needs the manual drill in evals/runtime/README.md.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
