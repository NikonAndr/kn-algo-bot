import discord 
from discord.ext import commands
import asyncio
import logging
import os
from config import TOKEN
from database.db import init_db
from utils.logging_setup import setup_logging

log = logging.getLogger("bot")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(
    command_prefix="!", intents=intents, help_command=None,
    allowed_mentions=discord.AllowedMentions(everyone=False)
)

@bot.event
async def on_ready():
    log.info("Logged in as %s", bot.user)

    for guild in bot.guilds:
        bot.tree.copy_global_to(guild=guild)
        await bot.tree.sync(guild=guild)

@bot.event
async def on_message(message):
    pass

@bot.event
async def on_command_error(ctx, error):
    log.error("Command error in %s: %s", ctx.command, error, exc_info=error)
    await ctx.send(f"⚠️ Error: {error}")

async def main():

    setup_logging()
    init_db()

    async with bot:

        for file in os.listdir("./commands"):

            if file.endswith(".py"):

                await bot.load_extension(f"commands.{file[:-3]}")

        await bot.start(TOKEN)

asyncio.run(main())