import json
from discord.ext import tasks

from database.scheduled_tasks import get_due_tasks, mark_task_done

class SchedulerService:

    def __init__(self, bot):
        self.bot = bot
        self.scheduler_loop.start()

    def cog_unload(self):
        self.scheduler_loop.cancel()

    @tasks.loop(seconds=30)
    async def scheduler_loop(self):

        tasks = get_due_tasks()

        for task_id, task_type, payload in tasks:
            payload = json.loads(payload)

            if task_type == "send_message":
                channel = self.bot.get_channel(payload["channel_id"])

                if channel:
                    await channel.send(payload["message"])

            #weekly notes ----

            
            mark_task_done(task_id)

    @scheduler_loop.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()

