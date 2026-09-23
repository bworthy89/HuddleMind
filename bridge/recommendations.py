"""Record and review recommendation history; this command does not generate advice."""
import argparse
import json
from pathlib import Path
import sqlite3

from bridge.local_store import initialize_database, DATABASE_VERSION
from bridge.recommendation_store import (record_recommendation, record_event,
                                         list_recommendations, get_recommendation)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('init', 'add', 'choice', 'outcome', 'list', 'show'):
        command = commands.add_parser(name)
        command.add_argument('--database', type=Path, default=Path('local_data/huddlemind.sqlite3'))
        if name != 'init':
            command.add_argument('dynasty_id')
        if name == 'add':
            command.add_argument('observation_id', type=int)
            command.add_argument('--advice', required=True)
            command.add_argument('--rationale', required=True)
        if name in ('choice', 'outcome', 'show'):
            command.add_argument('recommendation_id')
        if name in ('choice', 'outcome'):
            command.add_argument('--detail', required=True)
        if name in ('add', 'choice', 'outcome'):
            command.add_argument('--source', default='manual', help='Provenance, such as manual or a versioned engine name.')
    args = parser.parse_args()
    try:
        if args.command == 'init':
            initialize_database(args.database)
            print('Database ready. Version:', DATABASE_VERSION)
        elif args.command == 'add':
            identity = record_recommendation(args.database, args.dynasty_id, args.observation_id,
                                             args.advice, args.rationale, args.source)
            print('Recommendation ID:', identity)
        elif args.command in ('choice', 'outcome'):
            identity = record_event(args.database, args.dynasty_id, args.recommendation_id,
                                    args.command, args.detail, args.source)
            print('Event ID:', identity)
        elif args.command == 'list':
            rows = list_recommendations(args.database, args.dynasty_id)
            if not rows:
                print('No recommendations recorded.')
            for identity, observation, created, advice in rows:
                print(f'{identity} | Observation: {observation} | {created} | {advice}')
        else:
            result = get_recommendation(args.database, args.dynasty_id, args.recommendation_id)
            if result is None:
                raise ValueError('Recommendation not found for this dynasty')
            print(json.dumps(result, ensure_ascii=False, indent=2))
    except (OSError, ValueError, sqlite3.Error) as error:
        parser.exit(1, f'Could not process recommendation history: {error}\n')


if __name__ == '__main__':
    main()
