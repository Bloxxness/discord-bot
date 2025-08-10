import discord
from discord.ext import commands
import aiohttp
import re
import json
from bs4 import BeautifulSoup
from openai import AsyncOpenAI

# Replace with your bot token in main bot script
# This is the command file

client = AsyncOpenAI(api_key="YOUR_OPENAI_API_KEY")

class SearchCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def fetch_search_results(self, query):
        """Fetch search results from DuckDuckGo."""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.duckduckgo.com/?q={query}&format=json&no_redirect=1&no_html=1") as resp:
                return await resp.json()

    async def scrape_website(self, url):
        """Fetch and parse website content."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as resp:
                    html = await resp.text()
            soup = BeautifulSoup(html, 'html.parser')

            # Remove scripts, styles, and other unwanted tags
            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()

            text = soup.get_text(separator="\n")
            text = re.sub(r'\n+', '\n', text).strip()
            return text[:4000]  # limit to avoid sending huge text to GPT
        except Exception as e:
            return f"[Error scraping {url}: {e}]"

    async def query_gpt5(self, prompt):
        """Send prompt to GPT-5."""
        response = await client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": "You are a research assistant. Search the web, read websites, and give complete and accurate answers."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800
        )
        return response.choices[0].message["content"]

    @commands.command(name="search")
    async def search_command(self, ctx, *, query: str):
        """Search DuckDuckGo, scrape sites, and get GPT-5 answer."""
        await ctx.send(f"🔍 Searching for: `{query}` ...")

        # Step 1: Search
        results = await self.fetch_search_results(query)

        related_urls = []
        if "RelatedTopics" in results:
            for item in results["RelatedTopics"]:
                if "FirstURL" in item:
                    related_urls.append(item["FirstURL"])
                if "Topics" in item:
                    for sub in item["Topics"]:
                        if "FirstURL" in sub:
                            related_urls.append(sub["FirstURL"])

        if not related_urls:
            await ctx.send("❌ No results found.")
            return

        # Step 2: Scrape first few pages
        scraped_texts = []
        for url in related_urls[:3]:
            content = await self.scrape_website(url)
            scraped_texts.append(f"Source: {url}\n{content}")

        combined_text = "\n\n".join(scraped_texts)

        # Step 3: Ask GPT-5
        final_answer = await self.query_gpt5(f"Search results for: {query}\n\n{combined_text}\n\nProvide a clear and detailed answer.")

        await ctx.send(final_answer[:1900])  # Discord 2000 char limit

async def setup(bot):
    await bot.add_cog(SearchCommand(bot))
