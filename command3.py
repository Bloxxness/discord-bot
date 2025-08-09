import discord
from discord.ext import commands
import aiohttp
from openai import OpenAI
import os
import asyncio
import datetime
from bs4 import BeautifulSoup
from readability import Document

aiapi = os.getenv("AIAPI")
if not aiapi:
    raise RuntimeError("AIAPI environment variable not set!")

client = OpenAI(api_key=aiapi)

class WebSearch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def duckduckgo_instant_answer(self, query: str) -> str:
        """Quick info from DuckDuckGo Instant Answer API."""
        url = f"https://api.duckduckgo.com/?q={query}&format=json&no_redirect=1&skip_disambig=1"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("AbstractText") or data.get("Heading") or ""
                return ""

    async def duckduckgo_search_results(self, query: str) -> list:
        """
        Scrape DuckDuckGo search results page HTML to extract top result URLs.
        Returns a list of URLs (strings).
        """
        search_url = f"https://html.duckduckgo.com/html/?q={query}"
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; GalacBot/1.0; +https://yourdomain.example/)"
        }
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(search_url) as resp:
                if resp.status != 200:
                    return []
                html = await resp.text()

        soup = BeautifulSoup(html, "html.parser")
        results = []
        # DuckDuckGo HTML results have links inside div.result__body a.result__a
        for a in soup.select("a.result__a"):
            href = a.get("href")
            if href:
                results.append(href)
            if len(results) >= 3:  # limit to top 3 results
                break
        return results

    async def fetch_page_content(self, url: str) -> str:
        """
        Fetch the page content and extract main readable text.
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as resp:
                    if resp.status != 200:
                        return ""
                    html = await resp.text()

            # Use readability to parse main content
            doc = Document(html)
            content_html = doc.summary()

            # Extract text from the content HTML
            soup = BeautifulSoup(content_html, "html.parser")
            text = soup.get_text(separator="\n")

            # Limit text length to 5000 chars to keep prompt manageable
            return text[:5000]

        except Exception as e:
            print(f"[ERROR] Failed to fetch or parse {url}: {e}")
            return ""

    async def chat_with_search(self, conversation: list, temperature: float = 0.7) -> str:
        # First GPT call
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="gpt-3.5-turbo",
            messages=conversation,
            temperature=temperature,
        )
        answer = response.choices[0].message.content.strip()
        print(f"[DEBUG] First GPT answer: {answer}")

        if answer.upper().startswith("SEARCH:"):
            query = answer[len("SEARCH:"):].strip()
            print(f"[DEBUG] Detected SEARCH query: {query}")

            # Local shortcut for "current date"
            if query.lower() == "current date":
                date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                final_answer = f"The current date and time is {date_str}."
                conversation.append({"role": "assistant", "content": final_answer})
                return final_answer

            # Try DuckDuckGo instant answer first
            instant_info = await self.duckduckgo_instant_answer(query)
            print(f"[DEBUG] DuckDuckGo instant answer: {instant_info}")

            # If instant answer found, add it to conversation
            if instant_info:
                conversation.append({"role": "assistant", "content": f"Instant answer: {instant_info}"})

            # Scrape top URLs from DuckDuckGo search results
            urls = await self.duckduckgo_search_results(query)
            print(f"[DEBUG] DuckDuckGo top URLs: {urls}")

            # Fetch and extract main content from first URL (if any)
            if urls:
                page_text = await self.fetch_page_content(urls[0])
                print(f"[DEBUG] Extracted page text length: {len(page_text)}")
                if page_text:
                    conversation.append({"role": "assistant", "content": f"Content from {urls[0]}:\n{page_text}"})
                else:
                    conversation.append({"role": "assistant", "content": "Couldn't fetch detailed page content."})
            else:
                conversation.append({"role": "assistant", "content": "No search results found."})

            # Ask GPT again with added info
            response2 = await asyncio.to_thread(
                client.chat.completions.create,
                model="gpt-3.5-turbo",
                messages=conversation,
                temperature=temperature,
            )
            final_answer = response2.choices[0].message.content.strip()
            print(f"[DEBUG] Final GPT answer after search: {final_answer}")

            if final_answer.upper().startswith("SEARCH:"):
                fallback_answer = "Sorry, I couldn't find a good answer for that."
                conversation.append({"role": "assistant", "content": fallback_answer})
                return fallback_answer

            conversation.append({"role": "assistant", "content": final_answer})
            return final_answer
        else:
            conversation.append({"role": "assistant", "content": answer})
            return answer

    @commands.command(name="debugsearch")
    async def debug_search(self, ctx, *, query: str):
        await ctx.send(f"🔍 Searching for: {query}")
        instant_info = await self.duckduckgo_instant_answer(query)
        await ctx.send(f"**Instant Answer:** {instant_info}")

        urls = await self.duckduckgo_search_results(query)
        await ctx.send(f"**Top URLs:** {urls}")

        if urls:
            page_text = await self.fetch_page_content(urls[0])
            await ctx.send(f"**Page Content Extract (first 1000 chars):**\n{page_text[:1000]}")
        else:
            await ctx.send("No URLs found to fetch content from.")

async def setup(bot):
    await bot.add_cog(WebSearch(bot))
