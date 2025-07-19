import discord
from discord import app_commands
from discord.ext import commands
import json

repo = None
file_path = "blacklist.json"
blacklist = {}

def load_blacklist():
    global blacklist
    try:
        file_content = repo.get_contents(file_path)
        blacklist = json.loads(file_content.decoded_content.decode())
    except Exception as e:
        print(f"Error loading blacklist from GitHub: {e}")
        blacklist = {}

def save_blacklist():
    try:
        content = json.dumps(blacklist, indent=4)
        repo.update_file(file_path, "Update blacklist.json", content, repo.get_contents(file_path).sha)
    except Exception as e:
        print(f"Error saving blacklist to GitHub: {e}")

class BlacklistCog(commands.Cog):
    def __init__(self, bot, github_repo):
        self.bot = bot
        global repo
        repo = github_repo
        load_blacklist()

    @app_commands.command(name="blacklist", description="Blacklist a user with a reason.")
    @app_commands.describe(user="User to blacklist", reason="Reason for blacklisting")
    async def blacklist_user(self, interaction: discord.Interaction, user: discord.User, reason: str):
        if interaction.user.id != 1045850558499655770:
            await interaction.response.send_message("🚫 Only Bloxx can use this command.", ephemeral=True)
            return

        blacklist[str(user.id)] = reason
        save_blacklist()

        try:
            await user.send(f"You have been blacklisted from interacting with GalacBot.\nReason: {reason}")
        except Exception:
            pass

        await interaction.response.send_message(f"✅ {user.mention} has been blacklisted.", ephemeral=True)

    @app_commands.command(name="unblacklist", description="Remove a user from the blacklist.")
    @app_commands.describe(user="User to remove from blacklist")
    async def unblacklist_user(self, interaction: discord.Interaction, user: discord.User):
        if interaction.user.id != 1045850558499655770:
            await interaction.response.send_message("🚫 Only Bloxx can use this command.", ephemeral=True)
            return

        if str(user.id) in blacklist:
            del blacklist[str(user.id)]
            save_blacklist()
            await interaction.response.send_message(f"✅ {user.mention} has been removed from the blacklist.", ephemeral=True)
        else:
            await interaction.response.send_message(f"⚠️ {user.mention} is not on the blacklist.", ephemeral=True)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type == discord.InteractionType.application_command:
            if interaction.command.name == "ask" and str(interaction.user.id) in blacklist:
                await interaction.response.send_message(
                    "🚫 You are blacklisted from interacting with GalacBot.", ephemeral=False
                )
                return

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if str(message.author.id) in blacklist:
            return

async def setup(bot, github_repo):
    await bot.add_cog(BlacklistCog(bot, github_repo))
