import discord
from discord.ext import commands
from services import horoscope_service

ZODIAC_SIGNS = [
    ("Aries", "♈"),
    ("Taurus", "♉"),
    ("Gemini", "♊"),
    ("Cancer", "♋"),
    ("Leo", "♌"),
    ("Virgo", "♍"),
    ("Libra", "♎"),
    ("Scorpio", "♏"),
    ("Sagittarius", "♐"),
    ("Capricorn", "♑"),
    ("Aquarius", "♒"),
    ("Pisces", "♓"),
]

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

class ZodiacSelect(discord.ui.Select):

    def __init__(self):
        options = [
            discord.SelectOption(label=name, emoji=emoji, value=name)
            for name, emoji in ZODIAC_SIGNS
        ]

        super().__init__(placeholder="Pick your zodiac sign", options=options)

    async def callback(self, interaction: discord.Interaction):

        sign = self.values[0]

        await interaction.response.defer()

        horoscope = await horoscope_service.get_daily_horoscope(sign)

        cleanup_view = SelfCleaningView(timeout=180)
        await interaction.edit_original_response(
            content=f"**{sign}** ✨\n{horoscope}",
            view=cleanup_view
        )
        cleanup_view.message = interaction.message
        self.view.stop()

class ZodiacView(SelfCleaningView):

    def __init__(self):
        super().__init__(timeout=120)
        self.add_item(ZodiacSelect())

class Horoscope(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(description="Get your daily horoscope")
    async def horoscope(self, ctx):
        view = ZodiacView()
        sent_message = await ctx.send("Pick your zodiac sign:", view=view, ephemeral=True)
        view.message = sent_message

async def setup(bot):
    await bot.add_cog(Horoscope(bot))
