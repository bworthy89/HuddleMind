from bridge.models import RecordId, ScheduleGame


def schedule_game_from_report(
        record: dict,
        selected_team: dict,
) -> ScheduleGame:

    # Match the controlled team using its source table and row.
    selected_id = (selected_team["table"], selected_team["row"])
    home_id = (record["home"]["table"], record["home"]["row"])
    away_id = (record["away"]["table"], record["away"]["row"])

    # The controlled team must appear on exactly one side of the matchup.
    if (selected_id == home_id) == (selected_id == away_id):
        raise ValueError(
            "Controlled team must match exactly one side of the game."
        )

    controlled_team_is_home = selected_id == home_id

    status = record["GameStatusLabel"]
    is_complete = status in ("HomeWon", "AwayWon", "Tied")
    # Preserve scores for completed games; hide unfinished scores with None.
    return ScheduleGame(
        record_id=RecordId(
            table_id=record["table"],
            row_id=record["row"],
        ),
        season_index=record["SeasonYear"],
        week=record["SeasonWeek"],
        home_team=record["home"]["name"],
        away_team=record["away"]["name"],
        status=status,
        home_score=record["HomeScore"] if is_complete else None,
        away_score=record["AwayScore"] if is_complete else None,
        controlled_team_is_home=controlled_team_is_home,
    )

def schedule_from_report(report: dict) -> tuple[ScheduleGame, ...]:
    # Pass the selected team's identity into each fixture conversion.
    selected_team = report["selected_team"]

    return tuple(
        schedule_game_from_report(record, selected_team)
        for record in report["fixtures"]
    )