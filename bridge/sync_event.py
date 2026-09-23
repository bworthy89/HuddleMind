import json

from dataclasses import asdict, dataclass
from pathlib import Path
from uuid import uuid4

from bridge.local_store import connect_database




@dataclass(frozen=True)
class ObservationEvent:
    # Identify this queued event independently of local database row numbers.
    event_id: str
    dynasty_id: str

    # Preserve the original observation capture time, not the upload time.
    observed_at: str

    # Carry the normalized snapshot already stored in SQLite.
    payload: dict

    # Version the network format separately from the database structure.
    schema_version: int =1
    event_type: str = "dynasty.observation.captured"

def build_observation_event(
    database_path: Path,
    dynasty_id: str,
    observation_id: int,
) -> ObservationEvent:
    # Read the stored timestamp and snapshot together without changing history.
    connection = connect_database(database_path, read_only=True)

    try:
        row = connection.execute(
            """
            SELECT observed_at, snapshot_json
            FROM observations
            WHERE dynasty_id = ? AND observation_id = ?
            """,
            (dynasty_id, observation_id),
        ).fetchone()

        if row is None:
            raise ValueError("Observation not found for this dynasty.")

        # Assign an ID to this new event and retain the original capture time.
        return ObservationEvent(
            event_id=str(uuid4()),
            dynasty_id=dynasty_id,
            observed_at=row[0],
            payload=json.loads(row[1]),
        )
    finally:
        connection.close()

def serialize_observation_event(event: ObservationEvent) -> str:
    # Convert the event and its snapshot into JSON suitable for transmission.
    # Reject NaN and infinity because they are not valid JSON numbers.
    return json.dumps(
        asdict(event),
        ensure_ascii=False,
        allow_nan=False,
    )