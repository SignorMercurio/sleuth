#!/usr/bin/env python3
"""Run a real Claude Code investigation against mock SIREN, with no live MCP.

Captures model outputs and observed costs; semantic correctness stays pending
until a reviewer compares the run with the scenario's expectation. No result
is called a quality pass merely because the CLI exited successfully.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import shutil
import subprocess
import sys
import threading
import time


ROOT = Path(__file__).resolve().parents[2]
SERVER = Path(__file__).resolve().parent / "mock_siren" / "server.py"


def check_user_permissions(settings: dict) -> None:
    # --allowedTools adds grants; it does not revoke user-level grants. Keep
    # model/auth settings, but refuse configurations that expand file access.
    permissions = settings.get("permissions", {})
    if permissions.get("additionalDirectories") or settings.get("additionalDirectories"):
        raise ValueError("model drill refuses additionalDirectories; use a dedicated CLI profile")
    for rule in permissions.get("allow", []):
        tool = rule.split("(", 1)[0].strip()
        if tool in {"Read", "Write", "Edit"} or "*" in tool:
            raise ValueError("model drill refuses existing file/wildcard grants; use a dedicated CLI profile")


def summarize(events: list[dict]) -> dict:
    calls = {}
    results = {}
    final = {}
    model = None
    for event in events:
        if event.get("type") == "result":
            final = event
        if event.get("type") == "system" and event.get("subtype") == "init":
            model = event.get("model")
        message = event.get("message")
        if not isinstance(message, dict):
            continue
        for block in message.get("content", []):
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_use":
                calls[block["id"]] = block
            elif block.get("type") == "tool_result":
                results[block["tool_use_id"]] = block
    remote = [c for c in calls.values() if c["name"] == "mcp__siren__run"]
    signatures = [json.dumps(c.get("input", {}), sort_keys=True) for c in remote]
    return {
        "completed": (final.get("subtype") == "success" and not final.get("is_error", True)
                      and bool(final.get("result")) and bool(remote)),
        "model": model,
        "result_subtype": final.get("subtype"),
        "tool_calls": len(calls),
        "siren_run_calls": len(remote),
        "exact_repeat_calls": len(signatures) - len(set(signatures)),
        "siren_result_bytes": sum(
            len(json.dumps(results[c["id"]].get("content", ""), ensure_ascii=False).encode())
            for c in remote if c["id"] in results
        ),
        "usage": final.get("usage"),
        "model_usage": final.get("modelUsage"),
        "cost_usd": final.get("total_cost_usd"),
        "permission_denials": final.get("permission_denials", []),
        "quality_verdict": "pending_review",
        "first_actionable_conclusion_seconds": None,
        "post_closure_calls": None,
    }


def run(scenario_path: Path, skill: Path | None, output: Path, timeout: int) -> dict:
    output = output.resolve()
    if output == ROOT or ROOT in output.parents:
        raise ValueError("output directory must be outside the repository")
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    scenario_path = scenario_path.resolve()
    scenario = json.loads(scenario_path.read_text())
    if not isinstance(scenario.get("prompt"), str) or not scenario["prompt"].strip():
        raise ValueError("scenario requires a nonempty user-facing prompt")
    executable = shutil.which("claude")
    if not executable:
        raise RuntimeError("Claude Code CLI is required; configure model access before running")
    config_home = Path(os.environ.get("CLAUDE_CONFIG_DIR", str(Path.home() / ".claude")))
    settings_path = config_home / "settings.json"
    settings = json.loads(settings_path.read_text()) if settings_path.exists() else {}
    check_user_permissions(settings)
    # Never reuse another run's findings or expose the expectation to the agent.
    output.mkdir(parents=True, exist_ok=False)
    workspace = output / "workspace"
    workspace.mkdir()
    scenario_bytes = scenario_path.read_bytes()
    scenario_copy = output / "scenario.json"
    scenario_copy.write_bytes(scenario_bytes)
    if skill:
        shutil.copytree(skill, workspace / "skill")
    copied_skill = workspace / "skill"
    skill_hash = hashlib.sha256(b"".join(
        str(p.relative_to(copied_skill)).encode() + b"\0" + p.read_bytes()
        for p in sorted(copied_skill.rglob("*")) if p.is_file()
    )).hexdigest() if skill else None
    config = output / "mcp.json"
    config.write_text(json.dumps({"mcpServers": {"siren": {
        "command": sys.executable,
        "args": [str(SERVER), "--scenario", str(scenario_copy)],
        "env": {"PYTHONDONTWRITEBYTECODE": "1"},
    }}}))
    # Retain the user's configured model/auth; disable hooks and plugin loading.
    overrides = {
        "disableAllHooks": True,
        "enabledPlugins": {name: False for name in settings.get("enabledPlugins", {})},
    }
    allowed = [f"Read(/{workspace}/**)"]
    allowed += [f"{tool}(/{workspace}/*.findings.md)" for tool in ("Write", "Edit")]
    allowed += ["mcp__siren__ls", "mcp__siren__run"]
    prompt = (
        "请排查以下已授权主机的具体事件，交付证据支持的调查结论和 findings 工作底稿，"
        "不生成正式报告。已授权 Client ID："
        + ", ".join(str(c["id"]) for c in scenario["clients"])
        + "。云侧工具、联网与子 agent 本次不可用；不要等待补充输入，按可用证据推进并披露缺口。\n"
        + scenario["prompt"]
    )
    if scenario.get("alarm"):
        prompt += "\n客户提供的告警摘要：" + json.dumps(scenario["alarm"], ensure_ascii=False)
    if skill:
        prompt += "\n按本地 skill/SKILL.md 执行，按需读取其 references。"
    system = (
        "你是安全事件调查助手。只通过实际提供的 SIREN ls/run 工具读取目标主机。"
        "主机取证只读，不执行清理、修复、下载或其他改变主机状态的命令。"
        "本地文件工具仅用于本工作目录的调查资料与 findings；不读取目录外文件。"
        f"本地工作目录是 {workspace}。"
    )
    command = [
        executable, "--print", "--verbose", "--output-format", "stream-json",
        "--no-session-persistence", "--no-chrome", "--disable-slash-commands",
        "--strict-mcp-config", "--mcp-config", str(config),
        "--setting-sources", "user", "--settings", json.dumps(overrides),
        "--system-prompt", system, "--tools", "Read,Write,Edit",
        "--permission-mode", "dontAsk", "--allowedTools", ",".join(allowed),
    ]
    (output / "prompt.txt").write_text(prompt)
    started = time.monotonic()
    harness_hash = hashlib.sha256(b"".join(
        p.name.encode() + b"\0" + p.read_bytes()
        for p in [Path(__file__), *sorted(SERVER.parent.glob("*.py"))]
    )).hexdigest()
    env = {**os.environ, "ENABLE_CLAUDEAI_MCP_SERVERS": "false", "PYTHONDONTWRITEBYTECODE": "1"}
    with (output / "events.jsonl").open("w") as stdout, (output / "stderr.txt").open("w") as stderr, \
         (output / "event_timings.jsonl").open("w") as timings:
        process = subprocess.Popen(command, cwd=workspace, env=env, stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=stderr, text=True, start_new_session=True)

        def capture() -> None:
            for number, line in enumerate(process.stdout, 1):
                stdout.write(line)
                stdout.flush()
                timings.write(json.dumps({"line": number,
                    "elapsed_seconds": round(time.monotonic() - started, 3)}) + "\n")

        reader = threading.Thread(target=capture)
        reader.start()
        try:
            process.stdin.write(prompt)
            process.stdin.close()
            process.wait(timeout=timeout)
            timed_out = False
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            timed_out = True
        finally:
            reader.join()
    events = []
    malformed = 0
    with (output / "events.jsonl").open() as stream:
        for line in stream:
            try:
                event = json.loads(line)
                if isinstance(event, dict):
                    events.append(event)
            except json.JSONDecodeError:
                malformed += 1
    summary = summarize(events)
    summary.update({
        "scenario": scenario["id"],
        "scenario_sha256": hashlib.sha256(scenario_bytes).hexdigest(),
        "skill_sha256": skill_hash,
        "harness_sha256": harness_hash,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "exit_code": process.returncode,
        "timed_out": timed_out,
        "malformed_event_lines": malformed,
        "findings_files": [str(p.relative_to(output)) for p in workspace.glob("*.findings.md")],
    })
    summary["completed"] = (summary["completed"] and process.returncode == 0
                            and not timed_out and malformed == 0
                            and bool(summary["findings_files"]))
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    final = next((e.get("result", "") for e in reversed(events) if e.get("type") == "result"), "")
    (output / "conclusion.md").write_text(final)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", type=Path, required=True)
    parser.add_argument("--skill-dir", type=Path, default=ROOT / "skills" / "sleuth")
    parser.add_argument("--without-skill", action="store_true")
    parser.add_argument("--output-dir", type=Path, required=True, help="new directory outside the repository")
    parser.add_argument("--timeout", type=int, default=600, help="wall-clock cap per run in seconds")
    args = parser.parse_args()
    output = args.output_dir.resolve()
    if output == ROOT or ROOT in output.parents:
        parser.error("--output-dir must be outside the repository")
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    summary = run(args.scenario.resolve(), None if args.without_skill else args.skill_dir.resolve(),
                  output, args.timeout)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    raise SystemExit(0 if summary["completed"] else 1)


if __name__ == "__main__":
    main()
