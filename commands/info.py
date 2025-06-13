import discord
from discord.ext import commands

class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="info", description="Informacje o bocie i Riot Games")
    async def info(self, interaction: discord.Interaction):
        disclaimer = (
            "**Ten bot nie jest zatwierdzony przez Riot Games i nie odzwierciedla ich poglądów.**\n"
            "League of Legends oraz wszystkie powiązane znaki towarowe są własnością Riot Games, Inc."
        )
        await interaction.response.send_message(disclaimer, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Info(bot))
