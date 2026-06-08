from dataclasses import dataclass
import csv
import logging
import os

from utils.config import SPREADSHEET_ID, TEAM_INFO_SHEET_NAME

@dataclass
class Team:
    team_name: str
    role_id: int
    arena_name: str
    abbreviation: str

TEAMS = []
TEAM_INFO_FILE = "team_info.csv"

def save_teams_from_sheets(bot) -> str:
    data_range = f"'{TEAM_INFO_SHEET_NAME}'!A2:I"
    result = (
        bot.sheets.values()
        .get(spreadsheetId=SPREADSHEET_ID, range=data_range)
        .execute()
    )
    rows = result.get("values", [])

    if not rows:
        return "⚠️ No data retrieved from the Google Sheet."

    dir_name = os.path.dirname(TEAM_INFO_FILE)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    with open(TEAM_INFO_FILE, mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["team_name", "role_id", "arena_name", "abbreviation"])

        for row in rows:
            if len(row) > 5 and row[2].strip():
                # Assuming Schema: A=Conference, B=Division, C=Team Name, D=Abbreviation, E=Home Arena, F=Role ID
                writer.writerow([row[2].strip(), row[5].strip(), row[4].strip(), row[3].strip()])

    return "✅ Team information updated successfully."

def load_teams() -> None:
    global TEAMS
    TEAMS.clear()

    try:
        with open(TEAM_INFO_FILE, newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                team = Team(
                    team_name=row["team_name"],
                    role_id=int(row["role_id"]),
                    arena_name=row["arena_name"],
                    abbreviation=row["abbreviation"]
                )
                TEAMS.append(team)
    except FileNotFoundError:
        logger = logging.getLogger("discord")
        logger.error(f"Teams file not found: {TEAM_INFO_FILE}. Please run the /updateteams command to create and populate the team list.")

def is_valid_team_name(team_name: str) -> bool:
    return any(team.team_name == team_name for team in TEAMS)

def get_team_names() -> list[str]:
    return [team.team_name for team in TEAMS]

def get_abbreviation_by_team_name(team_name: str) -> str | None:
    for team in TEAMS:
        if team.team_name == team_name:
            return team.abbreviation
    return None
            
def get_role_id_by_team_name(team_name: str) -> int | None:
    for team in TEAMS:
        if team.team_name == team_name:
            return team.role_id
    return None

def get_arena_by_team_name(team_name: str) -> str | None:
    for team in TEAMS:
        if team.team_name == team_name:
            return team.arena_name
    return None