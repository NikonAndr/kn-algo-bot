import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

BOT_ADMIN_ROLE_ID = os.getenv("BOT_ADMIN_ROLE_ID")
TEAM_LEAD_ROLE_ID = os.getenv("TEAM_LEAD_ROLE_ID")
MEMBER_ROLE_ID = os.getenv("MEMBER_ROLE_ID")

WEEKLY_SEND_INTERVAL_MINUTES = int(os.getenv("WEEKLY_SEND_INTERVAL_MINUTES", str(7 * 24 * 60)))

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GH_UPDATES_CHANNEL_ID = os.getenv("GH_UPDATES_CHANNEL_ID")
GITHUB_TRACKED_REPOS = [
    repo.strip() for repo in os.getenv("GITHUB_TRACKED_REPOS", "").split(",") if repo.strip()
]

GOOGLE_SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "credentials/google-service-account.json")
GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID")
CALENDAR_UPDATES_CHANNEL_ID = os.getenv("CALENDAR_UPDATES_CHANNEL_ID")
DEFAULT_EVENT_REMINDER_MINUTES = int(os.getenv("DEFAULT_EVENT_REMINDER_MINUTES", "60"))
