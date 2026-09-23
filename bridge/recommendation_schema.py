"""Version-2 schema: immutable advice and append-only follow-up entries."""

TABLES = {
    'recommendations': '''CREATE TABLE recommendations (
        recommendation_id TEXT PRIMARY KEY NOT NULL,
        observation_id INTEGER NOT NULL REFERENCES observations(observation_id),
        created_at TEXT NOT NULL,
        advice TEXT NOT NULL,
        rationale TEXT NOT NULL,
        source TEXT NOT NULL
    )''',
    'recommendation_events': '''CREATE TABLE recommendation_events (
        event_id INTEGER PRIMARY KEY,
        recommendation_id TEXT NOT NULL REFERENCES recommendations(recommendation_id),
        created_at TEXT NOT NULL,
        kind TEXT NOT NULL CHECK (kind IN ('choice', 'outcome')),
        detail TEXT NOT NULL,
        source TEXT NOT NULL
    )''',
}


def create_schema(connection):
    # Caller owns the transaction; never commit a partially applied migration.
    for sql in TABLES.values():
        connection.execute(sql)


def validate_schema(connection):
    # Compare our own versioned DDL so altered constraints are not silently accepted.
    for name, expected in TABLES.items():
        row = connection.execute('SELECT sql FROM sqlite_master WHERE type=? AND name=?',
                                 ('table', name)).fetchone()
        normalize = lambda sql: ' '.join(sql.split()).strip().rstrip(';')
        if row is None or normalize(row[0]) != normalize(expected):
            raise ValueError(f'Unexpected recommendation table structure: {name}')
    for name in TABLES:
        if connection.execute(f'PRAGMA foreign_key_check({name})').fetchall():
            raise ValueError('Invalid recommendation history references')
