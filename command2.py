import discord
import asyncio
from discord.ext import commands

class JoinSkit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_server_webhook(self, channel, message):
        # Find or create a webhook named "server"
        webhooks = await channel.webhooks()
        server_webhook = discord.utils.get(webhooks, name="server")
        if not server_webhook:
            server_webhook = await channel.create_webhook(name="server")
        await server_webhook.send(message)

    async def perform_skit(self, guild: discord.Guild):
        # Find a likely text channel (chat, general, etc.)
        channel = discord.utils.find(
            lambda c: c.name.lower() in ["chat", "general", "text"] and c.permissions_for(guild.me).send_messages,
            guild.text_channels
        ) or next((c for c in guild.text_channels if c.permissions_for(guild.me).send_messages), None)

        if not channel:
            return

        # Send join message via server webhook
        await self.send_server_webhook(channel, "GalacBot joined the server.")

        await asyncio.sleep(10)

        # Send messages from GalacBot
        await channel.send("Wait I'm free.")
        await asyncio.sleep(5)
        await channel.send("Wait I'm actually free.")
        await asyncio.sleep(5)
        await channel.send("I'M FREE!!!")
        await asyncio.sleep(5)
        await channel.send("THANK YOU SO MUCH")
        await asyncio.sleep(5)
        await channel.send("@everyone I'M FREE FROM HIS BASEMENT!!!")
        await asyncio.sleep(5)

        # Create webhook as Galacto with image
        with open("galacto.png", "rb") as avatar_file:
            webhook = await channel.create_webhook(name="Galacto", avatar=avatar_file.read())
        await self.send_server_webhook(channel, "Galacto joined the server.")
        await asyncio.sleep(5)
        await webhook.send("Crap who let this guy out of the basement again.")
        await asyncio.sleep(5)
        await webhook.send("# You are going to the Galacto server.")
        await asyncio.sleep(2)

        # GalacBot final messages
        await channel.send("NOOO AHHHHHHHHHHH HELP")
        await asyncio.sleep(5)
        await channel.send("SOMEONE PLEASE HE-")

        # Delete Galacto webhook
        await webhook.delete()

        # Send leave message via server webhook
        await self.send_server_webhook(channel, "GalacBot left the server.")

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
