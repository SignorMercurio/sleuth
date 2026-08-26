"""Deterministic simulation of read-only shell commands over scenario host state.

The simulator is intentionally partial: it covers the command families SLEUTH
actually uses for remote forensics and returns exit code 127 with a
`mock-siren: unsupported command` message for everything else. Scenario
validation relies on that signal -- a scenario may only claim evidence that the
simulator can really produce, so an unsupported probe fails the test suite
instead of silently returning an empty result.

Paths must be absolute. `cd` is deliberately unsupported so scenarios cannot
depend on an implicit working directory.
"""

from __future__ import annotations

import fnmatch
import re
import shlex
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Iterable

UNSUPPORTED_EXIT = 127

_MONTHS = (
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
)


@dataclass
class CommandResult:
    """Result of one simulated command line."""

    stdout: str
    stderr: str
    exit_code: int

    @property
    def supported(self) -> bool:
        return self.exit_code != UNSUPPORTED_EXIT

    @property
    def combined(self) -> str:
        parts = [part for part in (self.stdout, self.stderr) if part]
        return "\n".join(parts)


class ScenarioDataError(ValueError):
    """Raised when host state in a scenario file cannot be interpreted."""


def _parse_time(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:  # pragma: no cover - guarded by scenario validation
        raise ScenarioDataError(f"invalid timestamp {value!r}") from exc


def _short_time(moment: datetime, reference: datetime | None = None) -> str:
    """`ls`-style stamp: clock time for the current year, the year otherwise."""
    stamp = f"{_MONTHS[moment.month - 1]} {moment.day:>2}"
    if reference is not None and moment.year != reference.year:
        return f"{stamp}  {moment.year}"
    return f"{stamp} {moment:%H:%M}"


def _full_time(moment: datetime) -> str:
    offset = moment.strftime("%z") or "+0000"
    return f"{moment:%Y-%m-%d %H:%M:%S}.000000000 {offset}"


def _human_size(size: int) -> str:
    value = float(size)
    for unit in ("", "K", "M", "G", "T"):
        if value < 1024 or unit == "T":
            if unit == "":
                return str(int(value))
            return f"{value:.1f}{unit}"
        value /= 1024
    return str(size)


def split_top_level(text: str, separators: Iterable[str]) -> list[str]:
    """Split on separators that are not inside single or double quotes."""
    ordered = sorted(separators, key=len, reverse=True)
    parts: list[str] = []
    buffer: list[str] = []
    quote = ""
    index = 0
    while index < len(text):
        char = text[index]
        if quote:
            buffer.append(char)
            if char == quote:
                quote = ""
            index += 1
            continue
        if char in "'\"":
            quote = char
            buffer.append(char)
            index += 1
            continue
        matched = next((sep for sep in ordered if text.startswith(sep, index)), None)
        if matched:
            parts.append("".join(buffer))
            buffer = []
            index += len(matched)
            continue
        buffer.append(char)
        index += 1
    parts.append("".join(buffer))
    return [part.strip() for part in parts]


_REDIRECT_NOISE = re.compile(r"\s*2>\s*/dev/null|\s*2>&1|\s*>\s*/dev/null")


class FileNode:
    """One file, directory, or symlink declared by a scenario."""

    def __init__(self, raw: dict, default_time: str):
        self.path: str = raw["path"].rstrip("/") or "/"
        self.kind: str = raw.get("kind", "file")
        self.user: str = raw.get("user", "root")
        self.group: str = raw.get("group", raw.get("user", "root"))
        self.uid: int = int(raw.get("uid", 0))
        self.gid: int = int(raw.get("gid", 0))
        self.nlink: int = int(raw.get("nlink", 2 if self.kind == "dir" else 1))
        self.lines: list[str] = list(raw.get("lines", []))
        self.symlink_target: str = raw.get("symlink_target", "")
        self.md5: str = raw.get("md5", "")
        self.sha256: str = raw.get("sha256", "")
        self.file_type: str = raw.get("file_type", "")
        self.strings: list[str] = list(raw.get("strings", []))
        self.inode: int = int(raw.get("inode", abs(hash(self.path)) % 9000000 + 1000000))
        default_mode = {
            "dir": "drwxr-xr-x",
            "link": "lrwxrwxrwx",
        }.get(self.kind, "-rw-r--r--")
        self.mode: str = raw.get("mode", default_mode)
        body = "\n".join(self.lines)
        self.size: int = int(raw.get("size", len(body.encode("utf-8")) + (1 if body else 0)))
        self.mtime = _parse_time(raw.get("mtime", default_time))
        self.ctime = _parse_time(raw.get("ctime", raw.get("mtime", default_time)))
        self.atime = _parse_time(raw.get("atime", raw.get("mtime", default_time)))

    @property
    def name(self) -> str:
        return self.path.rsplit("/", 1)[-1] or "/"

    @property
    def parent(self) -> str:
        if self.path == "/":
            return ""
        head = self.path.rsplit("/", 1)[0]
        return head or "/"

    @property
    def octal_mode(self) -> str:
        bits = self.mode[1:]
        digits = []
        for chunk in (bits[0:3], bits[3:6], bits[6:9]):
            value = 0
            value += 4 if chunk[0:1] == "r" else 0
            value += 2 if chunk[1:2] == "w" else 0
            value += 1 if chunk[2:3] in ("x", "s", "t") else 0
            digits.append(str(value))
        return "0" + "".join(digits)

    def display_name(self, with_target: bool = True) -> str:
        if self.kind == "link" and with_target and self.symlink_target:
            return f"{self.name} -> {self.symlink_target}"
        return self.name

    def type_word(self) -> str:
        return {"dir": "directory", "link": "symbolic link"}.get(self.kind, "regular file")


class HostSimulator:
    """Simulates read-only commands against one scenario host."""

    def __init__(self, host: dict):
        self.host = host
        self.now_raw: str = host.get("now", "2026-01-01T00:00:00+08:00")
        self.now = _parse_time(self.now_raw)
        self.nodes: dict[str, FileNode] = {}
        for raw in host.get("files", []):
            node = FileNode(raw, self.now_raw)
            self.nodes[node.path] = node
        self._synthesize_parents()
        self.overrides = [
            (re.compile(entry["match"]), entry)
            for entry in host.get("command_overrides", [])
        ]

    # -- filesystem helpers -------------------------------------------------

    def _synthesize_parents(self) -> None:
        for path in list(self.nodes):
            parent = self.nodes[path].parent
            while parent and parent not in self.nodes:
                self.nodes[parent] = FileNode(
                    {"path": parent, "kind": "dir"}, self.now_raw
                )
                parent = self.nodes[parent].parent

    def node(self, path: str) -> FileNode | None:
        return self.nodes.get(path.rstrip("/") or "/")

    def children(self, path: str) -> list[FileNode]:
        target = path.rstrip("/") or "/"
        return [node for node in self.nodes.values() if node.parent == target]

    def descendants(self, path: str) -> list[FileNode]:
        target = path.rstrip("/") or "/"
        prefix = target if target.endswith("/") else target + "/"
        return [
            node
            for node in self.nodes.values()
            if node.path == target or node.path.startswith(prefix)
        ]

    # -- entry point --------------------------------------------------------

    def execute(self, command: str) -> CommandResult:
        command = command.strip()
        if not command:
            return CommandResult("", "", 0)
        for pattern, entry in self.overrides:
            if pattern.search(command):
                return CommandResult(
                    "\n".join(entry.get("stdout", [])),
                    "\n".join(entry.get("stderr", [])),
                    int(entry.get("exit_code", 0)),
                )
        return self._run_sequence(command)

    def _run_sequence(self, command: str) -> CommandResult:
        statements = split_top_level(command, [";", "&&"])
        outs: list[str] = []
        errs: list[str] = []
        exit_code = 0
        for statement in statements:
            if not statement:
                continue
            result = self._run_pipeline(statement)
            if result.stdout:
                outs.append(result.stdout)
            if result.stderr:
                errs.append(result.stderr)
            exit_code = result.exit_code
            if exit_code == UNSUPPORTED_EXIT:
                break
        return CommandResult("\n".join(outs), "\n".join(errs), exit_code)

    def _run_pipeline(self, statement: str) -> CommandResult:
        stages = [stage for stage in split_top_level(statement, ["|"]) if stage]
        if not stages:
            return CommandResult("", "", 0)
        head, *rest = stages
        result = self._run_producer(head)
        if result.exit_code == UNSUPPORTED_EXIT:
            return result
        lines = result.stdout.splitlines()
        stderr = result.stderr
        exit_code = result.exit_code
        for stage in rest:
            filtered = self._run_filter(stage, lines)
            if filtered.exit_code == UNSUPPORTED_EXIT:
                return filtered
            lines = filtered.stdout.splitlines()
            if filtered.stderr:
                stderr = "\n".join(part for part in (stderr, filtered.stderr) if part)
            exit_code = filtered.exit_code
        return CommandResult("\n".join(lines), stderr, exit_code)

    # -- producers ----------------------------------------------------------

    def _tokens(self, stage: str) -> list[str]:
        cleaned = _REDIRECT_NOISE.sub("", stage).strip()
        try:
            return shlex.split(cleaned)
        except ValueError:
            return cleaned.split()

    def _run_producer(self, stage: str) -> CommandResult:
        tokens = self._tokens(stage)
        if not tokens:
            return CommandResult("", "", 0)
        if tokens[0] == "sudo":
            tokens = tokens[1:]
        if not tokens:
            return CommandResult("", "", 0)
        handler: Callable[[list[str]], CommandResult] | None = PRODUCERS.get(tokens[0])
        if handler is None:
            return self._unsupported(tokens[0])
        return handler(self, tokens[1:])

    def _run_filter(self, stage: str, lines: list[str]) -> CommandResult:
        tokens = self._tokens(stage)
        if not tokens:
            return CommandResult("\n".join(lines), "", 0)
        handler = FILTERS.get(tokens[0])
        if handler is None:
            return self._unsupported(tokens[0])
        return handler(self, tokens[1:], lines)

    @staticmethod
    def _unsupported(binary: str) -> CommandResult:
        return CommandResult(
            "", f"mock-siren: unsupported command: {binary}", UNSUPPORTED_EXIT
        )

    @staticmethod
    def _ok(lines: Iterable[str]) -> CommandResult:
        return CommandResult("\n".join(lines), "", 0)

    # -- individual commands ------------------------------------------------

    def cmd_hostname(self, args: list[str]) -> CommandResult:
        return self._ok([self.host.get("hostname", "localhost")])

    def cmd_uname(self, args: list[str]) -> CommandResult:
        if "-r" in args:
            return self._ok([self.host.get("kernel", "3.10.0-1160.el7.x86_64")])
        return self._ok([self.host.get("uname", "Linux localhost")])

    def cmd_date(self, args: list[str]) -> CommandResult:
        if args and args[0] == "+%Z":
            return self._ok([self.host.get("timezone_name", "CST")])
        zone = self.host.get("timezone_name", "CST")
        return self._ok([f"{self.now:%a %b %d %H:%M:%S} {zone} {self.now:%Y}"])

    def cmd_uptime(self, args: list[str]) -> CommandResult:
        value = self.host.get("uptime")
        if not value:
            return self._unsupported("uptime")
        return self._ok([value])

    def cmd_id(self, args: list[str]) -> CommandResult:
        return self._ok([self.host.get("id", "uid=0(root) gid=0(root) groups=0(root)")])

    def cmd_whoami(self, args: list[str]) -> CommandResult:
        return self._ok([self.host.get("whoami", "root")])

    def cmd_timedatectl(self, args: list[str]) -> CommandResult:
        offset = self.now.strftime("%z") or "+0000"
        return self._ok(
            [
                f"      Local time: {self.now:%a %Y-%m-%d %H:%M:%S} "
                f"{self.host.get('timezone_name', 'CST')}",
                f"       Time zone: {self.host.get('timezone', 'Asia/Shanghai')} "
                f"({self.host.get('timezone_name', 'CST')}, {offset})",
            ]
        )

    def cmd_cat(self, args: list[str]) -> CommandResult:
        paths = [arg for arg in args if not arg.startswith("-")]
        if not paths:
            return self._unsupported("cat")
        out: list[str] = []
        errs: list[str] = []
        code = 0
        for path in paths:
            node = self.node(path)
            if node is None:
                errs.append(f"cat: {path}: No such file or directory")
                code = 1
                continue
            if node.kind == "dir":
                errs.append(f"cat: {path}: Is a directory")
                code = 1
                continue
            out.extend(node.lines)
        return CommandResult("\n".join(out), "\n".join(errs), code)

    def cmd_head(self, args: list[str]) -> CommandResult:
        count, paths = _count_and_paths(args, default=10)
        return self._head_tail(paths, count, head=True)

    def cmd_tail(self, args: list[str]) -> CommandResult:
        count, paths = _count_and_paths(args, default=10)
        return self._head_tail(paths, count, head=False)

    def _head_tail(self, paths: list[str], count: int, head: bool) -> CommandResult:
        if not paths:
            return self._unsupported("head" if head else "tail")
        out: list[str] = []
        errs: list[str] = []
        code = 0
        for path in paths:
            node = self.node(path)
            if node is None or node.kind == "dir":
                binary = "head" if head else "tail"
                errs.append(
                    f"{binary}: cannot open '{path}' for reading: No such file or directory"
                )
                code = 1
                continue
            lines = node.lines[:count] if head else node.lines[-count:] if count else []
            if len(paths) > 1:
                out.append(f"==> {path} <==")
            out.extend(lines)
        return CommandResult("\n".join(out), "\n".join(errs), code)

    def cmd_wc(self, args: list[str]) -> CommandResult:
        paths = [arg for arg in args if not arg.startswith("-")]
        if not paths:
            return self._unsupported("wc")
        out: list[str] = []
        errs: list[str] = []
        code = 0
        total = 0
        for path in paths:
            node = self.node(path)
            if node is None or node.kind == "dir":
                errs.append(f"wc: {path}: No such file or directory")
                code = 1
                continue
            count = len(node.lines)
            total += count
            out.append(f"{count:>8} {path}")
        if len([p for p in paths if self.node(p)]) > 1:
            out.append(f"{total:>8} total")
        return CommandResult("\n".join(out), "\n".join(errs), code)

    def cmd_ls(self, args: list[str]) -> CommandResult:
        flags = {arg for arg in args if arg.startswith("-")}
        flag_chars = "".join(flag.lstrip("-") for flag in flags if not flag.startswith("--"))
        long_form = "l" in flag_chars
        show_all = "a" in flag_chars
        by_time = "t" in flag_chars
        reverse = "r" in flag_chars
        human = "h" in flag_chars
        full_time = "--full-time" in flags
        paths = [arg for arg in args if not arg.startswith("-")] or ["/"]
        out: list[str] = []
        errs: list[str] = []
        code = 0
        for path in paths:
            node = self.node(path)
            if node is None:
                errs.append(f"ls: cannot access '{path}': No such file or directory")
                code = 2
                continue
            entries = self.children(node.path) if node.kind == "dir" else [node]
            if not show_all:
                entries = [entry for entry in entries if not entry.name.startswith(".")]
            entries.sort(key=lambda item: (-item.mtime.timestamp(),) if by_time else (item.name,))
            if reverse:
                entries.reverse()
            if len(paths) > 1:
                out.append(f"{path}:")
            if long_form and node.kind == "dir":
                out.append(f"total {sum(max(entry.size // 1024, 1) for entry in entries)}")
            for entry in entries:
                if not long_form:
                    out.append(entry.display_name(with_target=False))
                    continue
                stamp = (
                    _full_time(entry.mtime)
                    if full_time
                    else _short_time(entry.mtime, self.now)
                )
                size = _human_size(entry.size) if human else str(entry.size)
                out.append(
                    f"{entry.mode} {entry.nlink:>2} {entry.user:<8} {entry.group:<8} "
                    f"{size:>8} {stamp} {entry.display_name()}"
                )
        return CommandResult("\n".join(out), "\n".join(errs), code)

    def cmd_stat(self, args: list[str]) -> CommandResult:
        paths = [arg for arg in args if not arg.startswith("-")]
        if not paths:
            return self._unsupported("stat")
        out: list[str] = []
        errs: list[str] = []
        code = 0
        for path in paths:
            node = self.node(path)
            if node is None:
                errs.append(f"stat: cannot stat '{path}': No such file or directory")
                code = 1
                continue
            out.extend(
                [
                    f"  File: {node.path}",
                    f"  Size: {node.size:<15} Blocks: {max(node.size // 512, 1):<10} "
                    f"IO Block: 4096   {node.type_word()}",
                    f"Device: fd00h/64768d    Inode: {node.inode:<11} Links: {node.nlink}",
                    f"Access: ({node.octal_mode}/{node.mode})  Uid: ({node.uid:>5}/{node.user:>8})   "
                    f"Gid: ({node.gid:>5}/{node.group:>8})",
                    f"Access: {_full_time(node.atime)}",
                    f"Modify: {_full_time(node.mtime)}",
                    f"Change: {_full_time(node.ctime)}",
                    " Birth: -",
                ]
            )
        return CommandResult("\n".join(out), "\n".join(errs), code)

    def cmd_md5sum(self, args: list[str]) -> CommandResult:
        return self._digest(args, "md5", "md5sum")

    def cmd_sha256sum(self, args: list[str]) -> CommandResult:
        return self._digest(args, "sha256", "sha256sum")

    def _digest(self, args: list[str], field: str, binary: str) -> CommandResult:
        paths = [arg for arg in args if not arg.startswith("-")]
        if not paths:
            return self._unsupported(binary)
        out: list[str] = []
        errs: list[str] = []
        code = 0
        for path in paths:
            node = self.node(path)
            if node is None:
                errs.append(f"{binary}: {path}: No such file or directory")
                code = 1
                continue
            digest = getattr(node, field)
            if not digest:
                errs.append(f"{binary}: {path}: digest not declared in scenario")
                code = 1
                continue
            out.append(f"{digest}  {path}")
        return CommandResult("\n".join(out), "\n".join(errs), code)

    def cmd_file(self, args: list[str]) -> CommandResult:
        paths = [arg for arg in args if not arg.startswith("-")]
        out: list[str] = []
        errs: list[str] = []
        code = 0
        for path in paths:
            node = self.node(path)
            if node is None:
                errs.append(f"{path}: cannot open (No such file or directory)")
                code = 1
                continue
            described = node.file_type or {
                "dir": "directory",
                "link": f"symbolic link to {node.symlink_target}",
            }.get(node.kind, "ASCII text")
            out.append(f"{path}: {described}")
        return CommandResult("\n".join(out), "\n".join(errs), code)

    def cmd_readlink(self, args: list[str]) -> CommandResult:
        paths = [arg for arg in args if not arg.startswith("-")]
        out: list[str] = []
        code = 0
        for path in paths:
            node = self.node(path)
            if node is None or node.kind != "link":
                code = 1
                continue
            out.append(node.symlink_target)
        return CommandResult("\n".join(out), "", code)

    def cmd_strings(self, args: list[str]) -> CommandResult:
        paths = [arg for arg in args if not arg.startswith("-")]
        out: list[str] = []
        errs: list[str] = []
        code = 0
        for path in paths:
            node = self.node(path)
            if node is None:
                errs.append(f"strings: '{path}': No such file")
                code = 1
                continue
            out.extend(node.strings or node.lines)
        return CommandResult("\n".join(out), "\n".join(errs), code)

    def cmd_find(self, args: list[str]) -> CommandResult:
        roots: list[str] = []
        index = 0
        while index < len(args) and not args[index].startswith("-"):
            roots.append(args[index])
            index += 1
        if not roots:
            roots = ["/"]
        name_pat = ""
        want_type = ""
        newer_than: datetime | None = None
        older_mtime_days: float | None = None
        newer_mmin: float | None = None
        maxdepth: int | None = None
        user = ""
        while index < len(args):
            token = args[index]
            value = args[index + 1] if index + 1 < len(args) else ""
            if token == "-name":
                name_pat = value
                index += 2
            elif token == "-type":
                want_type = value
                index += 2
            elif token == "-newermt":
                newer_than = _parse_loose_time(value, self.now)
                index += 2
            elif token == "-mtime":
                older_mtime_days = float(value.lstrip("-+"))
                index += 2
            elif token == "-mmin":
                newer_mmin = float(value.lstrip("-+"))
                index += 2
            elif token == "-maxdepth":
                maxdepth = int(value)
                index += 2
            elif token == "-user":
                user = value
                index += 2
            elif token in ("-print", "-print0"):
                index += 1
            else:
                return self._unsupported(f"find {token}")
        matches: list[FileNode] = []
        for root in roots:
            base = self.node(root)
            if base is None:
                continue
            for node in self.descendants(root):
                if maxdepth is not None:
                    depth = node.path.count("/") - root.rstrip("/").count("/")
                    if depth > maxdepth:
                        continue
                if want_type == "f" and node.kind != "file":
                    continue
                if want_type == "d" and node.kind != "dir":
                    continue
                if name_pat and not fnmatch.fnmatch(node.name, name_pat):
                    continue
                if user and node.user != user:
                    continue
                if newer_than and node.mtime <= newer_than:
                    continue
                if newer_mmin is not None:
                    age_min = (self.now - node.mtime).total_seconds() / 60
                    if age_min > newer_mmin:
                        continue
                if older_mtime_days is not None:
                    age_days = (self.now - node.mtime).total_seconds() / 86400
                    if age_days > older_mtime_days:
                        continue
                matches.append(node)
        matches.sort(key=lambda item: item.path)
        return self._ok(node.path for node in matches)

    def cmd_ps(self, args: list[str]) -> CommandResult:
        processes = self.host.get("processes", [])
        joined = "".join(args)
        if "ef" in joined:
            out = ["UID          PID    PPID  C STIME TTY          TIME CMD"]
            for proc in processes:
                out.append(
                    f"{proc.get('user', 'root'):<10} {proc.get('pid', 0):>7} "
                    f"{proc.get('ppid', 0):>7}  0 {proc.get('start', '00:00')} "
                    f"{proc.get('tty', '?'):<12} {proc.get('time', '00:00:00')} {proc.get('cmd', '')}"
                )
            return self._ok(out)
        out = ["USER        PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND"]
        for proc in processes:
            out.append(
                f"{proc.get('user', 'root'):<10} {proc.get('pid', 0):>5} "
                f"{proc.get('cpu', 0.0):>4} {proc.get('mem', 0.0):>4} "
                f"{proc.get('vsz', 0):>6} {proc.get('rss', 0):>5} "
                f"{proc.get('tty', '?'):<8} {proc.get('stat', 'S'):<4} "
                f"{proc.get('start', '00:00'):<7} {proc.get('time', '0:00')} {proc.get('cmd', '')}"
            )
        return self._ok(out)

    def cmd_pstree(self, args: list[str]) -> CommandResult:
        processes = self.host.get("processes", [])
        by_parent: dict[int, list[dict]] = {}
        for proc in processes:
            by_parent.setdefault(int(proc.get("ppid", 0)), []).append(proc)
        known = {int(proc.get("pid", 0)) for proc in processes}
        out: list[str] = []

        def walk(pid: int, depth: int) -> None:
            for child in by_parent.get(pid, []):
                out.append(
                    f"{'  ' * depth}{child.get('cmd', '').split()[0]}({child.get('pid')})"
                )
                walk(int(child.get("pid", 0)), depth + 1)

        for root_pid in sorted(set(by_parent) - known):
            walk(root_pid, 0)
        return self._ok(out)

    def cmd_netstat(self, args: list[str]) -> CommandResult:
        joined = "".join(args)
        want_listen = "l" in joined
        rows = self.host.get("connections", [])
        out = [
            "Active Internet connections (servers and established)",
            "Proto Recv-Q Send-Q Local Address           Foreign Address"
            "         State       PID/Program name",
        ]
        for row in rows:
            state = row.get("state", "ESTABLISHED")
            if want_listen and state != "LISTEN":
                continue
            program = row.get("program", "-")
            pid = row.get("pid")
            owner = f"{pid}/{program}" if pid else "-"
            out.append(
                f"{row.get('proto', 'tcp'):<5} {0:>6} {0:>6} "
                f"{row.get('local', ''):<23} {row.get('remote', ''):<23} "
                f"{state:<11} {owner}"
            )
        return self._ok(out)

    def cmd_ss(self, args: list[str]) -> CommandResult:
        joined = "".join(args)
        want_listen = "l" in joined
        rows = self.host.get("connections", [])
        out = ["State      Recv-Q Send-Q Local Address:Port    Peer Address:Port   Process"]
        for row in rows:
            state = row.get("state", "ESTAB")
            if want_listen and state != "LISTEN":
                continue
            display = "LISTEN" if state == "LISTEN" else "ESTAB"
            process = ""
            if row.get("pid"):
                process = f'users:(("{row.get("program", "?")}",pid={row["pid"]},fd=3))'
            out.append(
                f"{display:<10} {0:>6} {0:>6} {row.get('local', ''):<21} "
                f"{row.get('remote', ''):<19} {process}"
            )
        return self._ok(out)

    def cmd_lsof(self, args: list[str]) -> CommandResult:
        rows = self.host.get("open_files", [])
        if not rows:
            return self._unsupported("lsof")
        out = ["COMMAND     PID     USER   FD   TYPE DEVICE SIZE/OFF     NODE NAME"]
        for row in rows:
            out.append(
                f"{row.get('command', ''):<11} {row.get('pid', 0):>4} {row.get('user', 'root'):>8} "
                f"{row.get('fd', 'cwd'):>4} {row.get('type', 'REG'):>6} "
                f"{'253,0':>6} {row.get('size', 0):>8} {row.get('node', 0):>8} {row.get('name', '')}"
            )
        return self._ok(out)

    def cmd_last(self, args: list[str]) -> CommandResult:
        return self._login_table(self.host.get("logins", []), args)

    def cmd_lastb(self, args: list[str]) -> CommandResult:
        return self._login_table(self.host.get("failed_logins", []), args)

    def _login_table(self, rows: list[dict], args: list[str]) -> CommandResult:
        limit = None
        for index, token in enumerate(args):
            if token == "-n" and index + 1 < len(args):
                limit = int(args[index + 1])
            elif re.fullmatch(r"-\d+", token):
                limit = int(token.lstrip("-"))
        if not rows:
            return self._ok(["", "wtmp begins " + self.host.get("wtmp_begins", "-")])
        selected = rows[:limit] if limit else rows
        out = []
        for row in selected:
            out.append(
                f"{row.get('user', ''):<9}{row.get('tty', ''):<12}{row.get('from', ''):<17}"
                f"{row.get('start', '')} - {row.get('end', 'still logged in'):<9} "
                f"({row.get('duration', '')})"
            )
        out.append("")
        out.append("wtmp begins " + self.host.get("wtmp_begins", "-"))
        return self._ok(out)

    def cmd_who(self, args: list[str]) -> CommandResult:
        rows = self.host.get("sessions", [])
        return self._ok(
            f"{row.get('user', ''):<9}{row.get('tty', ''):<10}{row.get('since', '')} "
            f"({row.get('from', '')})"
            for row in rows
        )

    def cmd_crontab(self, args: list[str]) -> CommandResult:
        if "-l" not in args:
            return CommandResult("", "mock-siren: only `crontab -l` is simulated", 1)
        user = "root"
        if "-u" in args:
            user = args[args.index("-u") + 1]
        crontabs = self.host.get("crontabs", {})
        if user not in crontabs:
            return CommandResult("", f"no crontab for {user}", 1)
        return self._ok(crontabs[user])

    def cmd_systemctl(self, args: list[str]) -> CommandResult:
        if not args:
            return self._unsupported("systemctl")
        action = args[0]
        units = self.host.get("systemd_units", [])
        if action in ("list-units", "list-unit-files"):
            out = ["UNIT                          LOAD   ACTIVE SUB     DESCRIPTION"]
            for unit in units:
                out.append(
                    f"{unit.get('name', ''):<30}{unit.get('load', 'loaded'):<7}"
                    f"{unit.get('active', 'active'):<7}{unit.get('sub', 'running'):<8}"
                    f"{unit.get('description', '')}"
                )
            return self._ok(out)
        if action in ("status", "cat", "show", "is-enabled"):
            name = args[1] if len(args) > 1 else ""
            unit = next((item for item in units if item.get("name", "").startswith(name)), None)
            if unit is None:
                return CommandResult("", f"Unit {name} could not be found.", 4)
            if action == "cat":
                return self._ok(unit.get("content", []))
            if action == "is-enabled":
                return self._ok([unit.get("enabled", "enabled")])
            return self._ok(
                [
                    f"* {unit.get('name', '')} - {unit.get('description', '')}",
                    f"   Loaded: {unit.get('load', 'loaded')} ({unit.get('path', '')}; "
                    f"{unit.get('enabled', 'enabled')})",
                    f"   Active: {unit.get('active', 'active')} ({unit.get('sub', 'running')}) "
                    f"since {unit.get('since', '')}",
                    f" Main PID: {unit.get('main_pid', 0)} ({unit.get('exec', '')})",
                ]
            )
        return self._unsupported(f"systemctl {action}")

    def cmd_journalctl(self, args: list[str]) -> CommandResult:
        entries = self.host.get("journal", [])
        unit = ""
        since: datetime | None = None
        until: datetime | None = None
        limit: int | None = None
        index = 0
        while index < len(args):
            token = args[index]
            value = args[index + 1] if index + 1 < len(args) else ""
            if token in ("-u", "--unit"):
                unit = value
                index += 2
            elif token == "--since":
                since = _parse_loose_time(value, self.now)
                index += 2
            elif token == "--until":
                until = _parse_loose_time(value, self.now)
                index += 2
            elif token in ("-n", "--lines"):
                limit = int(value)
                index += 2
            elif token in ("--no-pager", "-r", "-x", "-e"):
                index += 1
            else:
                index += 1
        selected = []
        for entry in entries:
            stamp = _parse_time(entry["ts"])
            if unit and unit not in entry.get("unit", ""):
                continue
            if since and stamp < since:
                continue
            if until and stamp > until:
                continue
            selected.append(
                f"{_short_time(stamp)} {self.host.get('hostname', 'localhost')} "
                f"{entry.get('unit', 'kernel')}: {entry.get('message', '')}"
            )
        if not selected:
            boundary = self.host.get("journal_begins")
            note = f"-- No entries --{'' if not boundary else ' (journal begins ' + boundary + ')'}"
            return self._ok([note])
        if limit:
            selected = selected[-limit:]
        return self._ok(selected)

    def cmd_rpm(self, args: list[str]) -> CommandResult:
        if any(arg.startswith("-V") or arg == "-Va" for arg in args):
            return self._ok(self.host.get("package_verify", []))
        if any(arg.startswith("-q") for arg in args):
            return self._ok(self.host.get("package_query", []))
        return self._unsupported("rpm")

    def cmd_dpkg(self, args: list[str]) -> CommandResult:
        if "-V" in args or "--verify" in args:
            return self._ok(self.host.get("package_verify", []))
        if "-l" in args:
            return self._ok(self.host.get("package_query", []))
        return self._unsupported("dpkg")

    def cmd_lsattr(self, args: list[str]) -> CommandResult:
        table = self.host.get("lsattr", {})
        paths = [arg for arg in args if not arg.startswith("-")]
        out = []
        for path in paths:
            out.append(f"{table.get(path, '-------------e--')} {path}")
        return self._ok(out)

    def cmd_getenforce(self, args: list[str]) -> CommandResult:
        return self._ok([self.host.get("selinux", "Disabled")])

    def cmd_docker(self, args: list[str]) -> CommandResult:
        if not args:
            return self._unsupported("docker")
        if args[0] == "ps":
            rows = self.host.get("containers", [])
            out = ["CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES"]
            for row in rows:
                out.append(
                    f"{row.get('id', ''):<14} {row.get('image', ''):<9} "
                    f"{row.get('command', ''):<9} {row.get('created', ''):<9} "
                    f"{row.get('status', ''):<9} {row.get('ports', ''):<9} {row.get('name', '')}"
                )
            return self._ok(out)
        if args[0] == "logs":
            logs = self.host.get("container_logs", {})
            name = args[-1]
            if name not in logs:
                return CommandResult("", f"Error: No such container: {name}", 1)
            return self._ok(logs[name])
        return self._unsupported(f"docker {args[0]}")

    def cmd_grep(self, args: list[str]) -> CommandResult:
        opts, pattern, paths = _grep_args(args)
        if pattern is None:
            return self._unsupported("grep")
        if not paths:
            return self._unsupported("grep")
        lines: list[str] = []
        errs: list[str] = []
        code = 1
        multi = len(paths) > 1 or "r" in opts
        targets: list[FileNode] = []
        for path in paths:
            node = self.node(path)
            if node is None:
                errs.append(f"grep: {path}: No such file or directory")
                continue
            if node.kind == "dir":
                if "r" not in opts:
                    errs.append(f"grep: {path}: Is a directory")
                    continue
                targets.extend(item for item in self.descendants(path) if item.kind == "file")
                multi = True
                continue
            targets.append(node)
        for node in targets:
            matched = _grep_lines(node.lines, pattern, opts)
            if matched:
                code = 0
            for number, line in matched:
                prefix = f"{node.path}:" if multi else ""
                if "n" in opts:
                    prefix += f"{number}:"
                lines.append(prefix + line)
        if "c" in opts:
            return CommandResult(str(len(lines)), "\n".join(errs), code)
        return CommandResult("\n".join(lines), "\n".join(errs), code)

    def cmd_awk(self, args: list[str]) -> CommandResult:
        program = next((arg for arg in args if "{" in arg), "")
        paths = [arg for arg in args if "{" not in arg and not arg.startswith("-")]
        if not program or not paths:
            return self._unsupported("awk")
        lines: list[str] = []
        for path in paths:
            node = self.node(path)
            if node is None:
                continue
            lines.extend(node.lines)
        return _awk_apply(program, lines)


def _count_and_paths(args: list[str], default: int) -> tuple[int, list[str]]:
    count = default
    paths: list[str] = []
    index = 0
    while index < len(args):
        token = args[index]
        if token in ("-n", "-c"):
            count = int(args[index + 1].lstrip("+-")) if index + 1 < len(args) else default
            index += 2
            continue
        if re.fullmatch(r"-\d+", token):
            count = int(token.lstrip("-"))
            index += 1
            continue
        if token.startswith("-"):
            index += 1
            continue
        paths.append(token)
        index += 1
    return count, paths


def _grep_args(args: list[str]) -> tuple[set[str], str | None, list[str]]:
    opts: set[str] = set()
    pattern: str | None = None
    paths: list[str] = []
    for token in args:
        if token.startswith("-") and len(token) > 1 and not token.startswith("--"):
            opts.update(token[1:])
            continue
        if token in ("--color", "--color=auto", "--text"):
            continue
        if pattern is None:
            pattern = token
            continue
        paths.append(token)
    if "E" in opts or "e" in opts:
        opts.add("E")
    return opts, pattern, paths


def _grep_lines(lines: list[str], pattern: str, opts: set[str]) -> list[tuple[int, str]]:
    flags = re.IGNORECASE if "i" in opts else 0
    try:
        compiled = re.compile(pattern, flags)
    except re.error:
        compiled = re.compile(re.escape(pattern), flags)
    result = []
    for number, line in enumerate(lines, start=1):
        hit = bool(compiled.search(line))
        if "v" in opts:
            hit = not hit
        if hit:
            result.append((number, line))
    return result


def _awk_apply(program: str, lines: list[str]) -> CommandResult:
    body = program.strip().strip("'").strip()
    match = re.fullmatch(r"\{\s*print\s+(.+?)\s*\}", body)
    if not match:
        return CommandResult(
            "", "mock-siren: unsupported command: awk (only `{print $N}` is simulated)",
            UNSUPPORTED_EXIT,
        )
    fields = [item.strip() for item in match.group(1).split(",")]
    out: list[str] = []
    for line in lines:
        columns = line.split()
        values: list[str] = []
        for field in fields:
            if field == "$0":
                values.append(line)
                continue
            field_match = re.fullmatch(r"\$(\d+)", field)
            if not field_match:
                return CommandResult(
                    "", "mock-siren: unsupported command: awk (only `$N` fields)",
                    UNSUPPORTED_EXIT,
                )
            position = int(field_match.group(1))
            values.append(columns[position - 1] if position <= len(columns) else "")
        out.append(" ".join(values))
    return CommandResult("\n".join(out), "", 0)


def _parse_loose_time(value: str, now: datetime) -> datetime:
    text = value.strip().strip("'\"")
    for pattern in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            parsed = datetime.strptime(text, pattern)
        except ValueError:
            continue
        return parsed.replace(tzinfo=now.tzinfo)
    try:
        return datetime.fromisoformat(text)
    except ValueError as exc:
        raise ScenarioDataError(f"unparsable time expression {value!r}") from exc


# -- pipeline filters -------------------------------------------------------


def _filter_grep(sim: HostSimulator, args: list[str], lines: list[str]) -> CommandResult:
    opts, pattern, _ = _grep_args(args)
    if pattern is None:
        return CommandResult("", "mock-siren: unsupported command: grep", UNSUPPORTED_EXIT)
    matched = _grep_lines(lines, pattern, opts)
    if "c" in opts:
        return CommandResult(str(len(matched)), "", 0 if matched else 1)
    out = [f"{number}:{line}" if "n" in opts else line for number, line in matched]
    return CommandResult("\n".join(out), "", 0 if matched else 1)


def _filter_head(sim: HostSimulator, args: list[str], lines: list[str]) -> CommandResult:
    count, _ = _count_and_paths(args, default=10)
    return CommandResult("\n".join(lines[:count]), "", 0)


def _filter_tail(sim: HostSimulator, args: list[str], lines: list[str]) -> CommandResult:
    count, _ = _count_and_paths(args, default=10)
    return CommandResult("\n".join(lines[-count:] if count else []), "", 0)


def _filter_wc(sim: HostSimulator, args: list[str], lines: list[str]) -> CommandResult:
    flags = _short_flags(args)
    if "l" in flags or not args:
        return CommandResult(str(len(lines)), "", 0)
    if "c" in flags:
        return CommandResult(str(len("\n".join(lines).encode("utf-8"))), "", 0)
    return CommandResult("", "mock-siren: unsupported command: wc", UNSUPPORTED_EXIT)


def _short_flags(args: list[str]) -> set[str]:
    """Expand clustered short flags so `-rn` counts as both `-r` and `-n`."""
    flags: set[str] = set()
    for token in args:
        if token.startswith("-") and not token.startswith("--") and len(token) > 1:
            flags.update(token[1:])
    return flags


def _filter_sort(sim: HostSimulator, args: list[str], lines: list[str]) -> CommandResult:
    values = list(lines)
    flags = _short_flags(args)

    def numeric_key(item: str) -> tuple[int, str]:
        token = item.strip().split()[0] if item.strip() else "0"
        try:
            return (int(token), item)
        except ValueError:
            return (0, item)

    if "n" in flags:
        values.sort(key=numeric_key)
    else:
        values.sort()
    if "r" in flags:
        values.reverse()
    if "u" in flags:
        seen: set[str] = set()
        unique = []
        for value in values:
            if value not in seen:
                seen.add(value)
                unique.append(value)
        values = unique
    return CommandResult("\n".join(values), "", 0)


def _filter_uniq(sim: HostSimulator, args: list[str], lines: list[str]) -> CommandResult:
    with_counts = "c" in _short_flags(args)
    out: list[str] = []
    previous: str | None = None
    count = 0
    for line in lines:
        if line == previous:
            count += 1
            continue
        if previous is not None:
            out.append(f"{count:>7} {previous}" if with_counts else previous)
        previous = line
        count = 1
    if previous is not None:
        out.append(f"{count:>7} {previous}" if with_counts else previous)
    return CommandResult("\n".join(out), "", 0)


def _filter_awk(sim: HostSimulator, args: list[str], lines: list[str]) -> CommandResult:
    program = next((arg for arg in args if "{" in arg), "")
    if not program:
        return CommandResult("", "mock-siren: unsupported command: awk", UNSUPPORTED_EXIT)
    return _awk_apply(program, lines)


def _filter_cut(sim: HostSimulator, args: list[str], lines: list[str]) -> CommandResult:
    delimiter = " "
    fields: list[int] = []
    index = 0
    while index < len(args):
        token = args[index]
        if token.startswith("-d"):
            delimiter = token[2:] or (args[index + 1] if index + 1 < len(args) else " ")
            index += 1 if token[2:] else 2
            continue
        if token.startswith("-f"):
            spec = token[2:] or (args[index + 1] if index + 1 < len(args) else "1")
            fields = [int(part) for part in spec.split(",") if part.isdigit()]
            index += 1 if token[2:] else 2
            continue
        index += 1
    if not fields:
        return CommandResult("", "mock-siren: unsupported command: cut", UNSUPPORTED_EXIT)
    out = []
    for line in lines:
        columns = line.split(delimiter)
        out.append(
            delimiter.join(columns[position - 1] for position in fields if position <= len(columns))
        )
    return CommandResult("\n".join(out), "", 0)


PRODUCERS: dict[str, Callable[[HostSimulator, list[str]], CommandResult]] = {
    "hostname": HostSimulator.cmd_hostname,
    "uname": HostSimulator.cmd_uname,
    "date": HostSimulator.cmd_date,
    "uptime": HostSimulator.cmd_uptime,
    "id": HostSimulator.cmd_id,
    "whoami": HostSimulator.cmd_whoami,
    "timedatectl": HostSimulator.cmd_timedatectl,
    "cat": HostSimulator.cmd_cat,
    "head": HostSimulator.cmd_head,
    "tail": HostSimulator.cmd_tail,
    "wc": HostSimulator.cmd_wc,
    "ls": HostSimulator.cmd_ls,
    "stat": HostSimulator.cmd_stat,
    "md5sum": HostSimulator.cmd_md5sum,
    "sha256sum": HostSimulator.cmd_sha256sum,
    "file": HostSimulator.cmd_file,
    "readlink": HostSimulator.cmd_readlink,
    "strings": HostSimulator.cmd_strings,
    "find": HostSimulator.cmd_find,
    "ps": HostSimulator.cmd_ps,
    "pstree": HostSimulator.cmd_pstree,
    "netstat": HostSimulator.cmd_netstat,
    "ss": HostSimulator.cmd_ss,
    "lsof": HostSimulator.cmd_lsof,
    "last": HostSimulator.cmd_last,
    "lastb": HostSimulator.cmd_lastb,
    "who": HostSimulator.cmd_who,
    "w": HostSimulator.cmd_who,
    "crontab": HostSimulator.cmd_crontab,
    "systemctl": HostSimulator.cmd_systemctl,
    "journalctl": HostSimulator.cmd_journalctl,
    "rpm": HostSimulator.cmd_rpm,
    "dpkg": HostSimulator.cmd_dpkg,
    "lsattr": HostSimulator.cmd_lsattr,
    "getenforce": HostSimulator.cmd_getenforce,
    "docker": HostSimulator.cmd_docker,
    "grep": HostSimulator.cmd_grep,
    "egrep": HostSimulator.cmd_grep,
    "awk": HostSimulator.cmd_awk,
}

FILTERS: dict[str, Callable[[HostSimulator, list[str], list[str]], CommandResult]] = {
    "grep": _filter_grep,
    "egrep": _filter_grep,
    "head": _filter_head,
    "tail": _filter_tail,
    "wc": _filter_wc,
    "sort": _filter_sort,
    "uniq": _filter_uniq,
    "awk": _filter_awk,
    "cut": _filter_cut,
}
