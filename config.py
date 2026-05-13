import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ["BOT_TOKEN"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///kontrlve.db")

PERFORMANCE_TIMEOUT = 180  # seconds
HAIKU_MODEL = "claude-haiku-4-5-20251001"
