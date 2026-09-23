"""History command checks against disposable databases."""
from contextlib import redirect_stdout, redirect_stderr
from dataclasses import replace
from io import StringIO
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from bridge.local_store import (initialize_database, create_dynasty, save_observation,
                                list_observations, connect_database)
from bridge.show_history import main
from bridge.test_dynasty_details import sample


class HistoryCommandTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / 'history #1.sqlite3'
        initialize_database(self.path)
        self.dynasty = create_dynasty(self.path, 'Sample Dynasty')

    def invoke(self, args=None):
        args = args if args is not None else [self.dynasty, '--database', str(self.path)]
        out, err = StringIO(), StringIO()
        code = 0
        with patch('sys.argv', ['show_history', *args]), redirect_stdout(out), redirect_stderr(err):
            try:
                main()
            except SystemExit as error:
                code = error.code
        return code, out.getvalue(), err.getvalue()

    def test_lists_only_selected_dynasty_newest_first_without_changes(self):
        details = sample()
        first = save_observation(self.path, self.dynasty, details)
        second = save_observation(self.path, self.dynasty,
                                 replace(details, roster=replace(details.roster, save_sha256='new')))
        other = create_dynasty(self.path, 'Other')
        save_observation(self.path, other, details)
        history = list_observations(self.path, self.dynasty)
        before = self.path.read_bytes()
        code, out, err = self.invoke()
        self.assertEqual((code, err), (0, ''))
        expected = ['Dynasty: Sample Dynasty', 'Observations: 2', '', 'Newest captures first:']
        expected += [f'Observation: {identity} | Captured: {timestamp}' for identity, timestamp in history]
        self.assertEqual(out.splitlines(), expected)
        self.assertEqual([row[0] for row in history], [second, first])
        self.assertEqual(self.path.read_bytes(), before)

    def test_empty_history(self):
        code, out, err = self.invoke()
        self.assertEqual((code, err), (0, ''))
        self.assertIn('Observations: 0\nNo observations found.', out)
        self.assertNotIn('Newest captures first', out)

    def test_unknown_dynasty_does_not_list(self):
        with patch('bridge.show_history.list_observations') as listing:
            code, out, err = self.invoke(['missing', '--database', str(self.path)])
        self.assertEqual((code, out), (1, ''))
        self.assertEqual(err, 'Could not load history: Dynasty not found: missing\n')
        listing.assert_not_called()

    def test_missing_database_not_created_and_directory_rejected(self):
        missing = self.path.parent / 'missing.sqlite3'
        for path in (missing, self.path.parent):
            with self.subTest(path=path), patch('bridge.show_history.get_dynasty') as lookup:
                code, out, err = self.invoke(['id', '--database', str(path)])
                self.assertEqual((code, out), (1, ''))
                self.assertIn('Database not found:', err)
                lookup.assert_not_called()
        self.assertFalse(missing.exists())

    def test_corrupt_database_reports_clean_error(self):
        broken = self.path.parent / 'broken.sqlite3'
        broken.write_bytes(b'not sqlite')
        code, out, err = self.invoke(['id', '--database', str(broken)])
        self.assertEqual((code, out), (1, ''))
        self.assertIn('Could not load history:', err)
        self.assertNotIn('Traceback', err)

    def test_listing_error_produces_no_partial_success(self):
        with patch('bridge.show_history.list_observations', side_effect=sqlite3.OperationalError('locked')):
            code, out, err = self.invoke()
        self.assertEqual((code, out), (1, ''))
        self.assertEqual(err, 'Could not load history: locked\n')

    def test_help_and_invalid_arguments_do_not_access_database(self):
        for args, expected in ((['--help'], 0), ([], 2), (['id', '--unknown'], 2)):
            with self.subTest(args=args), patch('bridge.show_history.get_dynasty') as lookup:
                self.assertEqual(self.invoke(args)[0], expected)
                lookup.assert_not_called()

    def test_default_path_and_read_only_flags(self):
        with patch('bridge.show_history.Path.is_file', return_value=True), \
             patch('bridge.show_history.get_dynasty', return_value=('id', 'Sample')) as lookup, \
             patch('bridge.show_history.list_observations', return_value=[]) as listing:
            self.assertEqual(self.invoke(['id'])[0], 0)
        for operation in (lookup, listing):
            operation.assert_called_once_with(Path('local_data/huddlemind.sqlite3'), 'id', read_only=True)

    def test_read_only_connection_refuses_writes_and_creation(self):
        connection = connect_database(self.path, read_only=True)
        try:
            with self.assertRaises(sqlite3.OperationalError):
                connection.execute('DELETE FROM dynasties')
        finally:
            connection.close()
        missing = self.path.parent / 'missing.sqlite3'
        with self.assertRaises(sqlite3.OperationalError):
            connect_database(missing, read_only=True)
        self.assertFalse(missing.exists())


if __name__ == '__main__':
    unittest.main()
