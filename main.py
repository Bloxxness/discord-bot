import discord
from discord.ext import commands
from discord import app_commands
import os
from keep_alive import keep_alive

# Hi Galacto
# Role names
VERIFIED_ROLE_NAME = "[✅] Verified"
UNVERIFIED_ROLE_NAME = "[❌] Unverified"
FANS_ROLE_NAME = "[�] Fans"

# Keep Alive
keep_alive()

# Intents setup
intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.message_content = True  # Required for on_message

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
            if verified_role in member.roles and unverified_role in member.roles:
                await member.remove_roles(unverified_role)
                print(f"🧙‍♂️ Removed '{UNVERIFIED_ROLE_NAME}' from {member.display_name}")

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

    if VERIFIED_ROLE_NAME not in before_roles and VERIFIED_ROLE_NAME in after_roles:
        if fans_role and fans_role not in after.roles:
            await after.add_roles(fans_role)
            print(f"🌟 Added '{FANS_ROLE_NAME}' to {after.display_name}")

        if unverified_role and unverified_role in after.roles:
            await after.remove_roles(unverified_role)
            print(f"❌ Removed '{UNVERIFIED_ROLE_NAME}' from {after.display_name}")

    if VERIFIED_ROLE_NAME in before_roles and VERIFIED_ROLE_NAME not in after_roles:
        if fans_role and fans_role in after.roles:
            await after.remove_roles(fans_role)
            print(f"🚫 Removed '{FANS_ROLE_NAME}' from {after.display_name}")

@bot.tree.command(name="giverole", description="Give a role to a user.")
@app_commands.describe(member="The user you want to give the role to", role_name="The name or mention of the role you want to give")
async def giverole(interaction: discord.Interaction, member: discord.Member, role_name: str):
    await interaction.response.defer(ephemeral=True)

    ALLOWED_USER_IDS = [
        1045850558499655770,
        1236750566408061060,
    ]

    if interaction.user.id not in ALLOWED_USER_IDS:
        await interaction.followup.send("🚫 You don't have permission to use this command.", ephemeral=True)
        return

    role = None
    if role_name.startswith("<@&") and role_name.endswith(">"):
        role_id = int(role_name[3:-1])
        role = interaction.guild.get_role(role_id)
    else:
        role = discord.utils.find(lambda r: r.name.lower() == role_name.lower(), interaction.guild.roles)

    if not role:
        await interaction.followup.send(f"⚠️ Role '{role_name}' not found.", ephemeral=True)
        return

    try:
        await member.add_roles(role)
        await interaction.followup.send(f"✅ Gave '{role.name}' to {member.mention}!", ephemeral=True)
    except discord.Forbidden:
        await interaction.followup.send("⚠️ I don't have permission to assign that role.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    trigger_phrases = ["tv women is hot", "tv woman is hot", "tv women hot", "tv girl hot"]
    content_lower = message.content.lower()

    if any(phrase in content_lower for phrase in trigger_phrases):
        try:
            log_channel = bot.get_channel(1351710526283190373)
            await message.delete()
            await message.author.kick(reason="Sent prohibited message: 'tv women is hot'")

            embed = discord.Embed(
                title="🚨 User Kicked for Inappropriate Message",
                description=f"**Message:** {message.content}",
                color=discord.Color.red()
            )
            embed.set_thumbnail(url=message.author.display_avatar.url)
            embed.add_field(name="Username", value=message.author.name, inline=True)
            embed.add_field(name="Display Name", value=message.author.display_name, inline=True)
            embed.add_field(name="User ID", value=str(message.author.id), inline=False)
            embed.set_footer(text=f"User was kicked from {message.guild.name}")

            if log_channel:
                await log_channel.send(embed=embed)

        except Exception as e:
            print(f"Error handling message: {e}")

    await bot.process_commands(message)

# Start the bot
bot.run(os.getenv("TOKEN"))
