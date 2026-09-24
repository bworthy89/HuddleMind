"""Version 4 records acknowledgments separately for each receiver origin."""
SQL = '''CREATE TABLE sync_deliveries (
    event_id TEXT NOT NULL REFERENCES sync_outbox(event_id),
    receiver TEXT NOT NULL,
    delivered_at TEXT NOT NULL,
    PRIMARY KEY (event_id, receiver)
)'''


def create_schema(connection):
    connection.execute(SQL)
    # Legacy acknowledgments lack a destination. Preserve them in sync_outbox;
    # do not invent a receiver or let them suppress delivery to a new host.


def validate_schema(connection):
    row = connection.execute("SELECT sql FROM sqlite_master WHERE name='sync_deliveries' AND type='table'").fetchone()
    if row is None or ' '.join(row[0].split()) != ' '.join(SQL.split()):
        raise ValueError('Unexpected sync delivery table structure')
    if connection.execute('PRAGMA foreign_key_check(sync_deliveries)').fetchall():
        raise ValueError('Invalid sync delivery event reference')
