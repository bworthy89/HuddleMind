"""Bounded research for packed fields and the record free list (read only)."""
from bridge.discover_rosters import u32, empty_rows, table_directory
from bridge.player_ratings import read_ratings


def layout(data, info, attributes):
    """Resolve stored fields, then reverse packing order within each 32-bit word.

    Reference: madden-franchise readOffsetTable. This accepts fully described
    words only; unexpected gaps or crossing fields fail instead of guessing.
    """
    if len(attributes) != info['fields']:
        raise ValueError('Schema member count mismatch')
    seen, fields = set(), []
    for index, attribute in enumerate(attributes):
        offset = u32(data, info['metadata'] + index * 4)
        if (attribute.get('final') == 'true' or attribute.get('const')
                or '()' in attribute['type'] or attribute['type'] == 'ITransaction_Sleep'
                or offset in seen):
            continue
        seen.add(offset)
        fields.append(dict(attribute, stored_offset=offset))
    fields.sort(key=lambda f: f['stored_offset'])
    end = info['words'] * 32
    for index, field in enumerate(fields):
        following = fields[index + 1]['stored_offset'] if index + 1 < len(fields) else end
        field['width'] = min(32, following - field['stored_offset'])
        if not 0 < field['width'] <= 32 or following > end:
            raise ValueError('Invalid field width')
    for word in range(info['words']):
        group = [f for f in fields if f['stored_offset'] // 32 == word]
        if not group or sum(f['width'] for f in group) != 32 or group[0]['stored_offset'] != word * 32:
            raise ValueError(f'Incomplete packed word {word}')
        cursor = word * 32
        for field in reversed(group):
            field['offset'] = cursor
            cursor += field['width']
    return {f['name']: f for f in fields}


def packed_value(data, info, fields, row, name):
    if not 0 <= row < info['count']:
        raise ValueError('Row outside table')
    field = fields[name]
    offset, width = field['offset'], field['width']
    word = u32(data, info['records'] + row * info['words'] * 4 + offset // 32 * 4)
    shift = 32 - offset % 32 - width
    if shift < 0:
        raise ValueError('Field crosses a word')
    value = (word >> shift) & ((1 << width) - 1)
    if field['type'] == 'bool':
        return bool(value)
    if field['type'] == 'int':
        minimum = int(field.get('minValue', 0))
        if minimum < 0:
            value += minimum
        if 'maxValue' in field and int(field['maxValue']) >= 0:
            if not minimum <= value <= int(field['maxValue']):
                raise ValueError(f'{name} exceeds schema range')
    return value


def controlled_selection(coaches):
    """Return an explicit selection outcome; never silently pick the first match."""
    if not coaches:
        return {'status': 'no_controlled_coach'}
    if len(coaches) > 1:
        return {'status': 'multiple_controlled_coaches'}
    teams = coaches[0]['team_candidates']
    if not teams:
        return {'status': 'missing_team'}
    if len(teams) > 1:
        return {'status': 'ambiguous_team'}
    return {'status': 'resolved', 'team': teams[0]}


def inspect_fields(save, schema):
    import gzip
    import hashlib
    import json
    import zlib
    from bridge.discover_rosters import inspect, table, word_field

    report = inspect(save, schema)
    raw = save.read_bytes()
    if hashlib.sha256(raw).hexdigest() != report['save_sha256']:
        raise ValueError('Save changed during discovery; retry on a stable save')
    decoder = zlib.decompressobj()
    data = decoder.decompress(raw[82:82 + int.from_bytes(raw[74:78], 'little')], 64 * 1024 * 1024)
    if not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
        raise ValueError('Invalid compressed stream')
    schemas = {s['name']: s for s in json.loads(gzip.decompress(schema.read_bytes()))['schemas']}
    tables = {}
    for choices in table_directory(data).values():
        info = choices[0]
        if info['name'] not in ('Team', 'Player', 'Coach'):
            continue
        tables[info['id']] = (info, layout(data, info, schemas[info['name']]['attributes']), empty_rows(data, info))
    controlled, counts, mismatches = [], [], []
    for info, fields, unused in tables.values():
        counts.append(dict(name=info['name'], table=info['id'], slots=info['count'], unused=len(unused)))
        if info['name'] != 'Coach':
            continue
        for row in range(info['count']):
            if row in unused or not packed_value(data, info, fields, row, 'IsUserControlled'):
                continue
            coach = {k: word_field(data, info, schemas['Coach']['attributes'], row, k) for k in ('FirstName', 'LastName')}
            coach.update(table=info['id'], row=row, TeamIndex=packed_value(data, info, fields, row, 'TeamIndex'))
            controlled.append(coach)
    active = []
    for team in report['teams']:
        info, fields, unused = tables[team['table']]
        if team['row'] in unused:
            continue
        team['TeamIndex'] = packed_value(data, info, fields, team['row'], 'TeamIndex')
        for player in team.get('players', []):
            pi, pf, empty = tables[player['table']]
            if player['row'] in empty:
                raise ValueError('Roster references an unused Player slot')
            for key in ('Position', 'OverallRating', 'TeamIndex'):
                player[key] = packed_value(data, pi, pf, player['row'], key)
            player['Ratings'] = read_ratings(data, pi, pf, player['row'], packed_value)
            enum = pf['Position']['enum']['_members']
            labels = [m['_name'] for m in enum if m['_value'] == player['Position'] and not m['_name'].endswith('_')]
            player['PositionLabel'] = labels[0] if len(labels) == 1 else f"Unknown ({player['Position']})"
            if player['TeamIndex'] != team['TeamIndex']:
                mismatches.append(dict(team=team['DisplayName'], player_row=player['row'], player_team_index=player['TeamIndex']))
        active.append(team)
    for coach in controlled:
        coach['team_candidates'] = [dict(table=t['table'], row=t['row'], name=t['DisplayName'])
                                    for t in active if t['TeamIndex'] == coach['TeamIndex']]
    report.update(teams=active, controlled_coaches=controlled, occupancy=counts,
                  roster_team_mismatches=mismatches,
                  selection=controlled_selection(controlled),
                  caveat='Structurally checked snapshot; in-game comparison and other builds remain unverified.')
    return report


if __name__ == '__main__':
    import argparse
    import json
    from pathlib import Path
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('save', type=Path)
    parser.add_argument('schema', type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect_fields(args.save, args.schema), indent=2))
