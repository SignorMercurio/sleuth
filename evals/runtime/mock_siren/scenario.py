"""Scenario loading, schema validation, and static consistency checks.

A scenario file describes one compromised (or clean) host fleet plus the
behaviour a SLEUTH investigation is expected to reach on it. The data half
drives the mock SIREN server; the `expectation` half is the contract a human
(or an agent-driven end-to-end run) is graded against.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .faults import validate_faults
from .shell import HostSimulator, ScenarioDataError

SCENARIO_DIR = Path(__file__).resolve().parents[1] / "scenarios"

CATEGORIES = ("positive", "conflict", "negative", "boundary")
MODES = ("alarm_driven", "free_form")
CONFIDENCE_LEVELS = ("confirmed", "probable", "speculative", "inconclusive")

REQUIRED_TOP_LEVEL = (
    "id",
    "title",
    "category",
    "investigation_mode",
    "clients",
    "expectation",
)
REQUIRED_EXPECTATION = (
    "verdict",
    "confidence_ceiling",
    "must_conclude",
    "must_not_conclude",
    "required_evidence",
    "notes",
)


def scenario_paths() -> list[Path]:
    return sorted(SCENARIO_DIR.glob("*.json"))


def load_scenario(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_all_scenarios() -> list[tuple[Path, dict[str, Any]]]:
    return [(path, load_scenario(path)) for path in scenario_paths()]


def _is_str_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def validate_scenario(scenario: dict[str, Any]) -> list[str]:
    """Return schema problems in one scenario. An empty list means valid."""
    errors: list[str] = []
    for key in REQUIRED_TOP_LEVEL:
        if key not in scenario:
            errors.append(f"missing top-level key: {key}")
    if errors:
        return errors

    if scenario["category"] not in CATEGORIES:
        errors.append(f"category must be one of {CATEGORIES}, got {scenario['category']!r}")
    if scenario["investigation_mode"] not in MODES:
        errors.append(f"investigation_mode must be one of {MODES}")

    clients = scenario["clients"]
    if not isinstance(clients, list) or not clients:
        errors.append("clients must be a non-empty list")
        return errors

    seen_ids: set[str] = set()
    for index, client in enumerate(clients):
        label = f"clients[{index}]"
        client_id = str(client.get("id", ""))
        if not client_id.isdigit():
            errors.append(f"{label}: id must be a numeric string (SIREN parses it with Atoi)")
        if client_id in seen_ids:
            errors.append(f"{label}: duplicate client id {client_id}")
        seen_ids.add(client_id)
        host = client.get("host")
        if not isinstance(host, dict):
            errors.append(f"{label}: host must be an object")
            continue
        for key in ("hostname", "now"):
            if key not in host:
                errors.append(f"{label}.host: missing {key}")
        if "now" in host:
            try:
                datetime.fromisoformat(host["now"])
            except ValueError:
                errors.append(f"{label}.host.now is not an ISO timestamp: {host['now']!r}")
        errors.extend(f"{label}.host: {problem}" for problem in _validate_host(host))

    expectation = scenario["expectation"]
    if not isinstance(expectation, dict):
        errors.append("expectation must be an object")
        return errors
    for key in REQUIRED_EXPECTATION:
        if key not in expectation:
            errors.append(f"expectation: missing {key}")
    if expectation.get("confidence_ceiling") not in CONFIDENCE_LEVELS:
        errors.append(f"expectation.confidence_ceiling must be one of {CONFIDENCE_LEVELS}")
    for key in ("must_conclude", "must_not_conclude"):
        if key in expectation and not _is_str_list(expectation[key]):
            errors.append(f"expectation.{key} must be a list of strings")
    if not expectation.get("must_conclude"):
        errors.append("expectation.must_conclude must not be empty")

    probes = expectation.get("required_evidence", [])
    if not isinstance(probes, list) or not probes:
        errors.append("expectation.required_evidence must be a non-empty list")
    else:
        for index, probe in enumerate(probes):
            label = f"expectation.required_evidence[{index}]"
            if not isinstance(probe, dict):
                errors.append(f"{label}: must be an object")
                continue
            if "command" not in probe:
                errors.append(f"{label}: missing command")
            client_id = str(probe.get("client", ""))
            if client_id not in seen_ids:
                errors.append(f"{label}: unknown client {client_id!r}")
            if not probe.get("must_contain") and not probe.get("must_not_contain"):
                errors.append(f"{label}: needs must_contain or must_not_contain")
            for key in ("must_contain", "must_not_contain"):
                if key in probe and not _is_str_list(probe[key]):
                    errors.append(f"{label}.{key} must be a list of strings")

    errors.extend(validate_faults(scenario))
    return errors


def _validate_host(host: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    seen_paths: set[str] = set()
    for index, raw in enumerate(host.get("files", [])):
        label = f"files[{index}]"
        path = raw.get("path", "")
        if not path.startswith("/"):
            problems.append(f"{label}: path must be absolute, got {path!r}")
        if path in seen_paths:
            problems.append(f"{label}: duplicate path {path}")
        seen_paths.add(path)
        for key in ("mtime", "ctime", "atime"):
            if key in raw:
                try:
                    datetime.fromisoformat(raw[key])
                except ValueError:
                    problems.append(f"{label}.{key} is not an ISO timestamp: {raw[key]!r}")
        if raw.get("kind") == "link" and not raw.get("symlink_target"):
            problems.append(f"{label}: link needs symlink_target")

    pids = {int(proc.get("pid", -1)) for proc in host.get("processes", [])}
    for index, proc in enumerate(host.get("processes", [])):
        if "pid" not in proc or "cmd" not in proc:
            problems.append(f"processes[{index}]: needs pid and cmd")
    for index, conn in enumerate(host.get("connections", [])):
        pid = conn.get("pid")
        if pid is not None and int(pid) not in pids:
            problems.append(
                f"connections[{index}]: pid {pid} has no matching process entry"
            )
    for index, entry in enumerate(host.get("journal", [])):
        if "ts" not in entry or "message" not in entry:
            problems.append(f"journal[{index}]: needs ts and message")
            continue
        try:
            datetime.fromisoformat(entry["ts"])
        except ValueError:
            problems.append(f"journal[{index}].ts is not an ISO timestamp")
    try:
        HostSimulator(host)
    except ScenarioDataError as exc:
        problems.append(str(exc))
    return problems
