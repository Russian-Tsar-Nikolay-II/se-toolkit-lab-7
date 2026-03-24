import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env.bot.secret if exists
env_path = Path(__file__).parent / ".env.bot.secret"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

LMS_API_BASE_URL = os.getenv("LMS_API_BASE_URL", "")
LMS_API_KEY = os.getenv("LMS_API_KEY", "")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
