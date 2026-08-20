import discord
from discord.ext import commands
from database.subscribers import add_subscriber, remove_subscriber, get_subscribers
from utils.validators import is_valid_email
from utils import checks

class SelfCleaningView(discord.ui.View):

    def __init__(self, timeout):
        super().__init__(timeout=timeout)
        self.message = None

    async def on_timeout(self):

        if self.message:
            try:
                await self.message.delete()
            except discord.NotFound:
                pass

class Subscribers(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(description="Subscribe an email to the weekly notes list")
    @checks.bot_admin_only()
    async def subscribe(self, ctx, email: str):

        if not is_valid_email(email):
            view = SelfCleaningView(timeout=120)
            sent_message = await ctx.send("Invalid email address", ephemeral=True, view=view)
            view.message = sent_message
            return

        success = add_subscriber(email)

        message = f"{email} has been added to the weekly notes list" if success else f"{email} already exists in the database"

        view = SelfCleaningView(timeout=120)
        sent_message = await ctx.send(message, ephemeral=True, view=view)
        view.message = sent_message

    @commands.hybrid_command(description="Unsubscribe an email from the weekly notes list")
    @checks.bot_admin_only()
    async def unsubscribe(self, ctx, email: str):

        success = remove_subscriber(email)

        message = f"{email} has been removed from the weekly notes list" if success else f"{email} does not exist in the database"

        view = SelfCleaningView(timeout=120)
        sent_message = await ctx.send(message, ephemeral=True, view=view)
        view.message = sent_message

    @commands.hybrid_command(description="Lists everyone subscribed to weekly notes")
    @checks.bot_admin_only()
    async def subscribers(self, ctx):

        emails = get_subscribers()

        message = "No subscribers yet." if not emails else "Subscribers\n" + "\n".join(f"- {email}" for email in emails)

        view = SelfCleaningView(timeout=120)
        sent_message = await ctx.send(message, ephemeral=True, view=view)
        view.message = sent_message

async def setup(bot):
    await bot.add_cog(Subscribers(bot))
