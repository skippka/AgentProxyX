from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any


@dataclass(frozen=True)
class FirewallDecision:
    allowed: bool
    reason: str
    matches: list[str]


def _normalize_command(command: str) -> str:
    return " ".join(command.strip().split())


def _normalize_path(path: str) -> str:
    path = path.replace("\\", "/")
    if path.startswith("./"):
        return path
    if path.startswith("/"):
        return path.lstrip("/")
    return f"./{path}"


class AgentFirewall:
    def __init__(self, config: dict[str, Any]):
        self.config = config.get("firewall", config)

    def check_command(self, command: str | None) -> FirewallDecision:
        if not command:
            return FirewallDecision(True, "No command supplied", [])
        normalized = _normalize_command(command)
        rules = self.config.get("commands", {})
        deny_matches = [pattern for pattern in rules.get("deny", []) if fnmatch.fnmatchcase(normalized.lower(), pattern.lower())]
        if deny_matches:
            return FirewallDecision(False, f"Command denied by pattern: {deny_matches[0]}", deny_matches)

        allow_patterns = rules.get("allow", [])
        if allow_patterns and any(fnmatch.fnmatchcase(normalized.lower(), pattern.lower()) for pattern in allow_patterns):
            return FirewallDecision(True, "Command explicitly allowed", allow_patterns)

        default_action = self.config.get("default_tool_action", "allow")
        if default_action == "deny":
            return FirewallDecision(False, "Command blocked by default-deny policy", [])
        return FirewallDecision(True, "Command allowed by default policy", [])

    def check_files(self, files: list[str] | None) -> FirewallDecision:
        if not files:
            return FirewallDecision(True, "No files supplied", [])
        rules = self.config.get("files", {})
        deny_patterns = rules.get("deny", [])
        allow_patterns = rules.get("allow", [])
        matches: list[str] = []

        for raw_path in files:
            normalized = _normalize_path(str(PurePosixPath(raw_path.replace("\\", "/"))))
            for pattern in deny_patterns:
                if fnmatch.fnmatchcase(normalized, _normalize_path(pattern)):
                    matches.append(f"{raw_path} -> {pattern}")

        if matches:
            return FirewallDecision(False, f"File access denied: {matches[0]}", matches)

        if allow_patterns:
            outside_allow = []
            for raw_path in files:
                normalized = _normalize_path(str(PurePosixPath(raw_path.replace("\\", "/"))))
                if not any(fnmatch.fnmatchcase(normalized, _normalize_path(pattern)) for pattern in allow_patterns):
                    outside_allow.append(raw_path)
            if outside_allow:
                return FirewallDecision(False, f"File outside allow-list: {outside_allow[0]}", outside_allow)

        return FirewallDecision(True, "File access allowed", [])

    def check_tool_call(self, payload: dict[str, Any]) -> FirewallDecision:
        command = payload.get("command") or payload.get("cmd")
        files = payload.get("files") or payload.get("paths")
        if isinstance(files, str):
            files = [files]

        command_decision = self.check_command(command)
        if not command_decision.allowed:
            return command_decision

        file_decision = self.check_files(files)
        if not file_decision.allowed:
            return file_decision

        return FirewallDecision(True, "Tool call allowed", command_decision.matches + file_decision.matches)

