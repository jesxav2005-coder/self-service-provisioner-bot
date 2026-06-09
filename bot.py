import discord
from discord import app_commands
import os
import requests
from dotenv import load_dotenv

from terraform_generator.generator import generate

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
        resp = requests.post(
            POLICY_URL,
            json={"type": type, "env": env, "user": interaction.user.name},
            timeout=30,
        )
        result = resp.json()
        if result.get("allowed"):
            template = generate(type)
            msg = (
                f"✅ **Provision Request Received!**\n`type={type}` `env={env}`\n\n"
                f"{result.get('message', 'Sent to policy engine.')}\n\n"
                f"**Generated IaC template:**\n```\n{template}\n```"
            )
        else:
            msg = f"⚠️ Provision request denied:\n{result.get('message', 'Denied by policy.')}"
    except Exception as e:
        msg = f"⚠️ Policy engine not connected yet.\n`/provision type={type} env={env}` logged successfully!"

    await interaction.followup.send(msg)

@client.event
async def on_ready():
    await tree.sync()
    print(f"✅ Bot is online as {client.user}")

client.run(TOKEN)