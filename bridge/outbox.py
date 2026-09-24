"""Persist immutable messages locally before any network delivery is attempted."""
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from uuid import uuid4

from bridge.local_store import connect_database, DATABASE_VERSION
from bridge.sync_event import ObservationEvent, EVENT_SCHEMA_VERSION, serialize_observation_event


@dataclass(frozen=True)
class QueuedEvent:
    event_id: str
    observation_id: int
    schema_version: int
    event_json: str
    queued_at: str
    delivered_at: str | None


def _connect(path, *, read_only):
    if not path.is_file():
        raise ValueError(f'Database not found: {path}')
    connection = connect_database(path, read_only=read_only)
    try:
        version = connection.execute('PRAGMA user_version').fetchone()[0]
        if version != DATABASE_VERSION:
            raise ValueError(f'Expected database version {DATABASE_VERSION}; found {version}. Run database initialization.')
    except Exception:
        connection.close()
        raise
    return connection


def queue_observation(path, dynasty_id: str, observation_id: int) -> QueuedEvent:
    connection = _connect(path, read_only=False)
    try:
        with connection:
            # Serialize competing writers before checking or creating the event.
            connection.execute('BEGIN IMMEDIATE')
            observation = connection.execute('''SELECT observed_at, snapshot_json
                FROM observations WHERE dynasty_id=? AND observation_id=?''',
                (dynasty_id, observation_id)).fetchone()
            if observation is None:
                raise ValueError('Observation not found for this dynasty.')
            existing = connection.execute('''SELECT event_id, observation_id, schema_version,
                event_json, queued_at, delivered_at FROM sync_outbox
                WHERE observation_id=? AND schema_version=?''',
                (observation_id, EVENT_SCHEMA_VERSION)).fetchone()
            if existing is not None:
                # Even delivered entries retain their original message and status.
                return QueuedEvent(*existing)
            event = ObservationEvent(str(uuid4()), dynasty_id, observation[0], json.loads(observation[1]))
            queued = QueuedEvent(event.event_id, observation_id, event.schema_version,
                                 serialize_observation_event(event),
                                 datetime.now(timezone.utc).isoformat(), None)
            connection.execute('''INSERT INTO sync_outbox
                (event_id, observation_id, schema_version, event_json, queued_at, delivered_at)
                VALUES (?, ?, ?, ?, ?, ?)''',
                (queued.event_id, queued.observation_id, queued.schema_version,
                 queued.event_json, queued.queued_at, queued.delivered_at))
        return queued
    finally:
        connection.close()


def list_pending_events(path, dynasty_id: str) -> tuple[QueuedEvent, ...]:
    connection = _connect(path, read_only=True)
    try:
        if connection.execute('SELECT 1 FROM dynasties WHERE dynasty_id=?', (dynasty_id,)).fetchone() is None:
            raise ValueError('Dynasty not found')
        # Return stored JSON exactly as queued, without rebuilding the envelope.
        rows = connection.execute('''SELECT q.event_id, q.observation_id, q.schema_version,
            q.event_json, q.queued_at, q.delivered_at FROM sync_outbox q
            JOIN observations o ON o.observation_id=q.observation_id
            WHERE o.dynasty_id=? AND q.delivered_at IS NULL ORDER BY q.rowid''', (dynasty_id,)).fetchall()
        return tuple(QueuedEvent(*row) for row in rows)
    finally:
        connection.close()


def mark_delivered(path, dynasty_id: str, event: QueuedEvent) -> None:
    """Record a verified acknowledgment without changing the queued message."""
    connection = _connect(path, read_only=False)
    try:
        with connection:
            connection.execute('BEGIN IMMEDIATE')
            row = connection.execute('''SELECT q.event_json FROM sync_outbox q
                JOIN observations o ON o.observation_id=q.observation_id
                WHERE q.event_id=? AND o.dynasty_id=?''',
                (event.event_id, dynasty_id)).fetchone()
            if row is None or row[0] != event.event_json:
                raise ValueError('Queued event no longer matches the acknowledged message')
            # Concurrent senders preserve the first successful delivery timestamp.
            connection.execute('''UPDATE sync_outbox SET delivered_at=?
                WHERE event_id=? AND delivered_at IS NULL''',
                (datetime.now(timezone.utc).isoformat(), event.event_id))
    finally:
        connection.close()
