#!/usr/bin/env python3
"""Consistency checks for the SLEUTH skill repo. Run from the repo root.

Checks:
  1. skills/sleuth/SKILL.md frontmatter parses as YAML, name is `sleuth`,
     description <= 1024 chars.
  2. skills/sleuth/agents/openai.yaml, skills/sleuth/agents/interface.yaml,
     and manifest.json parse; the shared
     display fields and activation posture agree between the canonical interface and
     the Codex adapter (they drift silently otherwise).
  3. Every `references/*.md` / `assets/*.md` skill-relative path and every
     `skills/sleuth/...` repo path mentioned in repo Markdown points at a file that
     exists -- catches typos and stale links. (Another skill's internal file paths
     should be described by topic, not hardcoded, so it can load its own references.)
  4. No orphan file under skills/sleuth/references/ -- each must be reachable from
     SKILL.md or another document, or the runtime will never load it.
"""

import json
import pathlib
import re
import sys

import yaml

DESCRIPTION_LIMIT = 1024
SKILL_ROOT = pathlib.Path("skills/sleuth")
SKILL_PATH = SKILL_ROOT / "SKILL.md"

errors = []

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
    except yaml.YAMLError as e:
        errors.append(f"{SKILL_PATH}: frontmatter YAML parse failed: {e}")

def load_yaml(path):
    try:
        return yaml.safe_load(pathlib.Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"{path}: missing")
    except yaml.YAMLError as e:
        errors.append(f"{path}: YAML parse failed: {e}")
    return None


openai_meta = load_yaml(SKILL_ROOT / "agents/openai.yaml")
iface = load_yaml(SKILL_ROOT / "agents/interface.yaml")

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
if openai_meta and iface:
    i_face = iface.get("interface") or {}
    o_face = openai_meta.get("interface") or {}
    for field in SHARED_INTERFACE_FIELDS:
        if i_face.get(field) != o_face.get(field):
            errors.append(
                f"adapter drift: interface.yaml interface.{field} != "
                f"openai.yaml interface.{field}"
            )
    mode = ((iface.get("compatibility") or {}).get("activation") or {}).get("mode")
    implicit = (openai_meta.get("policy") or {}).get("allow_implicit_invocation")
    if (mode == "implicit") != bool(implicit):
        errors.append(
            f"activation mismatch: interface.yaml activation.mode={mode!r} vs "
            f"openai.yaml allow_implicit_invocation={implicit!r}"
        )

ref_files = sorted(str(p) for p in (SKILL_ROOT / "references").glob("*.md"))
md_paths = (
    [SKILL_PATH, pathlib.Path("README.md")]
    + sorted((SKILL_ROOT / "references").glob("*.md"))
    + sorted((SKILL_ROOT / "assets").glob("**/*.md"))
)
md_files = [str(p) for p in md_paths]
bodies = {f: pathlib.Path(f).read_text(encoding="utf-8") for f in md_files}

ref_pattern = re.compile(
    r"(?:skills/sleuth/)?(?:references|assets)/[A-Za-z0-9_\-/]+\.md"
)


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

if errors:
    print("FAIL")
    for e in errors:
        print(f" - {e}")
    sys.exit(1)

print(f"OK: frontmatter valid, {len(md_files)} markdown files checked, no broken or orphan references")
