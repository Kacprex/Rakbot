import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from utils import load_data, get_player_strength, balance_teams

class Teams(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="teams", description="Tworzy zbalansowane drużyny (voice/manual)")
    @app_commands.describe(
        tryb="Wybierz tryb działania: voice - z kanału głosowego, manual - podajesz osoby ręcznie"
    )
    @app_commands.choices(
        tryb=[
            app_commands.Choice(name="voice", value="voice"),
            app_commands.Choice(name="manual", value="manual")
        ]
    )
    async def teams(self, interaction: discord.Interaction, tryb: app_commands.Choice[str]):
        await interaction.response.send_message("🔄 Zbieram dane...", ephemeral=True)
        tryb = tryb.value.lower()
        data = load_data()
        members = []

        if tryb == "voice":
            voice = interaction.user.voice
            if not voice or not voice.channel:
                await interaction.followup.send("❌ Nie jesteś na kanale głosowym.", ephemeral=True)
                return

            all_members = [m for m in voice.channel.members if not m.bot]

            class IgnoreView(discord.ui.View):
                def __init__(self, players):
                    super().__init__(timeout=60)
                    self.ignore_ids = []
                    self.stop_event = asyncio.Event()

                    options = [
                        discord.SelectOption(label="✅ Nie ignoruj nikogo", value="none", default=False)
                    ] + [
                        discord.SelectOption(label=member.display_name, value=str(member.id))
                        for member in players
                    ]

                    self.select = discord.ui.Select(
                        placeholder="Wybierz osoby do pominięcia",
                        min_values=0,
                        max_values=len(options),
                        options=options
                    )
                    self.select.callback = self.select_callback
                    self.add_item(self.select)

                async def select_callback(self, interaction_: discord.Interaction):
                    if "none" in self.select.values:
                        self.ignore_ids = []
                    else:
                        self.ignore_ids = [int(v) for v in self.select.values if v != "none"]
                    await interaction_.response.send_message("✅ Zapisano wybór.", ephemeral=True)
                    self.stop_event.set()

            view = IgnoreView(all_members)
            await interaction.followup.send("🔧 Wybierz osoby do pominięcia:", view=view, ephemeral=True)
            await view.stop_event.wait()
            members = [m for m in all_members if m.id not in view.ignore_ids]

        elif tryb == "manual":
            await interaction.followup.send("📝 Podaj ID lub ping graczy oddzielone spacjami:", ephemeral=True)

            def check(msg):
                return msg.author == interaction.user and msg.channel == interaction.channel

            try:
                msg = await self.bot.wait_for("message", timeout=60.0, check=check)
                for word in msg.content.split():
                    if word.startswith("<@") and word.endswith(">"):
                        uid = int(word.strip("<@!>"))
                    elif word.isdigit():
                        uid = int(word)
                    else:
                        continue
                    try:
                        user = await self.bot.fetch_user(uid)
                        members.append(user)
                    except:
                        continue
            except asyncio.TimeoutError:
                await interaction.followup.send("⏰ Czas minął. Spróbuj ponownie.", ephemeral=True)
                return
        else:
            await interaction.followup.send("❌ Nieprawidłowy tryb. Wybierz `voice` lub `manual`.", ephemeral=True)
            return

        players = []
        missing = []
        for m in members:
            uid = str(m.id)
            if uid not in data:
                missing.append(m.mention)
            else:
                power = await get_player_strength(data[uid])
                players.append((m.display_name, power))

        if missing:
            await interaction.followup.send(f"⚠️ Te osoby nie mają połączonego konta: {' '.join(missing)}", ephemeral=True)
            return

        if len(players) < 2:
            await interaction.followup.send("❌ Zbyt mało graczy do podziału.", ephemeral=True)
            return

        team1, team2 = balance_teams(players)

        power1 = sum(p[1] for p in team1)
        power2 = sum(p[1] for p in team2)
        diff = abs(power1 - power2)

        print("Team 1 | Strength | Team 2 | Strength")
        for p1, p2 in zip(team1, team2):
            left = f"{p1[0]:<15} | {p1[1]:<7.2f}"
            right = f"{p2[0]:<15} | {p2[1]:<7.2f}" if len(team2) > team1.index(p1) else ""
            print(f"{left} || {right}")
        print(f"\nBest diff: {diff:.2f}")

        embed = discord.Embed(title="⚔️ Zbalansowane Drużyny", color=discord.Color.green())
        embed.add_field(name="Team 1", value="\n".join(p[0] for p in team1), inline=True)
        embed.add_field(name="Team 2", value="\n".join(p[0] for p in team2), inline=True)
        await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Teams(bot))
