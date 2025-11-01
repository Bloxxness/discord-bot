# command3.py
import discord
from discord.ext import commands
import os
import aiohttp
import json

# ====== CONFIG ======
AIAPI = os.getenv("AIAPI")  # Your OpenAI API key
LANGSEARCH_API_KEY = os.getenv("LANGSEARCH_API_KEY")  # LangSearch API key
AI_MODEL = "gpt-5"
# ====================

class Search(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def perform_langsearch(self, query: str, max_results: int = 3):
        """
        Perform a web search using LangSearch API.
        Returns a list of results with title, url, and snippet/summary.
        """
        url = "https://api.langsearch.com/v1/web-search"
        headers = {"Authorization": f"Bearer {LANGSEARCH_API_KEY}"}
        payload = {
            "query": query,
            "count": max_results,
            "summary": True,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()

        results = []
        for item in data.get("results", []):
            results.append({
                "title": item.get("title"),
                "url": item.get("url"),
                "snippet": item.get("summary") or item.get("snippet")
            })
        return results

    async def run_gpt_with_context(self, query: str, context_snippets: list[dict]):
        """
        Sends the query plus snippets to OpenAI to generate a concise answer.
        """
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {AIAPI}",
            "Content-Type": "application/json",
        }

        # Build context from snippets
        snippet_text = "\n".join(
            f"{i+1}. {s['title']} — {s['url']}\n   {s['snippet']}"
            for i, s in enumerate(context_snippets)
        )

        messages = [
            {"role": "system", "content": "You are a helpful assistant that uses web search results to answer questions."},
            {"role": "user", "content": f"Here are some relevant web search results:\n{snippet_text}\n\nQuestion: {query}"}
        ]

        payload = {
            "model": AI_MODEL,
            "messages": messages,
            "max_tokens": 800,
            "temperature": 0.7,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                if resp.status != 200:
                    return f"❌ API request failed: {resp.status} - {await resp.text()}"
                data = await resp.json()

        try:
            return data["choices"][0]["message"]["content"]
        except Exception:
            return "❌ Unexpected response from API."

    async def handle_search_trigger(self, text: str):
        """
        Detects SEARCH: <query> lines and runs LangSearch + GPT on it.
        """
        if not text.startswith("SEARCH:"):
            return None

        query = text[len("SEARCH:"):].strip()
        snippets = await self.perform_langsearch(query)
        if not snippets:
            return "⚠️ Could not fetch web results."
        return await self.run_gpt_with_context(query, snippets)

    @commands.command(name="search", help="Search the web using LangSearch and summarize results.")
    async def search_command(self, ctx, *, query: str):
        await ctx.send(f"🔍 Searching the web for: **{query}**")
        snippets = await self.perform_langsearch(query)
        if not snippets:
            await ctx.send("⚠️ Could not fetch web results.")
            return
        answer = await self.run_gpt_with_context(query, snippets)
        await ctx.send(answer)

    async def chat_with_search(self, conversation, temperature=0.7):
        """
        For main.py to call when in active conversation mode.
        Checks if GPT output contains a SEARCH trigger and processes it.
        """
        last_user_msg = None
        for m in reversed(conversation):
            if m.get("role") == "user":
                last_user_msg = m.get("content")
                break
        if not last_user_msg:
            return "⚠️ No user message found in conversation."

        # First, let GPT generate the answer / detect search trigger
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {AIAPI}", "Content-Type": "application/json"}
        payload = {
            "model": AI_MODEL,
            "messages": conversation,
            "max_tokens": 300,
            "temperature": temperature,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                if resp.status != 200:
                    return f"❌ API request failed: {resp.status} - {await resp.text()}"
                data = await resp.json()

        try:
            gpt_output = data["choices"][0]["message"]["content"]
        except Exception:
            return "❌ Unexpected response from API."

        # Check for SEARCH trigger
        if gpt_output.startswith("SEARCH:"):
            return await self.handle_search_trigger(gpt_output)

        return gpt_output

async def setup(bot):
    await bot.add_cog(Search(bot))

