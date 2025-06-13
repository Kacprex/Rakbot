import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import os
import json

RIOT_TOKEN_FILE = "data/riot_token.txt"
DATA_FILE = "data/linked_accounts.json"
RANK_ICON_DIR = "rank_icons"

with open(RIOT_TOKEN_FILE, "r") as f:
    RIOT_TOKEN = f.read().strip()

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

class Profil(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="profil", description="Wyświetla Twój lub cudzy profil League of Legends")
    @app_commands.describe(użytkownik="Użytkownik Discord, którego profil chcesz zobaczyć")
    async def profil(self, interaction: discord.Interaction, użytkownik: discord.User = None):
        target = użytkownik or interaction.user
        user_id = str(target.id)
        data = load_data()

        if user_id not in data:
            msg = f"⚠️ Użytkownik **{target}** nie ma połączonego konta." if użytkownik else "⚠️ Nie masz połączonego konta. Użyj `/link`."
            await interaction.response.send_message(msg, ephemeral=True)
            return

        profile = data[user_id]
        name, tag, region = profile["summoner_name"], profile["tag"], profile["region"]

        headers = {"X-Riot-Token": RIOT_TOKEN}
        async with aiohttp.ClientSession() as session:
            url = f"https://europe.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name}/{tag}"
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    await interaction.response.send_message("❌ Błąd Riot API (1)", ephemeral=True)
                    return
                riot_data = await resp.json()
                puuid = riot_data["puuid"]
                riot_name = riot_data.get("gameName", name)
                riot_tag = riot_data.get("tagLine", tag)

            url2 = f"https://{region}.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
            async with session.get(url2, headers=headers) as resp:
                if resp.status != 200:
                    await interaction.response.send_message("❌ Błąd Riot API (2)", ephemeral=True)
                    return
                summ_data = await resp.json()
                summ_id = summ_data["id"]
                summ_level = summ_data["summonerLevel"]

            url3 = f"https://{region}.api.riotgames.com/lol/league/v4/entries/by-summoner/{summ_id}"
            async with session.get(url3, headers=headers) as resp:
                ranked_data = await resp.json()

        rank_info = next((entry for entry in ranked_data if entry["queueType"] == "RANKED_SOLO_5x5"), None)
        if rank_info:
            tier = rank_info["tier"].capitalize()
            division = rank_info["rank"]
            lp = rank_info["leaguePoints"]
            wins = rank_info["wins"]
            losses = rank_info["losses"]
            rank = f"{tier.upper()} {division} ({lp} LP)"
        else:
            tier = "Unranked"
            rank = "Unranked"
            wins = losses = 0

        icon_path = os.path.join(RANK_ICON_DIR, f"{tier}.png")
        file = discord.File(icon_path, filename="rank.png") if os.path.exists(icon_path) else None

        embed = discord.Embed(title=f"📜 Profil LoL: {riot_name}#{riot_tag}", color=discord.Color.blue())
        embed.add_field(name="Poziom", value=str(summ_level), inline=True)
        embed.add_field(name="Region", value=region.upper(), inline=True)
        embed.add_field(name="Ranga", value=rank, inline=False)
        embed.add_field(name="Wygrane", value=str(wins), inline=True)
        embed.add_field(name="Porażki", value=str(losses), inline=True)
        if file:
            embed.set_thumbnail(url="attachment://rank.png")

        await interaction.response.send_message(embed=embed, ephemeral=False, file=file if file else None)

async def setup(bot: commands.Bot):
    await bot.add_cog(Profil(bot))
