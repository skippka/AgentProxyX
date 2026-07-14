# AgentProxyX v0.1.0

Initial public MVP release.

## Highlights

- Multi-agent presets for Claude Code, Codex CLI, Gemini CLI, OpenAI Codex, Aider, Cursor, Windsurf, Cline, Roo Code, Amp, Continue.dev, OpenHands, OpenRouter-compatible clients, LiteLLM, and more.
- Secret Guard for API keys, private keys, database URLs, cookies, JWTs, seed-like phrases, and high-entropy tokens.
- Agent Firewall for risky shell commands and protected file access.
- Cost Meter with prompt-cache savings estimates.
- Local replay dashboard backed by SQLite.
- Zero required runtime dependencies for the first Python MVP.

## Quick Start

```powershell
git clone https://github.com/skippka/AgentProxyX
cd AgentProxyX
python -m agentproxyx doctor
python -m agentproxyx start --agent codex-cli --dry-run
```

Dashboard:

```text
http://127.0.0.1:7778
```

