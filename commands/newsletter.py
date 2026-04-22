from discord.ext import commands
from database.subscribers import add_subscriber, remove_subscriber, get_subscribers
from utils.validators import is_valid_email
from utils import checks
from services.email_service import send_bulk_email

class Newsletter(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def subscribe(self, ctx, email: str):

        if not is_valid_email(email):
            await ctx.send("Niepoprawny Adres Email")
            return

        success = add_subscriber(email)

        if success:
            await ctx.send(f"{email} został zapisany do Przypominania o Eventach")
        else:
            await ctx.send(f"{email} juź instnieje w bazie")

    @commands.command()
    async def unsubscribe(self, ctx, email: str):

        success = remove_subscriber(email)

        if success:
            await ctx.send(f"{email} został usunięty z bazy Przypominania o Eventach")
        else:
            await ctx.send(f"{email} nie istnieje w bazie")

    @commands.command()
    async def subscribers(self, ctx):

        newsletter = get_subscribers("newsletter")
        weekly_notes = get_subscribers("weekly_notes")

        await ctx.send(f"Subscribers\nNewsletter: {len(newsletter)}\nWeekly Notes: {len(weekly_notes)}")

    @commands.command()
    async def send_newsletter(self, ctx, title: str, message: str):

        emails = get_subscribers("newsletter")

        for email in emails:
            send_bulk_email(email, title, message)
        
        await ctx.send("Newsletter pomyślnie wysłany!")

        
async def setup(bot):
    await bot.add_cog(Newsletter(bot))