from datetime import datetime, timezone

import wikitextparser as wtp
from enum import Enum
import re

from utils.config import MEDIAWIKI_PAGE_TITLE

class TeamResult(Enum):
    REGULATION_WIN = "Regulation Win"
    OVERTIME_WIN = "Overtime Win"
    SHOOTOUT_WIN = "Shootout Win"
    SHOOTOUT_LOSS = "Shootout Loss"
    OVERTIME_LOSS = "Overtime Loss"
    REGULATION_LOSS = "Regulation Loss"

# Schema: Div | Team | Player | GP | W | OTW | OTL | L | Pts | Pct | GF | GA | GD
class StandingsSchema(Enum):
    Div = 0
    Team = 1
    Player = 2
    GP = 3
    W = 4
    OTW = 5
    OTL = 6
    L = 7
    Pts = 8
    Pct = 9
    GF = 10
    GA = 11
    GD = 12
    
    
def determine_result(team_score: int, opponent_score: int, result_type: str) -> TeamResult:
    if result_type == "REG":
        return TeamResult.REGULATION_WIN if team_score > opponent_score else TeamResult.REGULATION_LOSS
    elif result_type == "OT":
        return TeamResult.OVERTIME_WIN if team_score > opponent_score else TeamResult.OVERTIME_LOSS
    elif result_type == "SO":
        if team_score > opponent_score:
            return TeamResult.SHOOTOUT_WIN
        elif team_score < opponent_score:
            return TeamResult.SHOOTOUT_LOSS
    else:
        raise ValueError("Invalid result type while determining team result for wiki.")
    
def pct_formatting(value: float) -> str:  
    # Special formatting for pt%, eg 1.000 or .475
    formatted = f"{value:.3f}"
    return "1.000" if formatted == "1.000" else formatted.lstrip("0")

def update_cell(current_val: str, delta: int, bold: bool = False) -> str:
    # Clean out bold quotes (''') or whitespaces
    clean_val = re.sub(r"[X'\" ]", "", str(current_val))

    # Calculate new value and return
    new_val = int(clean_val or 0) + delta
    
    return f"'''{new_val}'''" if bold else str(new_val)

def update_team_stats(team_row: list, team_goals: int, opponent_goals: int, result: TeamResult):
    # Update GP
    team_row[StandingsSchema.GP.value] = update_cell(team_row[StandingsSchema.GP.value], 1)
    
    # Update GF, GA, and GD
    team_row[StandingsSchema.GF.value] = update_cell(team_row[StandingsSchema.GF.value], team_goals)
    team_row[StandingsSchema.GA.value] = update_cell(team_row[StandingsSchema.GA.value], opponent_goals)
    team_row[StandingsSchema.GD.value] = update_cell(team_row[StandingsSchema.GD.value], team_goals - opponent_goals)

    # Update W/OTW/OTL/L and Pts based on result
    match result:
        case TeamResult.REGULATION_WIN:
            team_row[StandingsSchema.W.value] = update_cell(team_row[StandingsSchema.W.value], 1)
            team_row[StandingsSchema.Pts.value] = update_cell(team_row[StandingsSchema.Pts.value], 3, bold=True) # 3 points for regulation win
        case TeamResult.OVERTIME_WIN | TeamResult.SHOOTOUT_WIN:
            team_row[StandingsSchema.OTW.value] = update_cell(team_row[StandingsSchema.OTW.value], 1)
            team_row[StandingsSchema.Pts.value] = update_cell(team_row[StandingsSchema.Pts.value], 2, bold=True) # 2 points for overtime win
        case TeamResult.OVERTIME_LOSS | TeamResult.SHOOTOUT_LOSS:
            team_row[StandingsSchema.OTL.value] = update_cell(team_row[StandingsSchema.OTL.value], 1)
            team_row[StandingsSchema.Pts.value] = update_cell(team_row[StandingsSchema.Pts.value], 1, bold=True) # 1 point for overtime loss
        case TeamResult.REGULATION_LOSS:
            team_row[StandingsSchema.L.value] = update_cell(team_row[StandingsSchema.L.value], 1)
            team_row[StandingsSchema.Pts.value] = update_cell(team_row[StandingsSchema.Pts.value], 0, bold=True) # 0 points for regulation loss
            
    # Recalculate Pct
    pts = int(str(team_row[StandingsSchema.Pts.value]).replace("'", ""))
    gp = int(team_row[StandingsSchema.GP.value])
    pct = pts / (gp * 3) if gp > 0 else 0
    team_row[StandingsSchema.Pct.value] = pct_formatting(pct)
    
def update_standings(raw_text: str, home_team: str, home_score: int, away_team: str, away_score: int, result_type: str) -> str:
    parsed = wtp.parse(raw_text)
    
    # Assuming first 2 tables are standings (one for each conference) and the 3rd table is the game log
    standings_tables = parsed.tables[:2]
    
    # Search for home and away teams to update their stats
    for table in standings_tables:
        matrix = table.data()
        team_rows = matrix[2:]
        for row in team_rows:
            if re.search(home_team, str(row[StandingsSchema.Team.value])):
                update_team_stats(row, home_score, away_score, determine_result(home_score, away_score, result_type))
            elif re.search(away_team, str(row[StandingsSchema.Team.value])):
                update_team_stats(row, away_score, home_score, determine_result(away_score, home_score, result_type))
        
        # Sort key using points (desc), GP (asc via negative), and wins (desc)
        team_rows.sort(
            key=lambda r: (
                int(str(r[StandingsSchema.Pts.value]).replace("'", "")),
                -int(r[StandingsSchema.GP.value]),
                int(r[StandingsSchema.W.value])
            ),
            reverse=True
        )
        
        match = re.search(r"\n\|[^\|\-\}].*", table.string)
        if match:
            header_block = table.string[: match.start()]
            team_body = "\n" + "\n|-\n".join(
                "| " + " || ".join(str(cell).strip() for cell in row)
                for row in team_rows
            )
            table.string = header_block + team_body + "\n|}"
        else:
            team_body = "\n|-\n".join(
                "| " + " || ".join(str(cell).strip() for cell in row)
                for row in team_rows
            )
            table.string = "{|\n" + team_body + "\n|}"

    return str(parsed)
                

def append_game_log(raw_text: str, home_team: str, home_score: int, away_team: str, away_score: int, result_type: str, arena: str) -> str:
    parsed = wtp.parse(raw_text)
    
    game_log_table = parsed.tables[2] # Assuming 3rd table is game log
    
    # Construct score string
    score_string = f"'''{away_score}–{home_score}"
    if result_type == "OT":
        score_string += " (OT)"
    elif result_type == "SO":
        score_string += " (SO)"
    score_string += "'''"
    
    date_string = datetime.now(timezone.utc).strftime("%d %B %Y")
    # Append new row to game log
    new_row = [away_team, score_string, home_team, date_string, arena, ""] # Empty placeholder for broadcast column
    table_str = game_log_table.string.rstrip()
    if table_str.endswith("|}"):
        new_row_str = "\n|-\n| " + " || ".join(str(cell).strip() for cell in new_row)
        game_log_table.string = table_str[:-2] + new_row_str + "\n|}"
    
    return str(parsed)

def update_wiki(bot, home_team: str, home_score: int, away_team: str, away_score: int, result_type: str, arena: str):
    # Fetch current wiki content
    page = bot.wiki.pages[MEDIAWIKI_PAGE_TITLE]
    current_content = page.text()
    
    # Update standings and game log
    updated_content = update_standings(current_content, home_team, home_score, away_team, away_score, result_type)
    updated_content = append_game_log(updated_content, home_team, home_score, away_team, away_score, result_type, arena)
    
    # Save updated content back to wiki
    page.save(updated_content, summary=f"CHL Scorekeeping Bot: Updated standings and game log for {away_team} vs {home_team}", bot=True)
    