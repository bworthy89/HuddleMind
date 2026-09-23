import sqlite3
import json

from pathlib import Path
from uuid import uuid4
from dataclasses import asdict
from bridge.dynasty_details import DynastyDetails
from datetime import datetime, timezone


def initialize_database(database_path: Path) -> None:
    # Create the parent folder if it does not exist.
    database_path.parent.mkdir(parents=True, exist_ok=True)

    # Open the SQLite file with the same settings used by other operations.
    connection = connect_database(database_path)

    try:
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


        # Commit any pending database changes.
        connection.commit()
    finally:
        connection.close()


def connect_database(database_path: Path) -> sqlite3.Connection:
    # Open the database and enforce relationships between its tables.
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
) -> tuple[str, str] | None:
    connection = connect_database(database_path)

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
) -> list[tuple[int, str]]:
    connection = connect_database(database_path)

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
