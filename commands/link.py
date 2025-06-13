import discord
from discord.ext import commands
from discord import app_commands
from utils import load_data, save_data, fetch_puuid

ROLES = ["TOP", "JUNGLE", "MID", "ADC", "SUPPORT"]

class RoleSelect(discord.ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label=role, value=role) for role in ROLES]
        super().__init__(
            placeholder="Wybierz min. 2 role",
            min_values=2,
            max_values=5,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        data = load_data()
        user_id = str(interaction.user.id)

        if user_id in data:
            data[user_id]["roles"] = self.values
            save_data(data)
            await interaction.response.send_message(
                f"✅ Role zapisane: {', '.join(self.values)}", ephemeral=True
            )
        else:
            await interaction.response.send_message("❌ Najpierw połącz konto.", ephemeral=True)

class RoleView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.add_item(RoleSelect())

class LinkModal(discord.ui.Modal, title="Połącz konto League of Legends"):
    summoner_name = discord.ui.TextInput(label="Nazwa", placeholder="Np. Kacperx")
    tag = discord.ui.TextInput(label="Tag", placeholder="Np. 1234")

    async def on_submit(self, interaction: discord.Interaction):
        name, tag = self.summoner_name.value.strip(), self.tag.value.strip()
        await interaction.response.defer(ephemeral=True)

        puuid = await fetch_puuid(name, tag)
        if not puuid:
            await interaction.followup.send("❌ Nie znaleziono konta. Sprawdź nazwę i tag.", ephemeral=True)
            return

        data = load_data()
        data[str(interaction.user.id)] = {
            "summoner_name": name,
            "tag": tag,
            "region": "eun1",
            "puuid": puuid,
            "roles": []
        }
        save_data(data)

        await interaction.followup.send(
            "✅ Konto połączone. Teraz wybierz swoje role:",
            view=RoleView(),
            ephemeral=True
        )

class AcceptView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="Akceptuję", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, _):
        await interaction.response.send_modal(LinkModal())

    @discord.ui.button(label="Anuluj", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, _):
        await interaction.response.send_message("❌ Anulowano.", ephemeral=True)

class LinkCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="link", description="Połącz swoje konto League of Legends")
    async def link(self, interaction: discord.Interaction):
        disclaimer = (
            "**Uwaga!** Bot nie jest powiązany z Riot Games.\n"
            "Kliknij **Akceptuję**, by kontynuować łączenie konta."
        )
        await interaction.response.send_message(disclaimer, view=AcceptView(), ephemeral=True)

async def setup(bot):
    await bot.add_cog(LinkCog(bot))
