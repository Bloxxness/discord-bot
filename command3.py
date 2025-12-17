import os
import asyncio
from discord.ext import commands
from openai import OpenAI

# ===== CONFIG =====
AI_MODEL = "gpt-5"
AIAPI = os.getenv("AIAPI")
# ==================

if not AIAPI:
    raise RuntimeError("AIAPI environment variable not set!")

client = OpenAI(api_key=AIAPI)


def safe_message(text: str) -> str:
    if not text or not text.strip():
        return "⚠️ AI returned an empty response."
    return text


def _blocking_gpt_call(conversation: list) -> str:
    """
    Runs in a background thread.
    MUST be synchronous.
    """
    response = client.chat.completions.create(
        model=AI_MODEL,
        messages=conversation,
        max_completion_tokens=300
    )
    return response.choices[0].message.content


class Search(commands.Cog):
    """
    Required by main.py:
      bot.get_cog("Search")
      await chat_with_search(conversation)
    """

    def __init__(self, bot):
        self.bot = bot

    async def chat_with_search(self, conversation: list) -> str:
        try:
            content = await asyncio.to_thread(
                _blocking_gpt_call,
                conversation
            )
            return safe_message(content)

        except Exception as e:
            return f"❌ AI error: {str(e)}"


async def setup(bot: commands.Bot):
    await bot.add_cog(Search(bot))
