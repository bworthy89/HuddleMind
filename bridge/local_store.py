import sqlite3
import json

from pathlib import Path
from uuid import uuid4
from dataclasses import asdict
from bridge.dynasty_details import DynastyDetails
from datetime import datetime, timezone

DATABASE_VERSION = 4

def validate_database_columns(connection: sqlite3.Connection) -> None:
    # Describe the columns required by database version 1.
    # Each tuple contains: name, type, NOT NULL flag, primary-key position.
    expected_tables = {
        "dynasties": [
            ("dynasty_id", "TEXT", 1, 1),
            ("name", "TEXT", 1, 0),
        ],
        "observations": [
            ("observation_id", "INTEGER", 0, 1),
            ("dynasty_id", "TEXT", 1, 0),
            ("observed_at", "TEXT", 1, 0),
            ("save_sha256", "TEXT", 1, 0),
            ("schema_sha256", "TEXT", 1, 0),
            ("snapshot_json", "TEXT", 1, 0),
        ],
    }

    for table_name, expected_columns in expected_tables.items():
        # Table names come only from the fixed definitions above.
        rows = connection.execute(
            f"PRAGMA table_info({table_name})"
        ).fetchall()

        actual_columns = [
            (row[1], row[2].upper(), row[3], row[5])
            for row in rows
        ]

        if actual_columns != expected_columns:
            raise ValueError(
                f"Unexpected column structure for table: {table_name}"
            )

def validate_database_relationships(
    connection: sqlite3.Connection,
) -> None:
    # Require the expected relationship between observations and dynasties.
    foreign_keys = connection.execute(
        "PRAGMA foreign_key_list(observations)"
    ).fetchall()

    expected_foreign_keys = [
        (
            0, 0,
            "dynasties",
            "dynasty_id",
            "dynasty_id",
            "NO ACTION",
            "NO ACTION",
            "NONE",
        )
    ]

    if foreign_keys != expected_foreign_keys:
        raise ValueError("Unexpected observation foreign-key structure.")

    # Find the UNIQUE constraint that prevents duplicate source snapshots.
    indexes = connection.execute(
        "PRAGMA index_list(observations)"
    ).fetchall()

    expected_columns = [
        "dynasty_id",
        "save_sha256",
        "schema_sha256",
    ]
    found_unique_constraint = False

    for index in indexes:
        # Require a non-partial index created by a UNIQUE constraint.
        if index[2] != 1 or index[3] != "u" or index[4] != 0:
            continue

        columns = connection.execute(
            "SELECT name FROM pragma_index_info(?) ORDER BY seqno",
            (index[1],),
        ).fetchall()

        if [column[0] for column in columns] == expected_columns:
            found_unique_constraint = True
            break

    if not found_unique_constraint:
        raise ValueError("Missing observation duplicate-prevention constraint.")


def initialize_database(database_path: Path) -> None:
    # Create the parent folder if it does not exist.
    database_path.parent.mkdir(parents=True, exist_ok=True)

    # Open the SQLite file with the same settings used by other operations.
    connection = connect_database(database_path)

    try:
        # Keep table creation, validation, and version assignment atomic.
        connection.execute("BEGIN IMMEDIATE")
        # Check compatibility before making any database changes.
        version = connection.execute(
            "PRAGMA user_version"
        ).fetchone()[0]

        if version > DATABASE_VERSION:
            raise ValueError(
                f"Database version {version} is newer than "
                f"supported version {DATABASE_VERSION}."
            )
        if version < 0:
            raise ValueError('Unsupported negative database version')
        # Create a table for HuddleMinds own dynasty identities.
        # IF NOT EXISTS makes repeated initialization safe.
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS dynasties (
                dynasty_id TEXT PRIMARY KEY NOT NULL,
                name TEXT NOT NULL
                )"""
        )

        # Preserve complete snapshots under their HuddleMind dynasty identity.
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS observations (
            observation_id INTEGER PRIMARY KEY,
            dynasty_id TEXT NOT NULL,
            observed_at TEXT NOT NULL,
            save_sha256 TEXT NOT NULL,
            schema_sha256 TEXT NOT NULL,
            snapshot_json TEXT NOT NULL,
            FOREIGN KEY (dynasty_id) REFERENCES dynasties(dynasty_id),
            UNIQUE (dynasty_id, save_sha256, schema_sha256)
            )"""

        )


        # Validate before changing the version; all steps share one transaction.
        validate_database_columns(connection)
        validate_database_relationships(connection)
        if connection.execute('PRAGMA foreign_key_check(observations)').fetchall():
            raise ValueError('Database contains invalid dynasty references.')
        from bridge.recommendation_schema import create_schema, validate_schema
        from bridge.outbox_schema import (
            create_outbox_schema,
            validate_outbox_schema,
        )

        # Apply earlier migrations before adding the outbox.
        if version < 2:
            create_schema(connection)
        validate_schema(connection)

        # Existing version-2 databases receive the new outbox table.
        if version < 3:
            create_outbox_schema(connection)
        validate_outbox_schema(connection)

        from bridge.delivery_schema import create_schema as create_deliveries, validate_schema as validate_deliveries
        if version < 4:
            create_deliveries(connection)
        validate_deliveries(connection)

        # Commit the schema changes and version assignment together.
        connection.execute("PRAGMA user_version = 4")
        connection.commit()
    except Exception:
        # Undo initialization changes if any validation or database step fails.
        connection.rollback()
        raise
    finally:
        connection.close()

def connect_database(database_path: Path, *, read_only: bool = False) -> sqlite3.Connection:
    # Open the database and enforce relationships between its tables.
    if read_only:
        # URI read-only mode also prevents creating a missing database.
        connection = sqlite3.connect(database_path.resolve().as_uri() + '?mode=ro', uri=True)
    else:
        connection = sqlite3.connect(database_path)

    try:
        connection.execute("PRAGMA foreign_keys = On")
    except sqlite3.Error:
        # Release the connection if setup fails.
        connection.close()
        raise

    return connection


def create_dynasty(database_path: Path, name: str) -> str:
    # Remove surrounding whitespace and reject a blank display name.
    name = name.strip()
    if not name:
        raise ValueError("Dynasty name cannot be blank.")

    # Assign an identity owned by HuddleMind, independent of the save filename.
    dynasty_id = str(uuid4())

    connection = connect_database(database_path)

    try:
        connection.execute(
            "INSERT INTO dynasties (dynasty_id, name) VALUES (?, ?)",
            (dynasty_id, name),
        )
        connection.commit()
    finally:
        connection.close()

    return dynasty_id


def get_dynasty(
        database_path: Path,
        dynasty_id: str,
        *, read_only: bool = False,
) -> tuple[str, str] | None:
    connection = connect_database(database_path, read_only=read_only)

    try:
        cursor = connection.execute(
            "SELECT dynasty_id, name FROM dynasties WHERE dynasty_id = ?",
            (dynasty_id,),
        )

        return cursor.fetchone()
    finally:
        connection.close()

def save_observation(
    database_path: Path,
    dynasty_id: str,
    details: DynastyDetails,
) -> int:
    # Serialize the complete snapshot before opening a database connection.
    snapshot_json = json.dumps(
        asdict(details),
        ensure_ascii=False,
    )
    observed_at = datetime.now(timezone.utc).isoformat()

    connection = connect_database(database_path)

    try:
        # Store each save/schema pair once per dynasty.
        # A duplicate leaves the original observation and timestamp unchanged.
        connection.execute(
            """
            INSERT INTO observations (
                dynasty_id,
                observed_at,
                save_sha256,
                schema_sha256,
                snapshot_json
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (dynasty_id, save_sha256, schema_sha256)
            DO NOTHING
            """,
            (
                dynasty_id,
                observed_at,
                details.roster.save_sha256,
                details.roster.schema_sha256,
                snapshot_json,
            ),
        )

        # Retrieve the ID whether this call inserted a row or found a duplicate.
        row = connection.execute(
            """
            SELECT observation_id
            FROM observations
            WHERE dynasty_id = ?
              AND save_sha256 = ?
              AND schema_sha256 = ?
            """,
            (
                dynasty_id,
                details.roster.save_sha256,
                details.roster.schema_sha256,
            ),
        ).fetchone()

        if row is None:
            raise RuntimeError("Observation was not stored.")

        connection.commit()
        return row[0]
    except Exception:
        # Undo pending changes if any part of the operation fails.
        connection.rollback()
        raise
    finally:
        connection.close()

def get_observation(
    database_path: Path,
    dynasty_id: str,
    observation_id: int,
) -> dict | None:
    connection = connect_database(database_path)

    try:
        # Match both IDs so we only retrieve this dynasty's observation.
        row = connection.execute(
            """
            SELECT snapshot_json
            FROM observations
            WHERE dynasty_id = ? AND observation_id = ?
            """,
            (dynasty_id, observation_id),
        ).fetchone()

        if row is None:
            return None

        # Decode the stored JSON into Python dictionaries and lists.
        return json.loads(row[0])
    finally:
        connection.close()


def list_observations(
        database_path: Path,
        dynasty_id: str,
        *, read_only: bool = False,
) -> list[tuple[int, str]]:
    connection = connect_database(database_path, read_only=read_only)

    try:
        # Return observation IDs and capture times, newest insertion first.
        cursor = connection.execute(
            """
            SELECT observation_id, observed_at
            FROM observations
            WHERE dynasty_id = ?
            ORDER BY observation_id DESC
            """,
            (dynasty_id,),
        )

        return cursor.fetchall()
    finally:
        connection.close()
