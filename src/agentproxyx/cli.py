from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .agents import get_preset, presets
from .config import load_config, write_default_config
from .dashboard import DashboardServer
from .firewall import AgentFirewall
from .mcp import wrap_mcp_server
from .proxy import AgentProxyServer
from .replay import ReplayStore
from .secrets import find_secrets


def _print_env(agent: str, port: int) -> None:
    preset = get_preset(agent, port)
    print(f"# {preset.name}")
    print(f"# {preset.notes}")
    for key, value in preset.env.items():
        print(f"{key}={value}")
    print(f"# Launch hint: {preset.launch_hint}")


def cmd_agents(args: argparse.Namespace) -> int:
    for preset in presets(args.port).values():
        flag = "experimental" if preset.experimental else "ready"
        print(f"{preset.key:24} {flag:12} {preset.name} ({preset.category})")
    return 0


def cmd_env(args: argparse.Namespace) -> int:
    _print_env(args.agent, args.port)
    return 0


def cmd_init(args: argparse.Namespace) -> int:
    target = write_default_config(args.path)
    print(f"Wrote default config: {target}")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    print(f"AgentProxyX {__version__}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Config: {'custom' if args.config else 'built-in default'}")
    cfg = load_config(args.config)
    print(f"Firewall default: {cfg['firewall'].get('default_tool_action', 'allow')}")
    print("Status: ready")
    return 0


def cmd_scan(args: argparse.Namespace) -> int:
    text = Path(args.file).read_text(encoding="utf-8", errors="replace") if args.file else args.text
    findings = find_secrets(text or "")
    if not findings:
        print("No obvious secrets found.")
        return 0
    for finding in findings:
        print(f"{finding.confidence.upper():8} {finding.kind} at {finding.start}:{finding.end}")
    return 2 if args.fail_on_findings else 0


def cmd_firewall(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    firewall = AgentFirewall(cfg)
    payload = {"command": args.command, "files": args.file or []}
    decision = firewall.check_tool_call(payload)
    print(json.dumps({"allowed": decision.allowed, "reason": decision.reason, "matches": decision.matches}, indent=2))
    return 0 if decision.allowed else 3


def cmd_mcp_wrap(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    firewall = AgentFirewall(cfg)
    store = ReplayStore(args.replay_db)
    return wrap_mcp_server(args.command, firewall, store, agent=args.agent)


def cmd_start(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    store = ReplayStore(args.replay_db)
    dashboard = DashboardServer(store, port=args.dashboard_port)
    dashboard.start_background()

    print(f"AgentProxyX {__version__}")
    print(f"Agent: {args.agent}")
    print(f"Proxy: http://127.0.0.1:{args.port}")
    print(f"Dashboard: http://127.0.0.1:{args.dashboard_port}")
    print(f"Mode: {'dry-run' if args.dry_run else 'forward'}")
    if args.target:
        print(f"Target: {args.target}")
    print("")
    _print_env(args.agent, args.port)
    print("")
    print("Press Ctrl+C to stop.")

    proxy = AgentProxyServer(
        config=cfg,
        store=store,
        agent=args.agent,
        target=args.target,
        port=args.port,
        dry_run=args.dry_run,
    )
    try:
        proxy.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped AgentProxyX.")
        return 0
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agentproxyx", description="Local security and cost-control gateway for AI coding agents.")
    parser.add_argument("--version", action="version", version=f"AgentProxyX {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    agents_parser = sub.add_parser("agents", help="List supported agent presets.")
    agents_parser.add_argument("--port", type=int, default=8080)
    agents_parser.set_defaults(func=cmd_agents)

    env_parser = sub.add_parser("env", help="Print environment variables for an agent preset.")
    env_parser.add_argument("--agent", default="claude-code")
    env_parser.add_argument("--port", type=int, default=8080)
    env_parser.set_defaults(func=cmd_env)

    init_parser = sub.add_parser("init", help="Write a default JSON config.")
    init_parser.add_argument("--path", default="agentproxyx.json")
    init_parser.set_defaults(func=cmd_init)

    doctor_parser = sub.add_parser("doctor", help="Check local runtime readiness.")
    doctor_parser.add_argument("--config")
    doctor_parser.set_defaults(func=cmd_doctor)

    scan_parser = sub.add_parser("scan", help="Scan text or a file for secrets.")
    scan_source = scan_parser.add_mutually_exclusive_group(required=True)
    scan_source.add_argument("--text")
    scan_source.add_argument("--file")
    scan_parser.add_argument("--fail-on-findings", action="store_true")
    scan_parser.set_defaults(func=cmd_scan)

    firewall_parser = sub.add_parser("firewall", help="Evaluate a command/files against the agent firewall.")
    firewall_parser.add_argument("--config")
    firewall_parser.add_argument("--command")
    firewall_parser.add_argument("--file", action="append")
    firewall_parser.set_defaults(func=cmd_firewall)

    mcp_parser = sub.add_parser("mcp", help="MCP server wrapper commands.")
    mcp_sub = mcp_parser.add_subparsers(dest="mcp_command", required=True)
    mcp_wrap_parser = mcp_sub.add_parser("wrap", help="Wrap a stdio MCP server and firewall tools/call requests.")
    mcp_wrap_parser.add_argument("--agent", default="mcp")
    mcp_wrap_parser.add_argument("--config")
    mcp_wrap_parser.add_argument("--replay-db", default=".agentproxyx/replay.sqlite")
    mcp_wrap_parser.add_argument("command", nargs=argparse.REMAINDER, help="MCP server command after --")
    mcp_wrap_parser.set_defaults(func=cmd_mcp_wrap)

    start_parser = sub.add_parser("start", help="Start the local proxy and replay dashboard.")
    start_parser.add_argument("--agent", default="claude-code")
    start_parser.add_argument("--config")
    start_parser.add_argument("--port", type=int, default=8080)
    start_parser.add_argument("--dashboard-port", type=int, default=7778)
    start_parser.add_argument("--target", help="Upstream provider URL, for example https://api.anthropic.com")
    start_parser.add_argument("--dry-run", action="store_true", help="Do not forward requests; return inspection reports.")
    start_parser.add_argument("--replay-db", default=".agentproxyx/replay.sqlite")
    start_parser.set_defaults(func=cmd_start)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except ValueError as exc:
        parser.error(str(exc))
        return 2

