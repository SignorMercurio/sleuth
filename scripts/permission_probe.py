#!/usr/bin/env python3
"""Runtime permission probe for the SLEUTH skill's packaged target adapters.

Closes the evidence gap named by the `permission-runtime` waiver in
reports/review_waivers.json. Read-only, no runtime execution against any
adapter: it statically checks that

  1. skills/sleuth/agents/interface.yaml's trust block still declares the
     invariants the whole read-only design depends on: execution.context is
     "inline", trust.source_tier is "local", trust.remote_inline_execution is
     "forbid".
  2. skills/sleuth/agents/openai.yaml (the Codex adapter) does not declare any
     execution permission beyond that canonical interface: no top-level
     execution-capability key of its own, and dependencies.tools contains
     only the mcp:siren entry.
  3. skills/sleuth/SKILL.md still states the guardrail semantics those
     invariants depend on (read-only principle, ban on state-changing
     commands, disposal commands never run through SIREN). The anchor
     phrases are declared in scripts/permission_probe_anchors.yaml rather
     than hardcoded here -- see that file's header for why.

Exit code 0 when every check passes; non-zero with the specific failing
check(s) printed otherwise. Only stdlib + pyyaml.
"""

from __future__ import annotations

import pathlib
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills/sleuth"
INTERFACE_PATH = SKILL_ROOT / "agents/interface.yaml"
OPENAI_PATH = SKILL_ROOT / "agents/openai.yaml"
SKILL_MD_PATH = SKILL_ROOT / "SKILL.md"
ANCHORS_PATH = ROOT / "scripts/permission_probe_anchors.yaml"

# Top-level keys openai.yaml has no business declaring: any of these would be
# an execution/shell capability not present in the canonical interface.yaml
# contract, which forbids remote inline execution outright.
DISALLOWED_OPENAI_KEYS = {"execution", "shell", "commands", "run", "exec", "permissions"}

errors: list[str] = []


def load_yaml(path: pathlib.Path):
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"{path.relative_to(ROOT)}: missing")
    except yaml.YAMLError as e:
        errors.append(f"{path.relative_to(ROOT)}: YAML parse failed: {e}")
    return None


def check_interface_trust_block(iface: dict) -> None:
    rel = INTERFACE_PATH.relative_to(ROOT)
    compat = iface.get("compatibility") or {}
    execution = compat.get("execution") or {}
    trust = compat.get("trust") or {}

    checks = (
        ("compatibility.execution.context", execution.get("context"), "inline"),
        ("compatibility.trust.source_tier", trust.get("source_tier"), "local"),
        ("compatibility.trust.remote_inline_execution", trust.get("remote_inline_execution"), "forbid"),
    )
    for field, actual, expected in checks:
        if actual != expected:
            errors.append(f"{rel}: {field} is {actual!r}, must be {expected!r}")


def check_openai_adapter(openai_meta: dict) -> None:
    rel = OPENAI_PATH.relative_to(ROOT)

    present_disallowed = sorted(DISALLOWED_OPENAI_KEYS & openai_meta.keys())
    if present_disallowed:
        errors.append(
            f"{rel}: declares execution-capability key(s) not present in interface.yaml: {present_disallowed}"
        )

    tools = ((openai_meta.get("dependencies") or {}).get("tools")) or []
    if not tools:
        errors.append(f"{rel}: dependencies.tools is empty; expected exactly the SIREN mcp entry")
    for i, tool in enumerate(tools):
        tool = tool or {}
        tool_type, tool_value = tool.get("type"), tool.get("value")
        if tool_type != "mcp" or tool_value != "siren":
            errors.append(
                f"{rel}: dependencies.tools[{i}] declares {tool_type}:{tool_value!r}; "
                "only mcp:siren is permitted (interface.yaml trust block forbids remote inline execution)"
            )


def check_skill_md_anchors() -> None:
    rel = SKILL_MD_PATH.relative_to(ROOT)
    if not SKILL_MD_PATH.exists():
        errors.append(f"{rel}: missing")
        return
    text = SKILL_MD_PATH.read_text(encoding="utf-8")

    anchors_doc = load_yaml(ANCHORS_PATH)
    if anchors_doc is None:
        return
    anchors = anchors_doc.get("anchors") or []
    if not anchors:
        errors.append(f"{ANCHORS_PATH.relative_to(ROOT)}: no anchors declared")
        return

    for anchor in anchors:
        if str(anchor) not in text:
            errors.append(
                f"{rel}: guardrail anchor not found: {anchor!r} (see {ANCHORS_PATH.relative_to(ROOT)})"
            )


def main() -> None:
    iface = load_yaml(INTERFACE_PATH)
    openai_meta = load_yaml(OPENAI_PATH)

    if iface is not None:
        check_interface_trust_block(iface)
    if openai_meta is not None:
        check_openai_adapter(openai_meta)
    check_skill_md_anchors()

    if errors:
        print("FAIL")
        for e in errors:
            print(f" - {e}")
        sys.exit(1)

    print(
        "OK: interface.yaml trust block intact, openai.yaml declares no extra execution "
        "permissions, SKILL.md guardrail anchors present"
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
