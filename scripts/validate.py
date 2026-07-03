#!/usr/bin/env python3
"""Consistency checks for the SLEUTH skill repo. Run from the repo root.

Checks:
  1. SKILL.md frontmatter parses as YAML, name is `sleuth`, description <= 1024 chars.
  2. agents/openai.yaml, agents/interface.yaml, and manifest.json parse; the activation
     posture agrees between the canonical interface and the Codex adapter.
  3. Every `references/*.md` / `assets/*.md` path mentioned in repo Markdown points at a
     file that exists -- catches typos and stale links. (Another skill's internal file
     paths should be described by topic, not hardcoded, so it can load its own references.)
  4. No orphan file under references/ -- each must be reachable from SKILL.md or
     another document, or the runtime will never load it.
"""

import glob
import json
import pathlib
import re
import sys

import yaml

DESCRIPTION_LIMIT = 1024

errors = []

skill = pathlib.Path("SKILL.md").read_text(encoding="utf-8")
m = re.match(r"^---\n(.*?)\n---\n", skill, re.S)
if not m:
    errors.append("SKILL.md: missing YAML frontmatter")
else:
    try:
        fm = yaml.safe_load(m.group(1))
        if fm.get("name") != "sleuth":
            errors.append(f"SKILL.md: frontmatter name must be 'sleuth', got {fm.get('name')!r}")
        desc = fm.get("description") or ""
        if not desc:
            errors.append("SKILL.md: frontmatter description missing")
        elif len(desc) > DESCRIPTION_LIMIT:
            errors.append(f"SKILL.md: description is {len(desc)} chars (limit {DESCRIPTION_LIMIT})")
    except yaml.YAMLError as e:
        errors.append(f"SKILL.md: frontmatter YAML parse failed: {e}")

def load_yaml(path):
    try:
        return yaml.safe_load(pathlib.Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"{path}: missing")
    except yaml.YAMLError as e:
        errors.append(f"{path}: YAML parse failed: {e}")
    return None


openai_meta = load_yaml("agents/openai.yaml")
iface = load_yaml("agents/interface.yaml")

try:
    json.loads(pathlib.Path("manifest.json").read_text(encoding="utf-8"))
except FileNotFoundError:
    errors.append("manifest.json: missing")
except json.JSONDecodeError as e:
    errors.append(f"manifest.json: JSON parse failed: {e}")

# Activation posture must agree between the canonical interface and the Codex adapter.
if openai_meta and iface:
    mode = ((iface.get("compatibility") or {}).get("activation") or {}).get("mode")
    implicit = ((openai_meta.get("policy") or {}).get("allow_implicit_invocation"))
    if (mode == "implicit") != bool(implicit):
        errors.append(
            f"activation mismatch: interface.yaml activation.mode={mode!r} vs "
            f"openai.yaml allow_implicit_invocation={implicit!r}"
        )

ref_files = sorted(glob.glob("references/*.md"))
md_files = ["SKILL.md", "README.md"] + ref_files + sorted(glob.glob("assets/*.md"))
bodies = {f: pathlib.Path(f).read_text(encoding="utf-8") for f in md_files}

ref_pattern = re.compile(r"(?:references|assets)/[A-Za-z0-9_/\-]+\.md")
referenced = set()
for f, body in bodies.items():
    for ref in sorted(set(ref_pattern.findall(body))):
        if ref != f:
            referenced.add(ref)
        if not pathlib.Path(ref).exists():
            errors.append(f"{f}: broken reference {ref}")

for p in ref_files:
    if p not in referenced:
        errors.append(f"{p}: orphan, not referenced from SKILL.md or any other document")

if errors:
    print("FAIL")
    for e in errors:
        print(f" - {e}")
    sys.exit(1)

print(f"OK: frontmatter valid, {len(md_files)} markdown files checked, no broken or orphan references")
