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
        contents = repo.get_contents(file_path)
        content = json.dumps(blacklist, indent=4)
        repo.update_file(file_path, "Update blacklist.json", content, contents.sha)
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
        await interaction.response.send_message(f"✅ {user.mention} has been blacklisted.", ephemeral=False)

    @app_commands.command(name="unblacklist", description="Remove a user from the blacklist.")
    @app_commands.describe(user="User to remove from blacklist")
    async def unblacklist_user(self, interaction: discord.Interaction, user: discord.User):
        if interaction.user.id != 1045850558499655770:
            await interaction.response.send_message("🚫 Only Bloxx can use this command.", ephemeral=True)
            return

        if str(user.id) in blacklist:
            del blacklist[str(user.id)]
            save_blacklist()
            await interaction.response.send_message(f"✅ {user.mention} has been removed from the blacklist.", ephemeral=False)
        else:
            await interaction.response.send_message(f"⚠️ {user.mention} is not on the blacklist.", ephemeral=False)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type == discord.InteractionType.application_command:
            if interaction.command.name == "ask" and str(interaction.user.id) in blacklist:
                # If not already responded, respond publicly in channel
                try:
                    await interaction.response.send_message(
                        "🚫 You are blacklisted from interacting with GalacBot.", ephemeral=False
                    )
                except discord.errors.InteractionResponded:
                    pass  # Already responded elsewhere
                return

async def setup(bot, github_repo):
    await bot.add_cog(BlacklistCog(bot, github_repo))
