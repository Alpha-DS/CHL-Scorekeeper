import asyncio

import discord
from discord import app_commands
from discord.ext import commands

from services.screenshot_services import update_standings_screenshot
from services.sheets_services import construct_payload, process_sheet_submission
from services.wiki_services import update_wiki
from utils.messaging import FailureStage, create_final_result_string, send_log_card, send_public_announcement, handle_errors
from utils.teams import get_arena_by_team_name, get_team_names
from utils.validation import validate_inputs


class SubmitScore(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.lock = asyncio.Lock()

    async def team_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name=team, value=team)
            for team in get_team_names()
            if current.lower() in team.lower()
        ][:25]

    @app_commands.command(name="submit", description="Submit game scores and results.")
    @app_commands.autocomplete(
        away_team=team_autocomplete,
        home_team=team_autocomplete,
    )
    @app_commands.choices(
        result_type=[
            app_commands.Choice(name="Regulation", value="REG"),
            app_commands.Choice(name="Overtime", value="OT"),
            app_commands.Choice(name="Shootout", value="SO"),
        ]
    )
    @app_commands.describe(
        away_team="The visiting team.",
        away_score="The total goals scored by the away team.",
        home_score="The total goals scored by the home team.",
        home_team="The hosting team.",
        result_type="Did the game end in Regulation, Overtime, or Shootout?",
        away_so_goals="Away team shootout goals scored (only if game ended in SO).",
        away_so_attempts="Away team shootout attempts (only if game ended in SO).",
        home_so_goals="Home team shootout goals scored (only if game ended in SO).",
        home_so_attempts="Home team shootout attempts (only if game ended in SO).",
    )
    async def submit_score(
        self,
        interaction: discord.Interaction,
        away_team: str,
        away_score: int,
        home_score: int,
        home_team: str,
        result_type: str,
        away_so_goals: int | None = None,
        away_so_attempts: int | None = None,
        home_so_goals: int | None = None,
        home_so_attempts: int | None = None,
    ):
        try:
            # Limit to one concurrent command process to prevent race conditions
            if self.lock.locked():
                await interaction.response.send_message(
                    "⏳ Another submission is currently being processed. Please wait a moment and try again.",
                    ephemeral=True,
                )
                return

            async with self.lock:
                await interaction.response.defer()
    
                # Stage variable for logging purposes in case of failure
                current_stage = FailureStage.VALIDATION
                
                # Validate inputs
                validate_inputs(
                    away_team,
                    away_score,
                    home_score,
                    home_team,
                    result_type,
                    away_so_goals,
                    away_so_attempts,
                    home_so_goals,
                    home_so_attempts,
                )

                # Public announcement of scores
                announcement_string = create_final_result_string(
                    interaction, away_team, away_score, home_score, home_team, result_type
                )
                await send_public_announcement(
                    interaction,
                    announcement_string
                )

                # Construct payload
                sheets_payload = construct_payload(
                    away_score,
                    home_score,
                    home_team,
                    result_type,
                    away_so_goals,
                    away_so_attempts,
                    home_so_goals,
                    home_so_attempts,
                )
                
                # Submit payload for updating Google Sheets
                current_stage = FailureStage.SHEET_UPDATE
                await process_sheet_submission(self.bot, away_team, home_team, sheets_payload)

                # Update standings screenshot in Discord
                current_stage = FailureStage.SCREENSHOT
                await update_standings_screenshot(self.bot)
                
                # Update wiki page with new standings and game log entry
                current_stage = FailureStage.WIKI
                update_wiki(self.bot, home_team, home_score, away_team, away_score, result_type, get_arena_by_team_name(home_team))

                # Send successful logging card
                await send_log_card(
                    interaction,
                    FailureStage.SUCCESS,
                    announcement_string,
                )

        except Exception as e:
            await handle_errors(
                interaction,
                str(e),
                failure_stage=current_stage
            )


async def setup(bot):
    await bot.add_cog(SubmitScore(bot))
