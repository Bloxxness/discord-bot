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


def _blocking_gpt_call(conversation: list) -> str:
    """
    Correct GPT-5 Responses API usage.
    Runs in a background thread to avoid blocking Discord.
    """

    response = client.responses.create(
        model=AI_MODEL,
        input=[
            {
                "role": msg["role"],
                "content": [
                    {
                        "type": "input_text",
                        "text": msg["content"]
                    }
                ]
            }
            for msg in conversation
        ],
        max_output_tokens=300
    )

    # Extract visible text from the response
    output_parts = []
    for item in response.output:
        if item["type"] == "message":
            for part in item["content"]:
                if part["type"] == "output_text":
                    output_parts.append(part["text"])

    return "\n".join(output_parts).strip()


class Search(commands.Cog):
    """
    REQUIRED by main.py:
      bot.get_cog("Search")
      await chat_with_search(conversation)
    """

    def __init__(self, bot):
        self.bot = bot

    async def chat_with_search(self, conversation: list) -> str:
        try:
            text = await asyncio.to_thread(
                _blocking_gpt_call,
                conversation
            )

            if not text:
                return "⚠️ AI returned no user-visible output."

            return text

        except Exception as e:
            return f"❌ AI error: {str(e)}"


async def setup(bot: commands.Bot):
    await bot.add_cog(Search(bot))
