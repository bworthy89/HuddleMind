"""Migration failures must preserve the previous database and version."""
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from bridge.local_store import initialize_database, DATABASE_VERSION


class MigrationTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name) / 'history.sqlite3'

    def execute(self, sql):
        with sqlite3.connect(self.path) as connection:
            connection.executescript(sql)
        connection.close()

    def state(self):
        connection = sqlite3.connect(self.path)
        try:
            return (connection.execute('PRAGMA user_version').fetchone()[0],
                    connection.execute("SELECT name, sql FROM sqlite_master ORDER BY name").fetchall())
        finally:
            connection.close()

    def test_fresh_and_repeated_initialization(self):
        initialize_database(self.path)
        before = self.state()
        self.assertEqual(before[0], DATABASE_VERSION)
        initialize_database(self.path)
        self.assertEqual(self.state(), before)

    def test_legacy_upgrade_preserves_records(self):
        initialize_database(self.path)
        self.execute("INSERT INTO dynasties VALUES ('id','Sample'); DROP TABLE sync_deliveries; DROP TABLE sync_outbox; DROP TABLE recommendation_events; DROP TABLE recommendations; PRAGMA user_version=0;")
        initialize_database(self.path)
        connection = sqlite3.connect(self.path)
        try:
            self.assertEqual(connection.execute('SELECT * FROM dynasties').fetchall(), [('id', 'Sample')])
            self.assertEqual(connection.execute('PRAGMA user_version').fetchone()[0], DATABASE_VERSION)
        finally:
            connection.close()

    def test_newer_version_is_untouched(self):
        self.execute(f'PRAGMA user_version={DATABASE_VERSION + 1};')
        before = self.state()
        with self.assertRaisesRegex(ValueError, 'newer'):
            initialize_database(self.path)
        self.assertEqual(self.state(), before)

    def test_bad_columns_roll_back_new_tables(self):
        self.execute('CREATE TABLE dynasties (wrong TEXT);')
        before = self.state()
        with self.assertRaisesRegex(ValueError, 'column structure'):
            initialize_database(self.path)
        self.assertEqual(self.state(), before)

    def test_missing_relationship_rejected(self):
        initialize_database(self.path)
        self.execute('DROP TABLE observations; CREATE TABLE observations ('
                     'observation_id INTEGER PRIMARY KEY, dynasty_id TEXT NOT NULL,'
                     'observed_at TEXT NOT NULL, save_sha256 TEXT NOT NULL,'
                     'schema_sha256 TEXT NOT NULL, snapshot_json TEXT NOT NULL); PRAGMA user_version=0;')
        before = self.state()
        with self.assertRaisesRegex(ValueError, 'foreign-key'):
            initialize_database(self.path)
        self.assertEqual(self.state(), before)

    def test_orphan_observation_rejected(self):
        initialize_database(self.path)
        self.execute("INSERT INTO observations VALUES (1,'missing','time','save','schema','{}'); PRAGMA user_version=0;")
        before = self.state()
        with self.assertRaisesRegex(ValueError, 'invalid dynasty'):
            initialize_database(self.path)
        self.assertEqual(self.state(), before)

    def test_failed_validation_rolls_back_all_ddl(self):
        with patch('bridge.local_store.validate_database_relationships', side_effect=ValueError('injected')):
            with self.assertRaisesRegex(ValueError, 'injected'):
                initialize_database(self.path)
        self.assertEqual(self.state(), (0, []))

    def test_version_one_upgrade_preserves_full_observation(self):
        initialize_database(self.path)
        self.execute("DROP TABLE sync_deliveries; DROP TABLE sync_outbox; DROP TABLE recommendation_events; DROP TABLE recommendations;"
                     "INSERT INTO dynasties VALUES ('id','Sample');"
                     "INSERT INTO observations VALUES (1,'id','original time','hash','schema','{\"sample\":true}');"
                     "PRAGMA user_version=1;")
        initialize_database(self.path)
        connection = sqlite3.connect(self.path)
        try:
            self.assertEqual(connection.execute('SELECT * FROM observations').fetchall(),
                             [(1, 'id', 'original time', 'hash', 'schema', '{"sample":true}')])
            self.assertEqual(connection.execute('PRAGMA user_version').fetchone()[0], DATABASE_VERSION)
        finally:
            connection.close()

    def test_version_two_validation_failure_rolls_back_new_tables(self):
        initialize_database(self.path)
        self.execute('DROP TABLE sync_deliveries; DROP TABLE sync_outbox; DROP TABLE recommendation_events; DROP TABLE recommendations; PRAGMA user_version=1;')
        before = self.state()
        with patch('bridge.recommendation_schema.validate_schema', side_effect=ValueError('injected')):
            with self.assertRaisesRegex(ValueError, 'injected'):
                initialize_database(self.path)
        self.assertEqual(self.state(), before)

    def test_missing_unique_constraint_rejected(self):
        initialize_database(self.path)
        self.execute('DROP TABLE observations; CREATE TABLE observations ('
                     'observation_id INTEGER PRIMARY KEY, dynasty_id TEXT NOT NULL REFERENCES dynasties(dynasty_id),'
                     'observed_at TEXT NOT NULL, save_sha256 TEXT NOT NULL,'
                     'schema_sha256 TEXT NOT NULL, snapshot_json TEXT NOT NULL);')
        with self.assertRaisesRegex(ValueError, 'duplicate-prevention'):
            initialize_database(self.path)


if __name__ == '__main__':
    unittest.main()
