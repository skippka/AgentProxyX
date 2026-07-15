from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CacheOptimizationResult:
    body: bytes
    changed: bool
    cacheable_chars: int
    provider: str


class CachePolicy:
    provider = "generic"

    def optimize(self, body: bytes, config: dict[str, Any]) -> CacheOptimizationResult:
        return CacheOptimizationResult(body, False, 0, self.provider)


class NoOpCachePolicy(CachePolicy):
    def __init__(self, provider: str):
        self.provider = provider


class AnthropicCachePolicy(CachePolicy):
    provider = "anthropic"

    def optimize(self, body: bytes, config: dict[str, Any]) -> CacheOptimizationResult:
        cache_cfg = config.get("cache", {})
        if not cache_cfg.get("enabled", True):
            return CacheOptimizationResult(body, False, 0, self.provider)
        try:
            payload = json.loads(body.decode("utf-8"))
        except Exception:
            return CacheOptimizationResult(body, False, 0, self.provider)

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
            return CacheOptimizationResult(body, False, 0, self.provider)
        return CacheOptimizationResult(json.dumps(payload, separators=(",", ":")).encode("utf-8"), True, cacheable_chars, self.provider)


def cache_policy_for(config: dict[str, Any]) -> CachePolicy:
    cache_cfg = config.get("cache", {})
    costs_cfg = config.get("costs", {})
    provider = str(cache_cfg.get("provider") or costs_cfg.get("provider") or "anthropic").lower()
    if provider == "anthropic":
        return AnthropicCachePolicy()
    if provider in {"openai", "openai-compatible", "openrouter", "litellm"}:
        return NoOpCachePolicy(provider)
    return NoOpCachePolicy(provider)


def optimize_payload(body: bytes, config: dict[str, Any]) -> CacheOptimizationResult:
    return cache_policy_for(config).optimize(body, config)


def maybe_optimize_anthropic_payload(body: bytes, config: dict[str, Any]) -> tuple[bytes, bool, int]:
    result = AnthropicCachePolicy().optimize(body, config)
    return result.body, result.changed, result.cacheable_chars

