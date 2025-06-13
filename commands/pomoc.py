import discord
from discord.ext import commands
from discord import app_commands

class Pomoc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="pomoc", description="Wyświetla listę komend lub szczegóły")
    @app_commands.describe(komenda="(opcjonalnie) Nazwa komendy, np. 'teams'")
    async def pomoc(self, interaction: discord.Interaction, komenda: str = None):
        if not komenda:
            text = (
                "**📘 Lista komend:**\n"
                "`/link` – Połączenie konta\n"
                "`/rola` – Wybór ról\n"
                "`/teams` – Tworzenie drużyn\n"
                "`/ranking` – Ranking graczy\n"
                "`/pomoc [komenda]` – Szczegóły komendy"
            )
            await interaction.response.send_message(text, ephemeral=True)
        elif komenda.lower() == "teams":
            await interaction.response.send_message(
                "**/teams (voice/manual)**\n"
                "- `voice`: bierze osoby z kanału głosowego\n"
                "- `manual`: wpisujesz ID lub oznaczasz osoby ręcznie", ephemeral=True)
        else:
            await interaction.response.send_message("❓ Nie znam tej komendy.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Pomoc(bot))
