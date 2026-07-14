from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CostEstimate:
    input_tokens: int
    output_tokens: int
    input_cost: float
    output_cost: float
    total_cost: float
    cache_savings: float


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4) if text else 0


def estimate_cost(
    request_text: str,
    response_text: str = "",
    config: dict[str, Any] | None = None,
    cacheable_chars: int = 0,
) -> CostEstimate:
    cfg = (config or {}).get("costs", config or {})
    input_per_million = float(cfg.get("input_per_million", 3.0))
    output_per_million = float(cfg.get("output_per_million", 15.0))
    cache_read_multiplier = float(cfg.get("cache_read_multiplier", 0.1))

    input_tokens = estimate_tokens(request_text)
    output_tokens = estimate_tokens(response_text)
    input_cost = input_tokens * input_per_million / 1_000_000
    output_cost = output_tokens * output_per_million / 1_000_000

    cacheable_tokens = estimate_tokens(request_text[:cacheable_chars]) if cacheable_chars else 0
    cache_savings = cacheable_tokens * input_per_million * (1 - cache_read_multiplier) / 1_000_000
    total = input_cost + output_cost
    return CostEstimate(input_tokens, output_tokens, input_cost, output_cost, total, cache_savings)

