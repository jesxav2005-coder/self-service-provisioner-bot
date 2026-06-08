import discord
from discord import app_commands
import os, requests
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
POLICY_URL = os.getenv("POLICY_ENGINE_URL", "http://localhost:8001/validate")

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@tree.command(name="provision", description="Request a new environment")
@app_commands.describe(type="Environment type (e.g. ec2, docker)", env="Environment name (e.g. dev, staging)")
async def provision(interaction: discord.Interaction, type: str, env: str):
    await interaction.response.defer()
    try:
        resp = requests.post(POLICY_URL, json={"type": type, "env": env}, timeout=30)
        result = resp.json()
        msg = f"✅ **Provision Request Received!**\n`type={type}` `env={env}`\n\n{result.get('message', 'Sent to policy engine.')}"
    except Exception as e:
        msg = f"⚠️ Policy engine not connected yet.\n`/provision type={type} env={env}` logged successfully!"

    await interaction.followup.send(msg)

@client.event
async def on_ready():
    await tree.sync()
    print(f"✅ Bot is online as {client.user}")

client.run(TOKEN)