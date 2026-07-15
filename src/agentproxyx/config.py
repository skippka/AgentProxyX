from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any


DEFAULT_CONFIG: dict[str, Any] = {
    "mode": "monitor",
    "redaction": {"action": "mask", "mask": "[REDACTED]"},
    "firewall": {
        "default_tool_action": "allow",
        "commands": {
            "allow": [
                "npm test*",
                "npm run test*",
                "pytest*",
                "python -m unittest*",
                "go test ./...",
                "cargo test*",
                "ruff check*",
                "mypy*",
            ],
            "deny": [
                "rm -rf*",
                "del /s*",
                "format *",
                "curl *|*sh*",
                "wget *|*sh*",
                "powershell*Invoke-WebRequest*",
                "cat .env*",
                "type .env*",
                "cat *id_rsa*",
                "type *id_rsa*",
                "ssh-keygen*",
                "scp *",
                "ssh *",
            ],
        },
        "files": {
            "allow": ["./src/**", "./tests/**", "./docs/**", "./README.md", "./pyproject.toml"],
            "deny": [
                ".env",
                ".env.*",
                "**/.env",
                "**/.env.*",
                "**/id_rsa",
                "**/id_ed25519",
                "**/.ssh/**",
                "**/*.pem",
                "**/*.key",
                "**/wallet.dat",
            ],
        },
        "urls": {
            "allow": [],
            "deny": [
                "http://169.254.169.254*",
                "https://169.254.169.254*",
                "http://metadata.google.internal*",
                "https://metadata.google.internal*",
            ],
        },
    },
    "costs": {
        "provider": "anthropic",
        "input_per_million": 3.0,
        "output_per_million": 15.0,
        "cache_write_multiplier": 1.25,
        "cache_read_multiplier": 0.1,
    },
    "cache": {"enabled": True, "min_static_chars": 4000, "anthropic_ttl": "1h"},
}


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(path: str | None = None) -> dict[str, Any]:
    if not path:
        return deepcopy(DEFAULT_CONFIG)
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as fh:
        user_config = json.load(fh)
    return deep_merge(DEFAULT_CONFIG, user_config)


def write_default_config(path: str) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(DEFAULT_CONFIG, indent=2), encoding="utf-8")
    return target

