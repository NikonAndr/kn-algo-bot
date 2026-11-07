import asyncio
import logging
from datetime import datetime, timedelta
from discord.ext import tasks

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

log = logging.getLogger(__name__)


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
        # discord.py permanently stops a loop on most exceptions (e.g. DNS
        # failures raise httplib2.ServerNotFoundError), so never let one escape.
        try:
            await self.poll_once()
        except Exception:
            log.exception("Calendar poll failed, retrying next cycle")

    async def poll_once(self):
        now = warsaw_now()

        # The Google client is blocking; keep it off the event loop.
        items = await asyncio.to_thread(calendar_service.list_events, now, now + timedelta(days=90))

        for item in items:
            try:
                self.sync_item(item)
            except Exception:
                log.exception("Skipping calendar event %s", item.get("id"))

    def sync_item(self, item):
        google_event_id = item["id"]
        existing = get_event_by_google_id(google_event_id)

        if item.get("status") == "cancelled":
            if existing and existing[9] != "cancelled":
                event_id = existing[0]
                mark_event_cancelled(event_id)
                cancel_reminders(event_id)

            return

        start_time = parse_event_time(item["start"])
        end_time = parse_event_time(item["end"])
        title = item.get("summary", "Untitled event")
        description = item.get("description", "")
        location = item.get("location", "")

        if not existing:
            event_id = create_event(
                google_event_id, title, description, start_time, end_time,
                event_type="google-calendar", source="calendar", created_by=None,
                location=location,
            )
            add_reminder(event_id, DEFAULT_EVENT_REMINDER_MINUTES, start_time - timedelta(minutes=DEFAULT_EVENT_REMINDER_MINUTES))

        elif (
            existing[2] != title
            or existing[3] != description
            or existing[4] != str(start_time)
            or (existing[10] or "") != location
        ):
            event_id = existing[0]
            start_changed = existing[4] != str(start_time)

            update_event_details(event_id, title, description, start_time, end_time, location)

            if start_changed:
                reschedule_reminders(event_id, start_time)

    @poll_loop.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()
