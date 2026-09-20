from bridge.models import Coach, DynastySnapshot, Player, RecordId, Team

# Build sample objects without reading a game save.
player = Player(
    record_id=RecordId(table_id=4255, row_id=10),
    first_name="Sample",
    last_name="Player",
    position="QB",
    overall=85,
)

team = Team(
    record_id=RecordId(table_id=6351, row_id=2),
    team_index=5,
    name="Sample Team",
    players=(player,),
)

coach = Coach(
    record_id=RecordId(table_id=4179, row_id=10),
    first_name="Sample",
    last_name="Coach",
    team_index=5,
    is_user_controlled=True,
)

# These placeholder hashes are only for checking the model structure.
snapshot = DynastySnapshot(
    save_sha256="sample_save_hash",
    schema_sha256="sample_schema_hash",
    coach=coach,
    team=team,
)

print("Coach:", snapshot.coach.full_name)
print("Team:", snapshot.team.name)
print("Roster size:", len(snapshot.team.players))

# Read each player through the snapshot's team.
for roster_player in snapshot.team.players:
    print(
        roster_player.full_name,
        '| Position:', roster_player.position,
        "| Overall:", roster_player.overall,
    )
