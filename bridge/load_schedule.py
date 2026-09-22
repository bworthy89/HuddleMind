from pathlib import Path

from bridge.discover_schedule import inspect_schedule
from bridge.models import ScheduleGame
from bridge.schedule_adapter import schedule_from_report


def load_schedule(
    save_path: Path,
    schema_path: Path,
) -> tuple[ScheduleGame, ...]:
    # Read the save and trace the controlled team's schedule references.
    report = inspect_schedule(save_path, schema_path)

    # Convert the checked fixture records into application models.
    return schedule_from_report(report)
