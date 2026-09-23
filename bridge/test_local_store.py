"""Exercise SQLite persistence with synthetic snapshots and disposable databases."""
from dataclasses import asdict, replace
from datetime import datetime, timedelta
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

from bridge.local_store import (
    connect_database, create_dynasty, get_dynasty, get_observation,
    initialize_database, list_observations, save_observation,
)
from bridge.test_dynasty_details import sample


class LocalStoreTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / 'nested' / 'history.sqlite3'
        initialize_database(self.path)
        self.dynasty = create_dynasty(self.path, 'Sample Dynasty')
        self.details = sample()

    def test_reinitialization_preserves_records(self):
        identity = save_observation(self.path, self.dynasty, self.details)
        initialize_database(self.path)
        self.assertEqual(get_dynasty(self.path, self.dynasty), (self.dynasty, 'Sample Dynasty'))
        self.assertIsNotNone(get_observation(self.path, self.dynasty, identity))

    def test_names_are_trimmed_and_parameterized(self):
        name = "Coach's Dynasty — 日本語; DROP TABLE dynasties;"
        identity = create_dynasty(self.path, f'  {name}  ')
        self.assertEqual(get_dynasty(self.path, identity), (identity, name))
        self.assertIsNotNone(get_dynasty(self.path, self.dynasty))

    def test_blank_names_rejected(self):
        for name in ('', ' ', '\t\n'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                create_dynasty(self.path, name)

    def test_same_name_still_creates_distinct_dynasties(self):
        second = create_dynasty(self.path, 'Sample Dynasty')
        self.assertNotEqual(second, self.dynasty)
        self.assertIsNotNone(get_dynasty(self.path, second))

    def test_missing_records(self):
        self.assertIsNone(get_dynasty(self.path, 'missing'))
        self.assertIsNone(get_observation(self.path, self.dynasty, 999))
        self.assertEqual(list_observations(self.path, self.dynasty), [])
        self.assertEqual(list_observations(self.path, 'missing'), [])

    def test_complete_json_round_trip(self):
        identity = save_observation(self.path, self.dynasty, self.details)
        # JSON represents dataclass tuples as lists; compare the full payload.
        expected = json.loads(json.dumps(asdict(self.details)))
        self.assertEqual(get_observation(self.path, self.dynasty, identity), expected)
        history = list_observations(self.path, self.dynasty)
        self.assertEqual(history[0][0], identity)
        self.assertEqual(datetime.fromisoformat(history[0][1]).utcoffset(), timedelta(0))

    def test_duplicate_preserves_id_timestamp_and_original_payload(self):
        identity = save_observation(self.path, self.dynasty, self.details)
        original = get_observation(self.path, self.dynasty, identity)
        history = list_observations(self.path, self.dynasty)
        altered = replace(self.details, schedule=())
        self.assertEqual(save_observation(self.path, self.dynasty, altered), identity)
        self.assertEqual(list_observations(self.path, self.dynasty), history)
        self.assertEqual(get_observation(self.path, self.dynasty, identity), original)

    def test_changed_hashes_create_new_observations_in_insertion_order(self):
        first = save_observation(self.path, self.dynasty, self.details)
        new_save = replace(self.details, roster=replace(self.details.roster, save_sha256='new-save'))
        second = save_observation(self.path, self.dynasty, new_save)
        new_schema = replace(self.details, roster=replace(self.details.roster, schema_sha256='new-schema'))
        third = save_observation(self.path, self.dynasty, new_schema)
        self.assertEqual([row[0] for row in list_observations(self.path, self.dynasty)],
                         [third, second, first])
        self.assertEqual(len({first, second, third}), 3)

    def test_dynasty_isolation_with_identical_source_hashes(self):
        other = create_dynasty(self.path, 'Other Dynasty')
        first = save_observation(self.path, self.dynasty, self.details)
        second = save_observation(self.path, other, self.details)
        self.assertNotEqual(first, second)
        self.assertIsNone(get_observation(self.path, other, first))
        self.assertIsNone(get_observation(self.path, self.dynasty, second))
        self.assertEqual([row[0] for row in list_observations(self.path, other)], [second])

    def test_foreign_keys_enabled_on_each_connection(self):
        for _ in range(2):
            connection = connect_database(self.path)
            try:
                self.assertEqual(connection.execute('PRAGMA foreign_keys').fetchone()[0], 1)
            finally:
                connection.close()

    def test_nonexistent_dynasty_rejected_and_writer_recovers(self):
        with self.assertRaises(sqlite3.IntegrityError):
            save_observation(self.path, 'missing', self.details)
        self.assertEqual(list_observations(self.path, 'missing'), [])
        identity = save_observation(self.path, self.dynasty, self.details)
        self.assertIsNotNone(get_observation(self.path, self.dynasty, identity))

    def test_insert_failure_rolls_back_and_releases_connection(self):
        connection = connect_database(self.path)
        try:
            connection.execute("""CREATE TRIGGER reject_observation AFTER INSERT ON observations
                BEGIN SELECT RAISE(ABORT, 'intentional write failure'); END""")
            connection.commit()
        finally:
            connection.close()
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'intentional write failure'):
            save_observation(self.path, self.dynasty, self.details)
        self.assertEqual(list_observations(self.path, self.dynasty), [])
        connection = connect_database(self.path)
        try:
            connection.execute('DROP TRIGGER reject_observation')
            connection.commit()
        finally:
            connection.close()
        self.assertIsInstance(save_observation(self.path, self.dynasty, self.details), int)

    def test_observation_survives_a_new_python_process(self):
        identity = save_observation(self.path, self.dynasty, self.details)
        code = (
            'import json,sys; from pathlib import Path; '
            'from bridge.local_store import get_observation; '
            'print(json.dumps(get_observation(Path(sys.argv[1]), sys.argv[2], int(sys.argv[3]))))'
        )
        result = subprocess.run([sys.executable, '-c', code, str(self.path), self.dynasty, str(identity)],
                                cwd=Path(__file__).resolve().parents[1], capture_output=True,
                                text=True, check=True, timeout=30)
        self.assertEqual(json.loads(result.stdout), get_observation(self.path, self.dynasty, identity))


if __name__ == '__main__':
    unittest.main()
