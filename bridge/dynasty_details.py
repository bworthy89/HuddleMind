"""Normalized dynasty context, with source values retained for verification."""
from dataclasses import dataclass

from bridge.models import DynastySnapshot, RecordId, ScheduleGame


@dataclass(frozen=True)
class EnumValue:
    value: int
    label: str


@dataclass(frozen=True)
class SeasonContext:
    calendar_year: int
    season_index: int
    week: int
    week_type: EnumValue
    stage: EnumValue


@dataclass(frozen=True)
class DepthSlot:
    position: str
    depth: int
    player_id: RecordId | None


@dataclass(frozen=True)
class PlayerHealth:
    player_id: RecordId
    status: EnumValue
    injury_type: EnumValue
    severity: EnumValue
    min_duration: int
    max_duration: int
    total_duration: int
    injured_reserve: bool


@dataclass(frozen=True)
class RecruitingTarget:
    record_id: RecordId
    recruit_id: RecordId
    player_id: RecordId
    name: str
    position: EnumValue
    national_rank: int
    position_rank: int
    stage: EnumValue
    scholarship: EnumValue
    hours_spent_current: int


@dataclass(frozen=True)
class RecruitingBoard:
    record_id: RecordId
    hours_assigned: int
    hours_processed: int
    hours_total: int
    targets: tuple[RecruitingTarget, ...]


@dataclass(frozen=True)
class DynastyDetails:
    roster: DynastySnapshot
    season: SeasonContext
    schedule: tuple[ScheduleGame, ...]
    depth_chart: tuple[DepthSlot, ...] | None
    health: tuple[PlayerHealth, ...]
    recruiting: RecruitingBoard | None


def next_games(details: DynastyDetails) -> tuple[ScheduleGame, ...]:
    """Return all fixtures at the earliest eligible week; never guess a tie-break."""
    pending = [game for game in details.schedule
               if game.status in ('Unplayed', 'HomeScheduled', 'AwayScheduled')
               and game.season_index == details.season.season_index
               and game.week >= details.season.week]
    if not pending:
        return ()
    week = min(game.week for game in pending)
    return tuple(game for game in pending if game.week == week)
