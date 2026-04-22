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
    print(f"Zalogowano jako {bot.user}")

async def main():

    init_db()

    async with bot:

        for file in os.listdir("./commands"):

            if file.endswith(".py"):

                await bot.load_extension(f"commands.{file[:-3]}")

        await bot.start(TOKEN)

asyncio.run(main())