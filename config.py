import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

BOT_ADMIN_ROLE_ID = os.getenv("BOT_ADMIN_ROLE_ID")
BOT_NOTES_ROLE_ID = os.getenv("BOT_NOTES_ROLE_ID")
MEMBER_ROLE_ID = os.getenv("MEMBER_ROLE_ID")

WEEKLY_SEND_INTERVAL_MINUTES = int(os.getenv("WEEKLY_SEND_INTERVAL_MINUTES", str(7 * 24 * 60)))
