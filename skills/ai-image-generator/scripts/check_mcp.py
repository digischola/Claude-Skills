#!/usr/bin/env python3
"""check_mcp.py — verify Higgsfield MCP is connected and the plan tier is sufficient.

This script does NOT call MCP tools directly (Python can't invoke session-bound MCP).
Instead it prints the verification commands the user / Claude should run, and looks
for an optional `_engine/working/<entry>/mcp-status.json` written by Claude after
running `balance` in-session.

Usage:
    python3 check_mcp.py              # print verification instructions
    python3 check_mcp.py --status <working_dir>  # check the in-session status file
"""
import argparse
import json
import sys
from pathlib import Path


CONNECTOR_INSTALL = "claude mcp add --transport http higgsfield https://mcp.higgsfield.ai/mcp"
MCP_BALANCE_TOOL = "mcp__b39cf66e-63d0-49fc-a861-0eb724d588df__balance"
MIN_PLAN = "plus"  # 'free' is blocked by watermark; 'starter' too credit-starved
MIN_CREDITS = 50   # safety floor; warn if below


def print_instructions() -> int:
    print("=" * 72)
    print("Higgsfield MCP verification")
    print("=" * 72)
    print()
    print("Step 1. Confirm MCP is installed in Claude Code:")
    print(f"    {CONNECTOR_INSTALL}")
    print()
    print("Step 2. Inside Claude Code, call the balance tool:")
    print(f"    {MCP_BALANCE_TOOL}")
    print()
    print("Expected response shape:")
    print('    {"email": "...", "credits": <int>, "subscription_plan_type": "ultra"|"plus"|"starter"|"free"}')
    print()
    print(f"Hard requirements:")
    print(f"  - subscription_plan_type in {{'plus', 'ultra'}} (free is watermarked, starter too low)")
    print(f"  - credits >= {MIN_CREDITS} OR plan is 'ultra' (Ultra includes unlimited Nano Banana 2 Flash)")
    print()
    print("Once verified in-session, write the response to:")
    print("    _engine/working/<entry>/mcp-status.json")
    print()
    print("Then re-run with: python3 check_mcp.py --status <working_dir>")
    return 0


def check_status(working_dir: Path) -> int:
    status_path = working_dir / "mcp-status.json"
    if not status_path.exists():
        print(f"x mcp-status.json not found at {status_path}", file=sys.stderr)
        print(f"  Run the balance tool in-session and save the response to that path.", file=sys.stderr)
        return 1

    try:
        status = json.loads(status_path.read_text())
    except json.JSONDecodeError as e:
        print(f"x mcp-status.json is not valid JSON: {e}", file=sys.stderr)
        return 1

    email = status.get("email", "<unknown>")
    credits = status.get("credits", 0)
    plan = status.get("subscription_plan_type", "<unknown>").lower()

    print(f"  Higgsfield account: {email}")
    print(f"  Plan tier:          {plan}")
    print(f"  Credits available:  {credits}")
    print()

    fail = False
    if plan == "free":
        print("x Free tier — outputs are watermarked. Upgrade to Plus or Ultra.", file=sys.stderr)
        fail = True
    elif plan == "starter":
        print("x Starter tier too credit-starved for client work. Upgrade to Plus or Ultra.", file=sys.stderr)
        fail = True
    elif plan in {"plus", "ultra"}:
        print(f"  Plan tier OK ({plan}).")
    else:
        print(f"!  Unknown plan tier '{plan}'. Proceeding cautiously.")

    if plan == "ultra":
        print(f"  Ultra plan — Nano Banana 2 Flash is UNLIMITED. Default tier costs 0 credits.")
    elif credits < MIN_CREDITS:
        print(f"x Credits ({credits}) below safety floor ({MIN_CREDITS}). Top up before running.", file=sys.stderr)
        fail = True
    else:
        print(f"  Credits OK ({credits} >= {MIN_CREDITS}).")

    return 1 if fail else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", help="Path to working dir containing mcp-status.json")
    args = ap.parse_args()

    if args.status:
        return check_status(Path(args.status))
    return print_instructions()


if __name__ == "__main__":
    sys.exit(main())
