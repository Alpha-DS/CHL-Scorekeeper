import discord
from discord import app_commands
from discord.ext import commands

from utils.config import ADMIN_ROLE_ID
from utils.teams import load_teams, save_teams_from_sheets


class UpdateTeams(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="updateteams", description="Update team information from Google Sheets.")
    @app_commands.checks.has_role(ADMIN_ROLE_ID)
    async def updateteams(self, interaction: discord.Interaction):
        # Reload teams from Google Sheets
        status_message = save_teams_from_sheets(self.bot)
        load_teams()
        await interaction.response.send_message(status_message, ephemeral=True)

async def setup(bot):
    await bot.add_cog(UpdateTeams(bot))
