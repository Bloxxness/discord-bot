import discord
from discord.ext import commands
from discord import app_commands
import os

# Reuse environment + OpenAI style from main.py
from openai import OpenAI

AI_MODEL = "gpt-5"
client = OpenAI(api_key=os.getenv("AIAPI"))


def safe_message(text: str) -> str:
    if not text or not text.strip():
        return "⚠️ AI returned an empty response."
    return text


class AIQuick(commands.Cog):
    """One-off AI questions (non-conversational)."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def run_gpt(self, prompt: str, max_tokens: int = 300) -> str:
        try:
            response = client.chat.completions.create(
                model=AI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant. NEVER output 'SEARCH:' unless explicitly asked."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_completion_tokens=max_tokens
            )

            return safe_message(response.choices[0].message.content)

        except Exception as e:
            return f"❌ AI error: {e}"

    @app_commands.command(
        name="askonce",
        description="Ask GalacBot a single question (no chat session)."
    )
    async def askonce(
        self,
        interaction: discord.Interaction,
        question: str
    ):
        await interaction.response.defer(thinking=True)

        answer = await self.run_gpt(question)

        await interaction.followup.send(answer, ephemeral=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(AIQuick(bot))
