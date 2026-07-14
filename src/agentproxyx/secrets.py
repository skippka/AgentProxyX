from __future__ import annotations

import math
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class SecretFinding:
    kind: str
    value: str
    start: int
    end: int
    confidence: str


PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    ("OpenAI API key", re.compile(r"\bsk-[A-Za-z0-9_\-]{20,}\b"), "high"),
    ("Anthropic API key", re.compile(r"\bsk-ant-[A-Za-z0-9_\-]{20,}\b"), "high"),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"), "high"),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "high"),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_\-]{20,}\b"), "high"),
    ("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9\-]{10,}\b"), "high"),
    ("Private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]+?-----END [A-Z ]*PRIVATE KEY-----"), "critical"),
    ("Database URL", re.compile(r"\b(?:postgres|postgresql|mysql|mongodb|redis)://[^\s\"']+"), "high"),
    ("JWT", re.compile(r"\beyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\b"), "medium"),
    ("Cookie header", re.compile(r"(?i)\bcookie\s*:\s*[^\n\r]{12,}"), "medium"),
    ("Wallet seed phrase", re.compile(r"\b(?:[a-z]{3,10}\s+){11,23}[a-z]{3,10}\b"), "medium"),
]


def shannon_entropy(value: str) -> float:
    if not value:
        return 0.0
    counts = {char: value.count(char) for char in set(value)}
    return -sum((count / len(value)) * math.log2(count / len(value)) for count in counts.values())


def find_secrets(text: str) -> list[SecretFinding]:
    findings: list[SecretFinding] = []
    for kind, pattern, confidence in PATTERNS:
        for match in pattern.finditer(text):
            value = match.group(0)
            findings.append(SecretFinding(kind, value, match.start(), match.end(), confidence))

    token_pattern = re.compile(r"\b[A-Za-z0-9_\-+/=]{32,}\b")
    for match in token_pattern.finditer(text):
        value = match.group(0)
        if shannon_entropy(value) >= 4.2 and not any(f.start <= match.start() < f.end for f in findings):
            findings.append(SecretFinding("High entropy token", value, match.start(), match.end(), "medium"))
    return sorted(findings, key=lambda item: item.start)


def redact_text(text: str, mask: str = "[REDACTED]") -> tuple[str, list[SecretFinding]]:
    findings = find_secrets(text)
    if not findings:
        return text, []

    chunks: list[str] = []
    last = 0
    for finding in findings:
        chunks.append(text[last:finding.start])
        chunks.append(f"{mask}:{finding.kind}")
        last = finding.end
    chunks.append(text[last:])
    return "".join(chunks), findings

