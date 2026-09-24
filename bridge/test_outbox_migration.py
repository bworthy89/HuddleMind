"""Version-3 outbox migration checks using disposable history databases."""
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from bridge.local_store import initialize_database, DATABASE_VERSION
from bridge.outbox_schema import validate_outbox_schema


class OutboxMigrationTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name) / 'history.sqlite3'

    def execute(self, sql):
        connection = sqlite3.connect(self.path)
        try:
            connection.executescript(sql)
        finally:
            connection.close()

    def state(self):
        connection = sqlite3.connect(self.path)
        try:
            return (connection.execute('PRAGMA user_version').fetchone()[0],
                    tuple(connection.iterdump()))
        finally:
            connection.close()

    def legacy(self):
        initialize_database(self.path)
        self.execute("""DROP TABLE sync_deliveries; DROP TABLE sync_outbox;
            INSERT INTO dynasties VALUES ('d','Sample');
            INSERT INTO observations VALUES (1,'d','original time','save','schema','{}');
            INSERT INTO recommendations VALUES ('r',1,'time','advice','reason','manual');
            INSERT INTO recommendation_events VALUES (1,'r','time','choice','choice text','manual');
            PRAGMA user_version=2;""")

    def test_fresh_initialization_is_silent_and_version_three(self):
        output = StringIO()
        with redirect_stdout(output):
            initialize_database(self.path)
        self.assertEqual(output.getvalue(), '')
        self.assertEqual(self.state()[0], DATABASE_VERSION)
        connection = sqlite3.connect(self.path)
        try:
            validate_outbox_schema(connection)
            self.assertEqual(connection.execute('SELECT count(*) FROM sync_outbox').fetchone()[0], 0)
        finally:
            connection.close()

    def test_upgrade_preserves_all_existing_history(self):
        self.legacy()
        connection = sqlite3.connect(self.path)
        names = ('dynasties', 'observations', 'recommendations', 'recommendation_events')
        before = {name: connection.execute(f'SELECT * FROM {name}').fetchall() for name in names}
        connection.close()
        initialize_database(self.path)
        connection = sqlite3.connect(self.path)
        try:
            after = {name: connection.execute(f'SELECT * FROM {name}').fetchall() for name in names}
            self.assertEqual(before, after)
            self.assertEqual(connection.execute('PRAGMA user_version').fetchone()[0], DATABASE_VERSION)
        finally:
            connection.close()

    def test_repeat_initialization_preserves_queued_message(self):
        self.legacy()
        initialize_database(self.path)
        self.execute("INSERT INTO sync_outbox VALUES ('event',1,1,'exact message','time',NULL);")
        before = self.state()
        initialize_database(self.path)
        self.assertEqual(self.state(), before)

    def test_invalid_structure_rejected_without_changes(self):
        initialize_database(self.path)
        self.execute('DROP TABLE sync_deliveries; DROP TABLE sync_outbox; CREATE TABLE sync_outbox (wrong TEXT);')
        before = self.state()
        with self.assertRaisesRegex(ValueError, 'structure'):
            initialize_database(self.path)
        self.assertEqual(self.state(), before)

    def test_missing_version_three_table_rejected(self):
        initialize_database(self.path)
        self.execute('DROP TABLE sync_deliveries; DROP TABLE sync_outbox;')
        with self.assertRaisesRegex(ValueError, 'Missing sync outbox'):
            initialize_database(self.path)

    def test_orphan_rejected_without_changes(self):
        initialize_database(self.path)
        self.execute("INSERT INTO sync_outbox VALUES ('event',999,1,'{}','time',NULL);")
        before = self.state()
        with self.assertRaisesRegex(ValueError, 'invalid observation'):
            initialize_database(self.path)
        self.assertEqual(self.state(), before)

    def test_failed_upgrade_rolls_back_ddl_and_version(self):
        self.legacy()
        before = self.state()
        with patch('bridge.outbox_schema.validate_outbox_schema', side_effect=ValueError('injected')):
            with self.assertRaisesRegex(ValueError, 'injected'):
                initialize_database(self.path)
        self.assertEqual(self.state(), before)

    def test_constraints_protect_observation_and_contract_pair(self):
        self.legacy()
        initialize_database(self.path)
        connection = sqlite3.connect(self.path)
        try:
            connection.execute('PRAGMA foreign_keys=ON')
            connection.execute("INSERT INTO sync_outbox VALUES ('event',1,1,'{}','time',NULL)")
            for values in (('different',1,1), ('event',1,2), ('orphan',999,1)):
                with self.subTest(values=values), self.assertRaises(sqlite3.IntegrityError):
                    connection.execute("INSERT INTO sync_outbox VALUES (?,?,?,'{}','time',NULL)", values)
            connection.execute("INSERT INTO sync_outbox VALUES ('new-version',1,2,'{}','time',NULL)")
            self.assertEqual(connection.execute('SELECT count(*) FROM sync_outbox').fetchone()[0], 2)
        finally:
            connection.close()


if __name__ == '__main__':
    unittest.main()
