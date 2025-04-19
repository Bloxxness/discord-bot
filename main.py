import discord
from discord.ext import commands
import os
from keep_alive import keep_alive

keep_alive()

# Role names
VERIFIED_ROLE_NAME = "[✅] Verified"
UNVERIFIED_ROLE_NAME = "[❌] Unverified"
FANS_ROLE_NAME = "[ᓘ] Fans"

# Intents setup
intents = discord.Intents.default()
intents.members = True
intents.guilds = True

# Bot setup
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot is online as {bot.user}")

    for guild in bot.guilds:
        print(f"🔍 Checking members in guild: {guild.name}")
        verified_role = discord.utils.get(guild.roles, name=VERIFIED_ROLE_NAME)
        unverified_role = discord.utils.get(guild.roles, name=UNVERIFIED_ROLE_NAME)
        fans_role = discord.utils.get(guild.roles, name=FANS_ROLE_NAME)

        if not verified_role or not unverified_role or not fans_role:
            print("⚠️ One or more roles not found. Skipping.")
            continue

        for member in guild.members:
            # If member has Verified role
            if verified_role in member.roles:
                # If they have Unverified, remove it
                if unverified_role in member.roles:
                    await member.remove_roles(unverified_role)
                    print(f"🧙‍♂️ Removed '{UNVERIFIED_ROLE_NAME}' from {member.display_name}")

                # If they don't have Fans, add it
                if fans_role not in member.roles:
                    await member.add_roles(fans_role)
                    print(f"🌟 Added '{FANS_ROLE_NAME}' to {member.display_name}")

@bot.event
async def on_member_update(before, after):
    before_roles = [role.name for role in before.roles]
    after_roles = [role.name for role in after.roles]

    guild = after.guild
    verified_role = discord.utils.get(guild.roles, name=VERIFIED_ROLE_NAME)
    unverified_role = discord.utils.get(guild.roles, name=UNVERIFIED_ROLE_NAME)
    fans_role = discord.utils.get(guild.roles, name=FANS_ROLE_NAME)

    # If Verified was added
    if VERIFIED_ROLE_NAME not in before_roles and VERIFIED_ROLE_NAME in after_roles:
        if fans_role and fans_role not in after.roles:
            await after.add_roles(fans_role)
            print(f"🌟 Added '{FANS_ROLE_NAME}' to {after.display_name}")

        if unverified_role and unverified_role in after.roles:
            await after.remove_roles(unverified_role)
            print(f"❌ Removed '{UNVERIFIED_ROLE_NAME}' from {after.display_name}")

    # If Verified was removed
    if VERIFIED_ROLE_NAME in before_roles and VERIFIED_ROLE_NAME not in after_roles:
        if fans_role and fans_role in after.roles:
            await after.remove_roles(fans_role)
            print(f"🚫 Removed '{FANS_ROLE_NAME}' from {after.display_name}")

# Start the bot
bot.run(os.getenv("TOKEN"))
