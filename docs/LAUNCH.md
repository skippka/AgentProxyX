# Launch Notes

Use this short copy for GitHub, Product Hunt, Reddit, or Hacker News.

## One-liner

AgentProxyX is a local security and cost-control gateway for AI coding agents.

## Short Post

AI coding agents are powerful, but they repeatedly send huge contexts to model providers and can accidentally expose local secrets or run risky tool calls.

AgentProxyX is a Python-based local gateway for Claude Code, Codex CLI, Gemini CLI, Aider, Cursor, Cline, Roo Code, Continue.dev, OpenHands, OpenRouter-compatible tools, and more.

It provides:

- Secret Guard for API keys, private keys, tokens, cookies, database URLs, and high-entropy strings.
- Agent Firewall for blocking commands like `cat .env`, SSH key reads, and destructive shell patterns.
- Cost Meter for estimated spend and prompt-cache savings.
- Replay Dashboard for a local timeline of agent activity.

Try it:

```powershell
git clone https://github.com/skippka/AgentProxyX
cd AgentProxyX
python -m agentproxyx start --agent codex-cli --dry-run
```

