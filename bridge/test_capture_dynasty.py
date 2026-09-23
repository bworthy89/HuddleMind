"""Capture command checks using temporary databases and synthetic save models."""
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import replace
from io import StringIO
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from bridge.capture_dynasty import main
from bridge.local_store import initialize_database, create_dynasty, list_observations, get_observation
from bridge.test_dynasty_details import sample


class CaptureCommandTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / 'history.sqlite3'
        initialize_database(self.path)
        self.dynasty = create_dynasty(self.path, 'Sample Dynasty')

    def invoke(self, args=None, details=None, error=None):
        if args is None:
            args = ['sample save', 'sample schema', self.dynasty, '--database', str(self.path)]
        out, err = StringIO(), StringIO()
        code = 0
        with patch('sys.argv', ['capture_dynasty', *args]), \
             patch('bridge.capture_dynasty.load_dynasty', return_value=details or sample(), side_effect=error) as loader, \
             redirect_stdout(out), redirect_stderr(err):
            try:
                main()
            except SystemExit as failure:
                code = failure.code
        return code, out.getvalue(), err.getvalue(), loader

    def test_success_writes_complete_snapshot(self):
        code, out, err, loader = self.invoke()
        self.assertEqual((code, err), (0, ''))
        loader.assert_called_once_with(Path('sample save'), Path('sample schema'))
        identity = list_observations(self.path, self.dynasty)[0][0]
        self.assertEqual(out, f'Dynasty: Sample Dynasty\nObservation ID: {identity}\nTeam: Sample Team\n')
        snapshot = get_observation(self.path, self.dynasty, identity)
        self.assertEqual(snapshot['roster']['save_sha256'], sample().roster.save_sha256)
        self.assertEqual(len(snapshot['recruiting']['targets']), 1)

    def test_duplicate_keeps_id_and_timestamp(self):
        first = self.invoke()
        history = list_observations(self.path, self.dynasty)
        second = self.invoke()
        self.assertEqual(first[:3], second[:3])
        self.assertEqual(list_observations(self.path, self.dynasty), history)
        self.assertEqual(len(history), 1)

    def test_changed_save_creates_new_observation(self):
        self.invoke()
        details = sample()
        changed = replace(details, roster=replace(details.roster, save_sha256='changed'))
        code, _, err, _ = self.invoke(details=changed)
        self.assertEqual((code, err), (0, ''))
        self.assertEqual(len(list_observations(self.path, self.dynasty)), 2)

    def test_unknown_dynasty_rejected_before_loading(self):
        code, out, err, loader = self.invoke(['s', 't', 'missing', '--database', str(self.path)])
        self.assertEqual((code, out), (1, ''))
        self.assertEqual(err, 'Could not capture dynasty: Dynasty not found: missing\n')
        loader.assert_not_called()
        self.assertEqual(list_observations(self.path, self.dynasty), [])

    def test_missing_database_is_not_created(self):
        missing = self.path.parent / 'missing.sqlite3'
        with patch('bridge.capture_dynasty.get_dynasty') as lookup:
            code, out, err, loader = self.invoke(['s', 't', 'id', '--database', str(missing)])
        self.assertEqual((code, out), (1, ''))
        self.assertIn('Database not found:', err)
        self.assertFalse(missing.exists())
        lookup.assert_not_called()
        loader.assert_not_called()

    def test_directory_is_not_a_database(self):
        code, out, err, loader = self.invoke(['s', 't', 'id', '--database', str(self.path.parent)])
        self.assertEqual((code, out), (1, ''))
        self.assertIn('Database not found:', err)
        loader.assert_not_called()

    def test_invalid_database_reports_error_before_loading(self):
        broken = self.path.parent / 'broken.sqlite3'
        broken.write_bytes(b'not a database')
        code, out, err, loader = self.invoke(['s', 't', 'id', '--database', str(broken)])
        self.assertEqual((code, out), (1, ''))
        self.assertIn('Could not capture dynasty:', err)
        self.assertNotIn('Traceback', err)
        loader.assert_not_called()
        self.assertEqual(broken.read_bytes(), b'not a database')

    def test_loader_errors_do_not_store(self):
        for error in (FileNotFoundError('missing save'), PermissionError('denied'), ValueError('bad schema')):
            with self.subTest(error=error), patch('bridge.capture_dynasty.save_observation') as writer:
                code, out, err, _ = self.invoke(error=error)
                self.assertEqual((code, out), (1, ''))
                self.assertEqual(err, f'Could not capture dynasty: {error}\n')
                writer.assert_not_called()
        self.assertEqual(list_observations(self.path, self.dynasty), [])

    def test_storage_error_reports_failure_without_success_output(self):
        with patch('bridge.capture_dynasty.save_observation', side_effect=sqlite3.OperationalError('database is locked')):
            code, out, err, _ = self.invoke()
        self.assertEqual((code, out), (1, ''))
        self.assertEqual(err, 'Could not capture dynasty: database is locked\n')
        self.assertEqual(list_observations(self.path, self.dynasty), [])

    def test_help_and_invalid_arguments_do_not_access_database(self):
        for args, expected in ((['--help'], 0), ([], 2), (['s', 't'], 2),
                               (['s', 't', 'id', '--unknown'], 2)):
            with self.subTest(args=args), patch('bridge.capture_dynasty.get_dynasty') as lookup:
                code, _, _, loader = self.invoke(args)
                self.assertEqual(code, expected)
                lookup.assert_not_called()
                loader.assert_not_called()

    def test_default_database_path(self):
        # Mock all database access here so the user's default database is never opened.
        with patch('bridge.capture_dynasty.Path.is_file', return_value=True), \
             patch('bridge.capture_dynasty.get_dynasty', return_value=('id', 'Sample')) as lookup, \
             patch('bridge.capture_dynasty.save_observation', return_value=7) as writer:
            code, out, err, _ = self.invoke(['s', 't', 'id'])
        self.assertEqual((code, err), (0, ''))
        lookup.assert_called_once_with(Path('local_data/huddlemind.sqlite3'), 'id')
        writer.assert_called_once_with(Path('local_data/huddlemind.sqlite3'), 'id', sample())
        self.assertIn('Observation ID: 7', out)


if __name__ == '__main__':
    unittest.main()
