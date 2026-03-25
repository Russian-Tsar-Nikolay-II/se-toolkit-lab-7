import sys
from handlers import commands

COMMANDS = {
    "/start": commands.start_handler,
    "/help": commands.help_handler,
    "/health": commands.health_handler,
    "/labs": commands.labs_handler,
    "/scores": commands.scores_handler,
}


def run_test_mode():
    if len(sys.argv) < 3:
        print('Usage: uv run bot.py --test "/command [arg]"')
        sys.exit(1)

    cmd = sys.argv[2]
    parts = cmd.strip().split(maxsplit=1)
    command = parts[0]
    arg = parts[1] if len(parts) > 1 else None

    handler = COMMANDS.get(command)
    if not handler:
        print(f"Unknown command '{command}'. Try /help")
        return

    if command == "/scores":
        print(handler(arg))
    else:
        print(handler())

if __name__ == "__main__":
    if "--test" in sys.argv:
        run_test_mode()
