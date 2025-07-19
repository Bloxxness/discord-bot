import discord
from discord import app_commands
from discord.ext import commands
import json

# These will be injected or set after loading the cog
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

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("🚫 You are blacklisted from interacting with GalacBot.", ephemeral=True)

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

    async def cog_before_invoke(self, interaction: discord.Interaction):
        if str(interaction.user.id) in blacklist:
            await interaction.response.send_message(
                "🚫 You are blacklisted from interacting with GalacBot.", ephemeral=True
            )
            raise commands.CheckFailure("User is blacklisted.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if str(message.author.id) in blacklist:
            try:
                await message.author.send(
                    "You are blacklisted from using GalacBot. Please contact the admins if you think this is a mistake."
                )
            except Exception:
                pass
            return

async def setup(bot, github_repo):
    await bot.add_cog(BlacklistCog(bot, github_repo))
