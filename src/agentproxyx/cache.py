from __future__ import annotations

import json
from typing import Any


def maybe_optimize_anthropic_payload(body: bytes, config: dict[str, Any]) -> tuple[bytes, bool, int]:
    cache_cfg = config.get("cache", {})
    if not cache_cfg.get("enabled", True):
        return body, False, 0
    try:
        payload = json.loads(body.decode("utf-8"))
    except Exception:
        return body, False, 0

    changed = False
    cacheable_chars = 0
    min_static_chars = int(cache_cfg.get("min_static_chars", 4000))
    ttl = cache_cfg.get("anthropic_ttl", "1h")

    system = payload.get("system")
    if isinstance(system, str) and len(system) >= min_static_chars:
        payload["system"] = [
            {
                "type": "text",
                "text": system,
                "cache_control": {"type": "ephemeral", "ttl": ttl},
            }
        ]
        changed = True
        cacheable_chars += len(system)
    elif isinstance(system, list):
        for block in reversed(system):
            if isinstance(block, dict) and len(str(block.get("text", ""))) >= min_static_chars:
                block.setdefault("cache_control", {"type": "ephemeral", "ttl": ttl})
                changed = True
                cacheable_chars += len(str(block.get("text", "")))
                break

    tools = payload.get("tools")
    if isinstance(tools, list):
        tools_text = json.dumps(tools, separators=(",", ":"))
        if len(tools_text) >= min_static_chars and tools:
            last_tool = tools[-1]
            if isinstance(last_tool, dict):
                last_tool.setdefault("cache_control", {"type": "ephemeral", "ttl": ttl})
                changed = True
                cacheable_chars += len(tools_text)

    if not changed:
        return body, False, 0
    return json.dumps(payload, separators=(",", ":")).encode("utf-8"), True, cacheable_chars

