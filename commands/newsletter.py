import typing

from discord.ext import commands
from database.subscribers import add_subscriber, remove_subscriber, get_subscribers
from utils.validators import is_valid_email
from utils import checks
from services.email_service import send_bulk_email

class Newsletter(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command()
    async def subscribe(self, ctx, email: str, list_type: typing.Literal["newsletter", "weekly_notes"] = "newsletter"):

        if not is_valid_email(email):
            await ctx.send("Invalid email address")
            return

        if list_type not in ("newsletter", "weekly_notes"):
            await ctx.send("Invalid list. Use: newsletter or weekly_notes")
            return

        success = add_subscriber(email, list_type)

        if success:
            await ctx.send(f"{email} has been added to the {list_type} list")
        else:
            await ctx.send(f"{email} already exists in the database")

    @commands.hybrid_command()
    async def unsubscribe(self, ctx, email: str, list_type: typing.Literal["newsletter", "weekly_notes"] = "newsletter"):

        success = remove_subscriber(email, list_type)

        if success:
            await ctx.send(f"{email} has been removed from the {list_type} list")
        else:
            await ctx.send(f"{email} does not exist in the database")

    @commands.hybrid_command()
    async def subscribers(self, ctx):

        newsletter = get_subscribers("newsletter")
        weekly_notes = get_subscribers("weekly_notes")

        await ctx.send(f"Subscribers\nNewsletter: {len(newsletter)}\nWeekly Notes: {len(weekly_notes)}")

    @commands.hybrid_command()
    async def send_newsletter(self, ctx, title: str, message: str):

        emails = get_subscribers("newsletter")

        send_bulk_email(emails, title, message)

        await ctx.send("Newsletter sent successfully!")

        
async def setup(bot):
    await bot.add_cog(Newsletter(bot))