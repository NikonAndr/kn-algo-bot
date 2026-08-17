import json
from datetime import timedelta
from discord.ext import tasks

from config import WEEKLY_SEND_INTERVAL_MINUTES
from database.scheduled_tasks import (
    add_task,
    get_due_tasks,
    has_pending_task,
    mark_task_done,
)
from database.subscribers import get_subscribers
from services import email_service, notes_service
from utils.time_helpers import warsaw_now


def next_weekly_send_time():
    return warsaw_now() + timedelta(minutes=WEEKLY_SEND_INTERVAL_MINUTES)


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
                    recipients = get_subscribers("weekly_notes")
                    email_service.send_weekly_notes(recipients, notes)
                    notes_service.mark_notes_sent(notes)

                add_task("send_weekly_notes", {}, next_weekly_send_time())

            mark_task_done(task_id)

    @scheduler_loop.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()

