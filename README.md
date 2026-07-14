# AgentProxyX

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](pyproject.toml)

**AgentProxyX is a local security and cost-control gateway for AI coding agents.**

It sits between local AI development agents and model providers, then gives you four things most agent stacks still miss:

- **Secret Guard**: detects and redacts API keys, private keys, tokens, cookies, database URLs, wallet seed phrases, and high-entropy strings before they leave your machine.
- **Agent Firewall**: blocks risky tool calls such as `rm -rf`, `curl | sh`, `cat .env`, SSH key reads, and unapproved command/file access.
- **Cost Meter**: estimates input/output spend and prompt-cache savings per session.
- **Replay Dashboard**: local timeline of requests, blocked secrets, blocked tools, cache decisions, and estimated cost.

AgentProxyX is intentionally built as a practical Python MVP: easy to run, easy to audit, and ready to grow into deeper MCP and sandbox integrations.

## Supported Agents

AgentProxyX ships with presets for popular coding agents and agent-capable editors:

| Agent | Preset | Status |
|---|---:|---|
| Claude Code | `claude-code` | Ready |
| Codex CLI | `codex-cli` | Ready |
| Gemini CLI | `gemini-cli` | Ready |
| OpenAI Codex | `openai-codex` | Ready |
| Cursor | `cursor` | Ready |
| Windsurf | `windsurf` | Ready |
| Cline | `cline` | Ready |
| Roo Code | `roo-code` | Ready |
| Aider | `aider` | Ready |
| Amp | `amp` | Ready |
| Continue.dev | `continue-dev` | Ready |
| OpenHands | `openhands` | Ready |
| OpenRouter-compatible tools | `openrouter-compatible` | Ready |
| VS Code Copilot Chat | `vscode-copilot-chat` | Experimental |
| Zed AI | `zed-ai` | Experimental |
| JetBrains AI Assistant | `jetbrains-ai` | Experimental |
| Tabby | `tabby` | Experimental |
| LiteLLM clients | `litellm` | Ready |
| Cody | `cody` | Experimental |

## Quick Start

```powershell
cd C:\Users\vadim\Desktop\AgentProxyX
python -m agentproxyx doctor
python -m agentproxyx agents
python -m agentproxyx start --agent claude-code --dry-run
```

Open the dashboard:

```text
http://127.0.0.1:7778
```

Run a preset and print the environment variables your agent should use:

```powershell
python -m agentproxyx env --agent claude-code
python -m agentproxyx env --agent codex-cli
python -m agentproxyx env --agent gemini-cli
python -m agentproxyx env --agent aider
python -m agentproxyx env --agent cursor
```

## Example

```powershell
python -m agentproxyx start `
  --agent claude-code `
  --port 8080 `
  --dashboard-port 7778 `
  --target https://api.anthropic.com
```

Then configure your agent to send traffic through:

```text
ANTHROPIC_BASE_URL=http://127.0.0.1:8080
HTTPS_PROXY=http://127.0.0.1:8080
HTTP_PROXY=http://127.0.0.1:8080
```

For OpenAI-compatible agents:

```text
OPENAI_BASE_URL=http://127.0.0.1:8080/v1
```

## Tool Firewall Rules

AgentProxyX can inspect explicit tool-call payloads through its built-in endpoint:

```http
POST /v1/agentproxyx/tool-call
Content-Type: application/json
```

```json
{
  "tool": "bash",
  "command": "cat .env",
  "files": [".env"]
}
```

Response:

```json
{
  "allowed": false,
  "reason": "Command denied by pattern: cat .env"
}
```

Default rules live in [`configs/agentproxyx.default.json`](configs/agentproxyx.default.json).

## Why This Is Different

Most LLM proxies only log requests or route providers. Most secret scanners only scan static files. Most MCP security ideas are research prototypes.

AgentProxyX combines the useful middle:

- local proxy for real coding agents;
- secret filtering before provider calls;
- command and file firewall for agent tool use;
- prompt-cache optimization hints;
- cost accounting and local replay timeline;
- adapter presets for many agents instead of one vendor.

## GitHub Topics

Suggested repository topics:

```text
ai-agents llm-proxy mcp security developer-tools prompt-caching secret-scanning codex claude-code aider cursor openrouter
```

## Project Roadmap

- `0.1`: Python MVP with proxy, presets, secret guard, firewall, cost meter, replay dashboard.
- `0.2`: MCP server wrapper mode and richer tool-call normalization.
- `0.3`: provider-specific cache policy engine for Anthropic, OpenAI-compatible APIs, and OpenRouter.
- `0.4`: optional WASI sandbox runner for high-risk tools.
- `0.5`: signed session exports, shareable replay cards, and GitHub demo assets.

## Development

```powershell
python -m unittest discover -s tests
python -m agentproxyx start --dry-run
```

Optional package install for environments with `setuptools` available:

```powershell
python -m pip install -e .
agentproxyx doctor
```

## Security Model

AgentProxyX is a defense-in-depth development tool, not a formal sandbox in the first release. The MVP blocks and redacts risky data at the proxy/tool-call layer. For untrusted code execution, use OS-level isolation today and follow the WASI runner roadmap for future releases.

## License

MIT
