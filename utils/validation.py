from utils.teams import is_valid_team_name


# Check if shootout results are mathematically valid
def validate_shootout(
    away_so_goals: int,
    away_so_attempts: int,
    home_so_goals: int,
    home_so_attempts: int,
    winner_so_goals: int,
):
    # Basic checks for non-negative integers
    if any(
        x < 0
        for x in [away_so_goals, away_so_attempts, home_so_goals, home_so_attempts]
    ):
        raise ValueError("❌ Shootout goals and attempts cannot be negative.")

    # Goals cannot exceed attempts
    if away_so_goals > away_so_attempts or home_so_goals > home_so_attempts:
        raise ValueError("❌ Shootout goals cannot exceed attempts.")

    # At least one team must have more goals than the other
    if away_so_goals == home_so_goals:
        raise ValueError("❌ Shootout results must have a winner.")

    # With 3 rounds initially, the minimum attempts for both teams must be at least 2
    if away_so_attempts < 2 or home_so_attempts < 2:
        raise ValueError("❌ Each team must have at least 2 shootout attempts.")

    # Identify winner and loser of the shootout
    winner_goals, winner_attempts, loser_goals, loser_attempts = (
        (away_so_goals, away_so_attempts, home_so_goals, home_so_attempts)
        if away_so_goals > home_so_goals
        else (home_so_goals, home_so_attempts, away_so_goals, away_so_attempts)
    )

    # Check that the shootout winner is indeed the game winner
    if winner_so_goals != winner_goals:
        raise ValueError("❌ The winner of the shootout is not the winner of the game.")

    goal_diff = winner_goals - loser_goals
    max_rounds = max(winner_attempts, loser_attempts)

    # Initial 3 Rounds (Can end early if mathematically impossible for trailing team to catch up)
    if max_rounds <= 3:
        min_attempts = min(away_so_attempts, home_so_attempts)
        remaining_rounds = 3 - min_attempts

        if goal_diff <= remaining_rounds:
            raise ValueError(
                "❌ Invalid score. The trailing team still had enough remaining shots to tie the game."
            )
        if goal_diff > remaining_rounds + 1:
            raise ValueError(
                "❌ Invalid score. The game would have ended sooner based on this goal differential."
            )

    # Sudden Death (Must be perfectly equal attempts and a 1-goal difference)
    else:
        if away_so_attempts != home_so_attempts:
            raise ValueError(
                "❌ Invalid sudden death sequence. Both teams must have an equal number of attempts."
            )
        if goal_diff != 1:
            raise ValueError(
                "❌ Sudden death shootouts must end with a goal differential of exactly 1."
            )


# Sanity check command arguments
def validate_inputs(
    team_away: str,
    score_away: int,
    score_home: int,
    team_home: str,
    result_type: str,
    away_so_goals: int | None,
    away_so_attempts: int | None,
    home_so_goals: int | None,
    home_so_attempts: int | None,
):
    # Validate team names
    if not is_valid_team_name(team_away):
        raise ValueError(f"❌ `{team_away}` is not a registered team name.")
    if not is_valid_team_name(team_home):
        raise ValueError(f"❌ `{team_home}` is not a registered team name.")

    # Ensure teams are not the same
    if team_away == team_home:
        raise ValueError("❌ Away and Home teams cannot be the same.")
    # Check for negative scores
    if score_away < 0 or score_home < 0:
        raise ValueError("❌ Scores cannot be negative values.")
    # Games cannot end in a tie
    if score_away == score_home:
        raise ValueError("❌ Games cannot end in a tie.")

    # In Overtime or Shootout, the score difference must be exactly 1
    if result_type in ["OT", "SO"]:
        if abs(score_away - score_home) != 1:
            raise ValueError(
                f"❌ Games ending in {result_type} must have a goal differential of exactly 1."
            )

    # If not a shootout, shootout stats should not be provided
    if result_type != "SO":
        if any(
            x is not None
            for x in [
                away_so_goals,
                away_so_attempts,
                home_so_goals,
                home_so_attempts,
            ]
        ):
            raise ValueError(
                "❌ Shootout goals and attempts should not be provided for non-shootout results."
            )

    # Validate Shootout goals and attempts
    if result_type == "SO":
        if any(
            x is None
            for x in [
                away_so_goals,
                away_so_attempts,
                home_so_goals,
                home_so_attempts,
            ]
        ):
            raise ValueError(
                "❌ Shootout goals and attempts must be provided for shootout results."
            )
        # Main check for shootout validity
        winner_so_goals = away_so_goals if score_away > score_home else home_so_goals
        validate_shootout(
            away_so_goals,
            away_so_attempts,
            home_so_goals,
            home_so_attempts,
            winner_so_goals,
        )
