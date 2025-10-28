from flask import Flask
from threading import Thread
from waitress import serve  # <== toegevoegd

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    # Gebruik Waitress i.p.v. Flask dev server
    serve(app, host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# === Embark ID Discord Bot ===
# Deze versie gebruikt een .env bestand voor veilige opslag van je token

from dotenv import load_dotenv
import os
import discord
from discord.ext import commands
import json

# === CONFIGURATIE ===
load_dotenv()  # Laadt waarden uit .env bestand

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID"))  # jouw server ID
DATA_FILE = "embark_data.json"

# Controleer of token gevonden is
if not TOKEN:
    print("❌ Fout: geen DISCORD_BOT_TOKEN gevonden in .env!")
    exit()

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# === Helper functies voor opslag ===
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# === Events & Commands ===
@bot.event
async def on_ready():
    print(f"✅ Ingelogd als {bot.user}")
    try:
        await bot.tree.sync()  # wereldwijde sync
        print("🌍 Globale slash-commands gesynchroniseerd.")
    except Exception as e:
        print(f"⚠️ Fout bij globale sync: {e}")


# Voeg /embark_add command toe
@bot.tree.command(name="embark_add", description="Voeg je Embark ID toe aan de lijst.")
async def embark_add(interaction: discord.Interaction, embark_id: str):
    data = load_data()
    data[str(interaction.user.id)] = {
        "name": interaction.user.display_name,
        "embark_id": embark_id
    }
    save_data(data)
    await interaction.response.send_message(
        f"✅ Je Embark ID is opgeslagen: `{embark_id}`", ephemeral=True
    )

# Toon lijst
@bot.tree.command(name="embark_list", description="Toon de lijst met alle Embark ID's.")
async def embark_list(interaction: discord.Interaction):
    data = load_data()
    if not data:
        await interaction.response.send_message("📭 Nog geen Embark ID's geregistreerd.")
        return

    embed = discord.Embed(title="📜 Embark Lijst", color=0x00ff00)
    for info in data.values():
        embed.add_field(
            name=info["name"],
            value=f"`{info['embark_id']}`",
            inline=False
        )

    await interaction.response.send_message(embed=embed)

# Verwijder eigen ID
@bot.tree.command(name="embark_remove", description="Verwijder je Embark ID uit de lijst.")
async def embark_remove(interaction: discord.Interaction):
    data = load_data()
    uid = str(interaction.user.id)
    if uid in data:
        del data[uid]
        save_data(data)
        await interaction.response.send_message("🗑️ Je Embark ID is verwijderd.", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Je had nog geen Embark ID opgeslagen.", ephemeral=True)

@bot.command()
async def debug(ctx):
    guild = discord.Object(id=GUILD_ID)
    cmds = await bot.tree.fetch_commands(guild=guild)
    if not cmds:
        await ctx.send("⚠️ Geen slash-commands gevonden bij Discord.")
    else:
        msg = "📜 Geregistreerde commands:\n" + "\n".join([f"- {c.name}" for c in cmds])
        await ctx.send(msg)



# === Start de bot ===
keep_alive()
bot.run(TOKEN)
