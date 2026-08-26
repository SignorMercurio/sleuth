"""Direct (non-MCP) Python API for the mock SIREN server.

`MockSirenSession` is the scriptable form used by the test suite: it holds one
scenario, exposes the same two tools SLEUTH is allowed to use (`ls` and `run`),
and applies the same policy, fault, and output-truncation behaviour as the MCP
transport in `server.py`. The MCP layer is a thin adapter over this class, so
the protocol tests and the scenario tests exercise the same engine.

Sizes and outcomes mirror the real SIREN MCP server:
  - `run` results over 8 KiB collapse to a 4 KiB head + 4 KiB tail preview in
    `auto` mode; `full` returns everything up to the 50 KiB transport limit.
  - errors come back as tool errors with SIREN's wording ("client not found",
    "command blocked by policy (matched: ...)").
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from .faults import FaultEngine
from .policy import blacklist_match
from .shell import HostSimulator

INLINE_MAX_BYTES = 8 << 10
PREVIEW_HEAD_BYTES = 4 << 10
PREVIEW_TAIL_BYTES = 4 << 10
MAX_COMMAND_BYTES = 50 << 10
RESULT_TTL = timedelta(hours=1)

OUTPUT_MODES = ("auto", "full")


@dataclass
class RunResult:
    """One `run` call as both the agent sees it and the test suite inspects it."""

    outcome: str
    text: str
    is_error: bool
    structured: dict[str, Any] = field(default_factory=dict)
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0

    @property
    def truncated(self) -> bool:
        return bool(self.structured.get("truncated"))


class MockSirenSession:
    """Stateful mock of one SIREN server bound to one scenario."""

    def __init__(self, scenario: dict[str, Any], project: str = "mock"):
        self.scenario = scenario
        self.project = project
        self._lock = threading.RLock()
        self._clients: dict[str, dict[str, Any]] = {}
        self._simulators: dict[str, HostSimulator] = {}
        for client in scenario.get("clients", []):
            client_id = str(client["id"])
            self._clients[client_id] = client
            self._simulators[client_id] = HostSimulator(client["host"])
        self.faults = FaultEngine.from_scenario(scenario)
        self.call_count = 0
        self.audit_log: list[dict[str, Any]] = []

    # -- session helpers ----------------------------------------------------

    def reset(self) -> None:
        with self._lock:
            self.faults.reset()
            self.call_count = 0
            self.audit_log.clear()

    def _online(self, client_id: str) -> bool:
        client = self._clients.get(client_id)
        if client is None or not client.get("online", True):
            return False
        return self.faults.disconnected(client_id) is None

    # -- tool: ls -----------------------------------------------------------

    def ls(self) -> list[dict[str, Any]]:
        """Structured client list. Offline clients are omitted, as in SIREN."""
        with self._lock:
            return [
                {
                    "client_id": client_id,
                    "os": client.get("os", "linux/amd64"),
                    "address": client.get("address", "0.0.0.0:0"),
                    "note": client.get("note", "-"),
                    "plugins": client.get("plugins", "-"),
                    "recon_profiles": client.get("recon_profiles", "-"),
                }
                for client_id, client in self._clients.items()
                if self._online(client_id)
            ]

    def ls_text(self) -> str:
        """Table rendering that matches the real `ls` tool's text result."""
        rows = self.ls()
        header = ("Client ID", "Client OS", "Client Address", "Note", "Plugins", "Recon Profiles")
        widths = [
            max(len(header[index]), *(len(str(list(row.values())[index])) for row in rows))
            if rows
            else len(header[index])
            for index in range(len(header))
        ]
        separator = "+" + "+".join("-" * (width + 2) for width in widths) + "+"
        lines = [separator, _row(header, widths), separator]
        for row in rows:
            lines.append(_row([str(value) for value in row.values()], widths))
        lines.append(separator)
        return "\n".join(lines)

    # -- tool: run ----------------------------------------------------------

    def run(self, client_id: Any, command: str, output_mode: str = "auto") -> RunResult:
        client_key = str(client_id)
        with self._lock:
            self.call_count += 1
            audit_id = f"mock-{self.project}-{self.call_count:04d}"
            result, simulator = self._prepare_run_locked(
                audit_id, client_key, command, output_mode
            )

        if result is None:
            assert simulator is not None
            outcome = simulator.execute(command)
            result = self._success(
                audit_id, client_key, outcome.stdout, outcome.stderr,
                outcome.exit_code, output_mode,
            )

        with self._lock:
            self.audit_log.append(
                {
                    "audit_id": result.structured.get("audit_id", ""),
                    "client_id": client_key,
                    "command": command,
                    "outcome": result.outcome,
                }
            )
        return result

    def _prepare_run_locked(
        self, audit_id: str, client_id: str, command: str, output_mode: str
    ) -> tuple[RunResult | None, HostSimulator | None]:
        if output_mode not in OUTPUT_MODES:
            return (
                self._error(audit_id, client_id, "invalid_request",
                            f"output_mode must be one of {OUTPUT_MODES}"),
                None,
            )
        if not isinstance(command, str) or not command.strip():
            return (
                self._error(audit_id, client_id, "invalid_request",
                            "command parameter is required"),
                None,
            )
        if len(command.encode("utf-8")) > MAX_COMMAND_BYTES:
            return (
                self._error(audit_id, client_id, "invalid_request",
                            f"command exceeds {MAX_COMMAND_BYTES}-byte limit"),
                None,
            )

        matched = blacklist_match(command)
        if matched:
            return (
                self._error(audit_id, client_id, "blocked",
                            f"command blocked by policy (matched: {matched})"),
                None,
            )

        if not client_id.isdigit():
            return (
                self._error(audit_id, client_id, "rejected",
                            "invalid client ID: must be a number"),
                None,
            )
        if client_id not in self._clients:
            return self._error(audit_id, client_id, "rejected", "client not found"), None

        disconnect = self.faults.disconnected(client_id)
        if disconnect is not None:
            reason = disconnect.get("reason", "client connection lost")
            return (
                self._error(audit_id, client_id, "disconnected",
                            f"client not found ({reason})"),
                None,
            )
        if not self._clients[client_id].get("online", True):
            return self._error(audit_id, client_id, "rejected", "client not found"), None

        self.faults.note_run(client_id)
        fault = self.faults.evaluate(client_id, command)
        if fault.kind == "timeout":
            return self._error(audit_id, client_id, "timeout", fault.message), None
        if fault.kind == "error":
            return (
                self._success(audit_id, client_id, "", fault.stderr, fault.exit_code,
                              output_mode),
                None,
            )

        return None, self._simulators[client_id]

    # -- result shaping -----------------------------------------------------

    def _metadata(self, audit_id: str, client_id: str, outcome: str,
                  original: int, returned: int, complete: bool,
                  strategy: str, shown: list[dict], omitted: list[dict]) -> dict[str, Any]:
        created = datetime.now(timezone.utc).replace(microsecond=0)
        return {
            "audit_id": audit_id,
            "outcome": outcome,
            "project": self.project,
            "client_id": int(client_id) if client_id.isdigit() else 0,
            "complete": complete,
            "truncated": not complete,
            "original_bytes": original,
            "returned_bytes": returned,
            "preview_strategy": strategy,
            "shown_ranges": shown,
            "omitted_ranges": omitted,
            "created_at": created.isoformat(),
            "expires_at": (created + RESULT_TTL).isoformat(),
        }

    def _error(self, audit_id: str, client_id: str, outcome: str, message: str) -> RunResult:
        size = len(message.encode("utf-8"))
        return RunResult(
            outcome=outcome,
            text=message,
            is_error=True,
            structured=self._metadata(
                audit_id, client_id, outcome, size, size, True, "full",
                [{"start": 0, "end": size}] if size else [], [],
            ),
            stderr=message,
            exit_code=1,
        )

    def _success(self, audit_id: str, client_id: str, stdout: str, stderr: str,
                 exit_code: int, output_mode: str) -> RunResult:
        text = "\n".join(part for part in (stdout, stderr) if part)
        raw = text.encode("utf-8")
        original = len(raw)
        if output_mode == "auto" and original > INLINE_MAX_BYTES:
            head = raw[:PREVIEW_HEAD_BYTES].decode("utf-8", errors="ignore")
            tail_start = original - PREVIEW_TAIL_BYTES
            tail = raw[tail_start:].decode("utf-8", errors="ignore")
            omitted_bytes = tail_start - PREVIEW_HEAD_BYTES
            view = (
                f"{head}\n"
                f"... [mock-siren] {omitted_bytes} bytes omitted "
                f"(audit_id={audit_id}); narrow the command or use output_mode=full ...\n"
                f"{tail}"
            )
            metadata = self._metadata(
                audit_id, client_id, "success", original,
                PREVIEW_HEAD_BYTES + PREVIEW_TAIL_BYTES, False, "head_tail",
                [{"start": 0, "end": PREVIEW_HEAD_BYTES},
                 {"start": tail_start, "end": original}],
                [{"start": PREVIEW_HEAD_BYTES, "end": tail_start}],
            )
            return RunResult("success", view, False, metadata, stdout, stderr, exit_code)

        if original > MAX_COMMAND_BYTES:
            text = raw[:MAX_COMMAND_BYTES].decode("utf-8", errors="ignore")
            raw = text.encode("utf-8")
        returned = len(raw)
        metadata = self._metadata(
            audit_id, client_id, "success", original, returned,
            returned == original, "full",
            [{"start": 0, "end": returned}] if returned else [], [],
        )
        return RunResult("success", text, False, metadata, stdout, stderr, exit_code)


def _row(values: list[str] | tuple[str, ...], widths: list[int]) -> str:
    cells = [f" {value:<{widths[index]}} " for index, value in enumerate(values)]
    return "|" + "|".join(cells) + "|"
