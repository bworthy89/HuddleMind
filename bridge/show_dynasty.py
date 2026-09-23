"""Display or export the controlled team's normalized dynasty context."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path

from bridge.dynasty_details import next_games
from bridge.load_dynasty import load_dynasty
from bridge.schedule_summary import summarize_results


def display(details, section='overview'):
    print('Coach:', details.roster.coach.full_name)
    print('Team:', details.roster.team.name)
    print('Roster size:', len(details.roster.team.players))
    print(f'Season: {details.season.calendar_year} | Week: {details.season.week}'
          f' | {details.season.week_type.label}')
    results = summarize_results(details.schedule)
    print(f"Record (W-L-T): {results['wins']}-{results['losses']}-{results['ties']}")
    upcoming = next_games(details)
    if upcoming:
        for game in upcoming:
            print(f'Next scheduled: Week {game.week}: {game.away_team} at {game.home_team}')
    else:
        print('No upcoming scheduled fixture found in the current season.')
    print('Depth chart:', 'unavailable' if details.depth_chart is None else
          f'{len({d.position for d in details.depth_chart})} position groups')
    statuses = {}
    for health in details.health:
        statuses[health.status.label] = statuses.get(health.status.label, 0) + 1
    print('Roster health:', ', '.join(f'{label}: {count}' for label, count in sorted(statuses.items())))
    board = details.recruiting
    if board is None:
        print('Recruiting board: unavailable')
    else:
        print(f'Recruiting targets: {len(board.targets)} | Hours assigned: {board.hours_assigned}'
              f' | Total hours: {board.hours_total}')
    players = {p.record_id: p for p in details.roster.team.players}
    if section in ('depth', 'all') and details.depth_chart is not None:
        print('\nDepth chart (source order):')
        for slot in details.depth_chart:
            name = players[slot.player_id].full_name if slot.player_id else '(empty)'
            print(f'{slot.position:6} {slot.depth:2}  {name}')
    if section in ('health', 'all'):
        print('\nHealth (all roster players; duration units unverified):')
        for health in details.health:
            print(f'{players[health.player_id].full_name} | {health.status.label}'
                  f' [{health.status.value}] | Type: {health.injury_type.label}'
                  f' [{health.injury_type.value}] | Severity: {health.severity.label}'
                  f' [{health.severity.value}] | Duration min/max/total: '
                  f'{health.min_duration}/{health.max_duration}/{health.total_duration}'
                  f' | Reserve: {health.injured_reserve}')
    if section in ('recruiting', 'all') and board is not None:
        print('\nRecruiting board (source order):')
        for target in board.targets:
            print(f'{target.name} | {target.position.label} | National rank: {target.national_rank}'
                  f' | Position rank: {target.position_rank} | {target.stage.label}'
                  f' | Scholarship: {target.scholarship.label}'
                  f' | Current hours: {target.hours_spent_current}')


def export_dynasty(details, path):
    # Exclusive creation protects previous exports; game saves are never opened here.
    payload = {'format_version': 1, 'dynasty': asdict(details)}
    with path.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(payload, ensure_ascii=False, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('save', type=Path)
    parser.add_argument('schema', type=Path)
    parser.add_argument('--section', choices=('overview', 'depth', 'health', 'recruiting', 'all'), default='overview')
    parser.add_argument('--export', type=Path, help='Create a new JSON file with every section.')
    args = parser.parse_args()
    try:
        details = load_dynasty(args.save, args.schema)
    except (OSError, ValueError) as error:
        parser.exit(1, f'Could not load dynasty: {error}\n')
    if args.export:
        try:
            export_dynasty(details, args.export)
        except (OSError, ValueError) as error:
            parser.exit(1, f'Could not export dynasty: {error}\n')
        print('Exported:', args.export)
    display(details, args.section)


if __name__ == '__main__':
    main()
