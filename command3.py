import discord
from discord import app_commands
from discord.ext import commands
import os
import aiohttp

# ===== CONFIG =====
AIAPI = os.getenv("AIAPI")  # OpenAI API key
AI_MODEL = "gpt-5"
# ==================

def safe_message(text: str) -> str:
    """Ensure Discord never gets an empty message."""
    if not text or not text.strip():
        return "⚠️ AI returned an empty response."
    return text


class AI(commands.Cog):
    """Cog for GPT-5 AI commands using slash commands."""

    def __init__(self, bot):
        self.bot = bot

    # -------------------------
    # GPT CALL
    # -------------------------
    async def run_gpt(self, prompt: str, max_tokens: int = 300) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {AIAPI}",
            "Content-Type": "application/json"
        }

        system_message = {
            "role": "system",
            "content": "You are a helpful assistant. NEVER output 'SEARCH:' unless the user explicitly asks."
        }

        messages = [
            system_message,
            {"role": "user", "content": prompt}
        ]

        payload = {
            "model": AI_MODEL,
            "messages": messages,
            "max_completion_tokens": max_tokens
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    return f"❌ GPT API error {resp.status}: {text}"

                data = await resp.json()

        try:
            content = data["choices"][0]["message"]["content"]
            return safe_message(content)
        except Exception as e:
            return f"❌ Unexpected response from API: {e}"

    # -------------------------
    # SLASH COMMAND
    # -------------------------
    @app_commands.command(name="ask", description="Ask GalacBot anything!")
    async def ask(self, interaction: discord.Interaction, question: str):
        # Defer interaction to allow >3s processing
        await interaction.response.defer(thinking=True)  # Public defer

        # Call GPT
        answer = await self.run_gpt(question)

        # Send the public message
        await interaction.followup.send(answer, ephemeral=False)


# -------------------------
# COG SETUP
# -------------------------
async def setup(bot: commands.Bot):
    await bot.add_cog(AI(bot))
