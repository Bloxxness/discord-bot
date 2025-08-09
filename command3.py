import discord
from discord.ext import commands
import aiohttp
from openai import OpenAI
import os
import asyncio
import urllib.parse

aiapi = os.getenv("AIAPI")
if not aiapi:
    raise RuntimeError("AIAPI environment variable not set!")

client = OpenAI(api_key=aiapi)


class WebSearch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def duckduckgo_search(self, query: str) -> str:
        """Fetch quick info from DuckDuckGo Instant Answer API (async)."""
        q = urllib.parse.quote_plus(query)
        url = f"https://api.duckduckgo.com/?q={q}&format=json&no_html=1&skip_disambig=1"
        timeout = aiohttp.ClientTimeout(total=10)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("AbstractText") or data.get("Heading") or "No information found."
                    return f"Search failed (status {resp.status})."
        except Exception as e:
            return f"Search error: {e}"

    async def _call_openai_sync(self, messages, temperature):
        """
        Run blocking OpenAI client call in a thread to avoid blocking the event loop.
        Returns the raw response object from the OpenAI client.
        """
        loop = asyncio.get_running_loop()

        def sync_call():
            return client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=temperature
            )

        return await loop.run_in_executor(None, sync_call)

    async def chat_with_search(self, conversation: list, temperature: float = 0.7) -> str:
        """
        1) Send the current conversation to the model.
        2) If the model outputs a `SEARCH:` instruction in its reply, run a DuckDuckGo lookup,
           append results into the conversation and ask the model again.
        3) Return final answer text.
        NOTE: The model must output `SEARCH: <query>` if it needs the bot to fetch live info.
        """
        try:
            # First (blocking) call moved to thread
            response = await self._call_openai_sync(conversation, temperature)
            answer = response.choices[0].message.content.strip()
        except Exception as e:
            return f"OpenAI call failed: {e}"

        # Look for a SEARCH trigger (case-insensitive)
        if "SEARCH:" in answer.upper():
            idx = answer.upper().find("SEARCH:")
            query = answer[idx + len("SEARCH:"):].strip()
            if not query:
                return "⚠️ Model requested a search but did not provide a query."

            # Fetch search result (async)
            search_result = await self.duckduckgo_search(query)

            # Append search results and ask the model again
            conversation.append({"role": "assistant", "content": f"Search results: {search_result}"})
            try:
                response2 = await self._call_openai_sync(conversation, temperature)
                final_answer = response2.choices[0].message.content.strip()
                conversation.append({"role": "assistant", "content": final_answer})
                return final_answer
            except Exception as e:
                return f"OpenAI follow-up failed: {e}"
        else:
            # No search requested; append and return
            conversation.append({"role": "assistant", "content": answer})
            return answer

    @commands.command(name="debugsearch")
    async def debug_search(self, ctx, *, query: str):
        """Debug command to test DuckDuckGo integration."""
        await ctx.send(f"🔍 Searching for: {query}")
        result = await self.duckduckgo_search(query)
        await ctx.send(f"**Search Result:** {result}")


async def setup(bot):
    await bot.add_cog(WebSearch(bot))
