"""Build a complete read-only dynasty view from a single captured save."""
from bridge.discover_fields import inspect_fields
from bridge.discover_schedule import inspect_schedule
from bridge.dynasty_reader import DynastyReader, FrozenSource
from bridge.dynasty_details import (
    DepthSlot, DynastyDetails, EnumValue, PlayerHealth, RecruitingBoard,
    RecruitingTarget, SeasonContext,
)
from bridge.models import RecordId
from bridge.schedule_adapter import schedule_from_report
from bridge.snapshot_adapter import snapshot_from_report


def record_id(reference):
    return RecordId(*divmod(reference, 1 << 17))


def read_depth(reader, team, row, roster):
    pointer = reader.pointer(team, row, 'DepthChart')
    if pointer == 0:
        return None  # Missing source data is different from an empty chart.
    chart, chart_row = reader.resolve(pointer, 'DepthChart')
    players = {player.record_id for player in roster.players}
    slots = []
    for attribute in reader.schemas[chart['name']]:
        if attribute['type'] != 'Player[]':
            continue
        position = attribute['name']
        array = reader.pointer(chart, chart_row, position)
        if not array:
            continue
        seen = set()
        for depth, ref in enumerate(reader.array(array, 'Player', allow_null=True), 1):
            identity = record_id(ref) if ref is not None else None
            if identity is not None:
                if identity not in players:
                    raise ValueError('Depth chart references a player outside the controlled roster')
                if identity in seen:
                    raise ValueError('Duplicate player within a depth-chart position')
                seen.add(identity)
            slots.append(DepthSlot(position, depth, identity))
    return tuple(slots)


def read_enum(reader, info, row, name):
    value = reader.field(info, row, name)
    return EnumValue(value, reader.label(info, name, value))


def read_health(reader, players):
    records = []
    for player in players:
        info, row = reader.resolve((player.record_id.table_id << 17) | player.record_id.row_id, 'Player')
        records.append(PlayerHealth(
            player.record_id,
            read_enum(reader, info, row, 'InjuryStatus'),
            read_enum(reader, info, row, 'InjuryType'),
            read_enum(reader, info, row, 'InjurySeverity'),
            reader.field(info, row, 'MinInjuryDuration'),
            reader.field(info, row, 'MaxInjuryDuration'),
            reader.field(info, row, 'TotalInjuryDuration'),
            reader.field(info, row, 'IsInjuredReserve'),
        ))
    return tuple(records)


def read_recruiting(reader, team, row):
    pointer = reader.pointer(team, row, 'RecruitingBoard')
    if pointer == 0:
        return None
    board, board_row = reader.resolve(pointer, 'RecruitingBoard')
    array = reader.pointer(board, board_row, 'Recruits')
    refs = reader.array(array, 'RecruitTarget', allow_null=True) if array else []
    targets, seen = [], set()
    for ref in refs:
        if ref is None:
            continue
        target, target_row = reader.resolve(ref, 'RecruitTarget')
        recruit_ref = reader.field(target, target_row, 'Recruit')
        recruit, recruit_row = reader.resolve(recruit_ref, 'Recruit')
        if recruit_ref in seen:
            raise ValueError('Duplicate recruit on the controlled board')
        seen.add(recruit_ref)
        player_ref = reader.field(recruit, recruit_row, 'Player')
        player, player_row = reader.resolve(player_ref, 'Player')
        name = ' '.join(reader.field(player, player_row, key)
                        for key in ('FirstName', 'LastName')).strip()
        targets.append(RecruitingTarget(
            record_id(ref), record_id(recruit_ref), record_id(player_ref), name,
            read_enum(reader, player, player_row, 'Position'),
            reader.field(recruit, recruit_row, 'NationalRank'),
            reader.field(recruit, recruit_row, 'PositionRank'),
            read_enum(reader, recruit, recruit_row, 'RecruitStage'),
            read_enum(reader, target, target_row, 'ScholarshipStatus'),
            reader.field(target, target_row, 'ProspectHoursSpentCurrent'),
        ))
    return RecruitingBoard(record_id(pointer),
        reader.field(board, board_row, 'RecruitingHoursAssigned'),
        reader.field(board, board_row, 'RecruitingHoursProcessed'),
        reader.field(board, board_row, 'RecruitingHoursTotal'), tuple(targets))


def load_dynasty(save, schema):
    # Capture each input once so all sections describe identical source bytes.
    raw, schema_raw = save.read_bytes(), schema.read_bytes()
    frozen_save, frozen_schema = FrozenSource(raw), FrozenSource(schema_raw)
    reader = DynastyReader(raw, schema_raw)
    try:
        roster = snapshot_from_report(inspect_fields(frozen_save, frozen_schema))
        report = inspect_schedule(frozen_save, frozen_schema)
        if len(report['season_info']) != 1:
            raise ValueError('Expected one linked season context')
        info = report['season_info'][0]
        season = SeasonContext(info['CurrentSeasonYear'], info['CurrentYear'], info['CurrentWeek'],
            EnumValue(info['CurrentWeekType'], info['CurrentWeekTypeLabel']),
            EnumValue(info['CurrentStage'], info['CurrentStageLabel']))
        team, row = reader.resolve((roster.team.record_id.table_id << 17) | roster.team.record_id.row_id, 'Team')
        return DynastyDetails(roster, season, schedule_from_report(report),
                              read_depth(reader, team, row, roster.team),
                              read_health(reader, roster.team.players),
                              read_recruiting(reader, team, row))
    except (KeyError, StopIteration, TypeError, IndexError) as error:
        raise ValueError(f'Unsupported or incomplete dynasty schema: {error}') from error
