import discord
from discord.ext import commands
import os
from keep_alive import keep_alive

keep_alive()

# Role names — must match exactly what’s in your Discord server
VERIFIED_ROLE_NAME = "[✅] Verified"
UNVERIFIED_ROLE_NAME = "[❌] Unverified"

# Intents setup — this is required for tracking role changes
intents = discord.Intents.default()
intents.members = True
intents.guilds = True

# Bot setup
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot is online as {bot.user}")

    # NEW: Go through all members and remove Unverified if they already have Verified
    for guild in bot.guilds:
        print(f"🔍 Checking members in guild: {guild.name}")
        verified_role = discord.utils.get(guild.roles, name=VERIFIED_ROLE_NAME)
        unverified_role = discord.utils.get(guild.roles, name=UNVERIFIED_ROLE_NAME)

        if not verified_role or not unverified_role:
            print("⚠️ One or both roles not found in this guild. Skipping.")
            continue

        for member in guild.members:
            if verified_role in member.roles and unverified_role in member.roles:
                await member.remove_roles(unverified_role)
                print(f"🧹 Removed '{UNVERIFIED_ROLE_NAME}' from {member.display_name}")


@bot.event
async def on_member_update(before, after):
    before_roles = [role.name for role in before.roles]
    after_roles = [role.name for role in after.roles]

    if VERIFIED_ROLE_NAME in after_roles and UNVERIFIED_ROLE_NAME in before_roles:
        unverified_role = discord.utils.get(after.guild.roles, name=UNVERIFIED_ROLE_NAME)
        if unverified_role:
            await after.remove_roles(unverified_role)
            print(f"❌ Removed '{UNVERIFIED_ROLE_NAME}' from {after.display_name}")

# Start web server to keep Replit awake

# Start the bot using your token from .env
bot.run(os.getenv("TOKEN"))
