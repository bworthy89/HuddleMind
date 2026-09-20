"""Exercise the command with synthetic snapshots, without game files."""
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import replace
from io import StringIO
from pathlib import Path
import unittest
from unittest.mock import patch

from bridge.models import Coach, DynastySnapshot, Player, RecordId, Team
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
        self.assertNotIn('OVR', out)

    def test_empty_roster_without_filter(self):
        self.snapshot = replace(self.snapshot, team=replace(self.snapshot.team, players=()))
        code, out, err, _ = self.invoke(['save', 'schema'])
        self.assertEqual((code, err), (0, ''))
        self.assertIn('The team roster is empty.', out)
        self.assertNotIn('None', out)
        self.assertNotIn('OVR', out)

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
                          ['save', 'schema', '--position']):
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


if __name__ == '__main__':
    unittest.main()
