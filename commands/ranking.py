import discord
from discord.ext import commands
from discord import app_commands
from utils import load_data, get_rank_icon_and_info

class RankingView(discord.ui.View):
    def __init__(self, pages, interaction_user):
        super().__init__(timeout=60)
        self.pages = pages
        self.page = 0
        self.message = None
        self.interaction_user = interaction_user

    async def update(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🏆 Ranking graczy", color=discord.Color.gold())
        for name, tag, rank_text, icon in self.pages[self.page]:
            embed.add_field(
                name=f"{name}#{tag}",
                value=rank_text,
                inline=False
            )
        embed.set_footer(text=f"Strona {self.page+1}/{len(self.pages)}")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.secondary)
    async def previous(self, interaction: discord.Interaction, _):
        if interaction.user != self.interaction_user:
            return await interaction.response.send_message("❌ To nie twój ranking.", ephemeral=True)
        if self.page > 0:
            self.page -= 1
            await self.update(interaction)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, _):
        if interaction.user != self.interaction_user:
            return await interaction.response.send_message("❌ To nie twój ranking.", ephemeral=True)
        if self.page < len(self.pages) - 1:
            self.page += 1
            await self.update(interaction)

class Ranking(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ranking", description="Wyświetl ranking graczy")
    async def ranking(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)

        data = load_data()
        players = []

        for uid, profile in data.items():
            try:
                name = profile["summoner_name"]
                tag = profile["tag"]
                rank, icon = await get_rank_icon_and_info(profile)
                players.append((name, tag, rank, icon))
            except:
                continue

        # sortowanie według rangi (lepsza ranga wyżej)
        tier_order = {
            "IRON": 1, "BRONZE": 2, "SILVER": 3, "GOLD": 4,
            "PLATINUM": 5, "EMERALD": 6, "DIAMOND": 7,
            "MASTER": 8, "GRANDMASTER": 9, "CHALLENGER": 10
        }

        def rank_key(p):
            rank_name = p[2].split()[0].upper()
            return tier_order.get(rank_name, 0)

        players.sort(key=rank_key, reverse=True)

        # podział na strony
        page_size = 5
        pages = [players[i:i+page_size] for i in range(0, len(players), page_size)]

        if not pages:
            await interaction.followup.send("Brak danych do wyświetlenia.", ephemeral=True)
            return

        view = RankingView(pages, interaction.user)
        embed = discord.Embed(title="🏆 Ranking graczy", color=discord.Color.gold())
        for name, tag, rank_text, icon in pages[0]:
            embed.add_field(name=f"{name}#{tag}", value=rank_text, inline=False)
        embed.set_footer(text=f"Strona 1/{len(pages)}")

        await interaction.followup.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Ranking(bot))
