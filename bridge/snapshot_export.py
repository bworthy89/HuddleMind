from dataclasses import asdict
from bridge.models import DynastySnapshot
import json
from pathlib import Path


def snapshot_to_dict(snapshot: DynastySnapshot) -> dict:
    # Convert the snapshot and its nested dataclasses into dictionaries.
    return asdict(snapshot)

def write_snapshot_json(
        snapshot: DynastySnapshot,
        output_path:Path,
) -> None:
    # Format the snapshot as readable JSON, preserving Unicode names.
    json_text = json.dumps(
        snapshot_to_dict(snapshot),
        indent=2,
        ensure_ascii=False,
    )

    # Create a new export file; "x" prevents overwriting an existing file.
    with output_path.open("x", encoding="utf-8") as output_file:
        output_file.write(json_text + "\n")