"""Queue persistence, concurrency and failures using synthetic observations."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stdout, redirect_stderr
from dataclasses import replace
from io import StringIO
from pathlib import Path
import json
import sqlite3
import subprocess
import sys
import tempfile
from threading import Barrier
import unittest
from unittest.mock import patch

from bridge.local_store import initialize_database, create_dynasty, save_observation
from bridge.outbox import queue_observation, list_pending_events
from bridge.queue_observation import main
from bridge.test_dynasty_details import sample


class OutboxTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name) / 'history.sqlite3'
        initialize_database(self.path)
        self.dynasty = create_dynasty(self.path, 'Sample')
        self.observation = save_observation(self.path, self.dynasty, sample())

    def queue(self):
        return queue_observation(self.path, self.dynasty, self.observation)

    def execute(self, sql):
        connection = sqlite3.connect(self.path)
        try:
            connection.executescript(sql)
        finally:
            connection.close()

    def test_queue_preserves_capture_and_payload_and_reuses_exact_message(self):
        first = self.queue()
        with patch('bridge.outbox.uuid4', side_effect=AssertionError('Must not rebuild')):
            self.assertEqual(self.queue(), first)
        decoded = json.loads(first.event_json)
        self.assertEqual(decoded['event_id'], first.event_id)
        self.assertEqual(decoded['dynasty_id'], self.dynasty)
        self.assertEqual(decoded['payload']['roster']['team']['name'], 'Sample Team')
        self.assertIsNone(first.delivered_at)
        self.assertEqual(list_pending_events(self.path, self.dynasty), (first,))
        connection = sqlite3.connect(self.path)
        try:
            self.assertEqual(decoded['observed_at'], connection.execute('SELECT observed_at FROM observations').fetchone()[0])
        finally:
            connection.close()

    def test_concurrent_queue_attempts_return_one_event(self):
        barrier = Barrier(4)
        def attempt(_):
            barrier.wait(timeout=10)
            return self.queue()
        with ThreadPoolExecutor(max_workers=4) as workers:
            results = list(workers.map(attempt, range(4)))
        self.assertTrue(all(event == results[0] for event in results))
        self.assertEqual(len(list_pending_events(self.path, self.dynasty)), 1)

    def test_restart_reuses_original_json(self):
        first = self.queue()
        script = ('import sys,json; from pathlib import Path; from dataclasses import asdict; '
                  'from bridge.outbox import queue_observation; '
                  'print(json.dumps(asdict(queue_observation(Path(sys.argv[1]),sys.argv[2],int(sys.argv[3])))))')
        run = subprocess.run([sys.executable, '-c', script, str(self.path), self.dynasty, str(self.observation)],
                             cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, check=True, timeout=30)
        result = json.loads(run.stdout)
        self.assertEqual(result['event_id'], first.event_id)
        self.assertEqual(result['event_json'], first.event_json)
        self.assertEqual(result['queued_at'], first.queued_at)

    def test_dynasty_isolation_and_missing_records(self):
        other = create_dynasty(self.path, 'Other')
        self.queue()
        for dynasty, observation in ((other, self.observation), (self.dynasty, 999)):
            with self.subTest(dynasty=dynasty), self.assertRaises(ValueError):
                queue_observation(self.path, dynasty, observation)
        self.assertEqual(list_pending_events(self.path, other), ())
        with self.assertRaises(ValueError):
            list_pending_events(self.path, 'missing')

    def test_delivered_event_is_not_requeued(self):
        first = self.queue()
        self.execute("UPDATE sync_outbox SET delivered_at='acknowledged time';")
        repeated = self.queue()
        self.assertEqual(repeated.event_json, first.event_json)
        self.assertEqual(repeated.delivered_at, 'acknowledged time')
        self.assertEqual(list_pending_events(self.path, self.dynasty), ())

    def test_distinct_observations_are_listed_in_queue_order(self):
        first = self.queue()
        details = sample()
        second_id = save_observation(self.path, self.dynasty,
                                    replace(details, roster=replace(details.roster, save_sha256='new')))
        second = queue_observation(self.path, self.dynasty, second_id)
        self.assertEqual(list_pending_events(self.path, self.dynasty), (first, second))
        self.assertNotEqual(first.event_id, second.event_id)

    def test_serialization_failure_leaves_no_queued_row(self):
        with patch('bridge.outbox.serialize_observation_event', side_effect=ValueError('invalid JSON')):
            with self.assertRaises(ValueError):
                self.queue()
        self.assertEqual(list_pending_events(self.path, self.dynasty), ())
        self.queue()

    def test_insert_failure_rolls_back_and_writer_recovers(self):
        self.execute("CREATE TRIGGER fail_queue AFTER INSERT ON sync_outbox BEGIN SELECT RAISE(ABORT,'injected'); END;")
        with self.assertRaises(sqlite3.IntegrityError):
            self.queue()
        self.assertEqual(list_pending_events(self.path, self.dynasty), ())
        self.execute('DROP TRIGGER fail_queue;')
        self.queue()

    def test_missing_and_wrong_version_database_rejected(self):
        missing = self.path.parent / 'missing.sqlite3'
        with self.assertRaises(ValueError):
            queue_observation(missing, self.dynasty, 1)
        self.assertFalse(missing.exists())
        for version in (2, 99):
            self.execute(f'PRAGMA user_version={version};')
            with self.subTest(version=version), self.assertRaises(ValueError):
                self.queue()

    def invoke(self, args):
        out, err = StringIO(), StringIO()
        code = 0
        with patch('sys.argv', ['queue_observation', *args]), redirect_stdout(out), redirect_stderr(err):
            try:
                main()
            except SystemExit as error:
                code = error.code
        return code, out.getvalue(), err.getvalue()

    def test_cli_success_and_duplicate(self):
        args = [self.dynasty, str(self.observation), '--database', str(self.path)]
        first = self.invoke(args)
        self.assertEqual(first[0], 0)
        self.assertEqual(first[2], '')
        self.assertIn('Status: pending', first[1])
        self.assertEqual(self.invoke(args), first)

    def test_cli_errors_help_and_arguments(self):
        code, out, err = self.invoke(['missing', '1', '--database', str(self.path)])
        self.assertEqual((code, out), (1, ''))
        self.assertIn('Could not queue observation:', err)
        for args, code in ((['--help'], 0), ([], 2), (['id', 'bad-number'], 2)):
            with self.subTest(args=args), patch('bridge.queue_observation.queue_observation') as queue:
                self.assertEqual(self.invoke(args)[0], code)
                queue.assert_not_called()


if __name__ == '__main__':
    unittest.main()
