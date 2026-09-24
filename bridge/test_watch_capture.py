"""Readiness, recovery, and atomic queue tests use only temporary synthetic data."""
from contextlib import closing
from dataclasses import replace
import hashlib
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import Mock, patch

from bridge.local_store import initialize_database, create_dynasty, save_observation
from bridge.outbox import list_pending_events
from bridge.test_dynasty_details import sample
from bridge.watch_capture import CaptureWatcher, capture, signature


class WatchCaptureTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.save = self.root / 'DYNASTY-TEST'
        self.save.write_bytes(b'first')
        self.schema = self.root / 'schema.gz'
        self.schema.write_bytes(b'schema')
        self.db = self.root / 'history.sqlite3'
        initialize_database(self.db)
        self.dynasty = create_dynasty(self.db, 'Synthetic')
        self.messages = []

    def details(self, save, schema):
        value = sample()
        return replace(value, roster=replace(value.roster,
            save_sha256=hashlib.sha256(save.read_bytes()).hexdigest(),
            schema_sha256=hashlib.sha256(schema.read_bytes()).hexdigest()))

    def capture(self):
        return capture(self.save, self.schema, self.db, self.dynasty, signature(self.save))

    def count(self, table):
        with closing(sqlite3.connect(self.db)) as db:
            return db.execute(f'SELECT count(*) FROM {table}').fetchone()[0]

    def test_quiet_period_restarts_and_unchanged_file_is_not_reprocessed(self):
        callback = Mock(return_value=1)
        watcher = CaptureWatcher(self.save, callback, report=self.messages.append)
        watcher.poll(0)
        watcher.poll(2)
        callback.assert_not_called()
        self.save.write_bytes(b'longer save')
        watcher.poll(3)
        watcher.poll(5)
        callback.assert_not_called()
        watcher.poll(6)
        watcher.poll(20)
        callback.assert_called_once()

    def test_read_failure_retries_without_another_file_event(self):
        callback = Mock(side_effect=[PermissionError('locked'), 1])
        watcher = CaptureWatcher(self.save, callback, report=self.messages.append)
        for now in (0, 3, 4, 5):
            watcher.poll(now)
        self.assertEqual(callback.call_count, 2)
        self.assertIn('Captured and queued', self.messages[-1])

    def test_exhaustion_stops_and_new_contents_rearm(self):
        callback = Mock(side_effect=ValueError('incomplete'))
        watcher = CaptureWatcher(self.save, callback, attempts=2, report=self.messages.append)
        for now in (0, 3, 5, 100):
            watcher.poll(now)
        self.assertEqual(callback.call_count, 2)
        self.assertIn('needs attention', self.messages[-1])
        self.save.write_bytes(b'new bytes')
        watcher.poll(101)
        watcher.poll(104)
        self.assertEqual(callback.call_count, 3)

    def test_disappearance_and_atomic_replacement_are_recovered(self):
        callback = Mock(return_value=1)
        watcher = CaptureWatcher(self.save, callback, report=self.messages.append)
        watcher.poll(0)
        self.save.unlink()
        watcher.poll(3)
        replacement = self.root / 'temporary'
        replacement.write_bytes(b'replaced')
        replacement.replace(self.save)
        watcher.poll(4)
        watcher.poll(7)
        callback.assert_called_once()

    def test_duplicate_and_restart_reuse_one_observation_and_event(self):
        with patch('bridge.watch_capture.load_dynasty', side_effect=self.details):
            first = self.capture()
            original = list_pending_events(self.db, self.dynasty)
            self.assertEqual(self.capture(), first)
            self.assertEqual(list_pending_events(self.db, self.dynasty), original)
            self.save.write_bytes(b'next save')
            self.assertNotEqual(self.capture(), first)
        self.assertEqual(self.count('observations'), 2)
        self.assertEqual(self.count('sync_outbox'), 2)

    def test_write_during_parsing_is_not_persisted(self):
        def changed(save, schema):
            result = self.details(save, schema)
            self.save.write_bytes(b'write in progress')
            return result
        with patch('bridge.watch_capture.load_dynasty', side_effect=changed):
            with self.assertRaisesRegex(ValueError, 'changed during'):
                self.capture()
        self.assertEqual(self.count('observations'), 0)

    def test_parse_failure_does_not_create_observation(self):
        with self.assertRaises(ValueError):
            self.capture()
        self.assertEqual(self.count('observations'), 0)

    def test_queue_failure_rolls_back_observation_and_can_retry(self):
        with patch('bridge.watch_capture.load_dynasty', side_effect=self.details):
            with patch('bridge.outbox.queue_on_connection', side_effect=sqlite3.OperationalError('locked')):
                with self.assertRaises(sqlite3.Error):
                    self.capture()
            self.assertEqual(self.count('observations'), 0)
            self.capture()
        self.assertEqual(self.count('sync_outbox'), 1)

    def test_existing_unqueued_observation_gets_queued(self):
        existing = save_observation(self.db, self.dynasty, self.details(self.save, self.schema))
        with patch('bridge.watch_capture.load_dynasty', side_effect=self.details):
            self.assertEqual(self.capture(), existing)
        self.assertEqual(self.count('observations'), 1)
        self.assertEqual(self.count('sync_outbox'), 1)


if __name__ == '__main__':
    unittest.main()
