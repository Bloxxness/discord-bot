import discord
from discord.ext import commands
from discord import app_commands
import os
from openai import OpenAI
from keep_alive import keep_alive

# Role names
verifiedrolename = "[✅] Verified"
unverifiedrolename = "[❌] Unverified"
fansrolename = "[𖣘] Fans"

# AI Personality Prompt
aisystemprompt = (
    "You are GalacBot, a happy and joyful Discord bot who helps with server tasks and loves chatting naturally and helpfully."
)

# Privileged role ID for server control
privilegedroleid = 1361802790615253142

# Initialize OpenAI client explicitly with your env var OPENAIAPIKEY
openaiapikey = os.getenv("OPENAIAPIKEY")
if not openaiapikey:
    raise RuntimeError("OPENAIAPIKEY environment variable not set!")

bottoken = os.getenv("TOKEN")
if not bottoken:
    raise RuntimeError("TOKEN environment variable not set!")

client = OpenAI(api_key=openaiapikey)

keep_alive()

# Intents setup
intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.message_content = True  # Needed to read message content for chat

bot = commands.Bot(command_prefix="!", intents=intents)

# Store active conversations per user id
activeconversations = {}

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot is online as {bot.user}")

    for guild in bot.guilds:
        print(f"🔍 Checking members in guild: {guild.name}")
        verifiedrole = discord.utils.get(guild.roles, name=verifiedrolename)
        unverifiedrole = discord.utils.get(guild.roles, name=unverifiedrolename)
        fansrole = discord.utils.get(guild.roles, name=fansrolename)

        if not verifiedrole or not unverifiedrole or not fansrole:
            print("⚠️ One or more roles not found. Skipping.")
            continue

        for member in guild.members:
            if verifiedrole in member.roles and unverifiedrole in member.roles:
                await member.remove_roles(unverifiedrole)
                print(f"🧙‍♂️ Removed '{unverifiedrolename}' from {member.display_name}")
            if verifiedrole in member.roles and fansrole not in member.roles:
                await member.add_roles(fansrole)
                print(f"🌟 Added '{fansrolename}' to {member.display_name}")

@bot.event
async def on_member_update(before, after):
    beforeroles = [role.name for role in before.roles]
    afterroles = [role.name for role in after.roles]

    guild = after.guild
    verifiedrole = discord.utils.get(guild.roles, name=verifiedrolename)
    unverifiedrole = discord.utils.get(guild.roles, name=unverifiedrolename)
    fansrole = discord.utils.get(guild.roles, name=fansrolename)

    if verifiedrolename not in beforeroles and verifiedrolename in afterroles:
        if fansrole and fansrole not in after.roles:
            await after.add_roles(fansrole)
            print(f"🌟 Added '{fansrolename}' to {after.display_name}")
        if unverifiedrole and unverifiedrole in after.roles:
            await after.remove_roles(unverifiedrole)
            print(f"❌ Removed '{unverifiedrolename}' from {after.display_name}")

    if verifiedrolename in beforeroles and verifiedrolename not in afterroles:
        if fansrole and fansrole in after.roles:
            await after.remove_roles(fansrole)
            print(f"🚫 Removed '{fansrolename}' from {after.display_name}")

@bot.tree.command(name="giverole", description="Give a role to a user.")
@app_commands.describe(member="The user you want to give the role to", role_name="The name or mention of the role you want to give")
async def giverole(interaction: discord.Interaction, member: discord.Member, role_name: str):
    await interaction.response.defer(ephemeral=True)

    alloweduserids = [
        1045850558499655770,
        1236750566408061060,
    ]

    if interaction.user.id not in alloweduserids:
        await interaction.followup.send("🚫 You don't have permission to use this command.", ephemeral=True)
        return

    role = None
    if role_name.startswith("<@&") and role_name.endswith(">"):
        roleid = int(role_name[3:-1])
        role = interaction.guild.get_role(roleid)
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
    userid = interaction.user.id
    if userid in activeconversations:
        await interaction.response.send_message("You already have an active chat session! Just send me messages here.", ephemeral=True)
        return

    # Initialize conversation history for user
    activeconversations[userid] = [
        {"role": "system", "content": aisystemprompt},
        {"role": "assistant", "content": "Hi! I'm GalacBot the local server helper! How may I be of assistance?"}
    ]

    await interaction.response.send_message("Hi! I'm GalacBot the local server helper! How may I be of assistance? Please just message me here to chat!", ephemeral=False)

@bot.tree.command(name="endchat", description="End your chat session with GalacBot.")
async def endchat(interaction: discord.Interaction):
    userid = interaction.user.id
    if userid in activeconversations:
        activeconversations.pop(userid)
        await interaction.response.send_message("🛑 Your chat session has been ended. Thanks for chatting!", ephemeral=True)
    else:
        await interaction.response.send_message("You don't have an active chat session to end.", ephemeral=True)

@bot.event
async def on_message(message):
    if message.author.bot:
        return  # Ignore other bots

    userid = message.author.id

    if userid in activeconversations:
        botname = "galacbot"
        contentlower = message.content.lower()
        botmentioned = bot.user in message.mentions
        namementioned = botname in contentlower

        if botmentioned or namementioned:
            conversation = activeconversations[userid]
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

bot.run(bottoken)
