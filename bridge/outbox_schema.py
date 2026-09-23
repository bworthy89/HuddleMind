# Keep one queued event per observation and network-contract version.
OUTBOX_TABLE_SQL = """
CREATE TABLE sync_outbox (
    event_id TEXT PRIMARY KEY NOT NULL,
    observation_id INTEGER NOT NULL
        REFERENCES observations(observation_id),
    schema_version INTEGER NOT NULL,
    event_json TEXT NOT NULL,
    queued_at TEXT NOT NULL,
    delivered_at TEXT,
    UNIQUE (observation_id, schema_version)
)
"""


def create_outbox_schema(connection) -> None:
    # The migration owns the transaction and decides when to commit.
    connection.execute(OUTBOX_TABLE_SQL)

def validate_outbox_schema(connection) -> None:
    # Read the SQL definition SQLite stored for this table.
    row = connection.execute(
        """
        SELECT sql
        FROM sqlite_master
        WHERE type = 'table' AND name = 'sync_outbox'
        """
    ).fetchone()

    if row is None:
        raise ValueError("Missing sync outbox table.")

    # Ignore formatting differences when comparing our versioned definition.
    expected_sql = " ".join(OUTBOX_TABLE_SQL.split()).rstrip(";")
    actual_sql = " ".join(row[0].split()).rstrip(";")

    if actual_sql != expected_sql:
        raise ValueError("Unexpected sync outbox table structure.")

    # Check that every queued event references an existing observation.
    violations = connection.execute(
        "PRAGMA foreign_key_check(sync_outbox)"
    ).fetchall()

    if violations:
        raise ValueError("Outbox contains invalid observation references.")
