from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentPreset:
    key: str
    name: str
    category: str
    env: dict[str, str]
    launch_hint: str
    notes: str
    experimental: bool = False


def _proxy_env(port: int) -> dict[str, str]:
    proxy = f"http://127.0.0.1:{port}"
    return {
        "HTTP_PROXY": proxy,
        "HTTPS_PROXY": proxy,
        "ALL_PROXY": proxy,
    }


def presets(port: int = 8080) -> dict[str, AgentPreset]:
    proxy = f"http://127.0.0.1:{port}"
    openai_base = f"{proxy}/v1"
    return {
        "claude-code": AgentPreset(
            "claude-code",
            "Claude Code",
            "CLI",
            {**_proxy_env(port), "ANTHROPIC_BASE_URL": proxy},
            "claude",
            "Routes Anthropic traffic through AgentProxyX and enables prompt-cache hints.",
        ),
        "codex-cli": AgentPreset(
            "codex-cli",
            "Codex CLI",
            "CLI",
            {**_proxy_env(port), "OPENAI_BASE_URL": openai_base},
            "codex",
            "OpenAI-compatible base URL mode for local Codex CLI workflows.",
        ),
        "openai-codex": AgentPreset(
            "openai-codex",
            "OpenAI Codex",
            "CLI",
            {**_proxy_env(port), "OPENAI_BASE_URL": openai_base},
            "codex",
            "Preset for OpenAI Codex clients that honor OPENAI_BASE_URL.",
        ),
        "gemini-cli": AgentPreset(
            "gemini-cli",
            "Gemini CLI",
            "CLI",
            {**_proxy_env(port), "GOOGLE_GENAI_BASE_URL": proxy},
            "gemini",
            "Proxy mode for Gemini-compatible tools; exact env support depends on the client.",
        ),
        "aider": AgentPreset(
            "aider",
            "Aider",
            "CLI",
            {**_proxy_env(port), "OPENAI_API_BASE": openai_base, "OPENAI_BASE_URL": openai_base},
            "aider",
            "Works with OpenAI-compatible and OpenRouter-compatible Aider setups.",
        ),
        "cursor": AgentPreset(
            "cursor",
            "Cursor",
            "Editor",
            {**_proxy_env(port), "OPENAI_BASE_URL": openai_base},
            "Configure Cursor model provider base URL to AgentProxyX.",
            "Use custom provider settings or system proxy settings.",
        ),
        "windsurf": AgentPreset(
            "windsurf",
            "Windsurf",
            "Editor",
            {**_proxy_env(port), "OPENAI_BASE_URL": openai_base},
            "Configure Windsurf provider/proxy settings.",
            "Editor support depends on the configured provider.",
        ),
        "cline": AgentPreset(
            "cline",
            "Cline",
            "VS Code Extension",
            {**_proxy_env(port), "OPENAI_BASE_URL": openai_base, "ANTHROPIC_BASE_URL": proxy},
            "Set Cline API provider base URL to AgentProxyX.",
            "Good fit for MCP and tool-call firewall demos.",
        ),
        "roo-code": AgentPreset(
            "roo-code",
            "Roo Code",
            "VS Code Extension",
            {**_proxy_env(port), "OPENAI_BASE_URL": openai_base, "ANTHROPIC_BASE_URL": proxy},
            "Set Roo Code provider base URL to AgentProxyX.",
            "Good fit for local tool-use monitoring.",
        ),
        "amp": AgentPreset(
            "amp",
            "Amp",
            "CLI",
            {**_proxy_env(port), "OPENAI_BASE_URL": openai_base, "ANTHROPIC_BASE_URL": proxy},
            "amp",
            "Routes supported provider calls through AgentProxyX.",
        ),
        "continue-dev": AgentPreset(
            "continue-dev",
            "Continue.dev",
            "Editor Extension",
            {**_proxy_env(port), "OPENAI_BASE_URL": openai_base},
            "Set Continue model apiBase to AgentProxyX.",
            "Use Continue config for OpenAI-compatible providers.",
        ),
        "openhands": AgentPreset(
            "openhands",
            "OpenHands",
            "Agent Runtime",
            {**_proxy_env(port), "LLM_BASE_URL": openai_base, "OPENAI_BASE_URL": openai_base},
            "openhands",
            "Useful for monitoring autonomous agent sessions.",
        ),
        "openrouter-compatible": AgentPreset(
            "openrouter-compatible",
            "OpenRouter-compatible tools",
            "Provider",
            {**_proxy_env(port), "OPENAI_BASE_URL": openai_base, "OPENAI_API_BASE": openai_base},
            "Use any OpenAI-compatible client.",
            "Forward AgentProxyX to https://openrouter.ai/api when needed.",
        ),
        "vscode-copilot-chat": AgentPreset(
            "vscode-copilot-chat",
            "VS Code Copilot Chat",
            "Editor",
            _proxy_env(port),
            "Use system proxy settings.",
            "Some managed clients ignore custom base URLs.",
            experimental=True,
        ),
        "zed-ai": AgentPreset(
            "zed-ai",
            "Zed AI",
            "Editor",
            {**_proxy_env(port), "OPENAI_BASE_URL": openai_base},
            "Configure provider endpoint where supported.",
            "Experimental because editor provider settings vary.",
            experimental=True,
        ),
        "jetbrains-ai": AgentPreset(
            "jetbrains-ai",
            "JetBrains AI Assistant",
            "Editor",
            _proxy_env(port),
            "Use IDE proxy settings.",
            "Experimental for managed-provider traffic.",
            experimental=True,
        ),
        "tabby": AgentPreset(
            "tabby",
            "Tabby",
            "Self-hosted",
            {**_proxy_env(port), "OPENAI_BASE_URL": openai_base},
            "Point OpenAI-compatible provider settings at AgentProxyX.",
            "Useful for teams mixing local and hosted models.",
            experimental=True,
        ),
        "litellm": AgentPreset(
            "litellm",
            "LiteLLM clients",
            "Provider Router",
            {**_proxy_env(port), "OPENAI_BASE_URL": openai_base},
            "Use AgentProxyX as the upstream-compatible base URL.",
            "Good bridge for multi-provider teams.",
        ),
    }


def get_preset(agent: str, port: int = 8080) -> AgentPreset:
    all_presets = presets(port)
    try:
        return all_presets[agent]
    except KeyError as exc:
        available = ", ".join(sorted(all_presets))
        raise ValueError(f"Unknown agent '{agent}'. Available: {available}") from exc

