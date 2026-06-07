import discord
from discord import app_commands
from discord.ext import commands

from services.screenshot_services import update_standings_screenshot
from utils.config import ADMIN_ROLE_ID


class UpdateStandings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="updatestandings", description="Update the standings screenshot.")
    @app_commands.checks.has_role(ADMIN_ROLE_ID)
    async def updatestandings(self, interaction: discord.Interaction):
        try:
            # Update the standings screenshot
            await interaction.response.defer(ephemeral=True)
            await update_standings_screenshot(self.bot, screenshot_delay=0)
            await interaction.followup.send("✅ Standings screenshot updated successfully.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(
                f"❌ An error occurred while updating standings: {e}", ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(UpdateStandings(bot))
