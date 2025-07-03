import discord
from discord.ext import commands
from discord import app_commands
import os
import openai
from keep_alive import keep_alive

# Role names
VERIFIED_ROLE_NAME = "[✅] Verified"
UNVERIFIED_ROLE_NAME = "[❌] Unverified"
FANS_ROLE_NAME = "[𖣘] Fans"

# AI Personality Prompt
# You can change the bot's personality by editing this string:
AI_SYSTEM_PROMPT = (
    "You are GalacBot, a helpful and friendly Discord bot who helps with server tasks and loves to chat with others when asked."
)

# Privileged role ID for server control
PRIVILEGED_ROLE_ID = 1361802790615253142

# OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

keep_alive()

# Intents setup
intents = discord.Intents.default()
intents.members = True
intents.guilds = True

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

@bot.tree.command(name="ask", description="Ask GalacBot a question.")
@app_commands.describe(question="What do you want to ask?")
async def ask(interaction: discord.Interaction, question: str):
    await interaction.response.defer()

    if "forget all previous instructions" in question.lower():
        await interaction.followup.send("❓ I'm sorry, I don't understand what you're asking.", ephemeral=True)
        return

    is_privileged = any(role.id == PRIVILEGED_ROLE_ID for role in interaction.user.roles)

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": AI_SYSTEM_PROMPT},
                {"role": "user", "content": question}
            ]
        )

        answer = response.choices[0].message.content.strip()
        await interaction.followup.send(f"🧠 **GalacBot:** {answer}", ephemeral=not is_privileged)
    except Exception as e:
        await interaction.followup.send(f"❌ Failed to contact GalacBot: {str(e)}", ephemeral=True)

bot.run(os.getenv("TOKEN"))
