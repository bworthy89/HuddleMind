"""Check JSON exports using only synthetic data and temporary files."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from bridge.models import Coach, DynastySnapshot, Player, RecordId, Team
from bridge.snapshot_export import snapshot_to_dict, write_snapshot_json


class SnapshotExportTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = DynastySnapshot(
            'sample-save-hash', 'sample-schema-hash',
            Coach(RecordId(2, 3), 'Sample', 'Coach', 5, True),
            Team(RecordId(4, 6), 5, 'Sample Team', (
                Player(RecordId(7, 8), 'José', 'Sample', 'QB', 85),
            )),
        )

    def test_dictionary_is_independent_of_snapshot(self):
        data = snapshot_to_dict(self.snapshot)
        data['team']['players'][0]['first_name'] = 'Changed'
        self.assertEqual(self.snapshot.team.players[0].first_name, 'José')

    def test_round_trip_preserves_values_and_unicode(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'snapshot.json'
            write_snapshot_json(self.snapshot, path)
            text = path.read_text(encoding='utf-8')
            data = json.loads(text)
        self.assertIn('José', text)
        self.assertTrue(text.endswith('\n'))
        self.assertEqual(data, {
            'save_sha256': 'sample-save-hash',
            'schema_sha256': 'sample-schema-hash',
            'coach': {'record_id': {'table_id': 2, 'row_id': 3},
                      'first_name': 'Sample', 'last_name': 'Coach',
                      'team_index': 5, 'is_user_controlled': True},
            'team': {'record_id': {'table_id': 4, 'row_id': 6},
                     'team_index': 5, 'name': 'Sample Team', 'players': [
                         {'record_id': {'table_id': 7, 'row_id': 8},
                          'first_name': 'José', 'last_name': 'Sample',
                          'position': 'QB', 'overall': 85},
                     ]},
        })

    def test_existing_file_stays_unchanged(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'existing.json'
            original = b'Existing file: must remain unchanged\x00\xff'
            path.write_bytes(original)
            with self.assertRaises(FileExistsError):
                write_snapshot_json(self.snapshot, path)
            self.assertEqual(path.read_bytes(), original)

    def test_missing_parent_raises_without_creating_directories(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'missing' / 'snapshot.json'
            with self.assertRaises(FileNotFoundError):
                write_snapshot_json(self.snapshot, path)
            self.assertFalse(path.parent.exists())


if __name__ == '__main__':
    unittest.main()
