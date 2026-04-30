#!/usr/bin/env python3
"""check_mcp.py — verify Higgsfield MCP connector is registered with Claude Code.

Exits 0 if connected, 1 otherwise. Step 1 of the ai-video-generator pipeline calls
this and aborts loud with setup instructions if the MCP is missing.
"""
import json
import subprocess
import sys
from pathlib import Path

SETUP_DOC = Path(__file__).parent.parent / "references" / "mcp-setup.md"


def check_via_cli() -> tuple[bool, str]:
    """Use `claude mcp list` to see registered connectors."""
    try:
        out = subprocess.run(
            ["claude", "mcp", "list"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except FileNotFoundError:
        return False, "claude CLI not found on PATH"
    except subprocess.TimeoutExpired:
        return False, "claude mcp list timed out"

    text = (out.stdout or "") + (out.stderr or "")
    if "higgsfield" in text.lower() or "mcp.higgsfield.ai" in text.lower():
        return True, text.strip()
    return False, text.strip()


def main() -> int:
    connected, info = check_via_cli()
    if connected:
        print("✓ Higgsfield MCP connected")
        print(info)
        return 0

    print("✗ Higgsfield MCP NOT connected")
    print()
    print("Install it with:")
    print("  claude mcp add --transport http higgsfield https://mcp.higgsfield.ai/mcp")
    print()
    print(f"Full setup: {SETUP_DOC}")
    if info:
        print()
        print("--- claude mcp list output ---")
        print(info)
    return 1


if __name__ == "__main__":
    sys.exit(main())
