import json
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

        if CALENDAR_UPDATES_CHANNEL_ID:
            channel = self.bot.get_channel(int(CALENDAR_UPDATES_CHANNEL_ID))
            now = warsaw_now()

            for reminder_id, offset_minutes, title, start_time, exec_time in get_due_reminders():
                if is_within_grace(now, parse_naive_timestamp(exec_time)) and channel:
                    role_mention = f"<@&{MEMBER_ROLE_ID}> " if MEMBER_ROLE_ID else ""
                    formatted_start = parse_naive_timestamp(start_time).strftime("%d %b %H:%M")
                    await channel.send(
                        f"{role_mention}⏰ Reminder: **{title}** starts in {format_offset(offset_minutes)}! ({formatted_start})"
                    )

                mark_reminder_sent(reminder_id)

        tasks = get_due_tasks()

        for task_id, task_type, payload in tasks:
            payload = json.loads(payload)

            if task_type == "send_message":
                channel = self.bot.get_channel(payload["channel_id"])

                if channel:
                    await channel.send(payload["message"])

            elif task_type == "send_weekly_notes":
                notes = notes_service.get_notes_to_send()

                if notes:
                    recipients = get_subscribers()
                    email_service.send_weekly_notes(recipients, notes)
                    notes_service.mark_notes_sent(notes)

                add_task("send_weekly_notes", {}, next_weekly_send_time())

            mark_task_done(task_id)

    @scheduler_loop.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()

