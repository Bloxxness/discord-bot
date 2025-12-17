import os
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


class Search(commands.Cog):
    """
    This Cog exists because main.py explicitly looks for:
      bot.get_cog("Search")
    and then calls:
      chat_with_search(conversation)

    If this Cog is missing, chat WILL break.
    """

    def __init__(self, bot):
        self.bot = bot

    async def chat_with_search(self, conversation: list) -> str:
        try:
            response = client.chat.completions.create(
                model=AI_MODEL,
                messages=conversation,
                max_completion_tokens=300
            )

            content = response.choices[0].message.content
            return safe_message(content)

        except Exception as e:
            return f"❌ AI error: {str(e)}"


async def setup(bot: commands.Bot):
    await bot.add_cog(Search(bot))
