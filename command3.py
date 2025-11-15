import discord
from discord.ext import commands
import os
import aiohttp

# ====== CONFIG ======
AIAPI = os.getenv("AIAPI")  # OpenAI API key
AI_MODEL = "gpt-5"          # OpenAI model
# ====================


class Search(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # =============================
    # DUCKDUCKGO SEARCH (NO API KEY)
    # =============================
    async def perform_duckduckgo(self, query: str, max_results: int = 5):
        """Perform DuckDuckGo web search (free API)."""
        url = "https://api.duckduckgo.com/?q={}&format=json&no_redirect=1&no_html=1".format(query)

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return []

                data = await resp.json()

        results = []

        # Use abstract + related topics
        if "Abstract" in data and data["Abstract"]:
            results.append({
                "title": data.get("Heading", "Result"),
                "url": data.get("AbstractURL", ""),
                "snippet": data.get("Abstract", "")
            })

        for t in data.get("RelatedTopics", []):
            if isinstance(t, dict) and "Text" in t and "FirstURL" in t:
                results.append({
                    "title": t.get("Text", "").split(" - ")[0],
                    "url": t.get("FirstURL", ""),
                    "snippet": t.get("Text", "")
                })

        return results[:max_results]

    # =============================
    # GPT ANSWERING WITH CONTEXT
    # =============================
    async def run_gpt_with_context(self, query: str, context_snippets):
        snippet_text = "\n".join(
            f"{i+1}. {s['title']}\nURL: {s['url']}\n{s['snippet']}\n"
            for i, s in enumerate(context_snippets)
        )

        if not snippet_text.strip():
            snippet_text = "No results found."

        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {AIAPI}", "Content-Type": "application/json"}

        messages = [
            {"role": "system", "content": "You summarize information concisely using provided web search results. NEVER output SEARCH: unless the user explicitly asks."},
            {"role": "user", "content": f"Use these search results to answer the question.\n\n{snippet_text}\n\nQuestion: {query}"}
        ]

        payload = {
            "model": AI_MODEL,
            "messages": messages,
            "max_completion_tokens": 600,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    return f"❌ GPT API error {resp.status}: {text}"

                data = await resp.json()

        output = data.get("choices", [{}])[0].get("message", {}).get("content", "")

        if not output.strip():
            return "⚠️ GPT returned an empty response."

        return output

    # =============================
    # DISCORD COMMAND: /search
    # =============================
    @commands.command(name="search", help="Search the web using DuckDuckGo and summarize results.")
    async def search_command(self, ctx, *, query: str):
        await ctx.send(f"🔍 Searching the web for: **{query}**")

        snippets = await self.perform_duckduckgo(query)

        if not snippets:
            await ctx.send("⚠️ No results found.")
            return

        answer = await self.run_gpt_with_context(query, snippets)

        # Avoid empty message crash
        if not answer.strip():
            answer = "⚠️ Got an empty answer from GPT."

        await ctx.send(answer)

    # =============================
    # CHAT MODE WITH OPTIONAL SEARCH
    # =============================
    async def chat_with_search(self, conversation):
        """GPT conversation with optional SEARCH trigger."""
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {AIAPI}", "Content-Type": "application/json"}

        payload = {
            "model": AI_MODEL,
            "messages": conversation,
            "max_completion_tokens": 300
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                if resp.status != 200:
                    return f"❌ GPT error {resp.status}: {await resp.text()}"

                data = await resp.json()

        gpt_output = data.get("choices", [{}])[0].get("message", {}).get("content", "")

        if not gpt_output.strip():
            return "⚠️ GPT returned an empty message."

        # Detect SEARCH trigger
        if gpt_output.startswith("SEARCH:"):
            query = gpt_output[len("SEARCH:"):].strip()
            snippets = await self.perform_duckduckgo(query)

            if not snippets:
                return "⚠️ Web search returned no results."

            return await self.run_gpt_with_context(query, snippets)

        return gpt_output


async def setup(bot):
    await bot.add_cog(Search(bot))
