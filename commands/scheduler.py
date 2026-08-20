from discord.ext import commands
from services.scheduler_service import SchedulerService

class Scheduler(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.scheduler = SchedulerService(bot)

async def setup(bot):
    await bot.add_cog(Scheduler(bot))
