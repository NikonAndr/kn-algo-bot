import discord
import os
import random
from discord.ext import commands
from utils import checks

MEMES_DIR = "memes"
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".webp")

class Meme(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(description="Posts a random meme")
    @checks.member_only()
    async def meme(self, ctx):
        memes = [f for f in os.listdir(MEMES_DIR) if f.lower().endswith(IMAGE_EXTENSIONS)]

        if not memes:
            await ctx.send("No memes in the catalog yet.", ephemeral=True)
            return

        chosen = random.choice(memes)
        await ctx.send(file=discord.File(os.path.join(MEMES_DIR, chosen)))

async def setup(bot):
    await bot.add_cog(Meme(bot))
