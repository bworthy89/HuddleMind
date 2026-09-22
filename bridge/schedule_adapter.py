from bridge.models import RecordId, ScheduleGame


def schedule_game_from_report(record: dict) -> ScheduleGame:
    # Only these statuses represent completed games in the inspected schema.
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
    )

def schedule_from_report(report: dict) -> tuple[ScheduleGame, ...]:
    # Convert only manager-linked fixtures: discovery excludes practice records.
    return tuple(
        schedule_game_from_report(record)
        for record in report["fixtures"]
    )