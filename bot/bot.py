import argparse
from handlers import start, help_cmd, health

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", type=str, help="Run command in test mode")
    args = parser.parse_args()

    if args.test:
        cmd = args.test.lower()
        if cmd == "/start":
            print(start.handle())
        elif cmd == "/help":
            print(help_cmd.handle())
        elif cmd == "/health":
            print(health.handle())
        else:
            print(f"Command '{args.test}' not implemented yet")
        exit(0)

    # Placeholder: Telegram startup (future)
    print("Telegram mode not implemented yet")

if __name__ == "__main__":
    main()
