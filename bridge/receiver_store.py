"""Separate receiver database; acknowledgments follow committed transactions."""
from datetime import datetime, timezone
import json
import sqlite3

APPLICATION_ID = 1213022797


class EventConflict(ValueError):
    pass


def initialize_receiver(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    try:
        with connection:
            connection.execute('BEGIN IMMEDIATE')
            tables = connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            app_id = connection.execute('PRAGMA application_id').fetchone()[0]
            version = connection.execute('PRAGMA user_version').fetchone()[0]
            if tables:
                if app_id != APPLICATION_ID or version != 1:
                    raise ValueError('Not a supported receiver database; use a separate path')
                # Startup must verify the constraint that makes retries idempotent.
                columns = connection.execute('PRAGMA table_info(received_events)').fetchall()
                expected = [('owner_id', 'TEXT', 1, 1), ('event_id', 'TEXT', 1, 2),
                            ('dynasty_id', 'TEXT', 1, 0), ('event_json', 'TEXT', 1, 0),
                            ('received_at', 'TEXT', 1, 0)]
                if [(c[1], c[2], c[3], c[5]) for c in columns] != expected:
                    raise ValueError('Unexpected receiver table structure')
                return
            if app_id != 0 or version != 0:
                raise ValueError('Unsupported receiver database metadata')
            connection.execute('''CREATE TABLE received_events (
                owner_id TEXT NOT NULL, event_id TEXT NOT NULL, dynasty_id TEXT NOT NULL,
                event_json TEXT NOT NULL, received_at TEXT NOT NULL,
                PRIMARY KEY (owner_id, event_id))''')
            connection.execute(f'PRAGMA application_id={APPLICATION_ID}')
            connection.execute('PRAGMA user_version=1')
    finally:
        connection.close()


def store_event(path, owner_id, event):
    # Canonical JSON treats whitespace and object-key ordering as insignificant.
    payload = json.dumps(event, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(',', ':'))
    connection = sqlite3.connect(path, timeout=5)
    try:
        with connection:
            connection.execute('BEGIN IMMEDIATE')
            existing = connection.execute('SELECT event_json FROM received_events WHERE owner_id=? AND event_id=?',
                                          (owner_id, event['event_id'])).fetchone()
            if existing:
                if existing[0] != payload:
                    raise EventConflict('Event ID already has different content')
                return 'already_stored'
            connection.execute('INSERT INTO received_events VALUES (?, ?, ?, ?, ?)',
                               (owner_id, event['event_id'], event['dynasty_id'], payload,
                                datetime.now(timezone.utc).isoformat()))
        return 'stored'
    finally:
        connection.close()
