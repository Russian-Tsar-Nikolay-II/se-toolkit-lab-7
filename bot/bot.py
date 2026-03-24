import argparse
from handlers import start_handler, help_handler, health_handler

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", type=str, help="Run command in test mode")
    args = parser.parse_args()

    if args.test:
        cmd = args.test.lower()
        if cmd == "/start":
            print(start_handler())
        elif cmd == "/help":
            print(help_handler())
        elif cmd == "/health":
            print(health_handler())
        else:
            print(f"Command '{args.test}' not implemented yet")
        exit(0)

if __name__ == "__main__":
    main()