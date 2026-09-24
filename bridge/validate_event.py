"""Strict version-1 event validation at the receiver boundary."""
from dataclasses import fields, is_dataclass
from datetime import datetime, timedelta
import json
import re
import types
from typing import get_args, get_origin, get_type_hints
from uuid import UUID

from bridge.dynasty_details import DynastyDetails
from bridge.models import Player
from bridge.player_ratings import RATING_FIELDS


def uuid_text(value):
    if not isinstance(value, str) or str(UUID(value)) != value:
        raise ValueError('Expected a canonical UUID')
    return value


def _shape(value, annotation, path):
    origin, args = get_origin(annotation), get_args(annotation)
    if origin is types.UnionType:
        if value is None and type(None) in args:
            return
        for option in args:
            if option is not type(None):
                return _shape(value, option, path)
    if is_dataclass(annotation):
        expected_fields = {f.name for f in fields(annotation)}
        # Additive v1 compatibility: old immutable events lack ratings. Do not mutate them.
        legacy_player = annotation is Player and isinstance(value, dict) and 'ratings' not in value
        if legacy_player:
            expected_fields.remove('ratings')
        if not isinstance(value, dict) or set(value) != expected_fields:
            raise ValueError(f'Unexpected fields at {path}')
        for name, expected in get_type_hints(annotation).items():
            if legacy_player and name == 'ratings':
                continue
            _shape(value[name], expected, f'{path}.{name}')
    elif origin is tuple:
        if not isinstance(value, list) or len(value) > 10000:
            raise ValueError(f'Expected a bounded array at {path}')
        for item in value:
            _shape(item, args[0], path)
    elif type(value) is not annotation:
        raise ValueError(f'Incorrect value type at {path}')
    elif annotation is str:
        if len(value) > 10000:
            raise ValueError(f'Text too long at {path}')
        # JSON escapes can contain lone surrogates that cannot be stored as UTF-8.
        value.encode('utf-8')
    elif annotation is int and not -(2**63) <= value < 2**63:
        raise ValueError(f'Integer out of range at {path}')


def decode_event(body):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('Duplicate JSON key')
            result[key] = value
        return result
    def invalid_constant(value):
        raise ValueError('Non-finite JSON number')
    try:
        event = json.loads(body.decode('utf-8'), object_pairs_hook=pairs, parse_constant=invalid_constant)
        required = {'schema_version', 'event_id', 'event_type', 'dynasty_id', 'observed_at', 'payload'}
        if not isinstance(event, dict) or set(event) != required:
            raise ValueError('Unexpected event envelope')
        if type(event['schema_version']) is not int or event['schema_version'] != 1:
            raise ValueError('Unsupported event schema version')
        if event['event_type'] != 'dynasty.observation.captured':
            raise ValueError('Unsupported event type')
        uuid_text(event['event_id'])
        uuid_text(event['dynasty_id'])
        if not isinstance(event['observed_at'], str):
            raise ValueError('Invalid capture timestamp')
        timestamp = datetime.fromisoformat(event['observed_at'])
        if timestamp.utcoffset() != timedelta(0):
            raise ValueError('Capture timestamp must include UTC offset')
        _shape(event['payload'], DynastyDetails, 'payload')
        roster = event['payload']['roster']
        for key in ('save_sha256', 'schema_sha256'):
            if re.fullmatch('[0-9a-f]{64}', roster[key]) is None:
                raise ValueError('Invalid source hash')
        if roster['coach']['team_index'] != roster['team']['team_index'] or not roster['coach']['is_user_controlled']:
            raise ValueError('Inconsistent controlled team')
        players = roster['team']['players']
        def identity(value):
            table, row = value['table_id'], value['row_id']
            if not 0 < table < 2**15 or not 0 <= row < 2**17:
                raise ValueError('Invalid source record identity')
            return table, row
        ids = [identity(p['record_id']) for p in players]
        if len(ids) != len(set(ids)):
            raise ValueError('Duplicate roster player')
        if any(not 0 <= p['overall'] <= 100 for p in players):
            raise ValueError('Invalid overall rating')
        for player in players:
            ratings = player.get('ratings', [])
            names = [rating['field'] for rating in ratings]
            if len(names) != len(set(names)) or set(names) - set(RATING_FIELDS):
                raise ValueError('Invalid player rating fields')
            if any(r['value'] is not None and not 0 <= r['value'] <= 127 for r in ratings):
                raise ValueError('Invalid saved player rating')
        health_ids = [identity(h['player_id']) for h in event['payload']['health']]
        if len(health_ids) != len(ids) or set(health_ids) != set(ids):
            raise ValueError('Health records do not match roster')
        for slot in event['payload']['depth_chart'] or []:
            if slot['depth'] < 1 or (slot['player_id'] is not None and identity(slot['player_id']) not in ids):
                raise ValueError('Invalid depth slot')
        return event
    except (TypeError, KeyError, OverflowError, RecursionError, UnicodeError) as error:
        raise ValueError('Invalid event data') from error
