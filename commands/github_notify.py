from discord.ext import commands
from services.github_poll_service import GithubPollService

class GithubNotify(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.poller = GithubPollService(bot)

    def cog_unload(self):
        self.poller.poll_loop.cancel()

async def setup(bot):
    await bot.add_cog(GithubNotify(bot))
