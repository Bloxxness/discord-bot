import discord
from discord.ext import commands
from discord import app_commands
import asyncio

AUTHORIZED_USER = 1045850558499655770

# Zero-width space to hide it from the slash menu
HIDDEN_PREFIX = "\u200B"  # zero width space

class NukePrank(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name=f"{HIDDEN_PREFIX}nuke",
        description="Totally real and very scary server nuke. (Hidden command)"
    )
    async def nuke(self, interaction: discord.Interaction):

        if interaction.user.id != AUTHORIZED_USER:
            await interaction.response.send_message(
                "You do not possess the forbidden detonator.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="⚠️ Server Nuke Initialized",
            description="Commencing in **30 seconds**…",
            color=discord.Color.red()
        )
        embed.set_footer(text="Stand by for detonation sequence.")

        await interaction.response.send_message(embed=embed)
        msg = await interaction.original_response()

        for i in range(30, -1, -1):
            embed.description = f"Commencing in **{i} seconds**…"
            await msg.edit(embed=embed)
            await asyncio.sleep(1)

        channel = interaction.channel
        for _ in range(50):
            await channel.send("# Nuked by Bloxx!")
            await asyncio.sleep(0)

        await channel.send("jk lol 😭")


async def setup(bot):
    await bot.add_cog(NukePrank(bot))
