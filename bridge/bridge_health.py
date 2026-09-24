"""Small health records contain status only, never saves, tokens, or player data."""
from contextlib import closing
from datetime import datetime, timezone
import json
import sqlite3


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def initialize_health(path):
    with closing(sqlite3.connect(path)) as db, db:
        db.execute('''CREATE TABLE IF NOT EXISTS bridge_health (
            owner_id TEXT NOT NULL, dynasty_id TEXT NOT NULL,
            received_at TEXT NOT NULL, report_json TEXT NOT NULL,
            PRIMARY KEY(owner_id, dynasty_id))''')


def validate_report(body):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('Duplicate field')
            result[key] = value
        return result
    report = json.loads(body.decode('utf-8'), object_pairs_hook=pairs)
    expected = {'dynasty_id', 'capture_running', 'last_capture_at', 'last_delivery_at',
                'pending_count', 'capture_error', 'delivery_error'}
    if not isinstance(report, dict) or set(report) != expected:
        raise ValueError('Invalid health fields')
    from bridge.validate_event import uuid_text
    uuid_text(report['dynasty_id'])
    if type(report['capture_running']) is not bool:
        raise ValueError('Invalid capture status')
    if type(report['pending_count']) is not int or not 0 <= report['pending_count'] <= 1000000:
        raise ValueError('Invalid queue count')
    for key in ('last_capture_at', 'last_delivery_at'):
        value = report[key]
        if value is not None:
            if not isinstance(value, str) or len(value) > 40:
                raise ValueError('Invalid timestamp')
            if datetime.fromisoformat(value).utcoffset() is None:
                raise ValueError('Timezone required')
    for key in ('capture_error', 'delivery_error'):
        if report[key] not in (None, 'capture_failed', 'delivery_failed'):
            raise ValueError('Invalid error code')
    return report


def store_health(path, owner, report):
    with closing(sqlite3.connect(path, timeout=5)) as db, db:
        db.execute('''INSERT INTO bridge_health VALUES (?, ?, ?, ?)
            ON CONFLICT(owner_id,dynasty_id) DO UPDATE SET
            received_at=excluded.received_at, report_json=excluded.report_json''',
            (owner, report['dynasty_id'], utc_now(), json.dumps(report)))


def read_health(path, owner, allowed, *, now=None):
    now = now or datetime.now(timezone.utc)
    with closing(sqlite3.connect(path)) as db:
        rows = dict((dynasty, (received, raw)) for dynasty, received, raw in db.execute(
            'SELECT dynasty_id, received_at, report_json FROM bridge_health WHERE owner_id=?', (owner,)))
    result = []
    for dynasty in sorted(allowed):
        if dynasty not in rows:
            result.append({'dynasty_id': dynasty, 'status': 'unknown', 'last_seen_at': None, 'report': None})
            continue
        received, raw = rows[dynasty]
        online = (now - datetime.fromisoformat(received)).total_seconds() <= 900
        result.append({'dynasty_id': dynasty, 'status': 'online' if online else 'offline',
                       'last_seen_at': received, 'report': json.loads(raw)})
    return result


def capture_status(database, dynasty, *, success=False, error=None, stopped=False):
    # A separate local database avoids changing the observation-history schema.
    path = database.with_suffix('.health.sqlite3')
    with closing(sqlite3.connect(path, timeout=5)) as db, db:
        db.execute('''CREATE TABLE IF NOT EXISTS capture_status (
            dynasty TEXT PRIMARY KEY, seen TEXT, captured TEXT, error TEXT, running INTEGER)''')
        now = utc_now()
        db.execute('''INSERT INTO capture_status VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(dynasty) DO UPDATE SET seen=excluded.seen,
            captured=COALESCE(excluded.captured,capture_status.captured),
            error=excluded.error, running=excluded.running''',
            (dynasty, now, now if success else None, error, int(not stopped)))


def local_report(database, dynasty, receiver, delivery_error=None):
    from bridge.outbox import list_pending_events
    report = dict(dynasty_id=dynasty, capture_running=False, last_capture_at=None,
                  last_delivery_at=None, pending_count=len(list_pending_events(database, dynasty, receiver)),
                  capture_error=None, delivery_error=delivery_error)
    path = database.with_suffix('.health.sqlite3')
    if path.exists():
        with closing(sqlite3.connect(path)) as db:
            row = db.execute('SELECT seen,captured,error,running FROM capture_status WHERE dynasty=?', (dynasty,)).fetchone()
        if row:
            age = (datetime.now(timezone.utc) - datetime.fromisoformat(row[0])).total_seconds()
            report.update(capture_running=bool(row[3]) and 0 <= age <= 180,
                          last_capture_at=row[1], capture_error=row[2])
    with closing(sqlite3.connect(database.resolve().as_uri() + '?mode=ro', uri=True)) as db:
        report['last_delivery_at'] = db.execute('''SELECT max(d.delivered_at) FROM sync_deliveries d
            JOIN sync_outbox q ON q.event_id=d.event_id JOIN observations o ON o.observation_id=q.observation_id
            WHERE o.dynasty_id=? AND d.receiver=?''', (dynasty, receiver)).fetchone()[0]
    return report
