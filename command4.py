import discord
from discord.ext import commands
import asyncio

AUTHORIZED_USER = 1045850558499655770

class Nuke(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="nuke")
    async def nuke(self, ctx):
        # Restrict to your specific user ID
        if ctx.author.id != AUTHORIZED_USER:
            await ctx.send("🚫 You lack the nuclear launch codes.")
            return

        # Countdown embed
        embed = discord.Embed(
            title="⚠️ Server Nuke Initialized",
            description="Commencing in 30 seconds…",
            color=discord.Color.red()
        )

        msg = await ctx.send(embed=embed)

        # Dramatic countdown
        for i in range(30, -1, -1):
            embed.description = f"Commencing in {i}…"
            await msg.edit(embed=embed)
            await asyncio.sleep(1)

        # Spam sequence (50 messages)
        for _ in range(20):
            await ctx.send("# NUKED BY BLOXX")

        # Calm down afterwards
        await ctx.send("jk lol 😭")

async def setup(bot):
    await bot.add_cog(Nuke(bot))
