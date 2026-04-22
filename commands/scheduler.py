from discord.ext import commands
from services.scheduler_service import SchedulerService

from datetime import datetime, timedelta
from database.scheduled_tasks import add_task

class Scheduler(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.scheduler = SchedulerService(bot)

    @commands.command()
    async def schedule_test(self, ctx):
        run_time = datetime.utcnow() + timedelta(minutes=1)

        payload = {
            "channel_id": ctx.channel.id,
            "message": "⏰ Scheduler działa!"
        }

        add_task("send_message", payload, run_time)

        await ctx.send("Zaplanowano wiadomość za minutę")

async def setup(bot):
    await bot.add_cog(Scheduler(bot))
