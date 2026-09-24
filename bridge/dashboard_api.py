"""Read the latest captured snapshot, not whichever retry arrived last."""
from contextlib import closing
import json
import sqlite3
from bridge.bridge_health import read_health


def dashboard(path, owner, allowed):
    dynasties = []
    with closing(sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)) as db:
        for dynasty in sorted(allowed):
            row = db.execute('''SELECT event_json, received_at FROM received_events
                WHERE owner_id=? AND dynasty_id=?
                ORDER BY julianday(json_extract(event_json, '$.observed_at')) DESC,
                    received_at DESC, event_id DESC LIMIT 1''', (owner, dynasty)).fetchone()
            dynasties.append({'dynasty_id': dynasty, 'snapshot': json.loads(row[0]) if row else None,
                              'received_at': row[1] if row else None})
    return {'dynasties': dynasties, 'bridges': read_health(path, owner, allowed)}
