import discord
from discord.ext import commands
from discord import app_commands
import os
from openai import OpenAI
from keep_alive import keep_alive

print("OPENAI_API_KEY =", os.getenv("OPENAI_API_KEY"))
print("TOKEN =", os.getenv("TOKEN"))

# Role names
VERIFIED_ROLE_NAME = "[✅] Verified"
UNVERIFIED_ROLE_NAME = "[❌] Unverified"
FANS_ROLE_NAME = "[𖣘] Fans"

# AI Personality Prompt
AI_SYSTEM_PROMPT = (
    "You are GalacBot, a happy and joyful Discord bot who helps with server tasks and loves chatting naturally and helpfully."
)

# Privileged role ID for server control
PRIVILEGED_ROLE_ID = 1361802790615253142

# Initialize OpenAI client explicitly with your env var OPENAI_API_KEY
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise RuntimeError("OPENAI_API_KEY environment variable not set!")

bot_token = os.getenv("TOKEN")
if not bot_token:
    raise RuntimeError("TOKEN environment variable not set!")

client = OpenAI(api_key=openai_api_key)

keep_alive()

# Intents setup
intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.message_content = True  # Needed to read message content for chat

bot = commands.Bot(command_prefix="!", intents=intents)

# Store active conversations per user id
active_conversations = {}

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

@bot.tree.command(name="ask", description="Start a chat with GalacBot.")
async def ask(interaction: discord.Interaction):
    user_id = interaction.user.id
    if user_id in active_conversations:
        await interaction.response.send_message("You already have an active chat session! Just send me messages here.", ephemeral=True)
        return

    # Initialize conversation history for user
    active_conversations[user_id] = [
        {"role": "system", "content": AI_SYSTEM_PROMPT},
        {"role": "assistant", "content": "Hi! I'm GalacBot the local server helper! How may I be of assistance?"}
    ]

    await interaction.response.send_message("Hi! I'm GalacBot the local server helper! How may I be of assistance? Please just message me here to chat!", ephemeral=False)

@bot.tree.command(name="endchat", description="End your chat session with GalacBot.")
async def endchat(interaction: discord.Interaction):
    user_id = interaction.user.id
    if user_id in active_conversations:
        active_conversations.pop(user_id)
        await interaction.response.send_message("🛑 Your chat session has been ended. Thanks for chatting!", ephemeral=True)
    else:
        await interaction.response.send_message("You don't have an active chat session to end.", ephemeral=True)

@bot.event
async def on_message(message):
    if message.author.bot:
        return  # Ignore other bots

    user_id = message.author.id

    if user_id in active_conversations:
        bot_name = "galacbot"
        content_lower = message.content.lower()
        bot_mentioned = bot.user in message.mentions
        name_mentioned = bot_name in content_lower

        if bot_mentioned or name_mentioned:
            conversation = active_conversations[user_id]
            conversation.append({"role": "user", "content": message.content})

            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=conversation,
                    temperature=0.7
                )
                answer = response.choices[0].message.content.strip()
                conversation.append({"role": "assistant", "content": answer})
                await message.channel.send(f"🧠 **GalacBot:** {answer}")
            except Exception as e:
                await message.channel.send(f"❌ Sorry, I had trouble responding: {str(e)}")
        else:
            # Ignore if user not addressing the bot
            pass
    else:
        await bot.process_commands(message)

bot.run(bot_token)
