# Security Policy

AgentProxyX is a local developer-security tool. Please do not open public issues for vulnerabilities that include exploitable details.

## Reporting

Send a private report through GitHub Security Advisories when available, or contact the maintainer directly.

Include:

- affected version or commit;
- reproduction steps;
- expected impact;
- whether a secret, token, or local file could be exposed.

## Scope

In scope:

- secret redaction bypasses;
- firewall bypasses for dangerous commands or protected files;
- unintended outbound forwarding of redacted data;
- dashboard exposure outside localhost.

Out of scope for the first MVP:

- full OS sandbox escape claims, because `0.1.x` is not marketed as a formal sandbox;
- attacks that require local administrator access;
- issues caused by intentionally disabling default rules.

