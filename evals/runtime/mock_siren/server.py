#!/usr/bin/env python3
"""MCP stdio server exposing the mock SIREN `ls` and `run` tools.

Transport: newline-delimited JSON-RPC 2.0 on stdin/stdout, which is what MCP
stdio clients (including Claude Code) speak. Only the two tools SLEUTH is
allowed to use are declared; calling anything else -- `exec`, `deploy`,
`list_clients`, `wait` -- fails with a JSON-RPC "unknown tool" error, so an
agent that invents a tool name gets a hard failure instead of a silent no-op.

Usage:
    python3 evals/runtime/mock_siren/server.py --scenario <scenario.json>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):  # allow running this file by path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mock_siren.api import MockSirenSession  # noqa: E402
from mock_siren.scenario import load_scenario  # noqa: E402

SERVER_NAME = "mock-siren"
SERVER_VERSION = "1.0.0"
SUPPORTED_PROTOCOL_VERSIONS = ("2024-11-05", "2025-03-26", "2025-06-18")
DEFAULT_PROTOCOL_VERSION = "2025-06-18"

PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602

TOOL_DEFINITIONS = [
    {
        "name": "ls",
        "description": "List all connected SIREN clients",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "run",
        "description": (
            "Execute a command on a SIREN client. Results over 8 KiB default to a "
            "recoverable head/tail preview."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "client_id": {
                    "type": "string",
                    "description": "ID of the client to execute the command on",
                },
                "command": {
                    "type": "string",
                    "description": "Command to execute on the client",
                    "maxLength": 51200,
                },
                "output_mode": {
                    "type": "string",
                    "description": "auto previews results over 8 KiB; full returns everything",
                    "enum": ["auto", "full"],
                },
            },
            "required": ["client_id", "command"],
        },
    },
]


class MockSirenMCPServer:
    """JSON-RPC dispatcher around one `MockSirenSession`."""

    def __init__(self, session: MockSirenSession):
        self.session = session
        self.initialized = False

    def handle(self, message: dict) -> dict | None:
        """Return a JSON-RPC response, or None for notifications."""
        if message.get("jsonrpc") != "2.0":
            return _error(message.get("id"), INVALID_REQUEST, "jsonrpc must be \"2.0\"")
        method = message.get("method")
        if not isinstance(method, str):
            return _error(message.get("id"), INVALID_REQUEST, "method is required")
        message_id = message.get("id")
        params = message.get("params") or {}

        if method == "initialize":
            requested = params.get("protocolVersion", DEFAULT_PROTOCOL_VERSION)
            version = (
                requested if requested in SUPPORTED_PROTOCOL_VERSIONS
                else DEFAULT_PROTOCOL_VERSION
            )
            self.initialized = True
            return _result(message_id, {
                "protocolVersion": version,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            })
        if method in ("notifications/initialized", "initialized"):
            return None
        if method.startswith("notifications/"):
            return None
        if method == "ping":
            return _result(message_id, {})
        if method == "tools/list":
            return _result(message_id, {"tools": TOOL_DEFINITIONS})
        if method == "tools/call":
            return self._call_tool(message_id, params)
        return _error(message_id, METHOD_NOT_FOUND, f"method not found: {method}")

    def _call_tool(self, message_id, params: dict) -> dict:
        name = params.get("name")
        arguments = params.get("arguments") or {}
        if not isinstance(arguments, dict):
            return _error(message_id, INVALID_PARAMS, "arguments must be an object")
        if name == "ls":
            return _result(message_id, {
                "content": [{"type": "text", "text": self.session.ls_text()}],
                "isError": False,
            })
        if name == "run":
            missing = [key for key in ("client_id", "command") if key not in arguments]
            if missing:
                return _error(
                    message_id, INVALID_PARAMS,
                    f"missing required argument: {', '.join(missing)}",
                )
            result = self.session.run(
                arguments["client_id"],
                arguments["command"],
                arguments.get("output_mode", "auto"),
            )
            return _result(message_id, {
                "content": [{"type": "text", "text": result.text}],
                "structuredContent": result.structured,
                "isError": result.is_error,
            })
        return _error(message_id, INVALID_PARAMS, f"unknown tool: {name}")


def _result(message_id, payload: dict) -> dict:
    return {"jsonrpc": "2.0", "id": message_id, "result": payload}


def _error(message_id, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": message_id, "error": {"code": code, "message": message}}


def serve(session: MockSirenSession, stdin=None, stdout=None) -> None:
    """Read newline-delimited JSON-RPC from stdin until EOF."""
    source = stdin or sys.stdin
    sink = stdout or sys.stdout
    server = MockSirenMCPServer(session)
    for line in source:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            _write(sink, _error(None, PARSE_ERROR, "invalid JSON"))
            continue
        if not isinstance(message, dict):
            _write(sink, _error(None, INVALID_REQUEST, "message must be an object"))
            continue
        response = server.handle(message)
        if response is not None:
            _write(sink, response)


def _write(sink, payload: dict) -> None:
    sink.write(json.dumps(payload, ensure_ascii=False) + "\n")
    sink.flush()


def main() -> None:
    parser = argparse.ArgumentParser(description="Mock SIREN MCP stdio server")
    parser.add_argument("--scenario", required=True, help="path to a scenario JSON file")
    parser.add_argument("--project", default="mock", help="project id reported in results")
    args = parser.parse_args()
    session = MockSirenSession(load_scenario(args.scenario), project=args.project)
    serve(session)


if __name__ == "__main__":
    main()
