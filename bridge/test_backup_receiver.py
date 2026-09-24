from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest

from bridge.backup_receiver import backup_receiver, inspect_database, verify_restore
from bridge.receiver_store import initialize_receiver, store_event


class ReceiverBackupTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.source = self.root / 'receiver.sqlite3'
        self.backups = self.root / 'backups'
        initialize_receiver(self.source)

    def test_committed_wal_data_restores_and_duplicate_remains_idempotent(self):
        with closing(sqlite3.connect(self.source)) as connection:
            connection.execute('PRAGMA journal_mode=WAL')
            event = {'event_id': 'sample', 'dynasty_id': 'dynasty'}
            store_event(self.source, 'owner', event)
            target, count = backup_receiver(self.source, self.backups)
            self.assertEqual(count, 1)
            self.assertEqual(inspect_database(target), inspect_database(self.source))
            self.assertEqual(verify_restore(target), 1)
            self.assertEqual(store_event(target, 'owner', event), 'already_stored')

    def test_missing_source_does_not_create_database_or_partial_backup(self):
        missing = self.root / 'missing.sqlite3'
        with self.assertRaises(sqlite3.Error):
            backup_receiver(missing, self.backups)
        self.assertFalse(missing.exists())
        self.assertEqual(list(self.backups.iterdir()), [])

    def test_wrong_database_does_not_prune_existing_backups(self):
        target, _ = backup_receiver(self.source, self.backups, keep=1)
        wrong = self.root / 'wrong.sqlite3'
        with closing(sqlite3.connect(wrong)) as db:
            db.execute('CREATE TABLE unrelated (value TEXT)')
        with self.assertRaises(ValueError):
            backup_receiver(wrong, self.backups, keep=1)
        self.assertEqual(list(self.backups.iterdir()), [target])

    def test_retention_preserves_unrelated_files(self):
        first, _ = backup_receiver(self.source, self.backups, keep=1)
        unrelated = self.backups / 'receiver-important.sqlite3'
        unrelated.write_text('preserve')
        second, _ = backup_receiver(self.source, self.backups, keep=1)
        self.assertFalse(first.exists())
        self.assertTrue(second.exists())
        self.assertEqual(unrelated.read_text(), 'preserve')

    def test_invalid_retention_rejected(self):
        with self.assertRaises(ValueError):
            backup_receiver(self.source, self.backups, keep=0)


if __name__ == '__main__':
    unittest.main()
