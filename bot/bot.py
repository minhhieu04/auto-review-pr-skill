#!/usr/bin/env python3
"""
🤖 PR-Agent & Antigravity Automated Review Bot
Supports:
  1. Polling Daemon (checks GitHub periodically for new commits)
  2. Webhook Server (receives GitHub events on /webhook)
  3. Cloudflare Tunnel (exposes local webhook to public Internet without server/IP)
  4. Manual one-off PR review
"""

import os
import sys
import json
import argparse
import threading

from state import StateManager
from review_engine import ReviewEngine
from polling_daemon import PollingDaemon
from webhook_server import start_webhook_server
from tunnel_manager import CloudflareTunnel

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot_config.json")

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "org": "deveop-com",
        "monitored_repos": ["deveop-com/clickessms_be", "deveop-com/clickessms_fe"],
        "poll_interval_seconds": 60,
        "webhook": {"port": 8765},
        "supported_commands": ["/review", "/improve", "/describe", "/ask"]
    }

def resolve_repo(repo_input: Optional[str], config: dict) -> str:
    org = config.get("org", "deveop-com")
    repos_map = config.get("repos", {})

    if repo_input and "/" in repo_input:
        return repo_input
    if repo_input and repo_input in repos_map:
        return f"{org}/{repos_map[repo_input]}"

    # Auto-detect if inside a git directory
    from interactive_menu import detect_current_repo
    detected = detect_current_repo()
    if detected:
        return detected

    if repo_input:
        return f"{org}/{repo_input}"

    monitored = config.get("monitored_repos", [])
    if monitored:
        return monitored[0]
    return f"{org}/clickessms_be"

def main():
    parser = argparse.ArgumentParser(description="Automated PR Code Review Bot")
    parser.add_argument("--mode", choices=["poll", "webhook", "both"], default=None,
                        help="Mode to run: poll (daemon), webhook (server), or both")
    parser.add_argument("--tunnel", action="store_true",
                        help="Start Cloudflare Tunnel to expose webhook server publicly")
    parser.add_argument("--port", type=int, default=None,
                        help="Port for webhook server (default: 8765)")
    parser.add_argument("--interval", type=int, default=None,
                        help="Polling interval in seconds (default: 60)")
    parser.add_argument("--pr", type=int, default=None,
                        help="Run manual review on a specific PR number and exit")
    parser.add_argument("--repo", type=str, default="be",
                        help="Repository key ('be', 'fe') or full name ('deveop-com/clickessms_be')")
    parser.add_argument("--menu", action="store_true",
                        help="Launch interactive PR review dashboard menu")

    args = parser.parse_args()
    config = load_config()

    state = StateManager()
    engine = ReviewEngine(state_manager=state)

    # Manual one-off run
    if args.pr:
        target_repo = resolve_repo(args.repo, config)
        print(f"🎯 Running manual review on {target_repo} PR #{args.pr}")
        engine.execute_review(target_repo, args.pr)
        sys.exit(0)

    # Interactive menu if no mode specified or --menu flag
    if args.menu or (args.mode is None and not args.tunnel):
        from interactive_menu import run_interactive_menu
        run_interactive_menu(engine, state, config)
        sys.exit(0)

    port = args.port or config.get("webhook", {}).get("port", 8765)
    interval = args.interval or config.get("poll_interval_seconds", 60)
    repos = config.get("monitored_repos", [])

    print("\n" + "=" * 60)
    print("🤖 PR-Agent & Antigravity Automated Review Bot")
    print(f"   Mode    : {args.mode.upper()}")
    print(f"   Repos   : {', '.join(repos)}")
    print("=" * 60 + "\n")

    tunnel = None
    if args.tunnel or args.mode in ["webhook", "both"]:
        if args.tunnel:
            tunnel = CloudflareTunnel(port=port)
            tunnel.start()

    # Start Polling
    if args.mode in ["poll", "both"]:
        daemon = PollingDaemon(repos=repos, engine=engine, state_manager=state, interval=interval)
        if args.mode == "both":
            t = threading.Thread(target=daemon.start, daemon=True)
            t.start()
        else:
            daemon.start()

    # Start Webhook
    if args.mode in ["webhook", "both"]:
        try:
            start_webhook_server(port=port, engine=engine, commands=config.get("supported_commands", []))
        except KeyboardInterrupt:
            print("\n⏹️ Webhook server stopped.")
        finally:
            if tunnel:
                tunnel.stop()

if __name__ == "__main__":
    main()
