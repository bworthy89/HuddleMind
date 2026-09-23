"""Preserve advice, user choices, and reported outcomes without rewriting history."""
from datetime import datetime, timezone
from uuid import uuid4

from bridge.local_store import connect_database, DATABASE_VERSION


def _text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{name} cannot be blank')
    return value.strip()


def _connect(path, *, read_only):
    if not path.is_file():
        raise ValueError(f'Database not found: {path}')
    connection = connect_database(path, read_only=read_only)
    try:
        version = connection.execute('PRAGMA user_version').fetchone()[0]
        if version != DATABASE_VERSION:
            raise ValueError(f'Database version {version} is not supported here; run the init command to upgrade')
    except Exception:
        connection.close()
        raise
    return connection


def _require_dynasty(connection, dynasty_id):
    if connection.execute('SELECT 1 FROM dynasties WHERE dynasty_id=?', (dynasty_id,)).fetchone() is None:
        raise ValueError('Dynasty not found')


def _find(connection, dynasty_id, recommendation_id):
    return connection.execute('''SELECT r.recommendation_id, r.observation_id,
        r.created_at, r.advice, r.rationale, r.source FROM recommendations r
        JOIN observations o ON o.observation_id=r.observation_id
        WHERE o.dynasty_id=? AND r.recommendation_id=?''',
        (dynasty_id, recommendation_id)).fetchone()


def record_recommendation(path, dynasty_id, observation_id, advice, rationale, source='manual'):
    advice, rationale, source = (_text(value, name) for value, name in
                                 ((advice, 'Advice'), (rationale, 'Rationale'), (source, 'Source')))
    connection = _connect(path, read_only=False)
    try:
        with connection:
            # Check ownership in the same write transaction as the insert.
            connection.execute('BEGIN IMMEDIATE')
            if connection.execute('SELECT 1 FROM observations WHERE dynasty_id=? AND observation_id=?',
                                  (dynasty_id, observation_id)).fetchone() is None:
                raise ValueError('Observation not found for this dynasty')
            identity = str(uuid4())
            connection.execute('INSERT INTO recommendations VALUES (?, ?, ?, ?, ?, ?)',
                               (identity, observation_id, datetime.now(timezone.utc).isoformat(),
                                advice, rationale, source))
        return identity
    finally:
        connection.close()


def record_event(path, dynasty_id, recommendation_id, kind, detail, source='manual'):
    if kind not in ('choice', 'outcome'):
        raise ValueError('Event kind must be choice or outcome')
    detail, source = _text(detail, 'Detail'), _text(source, 'Source')
    connection = _connect(path, read_only=False)
    try:
        with connection:
            connection.execute('BEGIN IMMEDIATE')
            if _find(connection, dynasty_id, recommendation_id) is None:
                raise ValueError('Recommendation not found for this dynasty')
            cursor = connection.execute('''INSERT INTO recommendation_events
                (recommendation_id, created_at, kind, detail, source) VALUES (?, ?, ?, ?, ?)''',
                (recommendation_id, datetime.now(timezone.utc).isoformat(), kind, detail, source))
        return cursor.lastrowid
    finally:
        connection.close()


def list_recommendations(path, dynasty_id):
    connection = _connect(path, read_only=True)
    try:
        _require_dynasty(connection, dynasty_id)
        return connection.execute('''SELECT r.recommendation_id, r.observation_id, r.created_at, r.advice
            FROM recommendations r JOIN observations o ON o.observation_id=r.observation_id
            WHERE o.dynasty_id=? ORDER BY r.rowid DESC''', (dynasty_id,)).fetchall()
    finally:
        connection.close()


def get_recommendation(path, dynasty_id, recommendation_id):
    connection = _connect(path, read_only=True)
    try:
        # Both reads see the same snapshot if another process records an event.
        connection.execute('BEGIN')
        row = _find(connection, dynasty_id, recommendation_id)
        if row is None:
            return None
        result = dict(zip(('recommendation_id', 'observation_id', 'created_at', 'advice', 'rationale', 'source'), row))
        events = connection.execute('''SELECT event_id, created_at, kind, detail, source
            FROM recommendation_events WHERE recommendation_id=? ORDER BY event_id''', (recommendation_id,)).fetchall()
        result['events'] = [dict(zip(('event_id', 'created_at', 'kind', 'detail', 'source'), event)) for event in events]
        return result
    finally:
        connection.close()
