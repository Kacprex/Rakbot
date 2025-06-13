import discord
from discord.ext import commands, tasks
import os
import asyncio
import aiohttp
import json

# Ścieżki
TOKEN = open("data/token.txt").read().strip()
RIOT_TOKEN = open("data/riot_token.txt").read().strip()
DATA_FILE = "data/linked_accounts.json"

# Intencje Discorda
intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True
intents.members = True

# Tworzenie bota
bot = commands.Bot(command_prefix="!", intents=intents)

# Funkcje pomocnicze do obsługi danych
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# Automatyczna aktualizacja Riot ID na podstawie PUUID
async def update_riot_ids():
    headers = {"X-Riot-Token": RIOT_TOKEN}
    data = load_data()
    changed = False

    async with aiohttp.ClientSession() as session:
        for user_id, info in data.items():
            puuid = info.get("puuid")
            if not puuid:
                continue

            url = f"https://europe.api.riotgames.com/riot/account/v1/accounts/by-puuid/{puuid}"
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    continue
                new_info = await resp.json()
                new_game_name = new_info.get("gameName")
                new_tag_line = new_info.get("tagLine")

                if (
                    new_game_name and new_tag_line and
                    (new_game_name != info.get("summoner_name") or new_tag_line != info.get("tag"))
                ):
                    print(f"🔄 Zaktualizowano {user_id}: {info.get('summoner_name')}#{info.get('tag')} ➜ {new_game_name}#{new_tag_line}")
                    info["summoner_name"] = new_game_name
                    info["tag"] = new_tag_line
                    changed = True

    if changed:
        save_data(data)

# Zadanie cykliczne co 2h
@tasks.loop(hours=2)
async def auto_update_task():
    print("🕒 Sprawdzanie aktualizacji Riot ID...")
    await update_riot_ids()

# Ładowanie komend z katalogu /commands
async def load_commands():
    for filename in os.listdir("./commands"):
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f"commands.{filename[:-3]}")
                print(f"✅ Załadowano {filename}")
            except Exception as e:
                print(f"❌ Błąd przy ładowaniu {filename}: {e}")

# Zdarzenie po starcie bota
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"🔌 Zalogowano jako {bot.user} (ID: {bot.user.id})")
    auto_update_task.start()

# Główna pętla
async def main():
    async with bot:
        await load_commands()
        await bot.start(TOKEN)

# Uruchomienie
asyncio.run(main())
