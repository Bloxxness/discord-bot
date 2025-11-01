# command3.py
import discord
from discord.ext import commands
import os
import aiohttp
import json

# ====== CONFIG ======
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Set this in your environment variables
AI_MODEL = "gpt-5"
# ====================

class Search(commands.Cog):   # renamed so bot.get_cog("Search") finds this cog
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
                # Defensive: make sure the structure exists
                try:
                    return data["choices"][0]["message"]["content"]
                except Exception:
                    return "❌ Unexpected response from API."

    async def chat_with_search(self, conversation, temperature=0.7):
        """
        Expected interface used by main.py:
        - conversation: list of message dicts like [{"role":"system","content":...}, {"role":"user",...}, ...]
        - temperature: float (unused here but kept for compatibility)
        This extracts the latest user message from the conversation and performs a web-enabled GPT request.
        """
        # Find the last user message in the conversation
        last_user_msg = None
        for msg in reversed(conversation):
            if msg.get("role") == "user":
                last_user_msg = msg.get("content")
                break

        if not last_user_msg:
            return "⚠️ No user message found in conversation."

        # Optionally you can enrich the prompt; keep it simple and hand off to the web-enabled call.
        prompt = f"Please search the web and answer this query concisely:\n\n{last_user_msg}"
        return await self.run_gpt_web(prompt)

    @commands.command(name="search", help="Search the web and access websites for more detailed results.")
    async def search_command(self, ctx, *, query: str):
        await ctx.send(f"🔍 Searching and reading web sources for: **{query}**")
        result = await self.run_gpt_web(query)
        await ctx.send(result)

async def setup(bot):
    await bot.add_cog(Search(bot))
