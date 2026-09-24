"""Exercise the command with synthetic snapshots, without game files."""
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import replace
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest
from unittest.mock import patch

from bridge.models import Coach, DynastySnapshot, Player, PlayerRating, RecordId, Team
from bridge.show_roster import main


class RosterCommandTests(unittest.TestCase):
    def setUp(self):
        # Deliberately unsorted, including a rating tie and another position.
        players = tuple(
            Player(RecordId(1, row), first, 'Sample', position, overall)
            for row, (first, position, overall) in enumerate([
                ('Zoe', 'QB', 90), ('Will', 'WR', 99),
                ('Ben', 'QB', 70), ('Amy', 'QB', 90),
            ])
        )
        self.snapshot = DynastySnapshot(
            'sample-save', 'sample-schema',
            Coach(RecordId(2, 0), 'Sample', 'Coach', 5, True),
            Team(RecordId(3, 0), 5, 'Sample Team', players),
        )

    def invoke(self, arguments, error=None):
        # Patch where the command looks up the loader, not its original module.
        stdout, stderr = StringIO(), StringIO()
        code = 0
        with patch('sys.argv', ['show_roster', *arguments]), \
                patch('bridge.show_roster.load_snapshot', return_value=self.snapshot,
                      side_effect=error) as loader, \
                redirect_stdout(stdout), redirect_stderr(stderr):
            try:
                main()
            except SystemExit as exit_error:
                code = exit_error.code
        return code, stdout.getvalue(), stderr.getvalue(), loader

    def test_full_roster_sorted_without_mutating_snapshot(self):
        original = self.snapshot.team.players
        code, out, err, loader = self.invoke(['sample save', 'sample schema'])
        self.assertEqual((code, err), (0, ''))
        loader.assert_called_once_with(Path('sample save'), Path('sample schema'))
        self.assertIn('Coach: Sample Coach', out)
        self.assertIn('Team: Sample Team', out)
        self.assertIn('Roster size: 4', out)
        rows = [line.split() for line in out.splitlines() if line.startswith(('Amy ', 'Zoe ', 'Ben ', 'Will '))]
        self.assertEqual(rows, [
            ['Amy', 'Sample', 'QB', '90'], ['Zoe', 'Sample', 'QB', '90'],
            ['Ben', 'Sample', 'QB', '70'], ['Will', 'Sample', 'WR', '99'],
        ])
        self.assertIs(self.snapshot.team.players, original)
        self.assertEqual(original[0].first_name, 'Zoe')

    def test_position_filter_accepts_lowercase(self):
        code, out, err, _ = self.invoke(['save', 'schema', '--position', 'qb'])
        self.assertEqual((code, err), (0, ''))
        self.assertIn('Roster size: 4', out)
        self.assertNotIn('Will Sample', out)
        self.assertLess(out.index('Amy Sample'), out.index('Zoe Sample'))
        self.assertLess(out.index('Zoe Sample'), out.index('Ben Sample'))

    def test_unmatched_filter_has_no_table(self):
        code, out, err, _ = self.invoke(['save', 'schema', '--position', 'xyz'])
        self.assertEqual((code, err), (0, ''))
        self.assertIn('No players found for position XYZ.', out)
        self.assertNotIn('Player                       Pos', out)

    def test_empty_roster_without_filter(self):
        self.snapshot = replace(self.snapshot, team=replace(self.snapshot.team, players=()))
        code, out, err, _ = self.invoke(['save', 'schema'])
        self.assertEqual((code, err), (0, ''))
        self.assertIn('The team roster is empty.', out)
        self.assertNotIn('None', out)
        self.assertNotIn('Player                       Pos', out)

    def test_summary_uses_full_roster_and_formats_average(self):
        # Summary totals stay unchanged even with an unmatched player filter.
        for position in (None, 'qb', 'xyz'):
            with self.subTest(position=position):
                args = ['save', 'schema']
                if position is not None:
                    args.extend(['--position', position])
                code, out, err, _ = self.invoke(args)
                self.assertEqual((code, err), (0, ''))
                rows = [line.split() for line in out.splitlines()
                        if line.split() and line.split()[0] in ('QB', 'WR')]
                self.assertEqual(rows, [['QB', '3', '90', '83.3'], ['WR', '1', '99', '99.0']])

    def test_expected_loader_errors_exit_cleanly(self):
        for error in (FileNotFoundError('missing sample save'),
                      PermissionError('sample access denied'),
                      ValueError('sample validation failed')):
            with self.subTest(error=type(error).__name__):
                code, out, err, _ = self.invoke(['save', 'schema'], error)
                self.assertEqual(code, 1)
                self.assertEqual(out, '')
                self.assertEqual(err, f'Could not load dynasty: {error}\n')
                self.assertNotIn('Traceback', err)

    def test_bad_arguments_do_not_load_save(self):
        for arguments in ([], ['save'], ['save', 'schema', '--unknown'],
                          ['save', 'schema', '--position'], ['save', 'schema', '--export']):
            with self.subTest(arguments=arguments):
                code, out, err, loader = self.invoke(arguments)
                self.assertEqual(code, 2)
                self.assertEqual(out, '')
                self.assertIn('usage:', err)
                loader.assert_not_called()

    def test_help_does_not_load_save(self):
        code, out, err, loader = self.invoke(['--help'])
        self.assertEqual((code, err), (0, ''))
        self.assertIn('--position', out)
        loader.assert_not_called()

    def test_export_keeps_full_roster_despite_display_filter(self):
        # Exercise the actual writer, substituting only the save loader.
        for position in ('qb', 'xyz'):
            with self.subTest(position=position), TemporaryDirectory() as folder:
                path = Path(folder) / 'snapshot.json'
                code, out, err, _ = self.invoke([
                    'save', 'schema', '--position', position, '--export', str(path),
                ])
                self.assertEqual((code, err), (0, ''))
                self.assertIn(f'Exported: {path}', out)
                self.assertNotIn('Will Sample', out)
                players = json.loads(path.read_text(encoding='utf-8'))['team']['players']
                self.assertEqual(len(players), 4)
                self.assertEqual({p['position'] for p in players}, {'QB', 'WR'})

    def test_existing_export_is_preserved_by_command(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'snapshot.json'
            path.write_bytes(b'preserve this file')
            code, out, err, _ = self.invoke(['save', 'schema', '--export', str(path)])
            self.assertEqual(code, 1)
            self.assertEqual(out, '')
            self.assertIn('Could not export snapshot:', err)
            self.assertNotIn('Traceback', err)
            self.assertEqual(path.read_bytes(), b'preserve this file')

    def test_export_permission_error_is_reported(self):
        # Simulate permissions for a deterministic test on Windows and Unix.
        with patch('bridge.show_roster.write_snapshot_json', side_effect=PermissionError('denied')):
            code, out, err, _ = self.invoke(['save', 'schema', '--export', 'sample.json'])
        self.assertEqual((code, out), (1, ''))
        self.assertEqual(err, 'Could not export snapshot: denied\n')

    def test_load_failure_does_not_create_export(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'snapshot.json'
            code, out, err, _ = self.invoke(
                ['save', 'schema', '--export', str(path)], ValueError('invalid save'))
            self.assertEqual(code, 1)
            self.assertIn('Could not load dynasty:', err)
            self.assertFalse(path.exists())

    def test_no_export_option_does_not_call_writer(self):
        with patch('bridge.show_roster.write_snapshot_json') as writer:
            code, _, _, _ = self.invoke(['save', 'schema'])
        self.assertEqual(code, 0)
        writer.assert_not_called()

    def test_rating_summary_formats_coverage_zero_missing_and_rounding(self):
        # The normal roster has three QBs and one WR; only two QBs have speed.
        players = list(self.snapshot.team.players)
        players[0] = replace(players[0], ratings=(PlayerRating('SpeedRating', 81),))
        players[2] = replace(players[2], ratings=(PlayerRating('SpeedRating', 0),))
        self.snapshot = replace(self.snapshot, team=replace(self.snapshot.team, players=tuple(players)))
        for position in (None, 'qb', 'xyz'):
            with self.subTest(position=position):
                args = ['save', 'schema', '--rating', 'SpeedRating']
                if position:
                    args += ['--position', position]
                code, out, err, _ = self.invoke(args)
                self.assertEqual((code, err), (0, ''))
                rows = [line.split() for line in out.splitlines()
                        if line.split() and line.split()[0] in ('QB', 'WR')]
                self.assertEqual(rows, [['QB', '2/3', '40.5'], ['WR', '0/1', 'Unavailable']])
                self.assertIn('Rating: SpeedRating', out)
                self.assertNotIn('Best OVR', out)
                self.assertNotIn('Zoe Sample', out)

    def test_rating_summary_handles_legacy_and_empty_rosters(self):
        code, out, err, _ = self.invoke(['save', 'schema', '--rating', 'StrengthRating'])
        self.assertEqual((code, err), (0, ''))
        self.assertIn('0/3', out)
        self.assertEqual(out.count('Unavailable'), 2)
        self.snapshot = replace(self.snapshot, team=replace(self.snapshot.team, players=()))
        code, out, err, _ = self.invoke(['save', 'schema', '--rating', 'StrengthRating'])
        self.assertEqual((code, err), (0, ''))
        self.assertIn('Roster size: 0', out)
        self.assertNotIn('Unavailable', out)

    def test_invalid_or_missing_rating_does_not_load_or_export(self):
        for suffix in (['--rating', 'SpeedRatting'], ['--rating']):
            with self.subTest(suffix=suffix), patch('bridge.show_roster.write_snapshot_json') as writer:
                code, out, err, loader = self.invoke(['save', 'schema', '--export', 'sample.json', *suffix])
                self.assertEqual((code, out), (2, ''))
                self.assertIn('--rating', err)
                loader.assert_not_called()
                writer.assert_not_called()

    def test_rating_summary_still_exports_complete_snapshot(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'snapshot.json'
            code, out, err, _ = self.invoke([
                'save', 'schema', '--rating', 'SpeedRating', '--export', str(path),
            ])
            self.assertEqual((code, err), (0, ''))
            self.assertIn('Rating: SpeedRating', out)
            players = json.loads(path.read_text(encoding='utf-8'))['team']['players']
            self.assertEqual(len(players), 4)

    def test_depth_output_uses_full_roster_and_distinguishes_ties_from_missing(self):
        for position in (None, 'qb', 'xyz'):
            with self.subTest(position=position):
                args = ['save', 'schema', '--depth']
                if position:
                    args += ['--position', position]
                code, out, err, _ = self.invoke(args)
                self.assertEqual((code, err), (0, ''))
                rows = [line.split() for line in out.splitlines()
                        if line.split() and line.split()[0] in ('QB', 'WR')]
                self.assertEqual(rows, [['QB', '3', '90', '90', '0'],
                                        ['WR', '1', '99', 'N/A', 'N/A']])
                self.assertIn("not the game's depth chart", out)
                self.assertNotIn('Zoe Sample', out)
                self.assertNotIn('Best OVR', out)

    def test_depth_empty_roster(self):
        self.snapshot = replace(self.snapshot, team=replace(self.snapshot.team, players=()))
        code, out, err, _ = self.invoke(['save', 'schema', '--depth'])
        self.assertEqual((code, err), (0, ''))
        self.assertIn('Roster size: 0', out)
        self.assertIn('Top OVR', out)

    def test_conflicting_summary_modes_rejected_before_io_in_both_orders(self):
        for options in (['--depth', '--rating', 'SpeedRating'],
                        ['--rating', 'SpeedRating', '--depth']):
            with self.subTest(options=options), patch('bridge.show_roster.write_snapshot_json') as writer:
                code, out, err, loader = self.invoke(
                    ['save', 'schema', '--export', 'sample.json', *options])
                self.assertEqual((code, out), (2, ''))
                self.assertIn('not allowed with argument', err)
                loader.assert_not_called()
                writer.assert_not_called()

    def test_depth_export_preserves_all_players_and_refuses_overwrite(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'snapshot.json'
            args = ['save', 'schema', '--depth', '--export', str(path)]
            code, out, err, _ = self.invoke(args)
            self.assertEqual((code, err), (0, ''))
            self.assertIn('Top OVR', out)
            saved = path.read_bytes()
            self.assertEqual(len(json.loads(saved)['team']['players']), 4)
            code, out, err, _ = self.invoke(args)
            self.assertEqual((code, out), (1, ''))
            self.assertIn('Could not export snapshot:', err)
            self.assertEqual(path.read_bytes(), saved)

    def test_depth_loader_error(self):
        code, out, err, _ = self.invoke(['save', 'schema', '--depth'],
                                       FileNotFoundError('missing save'))
        self.assertEqual((code, out), (1, ''))
        self.assertEqual(err, 'Could not load dynasty: missing save\n')

    def test_rating_load_failure_is_reported_cleanly(self):
        code, out, err, _ = self.invoke(['save', 'schema', '--rating', 'SpeedRating'],
                                       ValueError('invalid save'))
        self.assertEqual((code, out), (1, ''))
        self.assertEqual(err, 'Could not load dynasty: invalid save\n')


if __name__ == '__main__':
    unittest.main()
