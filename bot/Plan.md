Create a bot that works in Telegram and in test mode on a computer without an Internet connection. The test mode is needed to check commands and responses without connecting to Telegram. Main file: bot.py — entry point. Runs the bot in normal mode and in test mode (--test).

Command handlers: The handlers/ folder stores all commands. Each command (/start, /help, /health, etc.) has a separate function. The functions receive input data and return a response, regardless of Telegram. At first, the teams use stubs, and later they connect to real services.

Services and APIs: The services/ folder stores clients of external systems (for example, LMS and LLM). It makes it easy to expand functionality and add new integrations.

Settings and Dependencies: Settings are stored in .env.bot.secret and read via config.py . Dependencies are managed via pyproject.toml to make the project easy to run and update.

Advantages of the structure: It is easy to test commands without Telegram. Easy addition of new handlers and services. It is convenient to integrate with CI/CD systems for automatic assembly and deployment.