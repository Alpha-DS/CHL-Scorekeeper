import logging
from enum import Enum

import discord
from discord.utils import get

from utils.config import ADMIN_ROLE_ID, LOGGING_CHANNEL_ID
from utils.teams import get_abbreviation_by_team_name, get_role_id_by_team_name, get_team_names

logger = logging.getLogger("discord")


class FailureStage(Enum):
    VALIDATION = "User Input Validation"  # Argument validation failure
    SHEET_UPDATE = "Google Sheets Update"  # Google Sheets Update failure
    SCREENSHOT = "Publish Standings Screenshot"  # Standings screenshot failure
    WIKI = "Wiki Update"  # Wiki update failure
    SUCCESS = "Success"  # Successful execution for all stages

def reconstruct_command_string(interaction: discord.Interaction) -> str:
    if not interaction.data:
        return "/unknown"

    cmd_name = interaction.data.get("name", "unknown")
    options = interaction.data.get("options", [])

    args = []
    for opt in options:
        name = opt.get("name")
        value = opt.get("value")
        args.append(f"{name}: {value}")

    return f"/{cmd_name} {' '.join(args)}".strip()


async def send_log_card(
    interaction: discord.Interaction, failure_stage: FailureStage, message: str
):
    if not LOGGING_CHANNEL_ID:
        return

    logging_channel = interaction.client.get_channel(LOGGING_CHANNEL_ID)
    if not logging_channel:
        return
    
    # Assign green for success, red for errors
    if failure_stage == FailureStage.VALIDATION:
        embed_color = discord.Color.red()
        status_title = "❌ Argument Validation Failed"
    elif failure_stage == FailureStage.SUCCESS:
        embed_color = discord.Color.green()
        status_title = "✅ Execution Successful"
    else:
        embed_color = discord.Color.orange()
        status_title = f"⚠️ Failure at {failure_stage.value} Stage"

    embed = discord.Embed(title=status_title, description=message, color=embed_color)

    # Attach original user details
    embed.set_author(
        name=interaction.user.display_name,
        icon_url=interaction.user.display_avatar.url
        if interaction.user.display_avatar
        else None,
    )

    # Create visual pipeline except for failures in validation stage
    if failure_stage != FailureStage.VALIDATION:
        current_index = list(FailureStage).index(failure_stage)
        pipeline_visual = "".join(
            f"{'✅' if index < current_index else '❌'} {stage.value}\n"
            for index, stage in enumerate(list(FailureStage))
            if stage != FailureStage.SUCCESS  # Exclude SUCCESS from pipeline visualization
        )
        embed.add_field(name="Execution Pipeline", value=pipeline_visual, inline=False)

    # Reconstruct and add the exact terminal command used
    command_string = reconstruct_command_string(interaction)
    embed.add_field(
        name="**Original Command**", value=f"`{command_string}`", inline=False
    )

    await logging_channel.send(
        embed=embed, content=f"<@&{ADMIN_ROLE_ID}> 🔥🔥🔥🔥" if ADMIN_ROLE_ID and failure_stage != FailureStage.VALIDATION and failure_stage != FailureStage.SUCCESS else ""
    )

async def handle_errors(
    interaction: discord.Interaction, error_message: str, failure_stage: FailureStage
):
    # Send error message to user only if it originated from user input validation failure
    if failure_stage == FailureStage.VALIDATION:
        msg = await interaction.followup.send(error_message)
        await msg.delete(delay=15)

    # Log error in console
    logger.error(error_message)

    # Log in logging channel
    await send_log_card(interaction, failure_stage, error_message)

def create_final_result_string(
    interaction: discord.Interaction, away_team: str, away_score: int, home_score: int, home_team: str, result_type: str
) -> str:
    away_role = (
        f"<@&{get_role_id_by_team_name(away_team)}>"
        if away_team in get_team_names()
        else away_team
    )
    home_role = (
        f"<@&{get_role_id_by_team_name(home_team)}>"
        if home_team in get_team_names()
        else home_team
    )
    suffix = f"/{result_type}" if result_type in ["OT", "SO"] else ""

    # Grab team emoji. Emojis should be named after their abbreviations
    home_abbr = get_abbreviation_by_team_name(home_team)
    away_abbr = get_abbreviation_by_team_name(away_team)
    
    home_emoji = get(interaction.guild.emojis, name=home_abbr)
    away_emoji = get(interaction.guild.emojis, name=away_abbr)
    
    home_emoji_str = f"{str(home_emoji)}" if home_emoji else ""
    away_emoji_str = f"{str(away_emoji)}" if away_emoji else ""
    
    # Bold the winning team in the announcement
    if away_score > home_score:
        announcement = (
            f"**Final: {away_emoji_str}{away_role} {away_score}** - {home_score}{suffix} {home_role}{home_emoji_str}"
        )
    else:
        announcement = f"**Final:** {away_emoji_str}{away_role} {away_score} - **{home_score}**{suffix} {home_role}{home_emoji_str}"
        
    return announcement

async def send_public_announcement(
    interaction: discord.Interaction, announcement: str
):
    # Send public score announcement
    await interaction.followup.send(announcement)
