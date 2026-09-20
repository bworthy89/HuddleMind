"""Read-only schedule research; retain raw season values pending UI validation."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import zlib

from bridge.discover_fields import inspect_fields, layout, packed_value
from bridge.discover_rosters import empty_rows, table_directory, word_field


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
            games.append(game)
    return dict(save_sha256=roster['save_sha256'], schema_sha256=roster['schema_sha256'],
                selected_team=selected, season_info=season_info, tables=inventory, games=games,
                caveat='Candidate schedule: practice rows retained; no calendar/week mapping or final-result interpretation asserted.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('save', type=Path)
    parser.add_argument('schema', type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect_schedule(args.save, args.schema), indent=2))
