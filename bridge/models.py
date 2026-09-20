from dataclasses import dataclass


# Identify the record this object came from within one save snapshot.
@dataclass(frozen=True)
class RecordId:
    table_id: int
    row_id: int

# Store one player's basic information in a named, structured object.
@dataclass(frozen=True)
class Player:
    record_id: RecordId
    first_name: str
    last_name: str
    position: str
    overall: int

    @property
    def full_name(self) -> str:
        # Build the display name without storing a duplicate copy.
        return f"{self.first_name} {self.last_name}".strip()

# Store a team's identity and its roster from one save snapshot.
@dataclass(frozen=True)
class Team:
    record_id: RecordId
    team_index: int
    name: str
    players: tuple[Player, ...]

# Store a coach's identity and the team index used to find their team.
@dataclass(frozen=True)
class Coach:
    record_id: RecordId
    first_name: str
    last_name: str
    team_index: int
    is_user_controlled: bool

    @property
    def full_name(self) -> str:
        # Build the display name without storing a duplicate copy.
        return f"{self.first_name} {self.last_name}".strip()

# Group the selected coach and team with the hashes of their source files.
@dataclass(frozen=True)
class DynastySnapshot:
    save_sha256: str
    schema_sha256: str
    coach: Coach
    team: Team
