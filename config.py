import discord

with open("data/token.txt") as f:
    TOKEN = f.read().strip()

RIOT_TOKEN_FILE = "data/riot_token.txt"
with open(RIOT_TOKEN_FILE) as f:
    RIOT_TOKEN = f.read().strip()

INTENTS = discord.Intents.default()
INTENTS.message_content = True
INTENTS.guilds = True
INTENTS.members = True

RANK_ICON_DIR = "rank_icons"
