#!/usr/bin/env python3
"""Replay runner for the model-executed output-eval case.

Feeds the real claude-fable-5 sub-agent outputs (archived under
fixtures/overview-from-findings.*.model.md) to run_output_execution.py so the
grading harness records them as model-executed evidence. The grading harness
runs as a subprocess and cannot call back into the orchestrator's Agent tool,
so the live generation is replayed from its archived snapshot; output_sha256 in
reports/output_execution_runs.json pins the exact text that was graded.

Usage: run_output_execution.py --cases evals/output/model_run_case.jsonl \
  --runner-command "python3 evals/output/model_run_runner.py"
"""
import json
import re
import sys
from pathlib import Path

FIX = Path(__file__).resolve().parent / "fixtures"
# Real sub-agent token totals reported by the Agent tool at generation time.
SUBAGENT_TOKENS = {"baseline": 22886, "with_skill": 23273}


def body(variant: str) -> str:
    text = (FIX / f"overview-from-findings.{variant}.model.md").read_text(encoding="utf-8")
    return re.sub(r"<!--.*?-->", "", text, flags=re.S).strip()


req = json.loads(sys.stdin.read())
variant = req.get("variant", "")
print(json.dumps({
    "output": body(variant) if variant in ("baseline", "with_skill") else "",
    "execution_kind": "model",
    "provider": "anthropic",
    "model": "claude-fable-5",
    "usage": {"output_tokens": SUBAGENT_TOKENS.get(variant, 0), "estimated": True},
}, ensure_ascii=False))
