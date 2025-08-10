import discord
from discord.ext import commands
import os
import aiohttp
import json

# ====== CONFIG ======
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Set this in your environment variables
AI_MODEL = "gpt-5"
# ====================

class Command3(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def run_gpt_web(self, query):
        """
        Sends the query to GPT-5 with web search enabled so it can both search and read websites.
        """
        url = "https://api.openai.com/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": AI_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an AI assistant with live web search and browsing capabilities. "
                               "If needed, you can access websites to extract accurate and detailed information."
                },
                {
                    "role": "user",
                    "content": query
                }
            ],
            "tools": [
                {"type": "web_search"},  # Let GPT search the internet
                {"type": "web_browse"}   # Let GPT open and read sites
            ],
            "max_tokens": 1200
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status != 200:
                    return f"❌ API request failed: {response.status} - {await response.text()}"

                data = await response.json()
                return data["choices"][0]["message"]["content"]

    @commands.command(name="search", help="Search the web and access websites for more detailed results.")
    async def search_command(self, ctx, *, query: str):
        await ctx.send(f"🔍 Searching and reading web sources for: **{query}**")
        result = await self.run_gpt_web(query)
        await ctx.send(result)

async def setup(bot):
    await bot.add_cog(Command3(bot))
