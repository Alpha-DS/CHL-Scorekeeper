import os
import datetime
from utils.teams import get_arena_by_team_name
from utils.config import GAME_LOG_SHEET_NAME

SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

def construct_payload(
    away_score: int,
    home_score: int,
    home_team: str,
    result_type: str,
    away_so_goals: int | None,
    away_so_attempts: int | None,
    home_so_goals: int | None,
    home_so_attempts: int | None,
) -> list:
    is_ot = "TRUE" if result_type == "OT" else "FALSE"
    is_so = "TRUE" if result_type == "SO" else "FALSE"

    # Use empty cells instead of zeros if not a shootout
    so_a_g = away_so_goals if result_type == "SO" else ""
    so_a_a = away_so_attempts if result_type == "SO" else ""
    so_h_g = home_so_goals if result_type == "SO" else ""
    so_h_a = home_so_attempts if result_type == "SO" else ""

    current_utc_time = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%m/%d/%Y %H:%M:%S"
    )
    arena_location = get_arena_by_team_name(home_team) or ""

    payload = [
        away_score,
        home_score,
        home_team,
        is_ot,
        is_so,
        so_a_g,
        so_a_a,
        so_h_g,
        so_h_a,
        current_utc_time,
        arena_location,
    ]
    return payload

def find_matching_game_row(
    sheet_values: list, team_away: str, team_home: str
) -> int | None:
    # Assuming B = Away Team, C = Away Score, E = Home Team
    for index, row in enumerate(sheet_values):
        if len(row) > 2:
            row_away = row[1].strip().lower()
            row_away_score = row[2].strip()
            row_home = row[4].strip().lower()

            # Check if Cancelled column exists and contains text, else assume False
            is_cancelled = False
            # Assume Cancelled status is in Column N (Index 13) if it exists
            if len(row) > 13:
                is_cancelled = row[13].strip().lower() == "true"

            # Use away score as a proxy to determine if game has already been played
            if (
                row_away == team_away.lower()
                and row_home == team_home.lower()
                and row_away_score == ""
                and not is_cancelled
            ):
                return (
                    index + 1
                )  # Convert 0-indexed python list to 1-indexed Sheets row
    return None

async def process_sheet_submission(bot, away_team: str, home_team: str, payload: list):
    # Fetch Data
    result = bot.sheets.values().get(spreadsheetId=SPREADSHEET_ID, range=f"{GAME_LOG_SHEET_NAME}!A:N").execute()
    rows = result.get("values", [])
    
    # Match Data
    matched_row = find_matching_game_row(rows, away_team, home_team)
    if not matched_row:
        raise ValueError(
            f"❌ No unplayed game found between {away_team} and {home_team}."
        )
        
    # Write Data
    # Layout target map: C=AwayScore, D=HomeScore, F=Overtime, G=Shootout, H=AwaySOGoals, I=AwaySOAttempts, J=HomeSOGoals, K=HomeSOAttempts, L=Date, M=Arena
    bot.sheets.values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{GAME_LOG_SHEET_NAME}!C{matched_row}",
        valueInputOption="USER_ENTERED",
        body={"values": [payload]},
    ).execute()