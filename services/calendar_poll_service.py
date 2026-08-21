from datetime import datetime, timedelta
from discord.ext import tasks
from googleapiclient.errors import HttpError

from config import DEFAULT_EVENT_REMINDER_MINUTES
from database.events import (
    get_event_by_google_id,
    create_event,
    update_event_details,
    mark_event_cancelled,
    add_reminder,
    reschedule_reminders,
    cancel_reminders,
)
from services import calendar_service
from utils.time_helpers import warsaw_now, to_warsaw_naive


def parse_event_time(value):
    if "dateTime" in value:
        return to_warsaw_naive(datetime.fromisoformat(value["dateTime"]))

    return datetime.fromisoformat(value["date"])


class CalendarPollService:

    def __init__(self, bot):
        self.bot = bot
        self.poll_loop.start()

    def cog_unload(self):
        self.poll_loop.cancel()

    @tasks.loop(seconds=120)
    async def poll_loop(self):

        now = warsaw_now()

        try:
            items = calendar_service.list_events(now, now + timedelta(days=90))
        except HttpError as error:
            print(f"Calendar poll skipped, couldn't reach Google Calendar: {error}")
            return

        for item in items:
            google_event_id = item["id"]
            existing = get_event_by_google_id(google_event_id)

            if item.get("status") == "cancelled":
                if existing and existing[9] != "cancelled":
                    event_id = existing[0]
                    mark_event_cancelled(event_id)
                    cancel_reminders(event_id)

                continue

            start_time = parse_event_time(item["start"])
            end_time = parse_event_time(item["end"])
            title = item.get("summary", "Untitled event")
            description = item.get("description", "")

            if not existing:
                event_id = create_event(
                    google_event_id, title, description, start_time, end_time,
                    event_type="other", source="calendar", created_by=None
                )
                add_reminder(event_id, DEFAULT_EVENT_REMINDER_MINUTES, start_time - timedelta(minutes=DEFAULT_EVENT_REMINDER_MINUTES))

            elif existing[2] != title or existing[3] != description or existing[4] != str(start_time):
                event_id = existing[0]
                start_changed = existing[4] != str(start_time)

                update_event_details(event_id, title, description, start_time, end_time)

                if start_changed:
                    reschedule_reminders(event_id, start_time)

    @poll_loop.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()
