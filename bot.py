import discord 
from discord.ext import commands
import asyncio
import os
from config import TOKEN
from database.db import init_db

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    for guild in bot.guilds:
        bot.tree.copy_global_to(guild=guild)
        await bot.tree.sync(guild=guild)

@bot.event
async def on_message(message):
    pass

@bot.event
async def on_command_error(ctx, error):
    print(f"Command error in {ctx.command}: {error}")
    await ctx.send(f"⚠️ Error: {error}")

async def main():

    init_db()

    async with bot:

        for file in os.listdir("./commands"):

            if file.endswith(".py"):

                await bot.load_extension(f"commands.{file[:-3]}")

        await bot.start(TOKEN)

asyncio.run(main())