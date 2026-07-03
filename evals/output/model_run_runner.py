#!/usr/bin/env python3
"""Replay runner for the model-executed output-eval case.

Emits the {output, execution_kind, provider, model, usage} envelope that the
skill-creator harness `run_output_execution.py` expects from a `--runner-command`
(that harness is external — the same skill-creator toolchain every sleuth eval
uses; it is not vendored into this repo). The replayed text is the real
claude-fable-5 sub-agent output the harness passes in on stdin as `fixture_output`
(sourced from evals/output/model_run_case.jsonl, archived for humans under
fixtures/overview-from-findings.*.model.md); `output_sha256` in
reports/output_execution_runs.json pins the exact graded text.

This mirrors the stock local_output_eval_runner.py envelope, differing only by
reporting the real per-variant sub-agent token totals instead of its len/4
estimate. Both stay marked `estimated` because they are not provider-metered.

Usage: run_output_execution.py --cases evals/output/model_run_case.jsonl \
  --runner-command "python3 evals/output/model_run_runner.py"
"""
import json
import sys

# Real sub-agent token totals reported by the Agent tool at generation time.
SUBAGENT_TOKENS = {"baseline": 22886, "with_skill": 23273}

req = json.loads(sys.stdin.read())
variant = req.get("variant", "")
print(json.dumps({
    "output": req.get("fixture_output", ""),
    "execution_kind": "model",
    "provider": "anthropic",
    "model": "claude-fable-5",
    "usage": {"output_tokens": SUBAGENT_TOKENS.get(variant, 0), "estimated": True},
}, ensure_ascii=False))
