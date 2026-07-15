from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from threading import Thread
from typing import Any, TextIO

from .firewall import AgentFirewall, FirewallDecision
from .replay import ReplayStore


FILE_KEYS = {"file", "files", "filepath", "file_path", "filename", "path", "paths"}
URL_KEYS = {"url", "urls", "uri", "uris", "endpoint", "endpoints"}
COMMAND_KEYS = {"command", "cmd", "script", "shell", "input"}
FILE_TOOL_HINTS = ("file", "read", "write", "edit", "path", "directory")
NETWORK_TOOL_HINTS = ("fetch", "http", "url", "web", "request")
SHELL_TOOL_HINTS = ("bash", "shell", "terminal", "command", "exec", "powershell")


@dataclass(frozen=True)
class MCPInspection:
    should_forward: bool
    response: dict[str, Any] | None
    decision: FirewallDecision | None
    normalized: dict[str, Any]


def _values(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, (int, float, bool)):
        return [str(value)]
    if isinstance(value, list):
        items: list[str] = []
        for item in value:
            items.extend(_values(item))
        return items
    if isinstance(value, dict):
        items = []
        for item in value.values():
            items.extend(_values(item))
        return items
    return [str(value)]


def _walk_arguments(value: Any, key_hint: str | None = None) -> tuple[list[str], list[str], list[str]]:
    commands: list[str] = []
    files: list[str] = []
    urls: list[str] = []

    if isinstance(value, dict):
        for key, child in value.items():
            child_commands, child_files, child_urls = _walk_arguments(child, str(key).lower())
            commands.extend(child_commands)
            files.extend(child_files)
            urls.extend(child_urls)
        return commands, files, urls

    if isinstance(value, list):
        for child in value:
            child_commands, child_files, child_urls = _walk_arguments(child, key_hint)
            commands.extend(child_commands)
            files.extend(child_files)
            urls.extend(child_urls)
        return commands, files, urls

    values = _values(value)
    if key_hint in COMMAND_KEYS:
        commands.extend(values)
    elif key_hint in FILE_KEYS:
        files.extend(values)
    elif key_hint in URL_KEYS:
        urls.extend(values)
    else:
        urls.extend(item for item in values if item.startswith(("http://", "https://")))
    return commands, files, urls


def normalize_mcp_tool_call(message: dict[str, Any]) -> dict[str, Any]:
    params = message.get("params") if isinstance(message.get("params"), dict) else {}
    tool = str(params.get("name") or params.get("tool") or message.get("tool") or "")
    arguments = params.get("arguments")
    if arguments is None:
        arguments = params.get("input")
    if arguments is None:
        arguments = params.get("args")
    if not isinstance(arguments, dict):
        arguments = {"input": arguments} if arguments is not None else {}

    commands, files, urls = _walk_arguments(arguments)
    lowered_tool = tool.lower()

    if not commands and any(hint in lowered_tool for hint in SHELL_TOOL_HINTS):
        for key in ("input", "query"):
            if key in arguments:
                commands.extend(_values(arguments[key]))

    if any(hint in lowered_tool for hint in FILE_TOOL_HINTS):
        for key in ("input", "query", "target"):
            if key in arguments:
                files.extend(_values(arguments[key]))

    if any(hint in lowered_tool for hint in NETWORK_TOOL_HINTS):
        for key in ("input", "query", "target"):
            if key in arguments:
                urls.extend(item for item in _values(arguments[key]) if item.startswith(("http://", "https://")))

    normalized: dict[str, Any] = {"tool": tool}
    if commands:
        normalized["command"] = commands[0]
    if files:
        normalized["files"] = sorted(set(files))
    if urls:
        normalized["urls"] = sorted(set(urls))
    return normalized


def inspect_mcp_message(message: dict[str, Any], firewall: AgentFirewall, store: ReplayStore, agent: str = "mcp") -> MCPInspection:
    if message.get("method") != "tools/call":
        return MCPInspection(True, None, None, {})

    normalized = normalize_mcp_tool_call(message)
    decision = firewall.check_tool_call(normalized)
    event_kind = "tool_allowed" if decision.allowed else "tool_blocked"
    store.add(event_kind, agent, decision.reason, {"mcp": message, "normalized": normalized, "matches": decision.matches})
    if decision.allowed:
        return MCPInspection(True, None, decision, normalized)

    response = {
        "jsonrpc": message.get("jsonrpc", "2.0"),
        "id": message.get("id"),
        "error": {
            "code": -32001,
            "message": "AgentProxyX blocked MCP tool call",
            "data": {"reason": decision.reason, "matches": decision.matches, "normalized": normalized},
        },
    }
    return MCPInspection(False, response, decision, normalized)


def _copy_stream(source: TextIO, target: TextIO) -> None:
    for line in source:
        target.write(line)
        target.flush()


def wrap_mcp_server(command: list[str], firewall: AgentFirewall, store: ReplayStore, agent: str = "mcp") -> int:
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        raise ValueError("MCP wrap requires a server command after --")

    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    assert process.stdin is not None
    assert process.stdout is not None
    assert process.stderr is not None

    stdout_thread = Thread(target=_copy_stream, args=(process.stdout, sys.stdout), daemon=True)
    stderr_thread = Thread(target=_copy_stream, args=(process.stderr, sys.stderr), daemon=True)
    stdout_thread.start()
    stderr_thread.start()

    for line in sys.stdin:
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            process.stdin.write(line)
            process.stdin.flush()
            continue

        inspection = inspect_mcp_message(message, firewall, store, agent)
        if inspection.should_forward:
            process.stdin.write(line)
            process.stdin.flush()
            continue

        sys.stdout.write(json.dumps(inspection.response, ensure_ascii=False) + "\n")
        sys.stdout.flush()

    process.stdin.close()
    return process.wait()
