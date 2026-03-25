#!/usr/bin/env python3
import sys
import os
import asyncio

env_path = os.path.join(os.path.dirname(__file__), "..", ".env.docker.secret")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            if "=" in line and not line.strip().startswith("#"):
                key, value = line.strip().split("=", 1)
                os.environ[key] = value

from handlers.commands import (
    handle_start,
    handle_help,
    handle_health,
    handle_labs,
    handle_scores,
)

COMMANDS = {
    "/start": handle_start,
    "/help": handle_help,
    "/health": handle_health,
    "/labs": handle_labs,
    "/scores": handle_scores,
}

async def run_command(cmd: str):
    parts = cmd.strip().split()
    cmd_name = parts[0]
    args = parts[1:] if len(parts) > 1 else None
    if cmd_name not in COMMANDS:
        return "Unknown command. Use /help to see available commands."
    handler = COMMANDS[cmd_name]
    return await handler(args)

def main():
    if "--test" in sys.argv:
        idx = sys.argv.index("--test")
        if idx + 1 < len(sys.argv):
            cmd = sys.argv[idx + 1]
            result = asyncio.run(run_command(cmd))
            print(result)
            return
    print("LMS Bot running. Use --test <command> to test.")

if __name__ == "__main__":
    main()
