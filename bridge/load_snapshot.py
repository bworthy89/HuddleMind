from pathlib import Path

from bridge.discover_fields import inspect_fields
from bridge.models import DynastySnapshot
from bridge.snapshot_adapter import snapshot_from_report

def load_snapshot(save_path: Path, schema_path: Path) -> DynastySnapshot:
    # Read and inspect the save using the existing read-only discovery reader.
    report = inspect_fields(save_path, schema_path)

    # Validate the report and convert it into the application's data models.
    return snapshot_from_report(report)
