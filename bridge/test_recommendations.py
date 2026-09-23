"""Synthetic recommendation lifecycle, isolation, persistence, and CLI checks."""
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
from pathlib import Path
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from bridge.local_store import initialize_database, create_dynasty, save_observation, DATABASE_VERSION
from bridge.recommendation_store import record_recommendation, record_event, list_recommendations, get_recommendation
from bridge.recommendations import main
from bridge.test_dynasty_details import sample


class RecommendationTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name) / 'history.sqlite3'
        initialize_database(self.path)
        self.dynasty = create_dynasty(self.path, 'Sample')
        self.observation = save_observation(self.path, self.dynasty, sample())

    def add(self):
        return record_recommendation(self.path, self.dynasty, self.observation,
                                     "Try the player's backup — test", 'Synthetic rationale', 'test-v1')

    def test_full_lifecycle_retains_advice_and_events_in_order(self):
        identity = self.add()
        before = get_recommendation(self.path, self.dynasty, identity)
        first = record_event(self.path, self.dynasty, identity, 'choice', 'Chose another option')
        second = record_event(self.path, self.dynasty, identity, 'outcome', 'Reported result')
        third = record_event(self.path, self.dynasty, identity, 'outcome', 'Correction to prior report')
        after = get_recommendation(self.path, self.dynasty, identity)
        self.assertEqual({k:v for k,v in before.items() if k != 'events'},
                         {k:v for k,v in after.items() if k != 'events'})
        self.assertEqual([e['event_id'] for e in after['events']], [first, second, third])
        self.assertEqual([e['kind'] for e in after['events']], ['choice', 'outcome', 'outcome'])
        self.assertEqual(after['observation_id'], self.observation)
        self.assertEqual(after['source'], 'test-v1')

    def test_cross_dynasty_and_missing_links_rejected(self):
        other = create_dynasty(self.path, 'Other')
        identity = self.add()
        self.assertIsNone(get_recommendation(self.path, other, identity))
        self.assertEqual(list_recommendations(self.path, other), [])
        for dynasty, observation in ((other, self.observation), (self.dynasty, 999)):
            with self.subTest(dynasty=dynasty), self.assertRaises(ValueError):
                record_recommendation(self.path, dynasty, observation, 'Advice', 'Reason')
        with self.assertRaises(ValueError):
            record_event(self.path, other, identity, 'choice', 'No')
        with self.assertRaises(ValueError):
            record_event(self.path, self.dynasty, 'missing', 'outcome', 'No')
        with self.assertRaises(ValueError):
            list_recommendations(self.path, 'missing')

    def test_blank_values_and_invalid_event_rejected(self):
        for advice, reason, source in (('', 'r', 's'), ('a', ' ', 's'), ('a', 'r', '')):
            with self.subTest(advice=advice), self.assertRaises(ValueError):
                record_recommendation(self.path, self.dynasty, self.observation, advice, reason, source)
        identity = self.add()
        for kind, detail in (('invalid', 'text'), ('choice', ' ')):
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                record_event(self.path, self.dynasty, identity, kind, detail)
        self.assertEqual(get_recommendation(self.path, self.dynasty, identity)['events'], [])

    def test_same_advice_is_a_distinct_occurrence_and_list_is_newest_first(self):
        first, second = self.add(), self.add()
        self.assertNotEqual(first, second)
        self.assertEqual([r[0] for r in list_recommendations(self.path, self.dynasty)], [second, first])

    def test_read_operations_do_not_change_database(self):
        identity = self.add()
        before = self.path.read_bytes()
        get_recommendation(self.path, self.dynasty, identity)
        list_recommendations(self.path, self.dynasty)
        self.assertEqual(self.path.read_bytes(), before)

    def test_old_and_future_versions_rejected(self):
        for version in (1, 99):
            connection = sqlite3.connect(self.path)
            connection.execute(f'PRAGMA user_version={version}')
            connection.close()
            with self.subTest(version=version), self.assertRaises(ValueError):
                self.add()

    def test_event_survives_new_process(self):
        identity = self.add()
        record_event(self.path, self.dynasty, identity, 'outcome', 'Reported outcome')
        code = ('import json,sys; from pathlib import Path; '
                'from bridge.recommendation_store import get_recommendation; '
                'print(json.dumps(get_recommendation(Path(sys.argv[1]),sys.argv[2],sys.argv[3])))')
        run = subprocess.run([sys.executable, '-c', code, str(self.path), self.dynasty, identity],
                             cwd=Path(__file__).resolve().parents[1], capture_output=True,
                             text=True, check=True, timeout=30)
        self.assertEqual(json.loads(run.stdout)['events'][0]['detail'], 'Reported outcome')

    def test_failed_event_rolls_back_and_recovers(self):
        identity = self.add()
        connection = sqlite3.connect(self.path)
        connection.execute("CREATE TRIGGER reject_event AFTER INSERT ON recommendation_events BEGIN SELECT RAISE(ABORT,'test failure'); END")
        connection.commit()
        connection.close()
        with self.assertRaises(sqlite3.IntegrityError):
            record_event(self.path, self.dynasty, identity, 'choice', 'Test')
        self.assertEqual(get_recommendation(self.path, self.dynasty, identity)['events'], [])
        connection = sqlite3.connect(self.path)
        connection.execute('DROP TRIGGER reject_event')
        connection.commit()
        connection.close()
        self.assertIsInstance(record_event(self.path, self.dynasty, identity, 'choice', 'Test'), int)

    def invoke(self, args):
        out, err = StringIO(), StringIO()
        status = 0
        with patch('sys.argv', ['recommendations', *args]), redirect_stdout(out), redirect_stderr(err):
            try:
                main()
            except SystemExit as error:
                status = error.code
        return status, out.getvalue(), err.getvalue()

    def test_cli_lifecycle(self):
        db = ['--database', str(self.path)]
        status, out, err = self.invoke(['add', self.dynasty, str(self.observation), '--advice', 'Test advice', '--rationale', 'Test rationale', *db])
        self.assertEqual((status, err), (0, ''))
        identity = out.strip().split(': ')[1]
        for kind in ('choice', 'outcome'):
            self.assertEqual(self.invoke([kind, self.dynasty, identity, '--detail', 'Reported text', *db])[0], 0)
        status, out, err = self.invoke(['show', self.dynasty, identity, *db])
        self.assertEqual((status, err), (0, ''))
        self.assertEqual(len(json.loads(out)['events']), 2)
        self.assertIn(identity, self.invoke(['list', self.dynasty, *db])[1])

    def test_cli_init_empty_and_missing(self):
        db = ['--database', str(self.path)]
        self.assertIn(f'Version: {DATABASE_VERSION}', self.invoke(['init', *db])[1])
        self.assertEqual(self.invoke(['list', self.dynasty, *db]), (0, 'No recommendations recorded.\n', ''))
        code, out, err = self.invoke(['show', self.dynasty, 'missing', *db])
        self.assertEqual((code, out), (1, ''))
        self.assertIn('not found', err)
        missing = self.path.parent / 'missing.sqlite3'
        self.assertEqual(self.invoke(['list', 'id', '--database', str(missing)])[0], 1)
        self.assertFalse(missing.exists())

    def test_cli_help_and_invalid_arguments(self):
        for args, expected in ((['--help'], 0), ([], 2), (['add', 'id', '1'], 2)):
            with self.subTest(args=args):
                self.assertEqual(self.invoke(args)[0], expected)


if __name__ == '__main__':
    unittest.main()
