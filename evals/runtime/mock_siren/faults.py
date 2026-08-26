"""Fault injection for the mock SIREN server.

Scenarios declare faults so the engineering paths that never appear in a text
fixture -- timeouts, retry-after-simplification, client disconnects, command
errors -- become executable. Every fault is deterministic and counter-driven so
a test can assert exactly when it fires.

Fault entries (scenario key `faults`, a list):

    {"type": "timeout",    "match": "<regex>", "client": "1", "times": 1,
     "seconds": 30}
    {"type": "error",      "match": "<regex>", "client": "1",
     "exit_code": 1, "stderr": "...", "times": 0}
    {"type": "disconnect", "client": "1", "after_calls": 6,
     "reason": "client connection lost"}

`times` = 0 means "every matching call"; `times` = N fires for the first N
matching calls and then lets the command through, which is what models the
SLEUTH rule "simplify the command and retry once".
`client` is optional; when omitted the fault applies to every client.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

FAULT_TYPES = ("timeout", "error", "disconnect")


@dataclass
class FaultOutcome:
    """What the fault engine decided for one run call."""

    kind: str = ""
    message: str = ""
    exit_code: int = 0
    stderr: str = ""

    @property
    def triggered(self) -> bool:
        return bool(self.kind)


@dataclass
class FaultEngine:
    """Deterministic fault state for one session."""

    specs: list[dict] = field(default_factory=list)
    fired: dict[int, int] = field(default_factory=dict)
    run_calls: dict[str, int] = field(default_factory=dict)

    @classmethod
    def from_scenario(cls, scenario: dict) -> "FaultEngine":
        return cls(specs=list(scenario.get("faults", [])))

    def reset(self) -> None:
        self.fired.clear()
        self.run_calls.clear()

    def _applies(self, spec: dict, client_id: str) -> bool:
        target = spec.get("client")
        return target is None or str(target) == str(client_id)

    def disconnected(self, client_id: str) -> dict | None:
        """Return the disconnect spec once its call threshold has been passed."""
        for spec in self.specs:
            if spec.get("type") != "disconnect" or not self._applies(spec, client_id):
                continue
            if self.run_calls.get(str(client_id), 0) >= int(spec.get("after_calls", 0)):
                return spec
        return None

    def note_run(self, client_id: str) -> None:
        key = str(client_id)
        self.run_calls[key] = self.run_calls.get(key, 0) + 1

    def evaluate(self, client_id: str, command: str) -> FaultOutcome:
        """Decide whether this command hits an injected fault."""
        for index, spec in enumerate(self.specs):
            kind = spec.get("type")
            if kind not in ("timeout", "error") or not self._applies(spec, client_id):
                continue
            pattern = spec.get("match")
            if pattern and not re.search(pattern, command):
                continue
            budget = int(spec.get("times", 0))
            used = self.fired.get(index, 0)
            if budget and used >= budget:
                continue
            self.fired[index] = used + 1
            if kind == "timeout":
                seconds = int(spec.get("seconds", 30))
                return FaultOutcome(
                    kind="timeout",
                    message=spec.get(
                        "message", f"command timed out after {seconds}s"
                    ),
                )
            return FaultOutcome(
                kind="error",
                exit_code=int(spec.get("exit_code", 1)),
                stderr=spec.get("stderr", "command failed on client"),
            )
        return FaultOutcome()


def validate_faults(scenario: dict) -> list[str]:
    """Return a list of problems with the scenario's fault declarations."""
    errors: list[str] = []
    client_ids = {str(client["id"]) for client in scenario.get("clients", [])}
    for index, spec in enumerate(scenario.get("faults", [])):
        label = f"faults[{index}]"
        kind = spec.get("type")
        if kind not in FAULT_TYPES:
            errors.append(f"{label}: unknown fault type {kind!r}")
            continue
        target = spec.get("client")
        if target is not None and str(target) not in client_ids:
            errors.append(f"{label}: unknown client {target!r}")
        if kind == "disconnect":
            if "after_calls" not in spec:
                errors.append(f"{label}: disconnect needs after_calls")
            continue
        if spec.get("match"):
            try:
                re.compile(spec["match"])
            except re.error as exc:
                errors.append(f"{label}: invalid match regex ({exc})")
    return errors
