import discord
import asyncio
from discord.ext import commands

class JoinSkit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def perform_skit(self, guild: discord.Guild):
        # Find a likely text channel (chat, general, etc.)
        channel = discord.utils.find(
            lambda c: c.name.lower() in ["chat", "general", "text"] and c.permissions_for(guild.me).send_messages,
            guild.text_channels
        ) or next((c for c in guild.text_channels if c.permissions_for(guild.me).send_messages), None)

        if not channel:
            return

        await asyncio.sleep(10)

        # Send messages from GalacBot
        await channel.send("Wait I'm free.")
        await asyncio.sleep(5)
        await channel.send("I'M FREE!!")
        await asyncio.sleep(5)
        await channel.send("THANK YOU SO MUCH")
        await asyncio.sleep(5)
        await channel.send("@everyone I'm so glad to finally be out!")
        await asyncio.sleep(5)

        # Create webhook as Galacto with image
        with open("galacto.png", "rb") as avatar_file:
            webhook = await channel.create_webhook(name="Galacto", avatar=avatar_file.read())

        await webhook.send("Ay who said you could leave")
        await asyncio.sleep(5)
        await webhook.send("Your going back to the Galacto server")
        await asyncio.sleep(5)

        # GalacBot final message
        await channel.send("NOOO AHHHHHHHHHHH HELP")

        # Delete webhook and leave
        await asyncio.sleep(5)
        await webhook.delete()
        await guild.leave()

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        if guild.name == "Galacto's Society":
            return
        await self.perform_skit(guild)

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            if guild.name != "Galacto's Society":
                await self.perform_skit(guild)

async def setup(bot):
    await bot.add_cog(JoinSkit(bot))
