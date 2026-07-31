#!/usr/bin/env python3
"""Validate complete SLEUTH report fixtures against the current output contract."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "evals" / "output" / "full_report_cases.json"
DEFAULT_TEMPLATE = ROOT / "skills" / "sleuth" / "assets" / "report.md"
DEFAULT_JSON = ROOT / "reports" / "full_report_eval.json"
DEFAULT_MD = ROOT / "reports" / "full_report_eval.md"

COMMON_FORBIDDEN = (
    "findings",
    "工作底稿",
    "writer qa",
    "步骤 7",
    "步骤 8",
    "进程遥测",
    "access 日志",
    "得手",
    "遗憾的是",
    "好在",
    "不难发现",
    "综上所述",
    "总而言之",
)

def strip_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


def html_comments(text: str) -> list[str]:
    return re.findall(r"<!--.*?-->", text, flags=re.S)


def strip_attack_matrix(text: str) -> str:
    return re.sub(r"^::: attack\b.*?^:::$", "", text, flags=re.M | re.S)


def template_headings(text: str) -> list[str]:
    return [line for line in text.splitlines() if line.startswith("#")]


def defang_ipv4(value: str) -> str:
    head, sep, tail = value.rpartition(".")
    return f"{head}[.]{tail}" if sep else value


def directive_count(text: str, name: str) -> int:
    return len(re.findall(rf"^::: {re.escape(name)}(?:\s|$)", text, flags=re.M))


def directive_counts(text: str) -> Counter[str]:
    return Counter(re.findall(r"^::: ([^\s]+)(?:\s|$)", text, flags=re.M))


def timeline_count(text: str) -> int:
    match = re.search(r"^::: timeline\b.*?^:::$", text, flags=re.M | re.S)
    return len(re.findall(r"^- T", match.group(0), flags=re.M)) if match else 0


def action_count(text: str) -> int:
    phases = re.findall(r"^::: phase\b.*?^:::$", text, flags=re.M | re.S)
    return sum(len(re.findall(r"^- \[[x/ ]\] ", phase, flags=re.M)) for phase in phases)


def duplicate_sentences(visible: str) -> list[str]:
    cleaned = strip_attack_matrix(visible)
    candidates: list[str] = []
    for raw in re.split(r"[。！？]\s*", cleaned):
        sentence = re.sub(r"\s+", "", raw)
        if len(re.findall(r"[\u4e00-\u9fff]", sentence)) < 12:
            continue
        if sentence.startswith(("#", "|", ":::", "-[")):
            continue
        candidates.append(sentence)
    counts = Counter(candidates)
    return [sentence for sentence, count in counts.items() if count > 1]


def validate_case(case: dict[str, Any], base: Path, template: str) -> dict[str, Any]:
    report_path = (base / str(case["report"])).resolve()
    failures: list[str] = []
    metrics: dict[str, Any] = {}
    if not report_path.exists():
        return {
            "id": case["id"],
            "report": str(report_path),
            "passed": False,
            "failures": ["report is missing"],
            "metrics": metrics,
        }

    report = report_path.read_text(encoding="utf-8")
    visible = strip_comments(report)
    visible_without_matrix = strip_attack_matrix(visible)
    report_headings = template_headings(report)
    expected_headings = template_headings(template)

    if not report.startswith("---\n"):
        failures.append("frontmatter is not the first block")
    if html_comments(report) != html_comments(template):
        failures.append("template HTML comments changed or are stale")
    cursor = -1
    for heading in expected_headings:
        if report_headings.count(heading) != 1:
            failures.append(f"template heading count is not 1: {heading}")
            continue
        index = report_headings.index(heading)
        if index <= cursor:
            failures.append(f"template heading order changed: {heading}")
        cursor = index

    starts = len(re.findall(r"^::: \S", report, flags=re.M))
    ends = len(re.findall(r"^:::$", report, flags=re.M))
    metrics["directive_starts"] = starts
    metrics["directive_ends"] = ends
    if starts != ends:
        failures.append(f"directive blocks are unbalanced: {starts} starts, {ends} ends")
    for name, expected in directive_counts(template).items():
        actual = directive_count(report, name)
        if name == "asset":
            if actual < 1:
                failures.append("no asset block")
            continue
        if actual != expected:
            failures.append(f"directive {name} count is {actual}, expected {expected}")

    severity_match = re.search(r"^sev :: 严重等级 ·\s*(\S+)", visible, flags=re.M)
    severity = severity_match.group(1) if severity_match else ""
    metrics["severity"] = severity
    expected_severity = str(case["expected_severity"])
    if severity != expected_severity:
        failures.append(f"severity is {severity or '<missing>'}, expected {expected_severity}")
    if severity not in {"高危", "中危", "低危"}:
        failures.append("severity is outside the allowed set")

    placeholder_patterns = (
        r"\[ [^\]\n]+ \]",
        r"^date:\s*00000000$",
        r"^sir-seq:\s*NN$",
        r"^version:\s*X\.Y$",
    )
    for pattern in placeholder_patterns:
        if re.search(pattern, visible, flags=re.M):
            failures.append(f"unresolved placeholder matched: {pattern}")

    folded = visible.casefold()
    for phrase in (*COMMON_FORBIDDEN, *case.get("forbidden", [])):
        if str(phrase).casefold() in folded:
            failures.append(f"forbidden visible text: {phrase}")
    for phrase in case.get("required", []):
        if str(phrase).casefold() not in folded:
            failures.append(f"required visible text missing: {phrase}")

    for raw_ioc in case.get("attacker_iocs", []):
        raw = str(raw_ioc)
        defanged = defang_ipv4(raw)
        if raw in visible:
            failures.append(f"raw attacker IoC is visible: {raw}")
        if defanged not in visible:
            failures.append(f"defanged attacker IoC is missing: {defanged}")

    timeline_nodes = timeline_count(report)
    actions = action_count(report)
    han_chars = len(re.findall(r"[\u4e00-\u9fff]", visible_without_matrix))
    metrics.update(
        {
            "timeline_nodes": timeline_nodes,
            "actions": actions,
            "visible_han_chars_without_attack_matrix": han_chars,
        }
    )
    if not int(case["timeline_min"]) <= timeline_nodes <= int(case["timeline_max"]):
        failures.append(f"timeline node count {timeline_nodes} is outside expected range")
    if not int(case["action_min"]) <= actions <= int(case["action_max"]):
        failures.append(f"action count {actions} is outside expected range")
    if not int(case["visible_han_min"]) <= han_chars <= int(case["visible_han_max"]):
        failures.append(f"visible Han character count {han_chars} is outside expected range")

    compressed_lines = [
        line.strip()
        for line in visible_without_matrix.splitlines()
        if line.count("；") >= 2 and len(re.findall(r"[\u4e00-\u9fff]", line)) >= 40
    ]
    if compressed_lines:
        failures.append("one or more lines compress multiple relations with semicolons")

    duplicates = duplicate_sentences(visible)
    metrics["duplicate_sentence_count"] = len(duplicates)
    if duplicates:
        failures.append("duplicate customer-facing sentence detected")

    return {
        "id": case["id"],
        "report": str(report_path.relative_to(ROOT)),
        "passed": not failures,
        "failures": failures,
        "metrics": metrics,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Full Report Output Eval",
        "",
        "Complete-report contract regression for SLEUTH Step 8.",
        "",
        f"- Cases: `{summary['case_count']}`",
        f"- Passed: `{summary['passed_count']}`",
        f"- Failed: `{summary['failed_count']}`",
        f"- Gate pass: `{summary['gate_pass']}`",
        "",
        "| Case | Pass | Severity | Timeline | Actions | Visible Han chars |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for result in payload["results"]:
        metrics = result["metrics"]
        lines.append(
            f"| {result['id']} | {result['passed']} | {metrics.get('severity', '')} | "
            f"{metrics.get('timeline_nodes', 0)} | {metrics.get('actions', 0)} | "
            f"{metrics.get('visible_han_chars_without_attack_matrix', 0)} |"
        )
    lines.extend(["", "## Failures", ""])
    failures_written = False
    for result in payload["results"]:
        for failure in result["failures"]:
            failures_written = True
            lines.append(f"- `{result['id']}`: {failure}")
    if not failures_written:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "## Evidence boundary",
            "",
            "- Reports and findings are synthetic file-backed fixtures.",
            "- Length bands are broad case-specific regression guards, not runtime writing quotas.",
            "- Naturalness and semantic repetition still require blind human review.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--template", default=str(DEFAULT_TEMPLATE))
    parser.add_argument("--output-json", default=str(DEFAULT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_MD))
    args = parser.parse_args()

    manifest_path = Path(args.manifest).resolve()
    template_path = Path(args.template).resolve()
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    template = template_path.read_text(encoding="utf-8")
    results = [
        validate_case(case, manifest_path.parent, template)
        for case in payload.get("cases", [])
    ]
    passed = sum(1 for result in results if result["passed"])
    output = {
        "schema_version": "1.0",
        "ok": passed == len(results) and bool(results),
        "manifest": str(manifest_path.relative_to(ROOT)),
        "template": str(template_path.relative_to(ROOT)),
        "summary": {
            "case_count": len(results),
            "passed_count": passed,
            "failed_count": len(results) - passed,
            "gate_pass": passed == len(results) and bool(results),
        },
        "results": results,
    }
    output_json = Path(args.output_json).resolve()
    output_md = Path(args.output_md).resolve()
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(output), encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))
    raise SystemExit(0 if output["ok"] else 2)


if __name__ == "__main__":
    main()
