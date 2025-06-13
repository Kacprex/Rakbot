import discord
from discord.ext import commands

class Stop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="stop", description="Wyłącza bota (tylko właściciel)")
    async def stop(self, interaction: discord.Interaction):
        owner_id = 1146593849523851285  # Twój ID
        if interaction.user.id != owner_id:
            await interaction.response.send_message("⛔ Brak uprawnień.", ephemeral=True)
            return
        await interaction.response.send_message("🛑 Bot zamykany...", ephemeral=True)
        await self.bot.close()

async def setup(bot: commands.Bot):
    await bot.add_cog(Stop(bot))
