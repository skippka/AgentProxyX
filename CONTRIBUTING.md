# Contributing

Thanks for helping make AgentProxyX sharper.

## Development Setup

```powershell
python -m unittest discover -s tests
python -m agentproxyx doctor
python -m agentproxyx start --agent claude-code --dry-run
```

The project intentionally has no required runtime dependencies in the first release.

## Good First Contributions

- Add an agent preset in `src/agentproxyx/agents.py`.
- Add a secret pattern in `src/agentproxyx/secrets.py`.
- Add a firewall fixture in `tests/test_firewall.py`.
- Improve dashboard rendering in `src/agentproxyx/web`.

## Pull Request Checklist

- Add or update tests.
- Keep default behavior local-first and safe.
- Avoid adding required dependencies unless they unlock a clear product capability.
- Update README examples when CLI behavior changes.

