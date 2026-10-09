#!/usr/bin/env python3
"""Summarize model round trips and context load in Codex rollout .jsonl files."""

import json
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

IMAGE_TOOLS = re.compile(r"view_image|imagegen")
SKILL_READ = re.compile(r"\b(cat|sed|head)\b[^\n]*SKILL\.md")
BIG_OUTPUT = 20 * 1024


def percentile(values, pct):
    if not values:
        return 0
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(len(ordered) * pct / 100))]


def output_text(payload):
    output = payload.get("output", "")
    if isinstance(output, str):
        return output
    return json.dumps(output, ensure_ascii=False)


def summarize(path):
    model_calls = compactions = skill_reads = 0
    context = []
    total_usage = {}
    tools = Counter()
    image_call_ids = set()
    exec_call_ids = set()
    exec_outputs = []

    with Path(path).open(encoding="utf-8") as handle:
        for line in handle:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            kind = record.get("type")
            payload = record.get("payload") or {}
            subtype = payload.get("type", "")
            if kind == "compacted" or (kind == "event_msg" and "compact" in subtype):
                compactions += 1
            if kind == "event_msg" and subtype == "token_count":
                model_calls += 1
                info = payload.get("info") or {}
                last = (info.get("last_token_usage") or {}).get("input_tokens")
                if last is not None:
                    context.append(last)
                total_usage = info.get("total_token_usage") or total_usage
            if kind != "response_item":
                continue
            if subtype in ("custom_tool_call", "function_call"):
                name = payload.get("name", "?")
                tools[name] += 1
                call_input = payload.get("input") or payload.get("arguments") or ""
                if not isinstance(call_input, str):
                    call_input = json.dumps(call_input, ensure_ascii=False)
                if SKILL_READ.search(call_input):
                    skill_reads += 1
                if name == "exec":
                    if IMAGE_TOOLS.search(call_input):
                        image_call_ids.add(payload.get("call_id"))
                    else:
                        exec_call_ids.add(payload.get("call_id"))
            elif subtype in ("custom_tool_call_output", "function_call_output"):
                call_id = payload.get("call_id")
                if call_id in exec_call_ids:
                    exec_outputs.append(len(output_text(payload).encode("utf-8")))

    big = [size for size in exec_outputs if size > BIG_OUTPUT]
    total_bytes = sum(exec_outputs)
    print(f"== {path}")
    print(f"model calls: {model_calls}")
    if context:
        print(f"context input_tokens: median {int(statistics.median(context))}, peak {max(context)}")
    print(f"total usage: {json.dumps(total_usage, sort_keys=True)}")
    print(f"compactions: {compactions}")
    print("tool calls: " + ", ".join(f"{name}={count}" for name, count in tools.most_common()))
    if exec_outputs:
        print(
            f"exec output bytes (non-image, n={len(exec_outputs)}, image calls excluded={len(image_call_ids)}): "
            f"median {int(statistics.median(exec_outputs))}, p90 {percentile(exec_outputs, 90)}, "
            f"max {max(exec_outputs)}, total {total_bytes}"
        )
        print(
            f"exec outputs >20KB: {len(big)}/{len(exec_outputs)} calls "
            f"({len(big) / len(exec_outputs):.1%}), {sum(big) / total_bytes:.1%} of bytes"
        )
    print(f"SKILL.md reads (cat/sed/head): {skill_reads}")


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: air_session_stats.py ROLLOUT.jsonl [...]")
    for path in sys.argv[1:]:
        summarize(path)


if __name__ == "__main__":
    main()
