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


def get_policy_result(type: str, env: str, user: str, policy_url: str = POLICY_URL, timeout: int = 30) -> dict:
    try:
        resp = requests.post(
            policy_url,
            json={"type": type, "env": env, "user": user},
            timeout=timeout,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException:
        return {
            "allowed": False,
            "message": "Policy engine is unavailable. Please try again later.",
        }
    except ValueError:
        return {
            "allowed": False,
            "message": "Invalid response from policy engine.",
        }


def format_provision_message(type: str, env: str, result: dict) -> str:
    if result.get("allowed"):
        template = generate(type, env)
        return (
            f"✅ **Provision Request Received!**\n`type={type}` `env={env}`\n\n"
            f"{result.get('message', 'Sent to policy engine.')}\n\n"
            f"**Generated IaC template:**\n```\n{template}\n```"
        )

    return f"⚠️ Provision request denied:\n{result.get('message', 'Denied by policy.')}"


@tree.command(name="provision", description="Request a new environment")
@app_commands.describe(type="Environment type (e.g. ec2, docker)", env="Environment name (e.g. dev, staging)")
async def provision(interaction: discord.Interaction, type: str, env: str):
    await interaction.response.defer()
    result = get_policy_result(type, env, interaction.user.name)
    msg = format_provision_message(type, env, result)
    await interaction.followup.send(msg)


@client.event
async def on_ready():
    await tree.sync()
    print(f"✅ Bot is online as {client.user}")


if __name__ == "__main__":
    client.run(TOKEN)