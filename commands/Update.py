import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import aiohttp
from utils import save_data, load_data
from config import RIOT_TOKEN

class Update(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="update", description="Aktualizuje konta bez PUUID na podstawie Riot ID")
    async def update(self, interaction: discord.Interaction):
        await interaction.response.send_message("🔄 Aktualizacja kont...", ephemeral=True)

        data = load_data()
        updated = 0
        failed = 0

        headers = {"X-Riot-Token": RIOT_TOKEN}
        async with aiohttp.ClientSession() as session:
            for uid, profile in data.items():
                if "puuid" not in profile:
                    name = profile.get("summoner_name")
                    tag = profile.get("tag")
                    if not name or not tag:
                        failed += 1
                        continue

                    url = f"https://europe.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name}/{tag}"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status == 200:
                            riot_data = await resp.json()
                            data[uid]["puuid"] = riot_data["puuid"]
                            updated += 1
                        else:
                            failed += 1

        save_data(data)
        await interaction.followup.send(
            f"✅ Zaktualizowano kont: **{updated}**\n❌ Niepowodzeń: **{failed}**",
            ephemeral=True
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(Update(bot))
