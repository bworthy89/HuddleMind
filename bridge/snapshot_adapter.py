from bridge.models import Coach, DynastySnapshot, Player, RecordId, Team



def player_from_report(record: dict) -> Player:
    # Translate the discovery report's field names into our application model.
    return Player(
        record_id=RecordId(
            table_id=record["table"],
            row_id=record["row"],
        ),
        first_name=record["FirstName"],
        last_name=record["LastName"],
        position=record["PositionLabel"],
        overall=record["OverallRating"],
    )

def team_from_report(record: dict) -> Team:
    # Convert each roster dictionary into a player, keeping the roster immutable.
    players = tuple(
        player_from_report(player_record)
        for player_record in record["players"]
    )
    # Preserve the team's record identity and the index used for team joins.
    return Team(
        record_id=RecordId(
            table_id=record["table"],
            row_id=record["row"],
        ),
        team_index=record["TeamIndex"],
        name=record["DisplayName"],
        players=players,

    )

def controlled_coach_from_report(record: dict) -> Coach:
    # This function accepts a record from the report's controlled_coaches list.
    # The discovery reader has already checked its IsUserControlled flag.
    return Coach(
        record_id=RecordId(
            table_id=record["table"],
            row_id=record["row"],
        ),
        first_name=record["FirstName"],
        last_name=record["LastName"],
        team_index=record["TeamIndex"],
        is_user_controlled=True,
    )

def snapshot_from_report(report: dict) -> DynastySnapshot:
    # Build a snapshot only when the reader found one controlled team.
    selection = report["selection"]
    if selection["status"] != "resolved":
        raise ValueError(
            f"Cannot build snapshot: {selection['status']}"
        )

    if report["roster_team_mismatches"]:
        raise ValueError("Cannot build snapshot: roster/team mismatches found")

    # Match the selected team's source identity instead of its display name.
    selected_team = selection["team"]
    matching_teams = [
        team_record
        for team_record in report["teams"]
        if team_record["table"] == selected_team["table"]
        and team_record["row"] == selected_team["row"]
    ]

    if len(matching_teams) != 1:
        raise ValueError("Expected exactly one matching team record.")

    # A resolved snapshot must also contain exactly one controlled coach.
    coaches = report["controlled_coaches"]
    if len(coaches) != 1:
        raise ValueError("Expected exactly one controlled coach")

    team = team_from_report(matching_teams[0])
    coach = controlled_coach_from_report(coaches[0])

    # Confirm that the coach and selected team belong together.
    if coach.team_index != team.team_index:
        raise ValueError("Coach and team indexes do not match")

    return DynastySnapshot(
        save_sha256=report["save_sha256"],
        schema_sha256=report["schema_sha256"],
        coach=coach,
        team=team,
    )
