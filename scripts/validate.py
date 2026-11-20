#!/usr/bin/env python3
"""Consistency checks for the SLEUTH skill repo. Run from the repo root.

Checks:
  1. skills/sleuth/SKILL.md frontmatter parses as YAML, name is `sleuth`,
     description <= 1024 chars, and the routing, guardrail and workflow markers
     declared by evals/semantic_config.json remain present.
  2. skills/sleuth/agents/openai.yaml, skills/sleuth/agents/interface.yaml and
     manifest.json parse; the shared display fields and activation posture agree
     between the canonical interface and the Codex adapter.
  3. The interface trust block keeps the read-only invariants, and the Codex
     adapter declares no execution permission beyond the SIREN MCP.
  4. Every `references/*.md` skill-relative path and every `skills/sleuth/...`
     repo path mentioned in the skill or README points at a file that exists.
  5. No orphan file under skills/sleuth/references/ -- each must be reachable from
     SKILL.md or another document, or the runtime will never load it.
  6. No git-tracked file holds an Aliyun AccessKey ID, a private key block or a
     quoted credential literal.
"""

import json
import pathlib
import re
import subprocess
import sys

import yaml

DESCRIPTION_LIMIT = 1024
SKILL_ROOT = pathlib.Path("skills/sleuth")
SKILL_PATH = SKILL_ROOT / "SKILL.md"

errors = []

try:
    semantic_config = json.loads(
        pathlib.Path("evals/semantic_config.json").read_text(encoding="utf-8")
    )
except (FileNotFoundError, json.JSONDecodeError) as e:
    errors.append(f"evals/semantic_config.json: cannot load semantic contracts: {e}")
    semantic_config = {}


def string_list(values, label):
    """Return values when it is a non-empty list of non-empty strings, or report it."""
    if (
        not isinstance(values, list)
        or not values
        or not all(isinstance(value, str) and value for value in values)
    ):
        errors.append(f"evals/semantic_config.json: {label} must be a non-empty string list")
        return []
    return values


def markers(section, key):
    contract = semantic_config.get(section)
    values = contract.get(key) if isinstance(contract, dict) else None
    return string_list(values, f"{section}.{key}")


skill = SKILL_PATH.read_text(encoding="utf-8")
m = re.match(r"^---\n(.*?)\n---\n", skill, re.S)
if not m:
    errors.append(f"{SKILL_PATH}: missing YAML frontmatter")
else:
    try:
        fm = yaml.safe_load(m.group(1))
        if fm.get("name") != "sleuth":
            errors.append(f"{SKILL_PATH}: frontmatter name must be 'sleuth', got {fm.get('name')!r}")
        desc = fm.get("description") or ""
        if not desc:
            errors.append(f"{SKILL_PATH}: frontmatter description missing")
        elif len(desc) > DESCRIPTION_LIMIT:
            errors.append(f"{SKILL_PATH}: description is {len(desc)} chars (limit {DESCRIPTION_LIMIT})")
        else:
            missing_markers = [
                marker
                for marker in markers("frontmatter_contract", "required_exclusion_markers")
                if marker not in desc
            ]
            if missing_markers:
                errors.append(
                    f"{SKILL_PATH}: description missing routing exclusion markers "
                    f"{missing_markers!r}"
                )
    except yaml.YAMLError as e:
        errors.append(f"{SKILL_PATH}: frontmatter YAML parse failed: {e}")

# SKILL.md must keep stating the read-only safety contract. The anchors are short
# on purpose so that rewording survives; update them with any intentional change.
for anchor in markers("guardrail_contract", "required_anchors"):
    if anchor not in skill:
        errors.append(f"{SKILL_PATH}: guardrail anchor not found: {anchor!r}")


def load_yaml(path):
    try:
        return yaml.safe_load(pathlib.Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"{path}: missing")
    except yaml.YAMLError as e:
        errors.append(f"{path}: YAML parse failed: {e}")
    return None


INTERFACE_PATH = SKILL_ROOT / "agents/interface.yaml"
OPENAI_PATH = SKILL_ROOT / "agents/openai.yaml"
openai_meta = load_yaml(OPENAI_PATH)
iface = load_yaml(INTERFACE_PATH)

try:
    json.loads(pathlib.Path("manifest.json").read_text(encoding="utf-8"))
except FileNotFoundError:
    errors.append("manifest.json: missing")
except json.JSONDecodeError as e:
    errors.append(f"manifest.json: JSON parse failed: {e}")

# The canonical interface (interface.yaml) and the Codex adapter (openai.yaml) share
# display fields and an activation posture; both must agree or they drift silently.
# Add a synced field by extending SHARED_INTERFACE_FIELDS; activation stays separate
# because it is a boolean mapping, not a literal-equality check.
SHARED_INTERFACE_FIELDS = ("display_name", "short_description", "default_prompt")
compat = (iface or {}).get("compatibility") or {}
if openai_meta and iface:
    i_face = iface.get("interface") or {}
    o_face = openai_meta.get("interface") or {}
    for field in SHARED_INTERFACE_FIELDS:
        if i_face.get(field) != o_face.get(field):
            errors.append(
                f"adapter drift: interface.yaml interface.{field} != "
                f"openai.yaml interface.{field}"
            )
    mode = (compat.get("activation") or {}).get("mode")
    implicit = (openai_meta.get("policy") or {}).get("allow_implicit_invocation")
    if (mode == "implicit") != bool(implicit):
        errors.append(
            f"activation mismatch: interface.yaml activation.mode={mode!r} vs "
            f"openai.yaml allow_implicit_invocation={implicit!r}"
        )

# The read-only design depends on these trust invariants: the package runs no code
# on remote targets, and remote forensics go only through the SIREN MCP.
if iface:
    execution = compat.get("execution") or {}
    trust = compat.get("trust") or {}
    for field, actual, expected in (
        ("compatibility.execution.context", execution.get("context"), "inline"),
        ("compatibility.trust.source_tier", trust.get("source_tier"), "local"),
        ("compatibility.trust.remote_inline_execution", trust.get("remote_inline_execution"), "forbid"),
    ):
        if actual != expected:
            errors.append(f"{INTERFACE_PATH}: {field} is {actual!r}, must be {expected!r}")

# Top-level keys that would give the Codex adapter an execution capability the
# canonical interface does not declare.
DISALLOWED_OPENAI_KEYS = {"execution", "shell", "commands", "run", "exec", "permissions"}
if openai_meta:
    present_disallowed = sorted(DISALLOWED_OPENAI_KEYS & openai_meta.keys())
    if present_disallowed:
        errors.append(
            f"{OPENAI_PATH}: declares execution-capability key(s) not present in "
            f"interface.yaml: {present_disallowed}"
        )
    tools = ((openai_meta.get("dependencies") or {}).get("tools")) or []
    if not tools:
        errors.append(f"{OPENAI_PATH}: dependencies.tools is empty; expected the SIREN mcp entry")
    for i, tool in enumerate(tools):
        tool_type, tool_value = (tool or {}).get("type"), (tool or {}).get("value")
        if tool_type != "mcp" or tool_value != "siren":
            errors.append(
                f"{OPENAI_PATH}: dependencies.tools[{i}] declares "
                f"{tool_type}:{tool_value!r}; only mcp:siren is permitted"
            )

ref_files = sorted(str(p) for p in (SKILL_ROOT / "references").glob("*.md"))
md_paths = [SKILL_PATH, pathlib.Path("README.md")] + sorted(
    (SKILL_ROOT / "references").glob("*.md")
)
md_files = [str(p) for p in md_paths]
bodies = {f: pathlib.Path(f).read_text(encoding="utf-8") for f in md_files}

workflow_contract = semantic_config.get("workflow_contract", {})
if not isinstance(workflow_contract, dict) or not workflow_contract:
    errors.append("evals/semantic_config.json: workflow_contract must be a non-empty object")
else:
    for path, path_markers in workflow_contract.items():
        path_markers = string_list(path_markers, f"workflow_contract[{path!r}]")
        if not path_markers:
            continue
        contract_body = bodies.get(path)
        if contract_body is None:
            errors.append(f"evals/semantic_config.json: workflow contract file missing: {path}")
            continue
        missing_markers = [marker for marker in path_markers if marker not in contract_body]
        if missing_markers:
            errors.append(f"{path}: missing workflow contract markers {missing_markers!r}")

ref_pattern = re.compile(r"(?:skills/sleuth/)?references/[A-Za-z0-9_\-/]+\.md")


def resolve_ref(ref, source):
    if ref.startswith("skills/sleuth/"):
        return pathlib.Path(ref)
    source_path = pathlib.Path(source)
    if source_path == SKILL_PATH or SKILL_ROOT in source_path.parents:
        return SKILL_ROOT / ref
    return pathlib.Path(ref)


referenced = set()
for f, body in bodies.items():
    for ref in sorted(set(ref_pattern.findall(body))):
        resolved = resolve_ref(ref, f)
        resolved_str = str(resolved)
        if resolved_str != f:
            referenced.add(resolved_str)
        if not resolved.exists():
            errors.append(f"{f}: broken reference {ref} -> {resolved}")

for p in ref_files:
    if p not in referenced:
        errors.append(f"{p}: orphan, not referenced from {SKILL_PATH} or any other document")

# Secret scan over git-tracked files. The repository is public, so a leaked
# credential in a fixture or a note is the one release risk a static check can catch.
SECRET_RULES = (
    ("aliyun_access_key_id", re.compile(r"\bLTAI[A-Za-z0-9]{12,30}\b")),
    (
        "private_key_block",
        re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----"),
    ),
)
CREDENTIAL_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(?:access[_-]?key(?:[_-]?secret)?|secret[_-]?key|api[_-]?key|token|passwd|password)"
    r"\b\s*[:=]\s*['\"]([^'\"\n]{6,})['\"]"
)
PLACEHOLDER_MARKERS = (
    "xxx", "changeme", "example", "placeholder", "<", "{{", "$",
    "your_", "replace", "todo", "n/a", "null", "none", "test",
    "sample", "dummy", "fake",
)

tracked = subprocess.run(
    ["git", "ls-files", "-z"], check=True, capture_output=True
).stdout.decode("utf-8")
files_scanned = 0
for name in filter(None, tracked.split("\0")):
    path = pathlib.Path(name)
    try:
        text = path.read_text(encoding="utf-8")
    except (FileNotFoundError, UnicodeDecodeError):
        continue
    files_scanned += 1
    for lineno, line in enumerate(text.splitlines(), start=1):
        for rule, pattern in SECRET_RULES:
            if pattern.search(line):
                errors.append(f"{name}:{lineno}: possible secret ({rule})")
        for match in CREDENTIAL_ASSIGNMENT_RE.finditer(line):
            value = match.group(1).lower()
            if not any(marker in value for marker in PLACEHOLDER_MARKERS):
                errors.append(f"{name}:{lineno}: possible secret (credential_assignment)")

if errors:
    print("FAIL")
    for e in errors:
        print(f" - {e}")
    sys.exit(1)

print(
    f"OK: frontmatter, guardrail and workflow markers valid, trust block intact, "
    f"{len(md_files)} markdown files checked with no broken or orphan references, "
    f"{files_scanned} tracked files scanned for secrets"
)
