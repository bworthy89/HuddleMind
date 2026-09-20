"""Read-only schedule research; retain raw season values pending UI validation."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import zlib

from bridge.discover_fields import inspect_fields, layout, packed_value
from bridge.discover_rosters import empty_rows, table_directory, word_field, u32


def resolve_reference(data, tables, value, expected_name):
    table_id, row = divmod(value, 1 << 17)
    target = tables.get(table_id)
    if (value == 0 or target is None or target['name'] != expected_name
            or row >= target['count'] or row in empty_rows(data, target)):
        raise ValueError(f'Invalid or unused {expected_name} reference')
    return target, row


def schedule_references(data, tables, value):
    array, row = resolve_reference(data, tables, value, 'SeasonGame[]')
    length = u32(data, array['metadata'] + row * 4)
    if length > array['words']:
        raise ValueError('Schedule array exceeds row capacity')
    references = set()
    for index in range(length):
        value = u32(data, array['records'] + (row * array['words'] + index) * 4)
        target, game_row = resolve_reference(data, tables, value, 'SeasonGame')
        identity = (target['id'], game_row)
        if identity in references:
            raise ValueError('Duplicate game reference in schedule')
        references.add(identity)
    return references


def result_label(status, home_score, away_score, selected_is_home):
    # Unfinished states remain pending even if they contain scores.
    if status not in ('HomeWon', 'AwayWon', 'Tied'):
        return 'pending' if status in ('Unplayed', 'Unscheduled', 'HomeScheduled', 'AwayScheduled') else 'unknown'
    consistent = ((status == 'HomeWon' and home_score > away_score)
                  or (status == 'AwayWon' and away_score > home_score)
                  or (status == 'Tied' and home_score == away_score))
    if not consistent:
        raise ValueError('Completed status contradicts game scores')
    if status == 'Tied':
        return 'tie'
    return 'win' if (status == 'HomeWon') == selected_is_home else 'loss'


def enum_label(field, value):
    members = field.get('enum', {}).get('_members', [])
    names = [m['_name'] for m in members
             if m['_value'] == value and not m['_name'].endswith('_')]
    return names[0] if len(names) == 1 else f'Unknown ({value})'


def inspect_schedule(save, schema):
    roster = inspect_fields(save, schema)
    if roster['selection']['status'] != 'resolved':
        raise ValueError('Schedule discovery requires a resolved controlled team')
    raw = save.read_bytes()
    if hashlib.sha256(raw).hexdigest() != roster['save_sha256']:
        raise ValueError('Save changed during schedule discovery')
    decoder = zlib.decompressobj()
    data = decoder.decompress(raw[82:82 + int.from_bytes(raw[74:78], 'little')], 64 * 1024 * 1024)
    if not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
        raise ValueError('Invalid compressed stream')
    schema_bytes = schema.read_bytes()
    if hashlib.sha256(schema_bytes).hexdigest() != roster['schema_sha256']:
        raise ValueError('Schema changed during discovery')
    schemas = {s['name']: s for s in json.loads(gzip.decompress(schema_bytes))['schemas']}
    tables = {key: value[0] for key, value in table_directory(data).items()}
    selected = roster['selection']['team']
    selected_ref = (selected['table'], selected['row'])
    managers = [(t, row) for t in tables.values() if t['name'] == 'SeasonManager'
                for row in range(t['count']) if row not in empty_rows(data, t)]
    if len(managers) != 1:
        raise ValueError('Expected one occupied season manager')
    manager, manager_row = managers[0]
    attributes = schemas['SeasonManager']['attributes']
    # Only these isolated aligned pointers are needed; do not decode its methods.
    schedule_pointer = word_field(data, manager, attributes, manager_row, 'SeasonSchedule')
    linked_games = schedule_references(data, tables, schedule_pointer)
    info_table, info_row = resolve_reference(data, tables,
        word_field(data, manager, attributes, manager_row, 'SeasonInfo'), 'SeasonInfo')

    def team_reference(value):
        if value == 0:
            return None
        table_id, row = divmod(value, 1 << 17)
        target = tables.get(table_id)
        if target is None or target['name'] != 'Team' or row >= target['count'] or row in empty_rows(data, target):
            raise ValueError('Invalid schedule Team reference')
        return dict(table=table_id, row=row,
                    name=word_field(data, target, schemas['Team']['attributes'], row, 'DisplayName'))

    games, season_info, inventory = [], [], []
    keys = ('SeasonYear', 'SeasonWeek', 'SeasonWeekType', 'GameStatus',
            'HomeScore', 'AwayScore', 'IsPractice', 'HasBeenPublished',
            'GameDateMonth', 'GameDateDay', 'IsSimmed')
    for info in tables.values():
        if info['name'] not in ('SeasonGame', 'SeasonInfo'):
            continue
        fields = layout(data, info, schemas[info['name']]['attributes'])
        unused = empty_rows(data, info)
        inventory.append(dict(name=info['name'], table=info['id'], slots=info['count'], unused=len(unused)))
        for row in range(info['count']):
            if row in unused:
                continue
            read = lambda key: packed_value(data, info, fields, row, key)
            if info['name'] == 'SeasonInfo':
                if (info['id'], row) != (info_table['id'], info_row):
                    continue
                values = {k: read(k) for k in ('BaseCalendarYear', 'CurrentSeasonYear', 'CurrentYear', 'CurrentWeek', 'CurrentWeekType', 'CurrentStage')}
                for key in ('CurrentWeekType', 'CurrentStage'):
                    values[key + 'Label'] = enum_label(fields[key], values[key])
                season_info.append(values)
                continue
            home, away = read('HomeTeam'), read('AwayTeam')
            if selected_ref not in (divmod(home, 1 << 17), divmod(away, 1 << 17)):
                continue
            game = {key: read(key) for key in keys}
            game.update(table=info['id'], row=row, home=team_reference(home), away=team_reference(away))
            for key in ('GameStatus', 'SeasonWeekType'):
                game[key + 'Label'] = enum_label(fields[key], game[key])
            game['in_manager_schedule'] = (info['id'], row) in linked_games
            game['result'] = ('excluded_practice' if game['IsPractice'] else
                              result_label(game['GameStatusLabel'], game['HomeScore'],
                                           game['AwayScore'], divmod(home, 1 << 17) == selected_ref))
            games.append(game)
    fixtures = [g for g in games if g['in_manager_schedule'] and not g['IsPractice']]
    fixtures.sort(key=lambda g: (g['SeasonYear'], g['SeasonWeek'], g['row']))
    return dict(save_sha256=roster['save_sha256'], schema_sha256=roster['schema_sha256'],
                selected_team=selected, season_info=season_info, tables=inventory, games=games,
                manager_schedule_count=len(linked_games), fixtures=fixtures,
                caveat='Manager-linked fixtures; raw week/year values retained. Results use schema status and score consistency; UI validation pending.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('save', type=Path)
    parser.add_argument('schema', type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect_schedule(args.save, args.schema), indent=2))
