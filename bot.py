import discord
from discord import app_commands
import os
import requests
from dotenv import load_dotenv
from typing import Optional

from terraform_generator.generator import generate

try:
    import openai
except Exception:
    openai = None
try:
    from huggingface_hub import InferenceApi
except Exception:
    InferenceApi = None

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
POLICY_URL = os.getenv("POLICY_ENGINE_URL", "http://localhost:8001/validate")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if openai and OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
HUGGINGFACE_MODEL = os.getenv("HUGGINGFACE_MODEL", "google/flan-t5-small")
hf_inference = None
if InferenceApi and HUGGINGFACE_API_KEY:
    try:
        hf_inference = InferenceApi(repo_id=HUGGINGFACE_MODEL, token=HUGGINGFACE_API_KEY)
    except Exception:
        hf_inference = None

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


@tree.command(name="explain", description="Ask the project AI assistant a question or get a README summary")
@app_commands.describe(question="Optional question about the project")
async def explain(interaction: discord.Interaction, question: Optional[str] = None):
    await interaction.response.defer()

    # Prefer Hugging Face Inference API if configured
    if hf_inference is None and openai is None:
        await interaction.followup.send("No LLM integration is available. Install `huggingface-hub` or `openai` and set the API key.")
        return


    # Load README as context
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    if not os.path.exists(readme_path):
        readme_path = os.path.join(os.path.dirname(__file__), "..", "README.md")

    readme_text = ""
    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            readme_text = f.read()
    except Exception:
        readme_text = ""

    # Truncate README to a reasonable size
    context_excerpt = (readme_text[:4000] + "\n...[truncated]") if len(readme_text) > 4000 else readme_text

    if not question:
        if context_excerpt:
            summary = context_excerpt[:1500]
            await interaction.followup.send(f"Project README (excerpt):\n\n{summary}")
        else:
            await interaction.followup.send("No README found in the repository to summarize.")
        return

    # Build prompt
    prompt = f"Repository README:\n{context_excerpt}\n\nQuestion: {question}"

    answer = None
    # Use Hugging Face Inference API if available
    if hf_inference is not None:
        try:
            hf_resp = hf_inference(prompt)
            if isinstance(hf_resp, dict):
                # some models return {'generated_text': '...'}
                answer = hf_resp.get("generated_text") or hf_resp.get("text") or str(hf_resp)
            else:
                answer = str(hf_resp)
        except Exception as e:
            answer = f"Hugging Face request failed: {e}"
    # Fallback to OpenAI if configured
    elif openai is not None and OPENAI_API_KEY:
        system_prompt = (
            "You are an assistant that answers questions about a software repository. "
            "Use the provided README context to answer concisely and helpfully."
        )
        user_prompt = prompt
        try:
            resp = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=600,
                temperature=0.2,
            )
            answer = resp["choices"][0]["message"]["content"].strip()
        except Exception as e:
            answer = f"OpenAI request failed: {e}"

    await interaction.followup.send(answer)


@client.event
async def on_ready():
    await tree.sync()
    print(f"✅ Bot is online as {client.user}")


if __name__ == "__main__":
    client.run(TOKEN)