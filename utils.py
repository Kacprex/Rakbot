import os
import json
import aiohttp
import itertools
import discord

DATA_FILE = os.path.join("data", "linked_accounts.json")
RIOT_TOKEN_FILE = "data/riot_token.txt"

with open(RIOT_TOKEN_FILE, "r") as f:
    RIOT_TOKEN = f.read().strip()

def load_data():
    print(f"[DEBUG] Szukam pliku: {DATA_FILE}")
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        try:
            data = json.load(f)
            return data
        except json.JSONDecodeError:
            return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

async def fetch_puuid(name: str, tag: str) -> str | None:
    url = f"https://europe.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name}/{tag}"
    headers = {"X-Riot-Token": RIOT_TOKEN}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
            return data.get("puuid")

async def get_rank_icon_and_info(profile):
    region = profile.get("region", "eun1")
    puuid = profile.get("puuid")
    headers = {"X-Riot-Token": RIOT_TOKEN}

    async with aiohttp.ClientSession() as session:
        url = f"https://{region}.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
        async with session.get(url, headers=headers) as r1:
            if r1.status != 200:
                return ("Błąd API", None)
            summ_data = await r1.json()
            summ_id = summ_data["id"]

        url2 = f"https://{region}.api.riotgames.com/lol/league/v4/entries/by-summoner/{summ_id}"
        async with session.get(url2, headers=headers) as r2:
            ranked = await r2.json()

    solo = next((entry for entry in ranked if entry["queueType"] == "RANKED_SOLO_5x5"), None)
    if not solo:
        return ("Unranked", None)

    tier = solo["tier"].capitalize()
    division = solo["rank"]
    lp = solo["leaguePoints"]
    rank_str = f"{tier} {division} ({lp} LP)"

    filename = f"{tier}.png"
    icon_path = f"rank_icons/{filename}"

    if os.path.exists(icon_path):
        file = discord.File(icon_path, filename="rank.png")
        return (rank_str, file)
    else:
        return (rank_str, None)

async def get_player_strength(profile):
    name = profile["summoner_name"]
    tag = profile["tag"]
    region = profile["region"]

    headers = {"X-Riot-Token": RIOT_TOKEN}
    async with aiohttp.ClientSession() as session:
        url = f"https://europe.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name}/{tag}"
        async with session.get(url, headers=headers) as resp:
            riot_data = await resp.json()
            puuid = riot_data["puuid"]

        url2 = f"https://{region}.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
        async with session.get(url2, headers=headers) as resp:
            summ_data = await resp.json()
            summ_id = summ_data["id"]

        url3 = f"https://{region}.api.riotgames.com/lol/league/v4/entries/by-summoner/{summ_id}"
        async with session.get(url3, headers=headers) as resp:
            ranked = await resp.json()

    soloq = next((entry for entry in ranked if entry["queueType"] == "RANKED_SOLO_5x5"), None)
    if not soloq:
        return 0

    tier_weights = {
        "IRON": 1, "BRONZE": 2, "SILVER": 3, "GOLD": 4,
        "PLATINUM": 5, "EMERALD": 6, "DIAMOND": 7,
        "MASTER": 8, "GRANDMASTER": 9, "CHALLENGER": 10
    }
    division_weights = {"IV": 0, "III": 1, "II": 2, "I": 3}

    tier = soloq["tier"]
    rank = soloq["rank"]
    lp = soloq["leaguePoints"]
    wins = soloq["wins"]
    losses = soloq["losses"]

    wr = (wins / (wins + losses)) * 100 if wins + losses > 0 else 0

    base = tier_weights.get(tier.upper(), 0) * 4 + division_weights.get(rank.upper(), 0)
    base += lp / 100.0

    if wr > 60:
        base += 3
    elif wr < 38:
        base -= 5

    return base

def balance_teams(players):
    best_diff = float('inf')
    best_split = None

    for combo in itertools.combinations(players, len(players) // 2):
        team1 = list(combo)
        team2 = [p for p in players if p not in team1]

        power1 = sum(p[1] for p in team1)
        power2 = sum(p[1] for p in team2)
        diff = abs(power1 - power2)

        if diff < best_diff:
            best_diff = diff
            best_split = (team1, team2)

    team1, team2 = best_split
    power1 = sum(p[1] for p in team1)
    power2 = sum(p[1] for p in team2)

    print("\\n" + "-" * 60)
    print(f"{'Team 1':<25}Strength: {power1:>6.2f}    ||  {'Team 2':<25}Strength: {power2:>6.2f}")
    print("-" * 60)

    max_len = max(len(team1), len(team2))
    for i in range(max_len):
        name1, str1 = team1[i] if i < len(team1) else ("", 0)
        name2, str2 = team2[i] if i < len(team2) else ("", 0)
        print(f"{name1:<25} {str1:>6.2f}    ||  {name2:<25} {str2:>6.2f}")

    print(f"\\nBest diff: {best_diff:.2f}")
    return best_split