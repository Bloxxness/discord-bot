import discord
from discord.ext import commands
import requests
from bs4 import BeautifulSoup
import urllib.parse

class Search(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def duckduckgo_search(self, query):
        """Search DuckDuckGo and return top results."""
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_redirect": 1,
            "no_html": 1,
            "skip_disambig": 1
        }
        try:
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if data.get("AbstractText"):
                return data["AbstractText"]
            elif data.get("RelatedTopics"):
                topics = [t.get("Text") for t in data["RelatedTopics"] if "Text" in t][:3]
                return "\n".join(topics) if topics else None
            return None
        except Exception as e:
            return f"Error: {e}"

    def fetch_webpage_content(self, url):
        """Fetch and clean text content from a webpage."""
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # Remove scripts, styles, navs
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()

            text = soup.get_text(separator="\n")
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            cleaned_text = "\n".join(lines)
            return cleaned_text[:1500] + "..." if len(cleaned_text) > 1500 else cleaned_text
        except Exception as e:
            return f"Failed to fetch page: {e}"

    def get_first_result_url(self, query):
        """Get first URL result from DuckDuckGo HTML search."""
        try:
            encoded_query = urllib.parse.quote_plus(query)
            search_url = f"https://duckduckgo.com/html/?q={encoded_query}"
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(search_url, headers=headers, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            links = soup.select(".result__a")
            if links:
                return links[0].get("href")
            return None
        except Exception as e:
            return None

    @commands.command(name="search", help="Search DuckDuckGo and optionally fetch the top site.")
    async def search_command(self, ctx, *, query: str):
        await ctx.send(f"🔍 Searching for: **{query}**")

        # Step 1: Try DuckDuckGo Instant Answer
        snippet = self.duckduckgo_search(query)

        if snippet and len(snippet) > 20:
            await ctx.send(f"**DuckDuckGo says:**\n{snippet}")
        else:
            await ctx.send("⚠️ No useful snippet found. Trying to fetch a top website...")

            # Step 2: Get first result URL
            first_url = self.get_first_result_url(query)
            if not first_url:
                await ctx.send("❌ No search results found.")
                return

            # Step 3: Fetch and display webpage content
            content = self.fetch_webpage_content(first_url)
            await ctx.send(f"**From:** {first_url}\n\n{content}")

async def setup(bot):
    await bot.add_cog(Search(bot))
