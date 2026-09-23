from bridge.models import ScheduleGame

def summarize_results(
        games: tuple[ScheduleGame, ...]
) -> dict[str, int]:
    # Keep completed results separate from pending or unrecognized statuses.
    summary = {
        "wins": 0,
        "losses": 0,
        "ties": 0,
        "pending": 0,
        "unknown": 0,
    }

    for game in games:
        if game.status == "Tied":
            summary["ties"] += 1

        elif game.status in ("HomeWon", "AwayWon"):
            # Compare the winning side with the controlled team's side.
            home_won = game.status == "HomeWon"
            controlled_team_won = (
                home_won == game.controlled_team_is_home
            )

            if controlled_team_won:
                summary["wins"] += 1
            else:
                summary["losses"] += 1

        elif game.status in (
            "Unscheduled",
            "Unplayed",
            "HomeScheduled",
            "AwayScheduled",
        ):
            summary["pending"] += 1

        else:
            # Preserve uncertainty instead of assuming an unfamiliar status is pending.
            summary["unknown"] += 1

    return summary
