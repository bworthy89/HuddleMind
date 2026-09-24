from contextlib import closing
import sqlite3
import unittest
from unittest.mock import patch

from bridge import test_outbox
from bridge.local_store import initialize_database
from bridge.outbox import list_pending_events, mark_delivered
from bridge.send_observations import receiver_address, receiver_origin


class DestinationTests(unittest.TestCase):
    setUp = test_outbox.OutboxTests.setUp
    queue = test_outbox.OutboxTests.queue
    execute = test_outbox.OutboxTests.execute
    def test_two_destinations_have_independent_receipts(self):
        event = self.queue()
        mark_delivered(self.path, self.dynasty, event, 'https://one.example')
        self.assertEqual(list_pending_events(self.path, self.dynasty, 'https://one.example'), ())
        pending = list_pending_events(self.path, self.dynasty, 'https://two.example')
        self.assertEqual(pending[0].event_json, event.event_json)
        mark_delivered(self.path, self.dynasty, event, 'https://two.example')
        self.assertEqual(list_pending_events(self.path, self.dynasty, 'https://two.example'), ())
        with closing(sqlite3.connect(self.path)) as connection:
            before = connection.execute('SELECT * FROM sync_deliveries ORDER BY receiver').fetchall()
        mark_delivered(self.path, self.dynasty, event, 'https://two.example')
        with closing(sqlite3.connect(self.path)) as connection:
            self.assertEqual(connection.execute('SELECT * FROM sync_deliveries ORDER BY receiver').fetchall(), before)

    def test_v3_upgrade_preserves_legacy_ack_and_exact_event(self):
        event = self.queue()
        mark_delivered(self.path, self.dynasty, event)
        before = self.queue()
        self.execute('DROP TABLE sync_deliveries; PRAGMA user_version=3;')
        initialize_database(self.path)
        self.assertEqual(self.queue(), before)
        self.assertEqual(list_pending_events(self.path, self.dynasty, 'https://new.example'), (before,))

    def test_migration_validation_failure_rolls_back(self):
        self.execute('DROP TABLE sync_deliveries; PRAGMA user_version=3;')
        with patch('bridge.delivery_schema.validate_schema', side_effect=ValueError('test')):
            with self.assertRaises(ValueError):
                initialize_database(self.path)
        with closing(sqlite3.connect(self.path)) as connection:
            self.assertEqual(connection.execute('PRAGMA user_version').fetchone()[0], 3)
            self.assertIsNone(connection.execute("SELECT name FROM sqlite_master WHERE name='sync_deliveries'").fetchone())

    def test_origin_normalization(self):
        self.assertEqual(receiver_origin(receiver_address('https://EXAMPLE.com:443/')), 'https://example.com')
        self.assertEqual(receiver_origin(receiver_address('http://[::1]:8765')), 'http://[::1]:8765')
