
import discord
from discord.ext import commands
from discord import app_commands
import os
print("TOKEN:", os.getenv("TOKEN"))
# Hi Galacto
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
    await bot.tree.sync()
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
            # Remove Unverified if already Verified
            if verified_role in member.roles and unverified_role in member.roles:
                await member.remove_roles(unverified_role)
                print(f"🧙‍♂️ Removed '{UNVERIFIED_ROLE_NAME}' from {member.display_name}")

            # Add Fans if Verified but doesn't have Fans yet
            if verified_role in member.roles and fans_role not in member.roles:
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

    # If Verified added
    if VERIFIED_ROLE_NAME not in before_roles and VERIFIED_ROLE_NAME in after_roles:
        if fans_role and fans_role not in after.roles:
            await after.add_roles(fans_role)
            print(f"🌟 Added '{FANS_ROLE_NAME}' to {after.display_name}")

        if unverified_role and unverified_role in after.roles:
            await after.remove_roles(unverified_role)
            print(f"❌ Removed '{UNVERIFIED_ROLE_NAME}' from {after.display_name}")

    # If Verified removed
    if VERIFIED_ROLE_NAME in before_roles and VERIFIED_ROLE_NAME not in after_roles:
        if fans_role and fans_role in after.roles:
            await after.remove_roles(fans_role)
            print(f"🚫 Removed '{FANS_ROLE_NAME}' from {after.display_name}")

@bot.tree.command(name="giverole", description="Give a role to a user.")
@app_commands.describe(member="The user you want to give the role to", role_name="The name of the role you want to give")
async def giverole(interaction: discord.Interaction, member: discord.Member, role_name: str):
    # Only allow the user 'bloxxnes' to use this command
    if interaction.user.name.lower() != "bloxxnes":
        await interaction.response.send_message("🚫 You don't have permission to use this command.", ephemeral=True)
        return

    role = discord.utils.get(interaction.guild.roles, name=role_name)
    if not role:
        await interaction.response.send_message(f"⚠️ Role '{role_name}' not found.", ephemeral=True)
        return

    try:
        await member.add_roles(role)
        await interaction.response.send_message(f"✅ Gave '{role.name}' to {member.mention}!")
    except discord.Forbidden:
        await interaction.response.send_message("⚠️ I don't have permission to assign that role.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)

# Start the bot
bot.run(os.getenv("TOKEN"))
