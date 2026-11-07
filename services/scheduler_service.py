import asyncio
import json
import logging
from datetime import timedelta
from discord.ext import tasks

from config import CALENDAR_UPDATES_CHANNEL_ID, MEMBER_ROLE_ID
from database.scheduled_tasks import (
    add_task,
    get_due_tasks,
    has_pending_task,
    mark_task_done,
)
from database.subscribers import get_subscribers
from database.events import get_due_reminders, mark_reminder_sent
from services import email_service, notes_service
from utils.time_helpers import warsaw_now, parse_naive_timestamp

log = logging.getLogger(__name__)


REMINDER_GRACE_MINUTES = 2


def is_within_grace(now, exec_time, grace_minutes=REMINDER_GRACE_MINUTES):
    late_by_minutes = (now - exec_time).total_seconds() / 60
    return late_by_minutes <= grace_minutes


def format_offset(offset_minutes):
    if offset_minutes % 1440 == 0:
        return f"{offset_minutes // 1440} day(s)"
    if offset_minutes % 60 == 0:
        return f"{offset_minutes // 60} hour(s)"
    return f"{offset_minutes} minute(s)"


def format_reminder(title, offset_minutes, start_time, location):
    formatted_start = parse_naive_timestamp(start_time).strftime("%d %b %H:%M")
    message = f"⏰ Reminder: **{title}** starts in {format_offset(offset_minutes)}! ({formatted_start})"

    if location:
        message += f"\n📍 {location}"

    return message


WEEKLY_SEND_WEEKDAY = 6  # Monday=0 ... Sunday=6
WEEKLY_SEND_HOUR = 18


def next_weekly_send_time():
    now = warsaw_now()
    days_until = (WEEKLY_SEND_WEEKDAY - now.weekday()) % 7
    candidate = (now + timedelta(days=days_until)).replace(hour=WEEKLY_SEND_HOUR, minute=0, second=0, microsecond=0)

    if candidate <= now:
        candidate += timedelta(days=7)

    return candidate


class SchedulerService:

    def __init__(self, bot):
        self.bot = bot
        self.ensure_weekly_task_scheduled()
        self.scheduler_loop.start()

    def cog_unload(self):
        self.scheduler_loop.cancel()

    def ensure_weekly_task_scheduled(self):
        if not has_pending_task("send_weekly_notes"):
            add_task("send_weekly_notes", {}, next_weekly_send_time())

    @tasks.loop(seconds=30)
    async def scheduler_loop(self):
        # An exception escaping here would stop reminders and digests for good
        # (or, for OSErrors, make discord.py re-run already-sent work).
        try:
            await self.send_due_reminders()
            await self.run_due_tasks()
        except Exception:
            log.exception("Scheduler tick failed, retrying next cycle")

    async def send_due_reminders(self):
        if not CALENDAR_UPDATES_CHANNEL_ID:
            return

        channel = self.bot.get_channel(int(CALENDAR_UPDATES_CHANNEL_ID))
        now = warsaw_now()

        for reminder_id, offset_minutes, title, start_time, exec_time, location in get_due_reminders():
            try:
                if is_within_grace(now, parse_naive_timestamp(exec_time)) and channel:
                    role_mention = f"<@&{MEMBER_ROLE_ID}> " if MEMBER_ROLE_ID else ""
                    await channel.send(role_mention + format_reminder(title, offset_minutes, start_time, location))

                mark_reminder_sent(reminder_id)
            except Exception:
                # Left unsent: retried next tick until the grace window passes.
                log.exception("Failed to send reminder %s for %r", reminder_id, title)

    async def run_due_tasks(self):
        for task_id, task_type, payload in get_due_tasks():
            try:
                await self.run_task(task_type, json.loads(payload))
            except Exception:
                log.exception("Scheduled task %s (%s) failed", task_id, task_type)
            finally:
                # Never re-run a task: a partial send would reach the same
                # people again on every retry.
                mark_task_done(task_id)

    async def run_task(self, task_type, payload):
        if task_type == "send_message":
            channel = self.bot.get_channel(payload["channel_id"])

            if channel:
                await channel.send(payload["message"])
            else:
                log.warning("send_message task: channel %s not found", payload["channel_id"])

        elif task_type == "send_weekly_notes":
            try:
                notes = notes_service.get_notes_to_send()

                if notes:
                    recipients = get_subscribers()
                    # smtplib blocks (plus 1s sleep per recipient); keep it off the event loop.
                    await asyncio.to_thread(email_service.send_weekly_notes, recipients, notes)
                    notes_service.mark_notes_sent(notes)
            finally:
                # On failure the notes stay approved and go out next week.
                add_task("send_weekly_notes", {}, next_weekly_send_time())

        else:
            log.warning("Unknown scheduled task type %r", task_type)

    @scheduler_loop.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()

