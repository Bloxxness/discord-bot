import discord
from discord.ext import commands
import aiohttp
from openai import OpenAI
import os

aiapi = os.getenv("AIAPI")
if not aiapi:
    raise RuntimeError("AIAPI environment variable not set!")

client = OpenAI(api_key=aiapi)

class WebSearch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def duckduckgo_search(self, query: str) -> str:
        """Fetch quick info from DuckDuckGo Instant Answer API."""
        url = f"https://api.duckduckgo.com/?q={query}&format=json&no_redirect=1&skip_disambig=1"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    # Prefer AbstractText, then Heading, else fallback text
                    return data.get("AbstractText") or data.get("Heading") or "No information found."
                else:
                    return f"Search failed with status {resp.status}."

    async def chat_with_search(self, conversation: list, temperature: float = 0.7) -> str:
        """
        Sends conversation to OpenAI, checks for SEARCH: triggers,
        fetches real data if needed, then re-asks AI with search results.
        """
        # First GPT call
        response = await asyncio.to_thread(
        client.chat.completions.create,
            model="gpt-3.5-turbo",
            messages=conversation,
            temperature=temperature,
        )
        answer = response.choices[0].message.content.strip()

        if "SEARCH:" in answer:
            query = answer.split("SEARCH:", 1)[1].strip()
            search_result = await self.duckduckgo_search(query)

            conversation.append({"role": "assistant", "content": f"Search results: {search_result}"})

            # Ask GPT again with updated context
            response2 = await client.chat.completions.acreate(
                model="gpt-3.5-turbo",
                messages=conversation,
                temperature=temperature
            )
            final_answer = response2.choices[0].message.content.strip()
            conversation.append({"role": "assistant", "content": final_answer})
            return final_answer
        else:
            conversation.append({"role": "assistant", "content": answer})
            return answer

    @commands.command(name="debugsearch")
    async def debug_search(self, ctx, *, query: str):
        """Debug command to test DuckDuckGo search directly."""
        await ctx.send(f"🔍 Searching for: {query}")
        result = await self.duckduckgo_search(query)
        await ctx.send(f"**Search Result:** {result}")

async def setup(bot):
    await bot.add_cog(WebSearch(bot))



async def setup(bot):
    await bot.add_cog(WebSearch(bot))
