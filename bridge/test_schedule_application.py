"""Schedule application checks with synthetic data, never a game save."""
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
import unittest
from unittest.mock import patch

from bridge.load_schedule import load_schedule
from bridge.models import RecordId, ScheduleGame
from bridge.schedule_adapter import schedule_from_report, schedule_game_from_report
from bridge.show_schedule import main


def fixture(status='Unplayed', home_score=14, away_score=7):
    return dict(table=10, row=2, SeasonYear=0, SeasonWeek=2,
                home={'table': 20, 'row': 1, 'name': 'Sample Home'},
                away={'table': 20, 'row': 2, 'name': 'Sample Away'},
                GameStatusLabel=status, HomeScore=home_score, AwayScore=away_score)


class ScheduleAdapterTests(unittest.TestCase):
    def test_identity_and_pending_scores(self):
        record = fixture()
        game = schedule_game_from_report(record, record['home'])
        self.assertEqual(game, ScheduleGame(RecordId(10, 2), 0, 2,
                         'Sample Home', 'Sample Away', 'Unplayed', None, None, True))
        self.assertEqual(record['HomeScore'], 14)

    def test_all_completed_statuses_preserve_zero_scores(self):
        for status, home, away in [('HomeWon', 7, 0), ('AwayWon', 0, 7), ('Tied', 0, 0)]:
            with self.subTest(status=status):
                game = schedule_game_from_report(fixture(status, home, away), fixture()['home'])
                self.assertEqual((game.home_score, game.away_score), (home, away))

    def test_unfinished_and_unknown_statuses_hide_scores(self):
        for status in ('Unscheduled', 'Unplayed', 'HomeScheduled', 'AwayScheduled',
                       'StatsReported', 'Unknown (15)'):
            with self.subTest(status=status):
                game = schedule_game_from_report(fixture(status), fixture()['home'])
                self.assertEqual(game.status, status)
                self.assertIsNone(game.home_score)
                self.assertIsNone(game.away_score)

    def test_fixture_order_preserved_and_other_records_ignored(self):
        first, second = fixture(), fixture('HomeWon', 7, 0)
        first.update(row=8, SeasonWeek=6)
        second.update(row=3, SeasonWeek=1)
        games = schedule_from_report({'selected_team': first['home'], 'fixtures': [first, second], 'games': [fixture()]})
        self.assertIsInstance(games, tuple)
        self.assertEqual([(g.record_id.row_id, g.week) for g in games], [(8, 6), (3, 1)])

    def test_empty_fixtures(self):
        self.assertEqual(schedule_from_report({'selected_team': fixture()['home'], 'fixtures': []}), ())

    def test_away_identity_ignores_matching_display_names(self):
        record = fixture()
        record['away']['name'] = record['home']['name']
        self.assertFalse(schedule_game_from_report(record, record['away']).controlled_team_is_home)

    def test_rejects_neither_side(self):
        for selected in ({'table': 20, 'row': 99}, {'table': 99, 'row': 1}):
            with self.subTest(selected=selected), self.assertRaisesRegex(ValueError, 'exactly one side'):
                schedule_game_from_report(fixture(), selected)

    def test_rejects_both_sides(self):
        record = fixture()
        record['away'].update(table=20, row=1)
        with self.assertRaisesRegex(ValueError, 'exactly one side'):
            schedule_game_from_report(record, record['home'])


class ScheduleLoaderTests(unittest.TestCase):
    def test_reader_report_reaches_real_adapter(self):
        save, schema = Path('sample save'), Path('sample schema')
        with patch('bridge.load_schedule.inspect_schedule', return_value={'selected_team': fixture()['home'], 'fixtures': [fixture()]}) as reader:
            games = load_schedule(save, schema)
        reader.assert_called_once_with(save, schema)
        self.assertEqual(len(games), 1)
        self.assertEqual(games[0].away_team, 'Sample Away')
        self.assertIsNone(games[0].home_score)

    def test_reader_errors_propagate_without_conversion(self):
        for error in (OSError('missing save'), ValueError('invalid schedule')):
            with self.subTest(error=type(error).__name__), \
                    patch('bridge.load_schedule.inspect_schedule', side_effect=error), \
                    patch('bridge.load_schedule.schedule_from_report') as adapter:
                with self.assertRaises(type(error)):
                    load_schedule(Path('save'), Path('schema'))
                adapter.assert_not_called()


class ScheduleCommandTests(unittest.TestCase):
    def invoke(self, arguments, games=(), error=None):
        out, err = StringIO(), StringIO()
        code = 0
        with patch('sys.argv', ['show_schedule', *arguments]), \
                patch('bridge.show_schedule.load_schedule', return_value=games, side_effect=error) as loader, \
                redirect_stdout(out), redirect_stderr(err):
            try:
                main()
            except SystemExit as failure:
                code = failure.code
        return code, out.getvalue(), err.getvalue(), loader

    def test_completed_zero_scores_and_pending_display(self):
        games = tuple(schedule_game_from_report(fixture(status, home, away), fixture()['home'])
                      for status, home, away in [('HomeWon', 7, 0), ('AwayWon', 0, 7),
                                                ('Tied', 0, 0), ('Unplayed', 14, 7)])
        code, out, err, loader = self.invoke(['sample save', 'sample schema'], games)
        self.assertEqual((code, err), (0, ''))
        loader.assert_called_once_with(Path('sample save'), Path('sample schema'))
        self.assertEqual(out.splitlines(), [
            'Scheduled games: 4',
            'Completed: 3', 'Record (W-L-T): 1-1-1',
            'Pending: 1', 'Unknown status: 0', '',
            'Week 2: Sample Away at Sample Home | 0 - 7 | HomeWon',
            'Week 2: Sample Away at Sample Home | 7 - 0 | AwayWon',
            'Week 2: Sample Away at Sample Home | 0 - 0 | Tied',
            'Week 2: Sample Away at Sample Home | Unplayed',
        ])

    def test_empty_schedule(self):
        code, out, err, _ = self.invoke(['save', 'schema'])
        self.assertEqual((code, err), (0, ''))
        self.assertEqual(out, 'Scheduled games: 0\nCompleted: 0\nRecord (W-L-T): 0-0-0\n'
                         'Pending: 0\nUnknown status: 0\n\nNo scheduled games found.\n')

    def test_away_win_and_unknown_summary(self):
        games = tuple(schedule_game_from_report(fixture(status, 0, 7), fixture()['away'])
                      for status in ('AwayWon', 'StatsReported'))
        code, out, err, _ = self.invoke(['save', 'schema'], games)
        self.assertEqual((code, err), (0, ''))
        self.assertIn('Completed: 1\nRecord (W-L-T): 1-0-0\nPending: 0\nUnknown status: 1', out)
        self.assertIn('Week 2: Sample Away at Sample Home | StatsReported', out)

    def test_expected_errors_exit_cleanly(self):
        for error in (FileNotFoundError('missing'), PermissionError('denied'), ValueError('invalid')):
            with self.subTest(error=type(error).__name__):
                code, out, err, _ = self.invoke(['save', 'schema'], error=error)
                self.assertEqual((code, out), (1, ''))
                self.assertEqual(err, f'Could not load schedule: {error}\n')

    def test_invalid_arguments_do_not_read_save(self):
        for args in ([], ['save'], ['save', 'schema', '--unknown']):
            with self.subTest(args=args):
                code, out, err, loader = self.invoke(args)
                self.assertEqual((code, out), (2, ''))
                self.assertIn('usage:', err)
                loader.assert_not_called()

    def test_help_does_not_read_save(self):
        code, out, err, loader = self.invoke(['--help'])
        self.assertEqual((code, err), (0, ''))
        self.assertIn('usage:', out)
        loader.assert_not_called()


if __name__ == '__main__':
    unittest.main()
