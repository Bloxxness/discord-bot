import os
import asyncio
from discord.ext import commands
from openai import OpenAI

AI_MODEL = "gpt-5"
AIAPI = os.getenv("AIAPI")

if not AIAPI:
    raise RuntimeError("AIAPI environment variable not set!")

client = OpenAI(api_key=AIAPI)


def extract_text(response) -> str:
    """
    Safely extract text from GPT-5 responses.
    """
    try:
        msg = response.choices[0].message

        # Normal text response
        if msg.content:
            return msg.content

        # Tool / structured / reasoning-only response
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            return "⚠️ AI returned a tool call instead of text."

        return None

    except Exception:
        return None


def _blocking_gpt_call(conversation: list) -> str:
    response = client.chat.completions.create(
        model=AI_MODEL,
        messages=conversation,
        max_completion_tokens=300
    )

    text = extract_text(response)
    return text


class Search(commands.Cog):
    """Required Search cog for main.py"""

    def __init__(self, bot):
        self.bot = bot

    async def chat_with_search(self, conversation: list) -> str:
        try:
            text = await asyncio.to_thread(
                _blocking_gpt_call,
                conversation
            )

            if not text or not text.strip():
                return "⚠️ AI produced no readable text."

            return text

        except Exception as e:
            return f"❌ AI error: {e}"


async def setup(bot: commands.Bot):
    await bot.add_cog(Search(bot))
