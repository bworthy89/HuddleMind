"""List captured observations without opening the game save."""
import argparse
from pathlib import Path
import sqlite3

from bridge.local_store import get_dynasty, list_observations


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dynasty_id', help='Existing HuddleMind dynasty ID.')
    parser.add_argument('--database', type=Path,
                        default=Path('local_data/huddlemind.sqlite3'),
                        help="Path to HuddleMind's SQLite database.")
    args = parser.parse_args()

    try:
        if not args.database.is_file():
            raise ValueError(f'Database not found: {args.database}')
        # Read-only connections cannot create or change the history database.
        dynasty = get_dynasty(args.database, args.dynasty_id, read_only=True)
        if dynasty is None:
            raise ValueError(f'Dynasty not found: {args.dynasty_id}')
        observations = list_observations(args.database, args.dynasty_id, read_only=True)
    except (OSError, ValueError, sqlite3.Error) as error:
        parser.exit(1, f'Could not load history: {error}\n')

    print('Dynasty:', dynasty[1])
    print('Observations:', len(observations))
    if not observations:
        print('No observations found. Capture this dynasty to begin its history.')
        return

    # IDs reflect insertion order, not the in-game week or save modification time.
    print('\nNewest captures first:')
    for observation_id, observed_at in observations:
        print(f'Observation: {observation_id} | Captured: {observed_at}')


if __name__ == '__main__':
    main()
