import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHANNEL_ID = os.getenv("CHANNEL_ID", "")
ALLOWED_USERS = os.getenv("ALLOWED_USERS", "").split(",")
ADMIN_USERS = os.getenv("ADMIN_USERS", "").split(",")

TRADING_HOURS_START = "09:00"
TRADING_HOURS_END = "16:00"
TIMEZONE = "Asia/Jakarta"
DEFAULT_INTERVAL = 15

SCREEN_COMMANDS = ["/screen", "/s"]
ANALYZE_COMMANDS = ["/analyze", "/a"]
HELP_COMMANDS = ["/help", "/h", "/start"]
