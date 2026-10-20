#!/usr/bin/env python3
"""Density leads for an IR report, and change checks for a revision of it.

  check_report.py ORIGINAL           where the report is over its caps or dense
  check_report.py ORIGINAL REVISED   the same before -> after, plus FAIL checks that the
                                     revision kept the structure, attacker IoCs and hashes
                                     and introduced no concrete value the original lacks
  --summary TEXT                     also check the one-line summary for the tracking table

Reads Markdown only and writes nothing. Exits 1 when a FAIL check trips.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

# Caps are read from their owners: the report's own template comments, this skill's SKILL.md
# and, when this skill is installed next to sleuth, sleuth's cross-chapter writing rules.
SKILL = Path(__file__).resolve().parents[1] / "SKILL.md"
SLEUTH_RULES = Path(__file__).resolve().parents[2] / "sleuth" / "references" / "report_writing_rules.md"
DENSE_VALUES = 4  # more than three concrete values in one sentence
CELL_HAN = 50
REPEAT_GRAM, REPEAT_MIN = 10, 3  # same windows as sleuth's validate_full_reports.py
SHOW = 12

FIXED_BLOCKS = ("cover-hero", "cover-meta", "rev", "attack")
BLOCK = re.compile(r"^:::[ \t]*(\S+)([^\n]*)\n(.*?)^:::[ \t]*$", re.M | re.S)
FIELD = re.compile(r"^([^\s:|#>!\-{][^:\n]{0,30}?) :: (.*)$", re.M)
IMAGE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)\)(\{[^}\n]*\})?")
LAYOUT = re.compile(r"^\{(?:break|gap)\b[^}\n]*\}[ \t]*$", re.M)
CODE = re.compile(r"`[^`\n]+`")
# Order matters: each match is masked before the next pattern runs, so an IP's digits are
# not counted again as a number. Boundaries are ASCII-only because CJK text puts no space
# around values.
VALUES = (
    ("url", re.compile(r"(?:https?|hxxps?)://[^\s)）\]，。；`\"]+")),
    ("ip", re.compile(r"(?<![\d.])\d{1,3}\.\d{1,3}\.\d{1,3}(?:\.|\[\.\])\d{1,3}(?::\d{1,5})?(?![\d.])")),
    ("domain", re.compile(r"(?<![\w.-])[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\[\.\][A-Za-z]{2,}(?![\w-])")),
    ("hash", re.compile(r"(?<![0-9A-Za-z])[0-9a-fA-F]{32,}(?![0-9A-Za-z])")),
    ("path", re.compile(r"(?<![0-9A-Za-z_.\]/:])/(?:[A-Za-z0-9_.@*-]+/)*[A-Za-z0-9_.@*-]+")),
    ("date", re.compile(r"(?<!\d)\d{4}/\d{1,2}/\d{1,2}(?!\d)|\d{1,2} ?月 ?\d{1,2} ?日|(?<![\d/])\d{1,2}/\d{1,2}(?![\d/])")),
    ("time", re.compile(r"(?<![\d:])\d{1,2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?![\d:])")),
    ("count", re.compile(r"(?<![\d.,])\d[\d,]*(?:\.\d+)? ?[万亿]? ?(?:毫秒|秒|分钟|小时|天|周|个月|年|次|台|条|个|人|名|项|处|家|份|组|行|列|位|字节|批|轮|(?:[KMGT]B)(?![A-Za-z])|%)"
                         r"|(?<![一二两三四五六七八九十百千])[一二两三四五六七八九十百千]+ ?(?:毫秒|分钟|小时)")),
    ("number", re.compile(r"(?<![\d.,])(?:\d{1,3}(?:,\d{3})+|\d{3,})(?:\.\d+)?(?![\d,])")),
)
NEW_VALUE_FAILS = ("url", "ip", "domain", "hash", "path")
LOOSE = NEW_VALUE_FAILS + ("code",)  # a shortened form still counts as present; other kinds match whole
# Asset, service, API and parameter names: camelCase, snake/kebab/dotted, alphanumeric or capitalised.
NAME = re.compile(r"(?<![\w.-])[A-Za-z][\w.-]*[A-Za-z0-9]", re.A)


def han(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def blank(match: re.Match[str]) -> str:
    """Replace a match but keep its line breaks, so line numbers stay true."""
    return "\n" * match.group(0).count("\n")


class Report:
    def __init__(self, path: str) -> None:
        self.path = path
        self.text = Path(path).read_text(encoding="utf-8")
        self.comments = re.findall(r"<!--.*?-->", self.text, flags=re.S)
        self.visible = re.sub(r"<!--.*?-->", blank, self.text, flags=re.S)
        self.blocks = [(m.group(1), m.group(1) + m.group(2), m.group(3)) for m in BLOCK.finditer(self.visible)]
        fixed = "|".join(map(re.escape, FIXED_BLOCKS))
        # Customer prose: no comments, no fixed blocks (cover, revision table, ATT&CK matrix).
        self.prose = re.sub(rf"^:::[ \t]*(?:{fixed})\b.*?^:::[ \t]*$", blank, self.visible, flags=re.M | re.S)
        # Density is judged on narrative only: fenced log/command quotes may be cut but not rewritten.
        self.lines = re.sub(r"^```.*?^```[ \t]*$", blank, self.prose, flags=re.M | re.S).splitlines()

    # --- structure -------------------------------------------------------------------

    def frontmatter(self) -> str:
        match = re.match(r"---\n.*?\n---\n", self.text, flags=re.S)
        return match.group(0) if match else ""

    def headings(self, level: int) -> list[str]:
        prefix = "#" * level + " "
        return [line for line in self.visible.splitlines() if line.startswith(prefix)]

    def block(self, name: str) -> list[str]:
        return [body for kind, _, body in self.blocks if kind == name]

    def block_fields(self) -> list[tuple[str, list[str]]]:
        return [(header, [k for k, _ in FIELD.findall(body)]) for kind, header, body in self.blocks
                if kind not in FIXED_BLOCKS and kind not in ("timeline", "phase")]

    def loose_fields(self) -> list[str]:
        outside = BLOCK.sub(blank, self.visible)
        return [key for key, _ in FIELD.findall(outside)]

    def phase_status(self) -> list[tuple[str, list[str]]]:
        return [(header, re.findall(r"^- \[([x/ ])\] ", body, flags=re.M)) for kind, header, body in self.blocks if kind == "phase"]

    def first_recommendation(self) -> list[str]:
        for kind, header, body in self.blocks:
            if kind == "recommendation":
                return [header] + [line for line in body.splitlines() if line.startswith(("name ::", "reason ::"))]
        return []

    def images(self) -> list[tuple[str, str, str]]:
        found = []
        for match in IMAGE.finditer(self.visible):
            attrs = match.group(2) or ""
            size = re.search(r"size=(\w+)", attrs)
            caption = re.search(r'caption="([^"]*)"', attrs)
            found.append((match.group(1), size.group(1) if size else "", caption.group(1) if caption else ""))
        return found

    # --- density ---------------------------------------------------------------------

    def caps(self) -> dict[str, int | tuple[int, int] | None]:
        joined = "\n".join(self.comments)
        fields = re.search(r"headline 不超过 (\d+) 字，四个字段各不超过 (\d+) 字", joined)
        timeline = re.search(r"时间线保留 (\d+)-(\d+) 个", joined)
        rules = SLEUTH_RULES.read_text(encoding="utf-8") if SLEUTH_RULES.exists() else ""
        paragraph = re.search(r"正文自然段不超过 (\d+) 字", rules)
        return {
            "headline": int(fields.group(1)) if fields else None,
            "field": int(fields.group(2)) if fields else None,
            "timeline": (int(timeline.group(1)), int(timeline.group(2))) if timeline else None,
            "paragraph": int(paragraph.group(1)) if paragraph else None,
        }

    def summary_fields(self) -> list[tuple[str, str]]:
        """Key/value lines between the 核心结论 callout and the next heading."""
        callout = re.search(r"^:::[ \t]*callout\b.*?^:::[ \t]*$", self.visible, flags=re.M | re.S)
        if not callout:
            return []
        rest = self.visible[callout.end():]
        section = rest.split("\n#", 1)[0]
        return FIELD.findall(section)

    def headline(self) -> str:
        match = re.search(r"^headline :: (.*)$", self.visible, flags=re.M)
        return match.group(1) if match else ""

    def timeline_nodes(self) -> int:
        return sum(len(re.findall(r"^- [^\n]+ :: ", body, flags=re.M)) for body in self.block("timeline"))

    def paragraphs(self) -> list[tuple[int, str]]:
        skip = ("|", "#", ":::", "![", "- ", ">", "{", "```")
        return [(n, line) for n, line in enumerate(self.lines, 1)
                if line.strip() and not line.startswith(skip) and not FIELD.match(line)]

    def segments(self) -> list[tuple[int, str]]:
        """Sentences and table cells of customer prose, each with its line number."""
        out = []
        for n, line in enumerate(self.lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith(("#", ":::", "![", "{")) or re.fullmatch(r"\|[\s|:-]+\|?", stripped):
                continue
            parts = stripped.strip("|").split("|") if stripped.startswith("|") else [stripped]
            for part in parts:
                out.extend((n, s.strip()) for s in re.split(r"(?<=[。！？])", part) if han(s) or values(s))
        return out

    def cells(self) -> list[tuple[int, str]]:
        out = []
        for n, line in enumerate(self.lines, 1):
            if line.startswith("|") and not re.fullmatch(r"\|[\s|:-]+\|?", line.strip()):
                out.extend((n, cell.strip()) for cell in line.strip().strip("|").split("|"))
        return out

    def metrics(self) -> dict[str, object]:
        caps = self.caps()
        matrixless = re.sub(r"^:::[ \t]*attack\b.*?^:::[ \t]*$", "", self.visible, flags=re.M | re.S)
        segments = self.segments()
        paragraph_cap = caps["paragraph"]
        return {
            "visible Han chars": han(matrixless),
            "prose Han chars": han("\n".join(line for line in self.lines if not line.startswith(("#", "![")))),
            "headline Han chars": han(self.headline()),
            **{f"{key} Han chars": han(value) for key, value in self.summary_fields()},
            "timeline nodes": self.timeline_nodes(),
            f"paragraphs over {paragraph_cap}": sum(han(p) > paragraph_cap for _, p in self.paragraphs()) if paragraph_cap else None,
            f"dense sentences ({DENSE_VALUES}+ values)": len(self.dense(segments)),
            f"phrases repeated {REPEAT_MIN}+ times": len(self.repeated()),
            "long table cells": len(self.long_cells()),
            "times with seconds": sum(len(re.findall(r"\d:\d{2}:\d{2}", CODE.sub("", s))) for _, s in segments),
            "semicolon chains": sum(s.count("；") >= 2 for _, s in segments),
        }

    def dense(self, segments: list[tuple[int, str]] | None = None) -> list[tuple[int, int, str]]:
        found = []
        for n, sentence in segments if segments is not None else self.segments():
            count = len(values(sentence, code_as_value=True))
            if count >= DENSE_VALUES and not self.lines[n - 1].lstrip().startswith("|"):
                found.append((n, count, sentence))
        return found

    def repeated(self) -> list[str]:
        """Longest CJK runs whose every REPEAT_GRAM-char window recurs REPEAT_MIN+ times in the prose:
        the qualifier that review rounds paste into every chapter."""
        runs = re.findall(r"[一-鿿]+", "\n".join(text for _, text in self.segments()))
        grams = Counter(gram for run in runs for gram in {run[i:i + REPEAT_GRAM] for i in range(len(run) - REPEAT_GRAM + 1)})
        hot = {gram for gram, count in grams.items() if count >= REPEAT_MIN}
        phrases = set()
        for run in runs:
            covered = [False] * len(run)
            for i in range(len(run) - REPEAT_GRAM + 1):
                if run[i:i + REPEAT_GRAM] in hot:
                    covered[i:i + REPEAT_GRAM] = [True] * REPEAT_GRAM
            phrases.update(run[m.start():m.end()] for m in re.finditer("1+", "".join("1" if c else "0" for c in covered)))
        return sorted(phrases, key=len, reverse=True)

    def evidence_by_section(self) -> list[list]:
        """[heading, concrete evidence values] per ###/#### section of the technical-analysis chapter."""
        sections: list[list] = []
        inside = False
        for line in self.prose.splitlines():
            if line.startswith("## "):
                inside = "技术分析" in line
            elif line.startswith(("### ", "#### ")) and inside:
                sections.append([line, 0])
            elif inside and sections:
                sections[-1][1] += sum(kind not in ("number", "count", "date") for kind, _ in values(line.replace("`", " ")))
        return sections

    def long_cells(self) -> list[tuple[int, int, str]]:
        found = []
        for n, cell in self.cells():
            sentences = [s for s in re.split(r"[。！？]", cell) if han(s) >= 5]
            if han(cell) > CELL_HAN or len(sentences) >= 2:
                found.append((n, han(cell), cell))
        return found

    def leads(self) -> list[str]:
        caps = self.caps()
        out = []
        if caps["headline"] and han(self.headline()) > caps["headline"]:
            out.append(f"headline {han(self.headline())} Han chars, cap {caps['headline']}")
        for key, value in self.summary_fields():
            if caps["field"] and han(value) > caps["field"]:
                out.append(f"{key} {han(value)} Han chars, cap {caps['field']}")
        if caps["timeline"] and not caps["timeline"][0] <= self.timeline_nodes() <= caps["timeline"][1]:
            low, high = caps["timeline"]
            out.append(f"timeline has {self.timeline_nodes()} nodes, comment asks {low}-{high}")
        if caps["paragraph"]:
            for n, line in self.paragraphs():
                if han(line) > caps["paragraph"]:
                    out.append(f"L{n} paragraph {han(line)} Han chars, cap {caps['paragraph']}: {clip(line)}")
        else:
            out.append("paragraph cap unknown: sleuth writing rules not found next to this skill")
        out += [f"phrase repeated {REPEAT_MIN}+ times: {phrase}" for phrase in self.repeated()[:SHOW]]
        dense = sorted(self.dense(), key=lambda item: -item[1])
        out += [f"L{n} sentence with {count} values: {clip(s)}" for n, count, s in dense[:SHOW]]
        cells = sorted(self.long_cells(), key=lambda item: -item[1])
        out += [f"L{n} table cell {count} Han chars: {clip(c)}" for n, count, c in cells[:SHOW]]
        longest = sorted(self.paragraphs(), key=lambda item: -han(item[1]))[:5]
        out += [f"L{n} long paragraph {han(p)} Han chars: {clip(p)}" for n, p in longest if not caps["paragraph"] or han(p) <= caps["paragraph"]]
        return out

    # --- concrete values -------------------------------------------------------------

    def values(self) -> list[tuple[str, str]]:
        return values(self.prose.replace("`", " ")) + [("code", m.group(0)[1:-1]) for m in CODE.finditer(self.prose)]

    def names(self) -> list[tuple[str, str]]:
        """Names in the narrative, outside code, fenced quotes, link targets and other values."""
        text = re.sub(r"\]\([^)\s]*\)", "]", CODE.sub(" ", "\n".join(self.lines)))
        for _, pattern in VALUES:
            text = pattern.sub(" ", text)
        return [("name", word) for word in NAME.findall(text)
                if len(word) >= 3 and (not word.islower() or re.search(r"[\d_.-]", word))]


def values(text: str, code_as_value: bool = False) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []

    def take(kind: str):
        def mask(match: re.Match[str]) -> str:
            found.append((kind, match.group(0)))
            return " " * len(match.group(0))
        return mask

    if code_as_value:
        text = CODE.sub(take("code"), text)
    for kind, pattern in VALUES:
        text = pattern.sub(take(kind), text)
    return found


def norm(text: str) -> str:
    return text.replace("[.]", ".").replace("hxxp", "http").replace("`", "")


def key(kind: str, value: str) -> str:
    """Comparable form: dropping seconds, a port, spacing or digit grouping is not a change."""
    if kind == "time":
        hour, minute = value.split(":")[:2]
        return f"{int(hour):02d}:{minute}"
    if kind == "ip":
        return re.sub(r":\d+$", "", value)
    if kind == "date":
        return "/".join(str(int(n)) for n in re.findall(r"\d+", value))
    if kind in ("number", "count"):
        return re.sub(r"[\s,]", "", value)
    return value


def missing(found: list[tuple[str, str]], other: list[tuple[str, str]], other_text: str) -> dict[str, list[str]]:
    """Values of one report the other lacks. Numbers, times, dates and names must match a whole
    value there, so 158 is not found inside 172.16.158.143; LOOSE kinds may match a substring."""
    keys = {norm(key(kind, value)) for kind, value in other}
    out: dict[str, list[str]] = {}
    for kind, value in found:
        k = norm(key(kind, value))
        if k not in keys and not (kind in LOOSE and k in other_text) and key(kind, value) not in out.get(kind, []):
            out.setdefault(kind, []).append(key(kind, value))
    return out


def clip(text: str, width: int = 60) -> str:
    text = re.sub(r"\s+", " ", text.strip())
    return text if len(text) <= width else text[:width] + "…"


def compare(old: Report, new: Report) -> tuple[list[str], list[str], list[str]]:
    fails, warns, infos = [], [], []

    def same(label: str, a: object, b: object) -> None:
        if a != b:
            fails.append(f"structure changed: {label}")

    same("frontmatter (version is not bumped for wording changes)", old.frontmatter(), new.frontmatter())
    same("HTML comments", old.comments, new.comments)
    same("## headings", old.headings(2), new.headings(2))
    same("### headings", old.headings(3), new.headings(3))
    same("directive block sequence", [h for _, h, _ in old.blocks], [h for _, h, _ in new.blocks])
    for name in FIXED_BLOCKS:
        same(f"::: {name} block", old.block(name), new.block(name))
    same("first recommendation name/reason", old.first_recommendation(), new.first_recommendation())
    same("field names inside blocks", old.block_fields(), new.block_fields())
    same("field names outside blocks", old.loose_fields(), new.loose_fields())
    same("response action statuses", old.phase_status(), new.phase_status())
    old_images, new_images = old.images(), new.images()
    same("image paths, order or size", [i[:2] for i in old_images], [i[:2] for i in new_images])
    if [i[2] for i in old_images] != [i[2] for i in new_images] and len(old_images) == len(new_images):
        changed = sum(a[2] != b[2] for a, b in zip(old_images, new_images))
        infos.append(f"{changed} image captions changed")
    if LAYOUT.findall(old.visible) != LAYOUT.findall(new.visible):
        warns.append("{break}/{gap} layout markers changed")
    if old.headings(4) != new.headings(4):
        infos.append(f"#### headings: {len(old.headings(4))} -> {len(new.headings(4))}")
    old_evidence, new_evidence = old.evidence_by_section(), new.evidence_by_section()
    if len(old_evidence) == len(new_evidence):  # #### may be renamed: pair sections by position
        pairs = [(heading, before, after) for (heading, before), (_, after) in zip(old_evidence, new_evidence)]
    else:
        lookup = dict(new_evidence)
        pairs = [(heading, before, lookup.get(heading)) for heading, before in old_evidence]
    for heading, before, after in pairs:
        if before and after == 0:
            warns.append(f"section kept no concrete evidence: {heading}")

    old_values, new_values = old.values(), new.values()
    iocs = {re.sub(r":\d+$", "", v) for kind, v in old_values if "[.]" in v or v.startswith("hxxp")}
    for ioc in sorted(iocs):
        if ioc not in new.prose:
            fails.append(f"attacker IoC removed: {ioc}")
        raw = norm(ioc)
        if raw in new.prose and raw not in old.prose:
            fails.append(f"attacker IoC shown without defanging: {raw}")
    for value in sorted({v for kind, v in old_values if kind == "hash"}):
        if value not in new.prose:
            fails.append(f"hash removed: {value}")

    old_values += old.names()
    new_values += new.names()
    for kind, found in sorted(missing(new_values, old_values, norm(old.prose)).items()):
        line = f"{kind} not in original: {', '.join(found[:SHOW])}"
        (fails if kind in NEW_VALUE_FAILS else warns).append(line)
    for kind, found in sorted(missing(old_values, new_values, norm(new.prose)).items()):
        more = f" … +{len(found) - 40}" if len(found) > 40 else ""
        infos.append(f"removed {kind} ({len(found)}): {', '.join(found[:40])}{more}")
    return fails, warns, infos


def check_summary(text: str) -> list[str]:
    match = re.search(r"跟踪表[^\n]*?(\d+) 字以内", SKILL.read_text(encoding="utf-8")) if SKILL.exists() else None
    cap = int(match.group(1)) if match else None
    print(f"  summary: {han(text)} Han chars, cap {cap or 'unknown (SKILL.md not found)'}")
    fails = []
    if cap and han(text) > cap:
        fails.append(f"summary has {han(text)} Han chars, cap {cap}")
    if "\n" in text.strip() or len([s for s in re.split(r"[。！？]", text) if s.strip()]) > 1:
        fails.append("summary is more than one sentence")
    concrete = [v for kind, v in values(text) if kind not in ("number", "count")]
    if concrete:
        fails.append(f"summary carries IPs, paths, dates or times: {', '.join(concrete)}")
    return fails


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("reports", nargs="*", metavar="REPORT", help="ORIGINAL [REVISED]")
    parser.add_argument("--summary", help="one-line event summary for the IR tracking table")
    args = parser.parse_args()
    if len(args.reports) > 2 or not (args.reports or args.summary):
        parser.error("give ORIGINAL [REVISED], --summary TEXT, or both")
    fails, warns, infos = [], [], []
    reports = [Report(path) for path in args.reports]
    if reports:
        print("== Metrics ==" + (" (before -> after)" if len(reports) == 2 else ""))
        rows = [report.metrics() for report in reports]
        for name in rows[0]:
            print(f"  {name}: {' -> '.join(str(row.get(name)) for row in rows)}")
        print(f"== Leads in {reports[-1].path} ==")
        for lead in reports[-1].leads() or ["none"]:
            print(f"  {lead}")
    if len(reports) == 2:
        fails, warns, infos = compare(*reports)
    print("== Checks ==")
    if args.summary is not None:
        fails += check_summary(args.summary)
    for label, items in (("FAIL", fails), ("WARN", warns), ("INFO", infos)):
        for item in items:
            print(f"  {label} {item}")
    print(f"result: {len(fails)} FAIL, {len(warns)} WARN")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
