import discord
from discord.ext import commands
import os
import aiohttp
import json

# ====== CONFIG ======
AIAPI = os.getenv("AIAPI")  # OpenAI API key
AI_MODEL = "gpt-5"          # GPT-5 model
# ====================


def safe_message(text: str) -> str:
    """Ensure Discord never gets an empty message."""
    if not text or not text.strip():
        return "⚠️ AI returned an empty response."
    return text


class AI(commands.Cog):
    """Discord cog for GPT-5 AI commands."""

    def __init__(self, bot):
        self.bot = bot

    # =============================
    # GPT-5 COMPLETION CALL
    # =============================
    async def run_gpt(self, conversation: list[dict], max_tokens: int = 300) -> str:
        """Send conversation to GPT-5 and return AI response."""
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {AIAPI}",
            "Content-Type": "application/json"
        }

        # Prevent GPT from hallucinating SEARCH triggers
        system_message = {
            "role": "system",
            "content": "You are a helpful assistant. NEVER output 'SEARCH:' unless the user explicitly asks."
        }

        messages = [system_message] + conversation

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

    # =============================
    # DISCORD COMMAND
    # =============================
    @commands.command(name="ai", help="Talk to GPT-5 AI. Usage: !ai <your message>")
    async def ai_command(self, ctx, *, prompt: str):
        # Build conversation for GPT
        conversation = [{"role": "user", "content": prompt}]
        await ctx.send("🤖 Thinking...")

        answer = await self.run_gpt(conversation)
        await ctx.send(answer)

    # =============================
    # CHAT-STYLE CALL (Optional)
    # =============================
    async def chat_with_gpt(self, conversation: list[dict]):
        """General GPT chat call."""
        return await self.run_gpt(conversation)


# =============================
# COG SETUP
# =============================
async def setup(bot):
    await bot.add_cog(AI(bot))
