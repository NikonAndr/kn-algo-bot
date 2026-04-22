from discord.ext import commands
from utils import checks

class Ping(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @checks.notes_manager_only()
    async def ping(self, ctx):
        await ctx.send("Pong!")

async def setup(bot):
    await bot.add_cog(Ping(bot))