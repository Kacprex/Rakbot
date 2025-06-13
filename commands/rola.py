import discord
from discord.ext import commands
from discord import app_commands
from utils import load_data, save_data

class Rola(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="rola", description="Zmień przypisane role")
    async def rola(self, interaction: discord.Interaction):
        data = load_data()
        user_id = str(interaction.user.id)

        if user_id not in data:
            await interaction.response.send_message("❌ Najpierw połącz konto: `/link`", ephemeral=True)
            return

        class RoleSelect(discord.ui.Select):
            def __init__(self):
                roles = ["TOP", "JUNGLE", "MID", "ADC", "SUPPORT"]
                options = [discord.SelectOption(label=role) for role in roles]
                super().__init__(placeholder="Wybierz min. 2 role", min_values=2, max_values=5, options=options)

            async def callback(inner_self, interaction_):
                data[user_id]["roles"] = inner_self.values
                save_data(data)
                await interaction_.response.send_message(f"✅ Zapisano: {', '.join(inner_self.values)}", ephemeral=True)

        view = discord.ui.View()
        view.add_item(RoleSelect())
        await interaction.response.send_message("🎯 Wybierz swoje role:", view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Rola(bot))
