"""Queue a stored observation locally; no network request is made."""
import argparse
from pathlib import Path
import sqlite3

from bridge.outbox import queue_observation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dynasty_id')
    parser.add_argument('observation_id', type=int)
    parser.add_argument('--database', type=Path, default=Path('local_data/huddlemind.sqlite3'))
    args = parser.parse_args()
    try:
        event = queue_observation(args.database, args.dynasty_id, args.observation_id)
    except (OSError, ValueError, sqlite3.Error) as error:
        parser.exit(1, f'Could not queue observation: {error}\n')
    print('Event ID:', event.event_id)
    print('Observation ID:', event.observation_id)
    print('Queued:', event.queued_at)
    print('Status:', 'pending' if event.delivered_at is None else 'delivered')


if __name__ == '__main__':
    main()
